"""Camada de acesso ao banco de dados SQLite.

Gerencia a conexao, o esquema inicial e as consultas de tickets e SLA.
Todas as funcoes sao deterministas e nao possuem efeito colateral escondido.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

# Severidades suportadas e seus prazos de SLA em horas.
SLA_HOURS_BY_SEVERITY: dict[str, int] = {
    "critical": 4,
    "high": 8,
    "medium": 24,
    "low": 72,
}

VALID_SEVERITIES: frozenset[str] = frozenset(SLA_HOURS_BY_SEVERITY.keys())
VALID_STATUSES: frozenset[str] = frozenset({"open", "in_progress", "resolved", "closed"})


def get_db_path() -> Path:
    """Retorna o caminho do arquivo do banco de dados."""
    return Path(__file__).resolve().parent.parent / "data" / "sla_helpdesk.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Abre (e cria, se necessario) a conexao com o SQLite.

    Args:
        db_path: Caminho do banco. Se None, usa o padrao do projeto.

    Returns:
        Conexao SQLite aberta com row_factory habilitado.
    """
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Cria as tabelas se ainda nao existirem.

    Args:
        conn: Conexao SQLite aberta.
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
            status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT
        );
        """
    )
    conn.commit()


def create_ticket(
    conn: sqlite3.Connection,
    *,
    title: str,
    description: str = "",
    severity: str = "medium",
    status: str = "open",
    created_at: Optional[str] = None,
) -> int:
    """Insere um novo ticket e retorna o seu id.

    Args:
        conn: Conexao SQLite aberta.
        title: Titulo do ticket.
        description: Descricao opcional.
        severity: Nivel de severidade (critical, high, medium, low).
        status: Status inicial (default 'open').
        created_at: Timestamp ISO 8601. Se None, usa agora.

    Returns:
        ID do ticket criado.
    """
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"severidade invalida: {severity}")
    if status not in VALID_STATUSES:
        raise ValueError(f"status invalido: {status}")

    now = created_at or datetime.utcnow().isoformat()
    cursor = conn.execute(
        """
        INSERT INTO tickets (title, description, severity, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, description, severity, status, now, now),
    )
    conn.commit()
    return cursor.lastrowid


def update_ticket_status(
    conn: sqlite3.Connection,
    ticket_id: int,
    status: str,
    resolved_at: Optional[str] = None,
) -> None:
    """Atualiza o status de um ticket.

    Args:
        conn: Conexao SQLite aberta.
        ticket_id: ID do ticket.
        status: Novo status.
        resolved_at: Data de resolucao (obrigatorio se status for 'resolved' ou 'closed').

    Raises:
        ValueError: Se o status for invalido.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"status invalido: {status}")

    now = datetime.utcnow().isoformat()
    if status in ("resolved", "closed") and resolved_at is None:
        resolved_at = now

    conn.execute(
        """
        UPDATE tickets
        SET status = ?, updated_at = ?, resolved_at = ?
        WHERE id = ?
        """,
        (status, now, resolved_at, ticket_id),
    )
    conn.commit()


def get_ticket(conn: sqlite3.Connection, ticket_id: int) -> Optional[sqlite3.Row]:
    """Retorna um ticket pelo id, ou None se nao existir."""
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return row


def list_tickets(
    conn: sqlite3.Connection,
    *,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[sqlite3.Row]:
    """Lista tickets, com filtros opcionais de status e severidade.

    Args:
        conn: Conexao SQLite aberta.
        status: Filtrar por status (open, in_progress, resolved, closed).
        severity: Filtrar por severidade (critical, high, medium, low).

    Returns:
        Lista de linhas do banco ordenadas por created_at descendente.
    """
    query = "SELECT * FROM tickets"
    params: list[str] = []
    conditions: list[str] = []

    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"status invalido: {status}")
        conditions.append("status = ?")
        params.append(status)

    if severity is not None:
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"severidade invalida: {severity}")
        conditions.append("severity = ?")
        params.append(severity)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC"
    return conn.execute(query, params).fetchall()


def compute_sla_hours(severity: str) -> int:
    """Retorna o prazo de SLA em horas para uma severidade.

    Args:
        severity: Nivel de severidade.

    Returns:
        Horas de SLA.

    Raises:
        ValueError: Se a severidade for invalida.
    """
    if severity not in VALID_SEVERITIES:
        raise ValueError(f"severidade invalida: {severity}")
    return SLA_HOURS_BY_SEVERITY[severity]


def is_within_sla(created_at: str, resolved_at: str, severity: str) -> bool:
    """Verifica se a resolucao ocorreu dentro do prazo de SLA.

    Args:
        created_at: Timestamp de criacao (ISO 8601).
        resolved_at: Timestamp de resolucao (ISO 8601).
        severity: Nivel de severidade.

    Returns:
        True se dentro do SLA, False caso contrario.
    """
    sla_hours = compute_sla_hours(severity)
    start = datetime.fromisoformat(created_at)
    end = datetime.fromisoformat(resolved_at)
    return (end - start).total_seconds() <= sla_hours * 3600


def get_kpis(conn: sqlite3.Connection) -> dict[str, object]:
    """Calcula os indicadores-chave de desempenho (KPIs) do dashboard.

    Args:
        conn: Conexao SQLite aberta.

    Returns:
        Dicionario com total_tickets, tickets_abertos, tickets_resolvidos,
        tickets_fechados, tempo_medio_resolucao_horas, taxa_cumprimento_sla,
        e sla_por_severidade.
    """
    rows = list_tickets(conn)

    total = len(rows)
    abertos = sum(1 for r in rows if r["status"] == "open")
    resolvidos = sum(1 for r in rows if r["status"] == "resolved")
    fechados = sum(1 for r in rows if r["status"] == "closed")

    resolucao_tempos: list[float] = []
    sla_cumpridos = 0
    sla_total = 0
    sla_por_severidade: dict[str, dict[str, object]] = {}

    for sev in VALID_SEVERITIES:
        sla_por_severidade[sev] = {
            "sla_horas": compute_sla_hours(sev),
            "total": 0,
            "cumpridos": 0,
        }

    for r in rows:
        sev = r["severity"]
        if sev in sla_por_severidade:
            sla_por_severidade[sev]["total"] += 1

        if r["status"] in ("resolved", "closed") and r["resolved_at"]:
            resolucao_tempos.append(
                (datetime.fromisoformat(r["resolved_at"]) - datetime.fromisoformat(r["created_at"])).total_seconds()
                / 3600
            )
            if is_within_sla(r["created_at"], r["resolved_at"], sev):
                sla_cumpridos += 1
                if sev in sla_por_severidade:
                    sla_por_severidade[sev]["cumpridos"] += 1
            sla_total += 1

    tempo_medio = (
        sum(resolucao_tempos) / len(resolucao_tempos) if resolucao_tempos else 0.0
    )
    taxa_sla = (sla_cumpridos / sla_total * 100) if sla_total > 0 else 0.0

    return {
        "total_tickets": total,
        "tickets_abertos": abertos,
        "tickets_resolvidos": resolvidos,
        "tickets_fechados": fechados,
        "tempo_medio_resolucao_horas": round(tempo_medio, 2),
        "taxa_cumprimento_sla": round(taxa_sla, 2),
        "sla_por_severidade": sla_por_severidade,
    }

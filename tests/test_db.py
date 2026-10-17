"""Testes da camada de banco de dados (db.py).

Cobre: inicializacao, criacao de tickets, atualizacao de status,
listagem com filtros, calculo de SLA e KPIs.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from dashboard_sla_helpdesk import db as db_module


@pytest.fixture
def conn() -> sqlite3.Connection:
    """Conexao SQLite em arquivo temporario, inicializada para cada teste."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    connection = db_module.get_connection(path)
    db_module.init_db(connection)
    yield connection
    connection.close()
    path.unlink(missing_ok=True)


def test_init_db_creates_tickets_table(conn: sqlite3.Connection) -> None:
    """A tabela tickets deve existir apos init_db."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'"
    )
    assert cur.fetchone() is not None


def test_create_ticket_returns_id_and_persists(conn: sqlite3.Connection) -> None:
    """Criar um ticket deve retornar um ID e o ticket deve ser recuperavel."""
    ticket_id = db_module.create_ticket(
        conn, title="Servidor fora do ar", severity="critical"
    )
    assert isinstance(ticket_id, int)
    assert ticket_id > 0

    row = db_module.get_ticket(conn, ticket_id)
    assert row is not None
    assert row["title"] == "Servidor fora do ar"
    assert row["severity"] == "critical"
    assert row["status"] == "open"
    assert row["created_at"] is not None
    assert row["updated_at"] is not None


def test_create_ticket_invalid_severity_raises(conn: sqlite3.Connection) -> None:
    """Severidade invalida deve levantar ValueError."""
    with pytest.raises(ValueError):
        db_module.create_ticket(conn, title="x", severity="inexistente")


def test_update_ticket_status_to_resolved_sets_resolved_at(conn: sqlite3.Connection) -> None:
    """Ao resolver um ticket, resolved_at deve ser preenchido automaticamente."""
    ticket_id = db_module.create_ticket(conn, title="x", severity="medium")
    db_module.update_ticket_status(conn, ticket_id, "resolved")
    row = db_module.get_ticket(conn, ticket_id)
    assert row["status"] == "resolved"
    assert row["resolved_at"] is not None


def test_update_ticket_status_invalid_raises(conn: sqlite3.Connection) -> None:
    """Status invalido deve levantar ValueError."""
    ticket_id = db_module.create_ticket(conn, title="x")
    with pytest.raises(ValueError):
        db_module.update_ticket_status(conn, ticket_id, "inexistente")


def test_list_tickets_filters_by_status_and_severity(conn: sqlite3.Connection) -> None:
    """Filtros de status e severidade devem funcionar corretamente."""
    db_module.create_ticket(conn, title="A", severity="critical", status="open")
    db_module.create_ticket(conn, title="B", severity="high", status="resolved")
    db_module.create_ticket(conn, title="C", severity="critical", status="open")

    abertos = db_module.list_tickets(conn, status="open")
    assert len(abertos) == 2

    criticos = db_module.list_tickets(conn, severity="critical")
    assert len(criticos) == 2

    criticos_abertos = db_module.list_tickets(conn, status="open", severity="critical")
    assert len(criticos_abertos) == 2


def test_list_tickets_invalid_filters_raise(conn: sqlite3.Connection) -> None:
    """Filtros invalidos devem levantar ValueError."""
    with pytest.raises(ValueError):
        db_module.list_tickets(conn, status="inexistente")
    with pytest.raises(ValueError):
        db_module.list_tickets(conn, severity="inexistente")


def test_compute_sla_hours_by_severity() -> None:
    """O prazo de SLA deve corresponder a cada severidade."""
    assert db_module.compute_sla_hours("critical") == 4
    assert db_module.compute_sla_hours("high") == 8
    assert db_module.compute_sla_hours("medium") == 24
    assert db_module.compute_sla_hours("low") == 72


def test_compute_sla_hours_invalid_raises() -> None:
    """Severidade invalida deve levantar ValueError."""
    with pytest.raises(ValueError):
        db_module.compute_sla_hours("inexistente")


def test_is_within_sla_resolved_deadline(conn: sqlite3.Connection) -> None:
    """Ticket resolvido dentro do prazo deve retornar True."""
    from datetime import datetime, timedelta

    ticket_id = db_module.create_ticket(
        conn,
        title="x",
        severity="critical",
        created_at=datetime.utcnow().isoformat(),
    )
    sla_hours = db_module.compute_sla_hours("critical")
    resolvido_em = (
        datetime.utcnow() + timedelta(hours=sla_hours - 1)
    ).isoformat()
    assert db_module.is_within_sla(
        db_module.get_ticket(conn, ticket_id)["created_at"], resolvido_em, "critical"
    ) is True


def test_is_within_sla_missed_deadline() -> None:
    """Ticket resolvido fora do prazo deve retornar False."""
    from datetime import datetime, timedelta

    criado = datetime.utcnow().isoformat()
    resolvido_em = (datetime.utcnow() + timedelta(hours=5)).isoformat()
    assert db_module.is_within_sla(criado, resolvido_em, "critical") is False


def test_get_kpis_empty_database(conn: sqlite3.Connection) -> None:
    """KPIs de banco vazio devem ser zeros."""
    kpis = db_module.get_kpis(conn)
    assert kpis["total_tickets"] == 0
    assert kpis["tickets_abertos"] == 0
    assert kpis["tickets_resolvidos"] == 0
    assert kpis["tickets_fechados"] == 0
    assert kpis["tempo_medio_resolucao_horas"] == 0.0
    assert kpis["taxa_cumprimento_sla"] == 0.0
    assert set(kpis["sla_por_severidade"].keys()) == {
        "critical", "high", "medium", "low",
    }


def test_get_kpis_with_tickets(conn: sqlite3.Connection) -> None:
    """KPIs devem refletir tickets criados e resolvidos."""
    from datetime import datetime, timedelta

    agora = datetime.utcnow()
    t1 = db_module.create_ticket(
        conn, title="T1", severity="critical",
        created_at=agora.isoformat(),
    )
    db_module.update_ticket_status(
        conn, t1, "resolved",
        resolved_at=(agora + timedelta(hours=2)).isoformat(),
    )
    t2 = db_module.create_ticket(
        conn, title="T2", severity="high", status="open",
        created_at=agora.isoformat(),
    )

    kpis = db_module.get_kpis(conn)
    assert kpis["total_tickets"] == 2
    assert kpis["tickets_abertos"] == 1
    assert kpis["tickets_resolvidos"] == 1
    assert kpis["tickets_fechados"] == 0
    assert kpis["taxa_cumprimento_sla"] == 100.0  # 2h dentro do SLA de 4h

    sla_critico = kpis["sla_por_severidade"]["critical"]
    assert sla_critico["total"] == 1
    assert sla_critico["cumpridos"] == 1

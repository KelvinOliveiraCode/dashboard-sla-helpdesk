"""Rotas HTTP do dashboard de SLA.

Define o blueprint com os endpoints: lista de tickets (fila), criacao de
ticket, atualizacao de status e dashboard com KPIs.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from flask import Blueprint, redirect, render_template, request, url_for

from . import db as db_module
from .models import KPIs, Ticket

bp = Blueprint("helpdesk", __name__, template_folder="templates")


def _row_to_ticket(row: sqlite3.Row) -> Ticket:
    """Converte uma linha do SQLite em um modelo Ticket."""
    return Ticket(
        id=row["id"],
        title=row["title"],
        description=row["description"] or "",
        severity=row["severity"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        resolved_at=(
            datetime.fromisoformat(row["resolved_at"])
            if row["resolved_at"]
            else None
        ),
    )


@bp.route("/")
def index() -> str:
    """Pagina inicial: redireciona para o dashboard."""
    return redirect(url_for("helpdesk.dashboard"))


@bp.route("/dashboard")
def dashboard() -> str:
    """Renderiza o dashboard com KPIs e lista de tickets recentes."""
    conn = db_module.get_connection()
    try:
        db_module.init_db(conn)
        kpis_raw = db_module.get_kpis(conn)
        tickets_raw = db_module.list_tickets(conn)[:20]
    finally:
        conn.close()

    kpis = KPIs(
        total_tickets=int(kpis_raw["total_tickets"]),
        tickets_abertos=int(kpis_raw["tickets_abertos"]),
        tickets_resolvidos=int(kpis_raw["tickets_resolvidos"]),
        tickets_fechados=int(kpis_raw["tickets_fechados"]),
        tempo_medio_resolucao_horas=float(kpis_raw["tempo_medio_resolucao_horas"]),
        taxa_cumprimento_sla=float(kpis_raw["taxa_cumprimento_sla"]),
        sla_por_severidade=kpis_raw["sla_por_severidade"],
    )
    tickets = [_row_to_ticket(r) for r in tickets_raw]
    return render_template("dashboard.html", kpis=kpis, tickets=tickets)


@bp.route("/tickets")
def tickets_list() -> str:
    """Lista todos os tickets (fila), com filtros opcionais por status e severidade."""
    status = request.args.get("status") or None
    severity = request.args.get("severity") or None

    conn = db_module.get_connection()
    try:
        db_module.init_db(conn)
        rows = db_module.list_tickets(conn, status=status, severity=severity)
    finally:
        conn.close()

    tickets = [_row_to_ticket(r) for r in rows]
    return render_template("tickets.html", tickets=tickets, status=status, severity=severity)


@bp.route("/tickets/new", methods=["GET", "POST"])
def new_ticket() -> str:
    """Cria um novo ticket. GET exibe o formulario, POST processa a criacao."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        severity = request.form.get("severity", "medium").strip()

        if not title:
            return render_template("new_ticket.html", error="Titulo e obrigatorio"), 400

        conn = db_module.get_connection()
        try:
            db_module.init_db(conn)
            db_module.create_ticket(
                conn,
                title=title,
                description=description,
                severity=severity,
            )
        finally:
            conn.close()
        return redirect(url_for("helpdesk.dashboard"))

    return render_template("new_ticket.html")


@bp.route("/tickets/<int:ticket_id>/status", methods=["POST"])
def update_ticket_status(ticket_id: int) -> str:
    """Atualiza o status de um ticket existente."""
    status = request.form.get("status", "").strip()
    resolved_at = request.form.get("resolved_at") or None

    conn = db_module.get_connection()
    try:
        db_module.init_db(conn)
        ticket = db_module.get_ticket(conn, ticket_id)
        if ticket is None:
            return "Ticket nao encontrado", 404
        db_module.update_ticket_status(conn, ticket_id, status, resolved_at)
    finally:
        conn.close()

    return redirect(url_for("helpdesk.dashboard"))


def init_app(app) -> None:  # type: ignore[valid-type]
    """Registra o blueprint na aplicacao Flask (compatibilidade)."""
    app.register_blueprint(bp)

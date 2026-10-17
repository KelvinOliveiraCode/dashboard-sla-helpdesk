"""Testes da fabricacao da aplicacao Flask (app.py)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from dashboard_sla_helpdesk.app import create_app


@pytest.fixture
def app():
    """Aplicacao Flask com banco temporario para testes."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    application = create_app(db_path=str(path))
    application.config["TESTING"] = True
    yield application
    path.unlink(missing_ok=True)


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


def test_create_app_returns_flask_instance(app) -> None:
    """create_app deve retornar uma instancia do Flask."""
    from flask import Flask

    assert isinstance(app, Flask)


def test_dashboard_endpoint_returns_200(client) -> None:
    """GET /dashboard deve retornar HTTP 200."""
    resposta = client.get("/dashboard")
    assert resposta.status_code == 200


def test_index_redirects_to_dashboard(client) -> None:
    """GET / deve redirecionar para /dashboard."""
    resposta = client.get("/")
    assert resposta.status_code == 302


def test_dashboard_contains_kpi_labels(client) -> None:
    """O dashboard deve exibir os rotulos dos KPIs."""
    resposta = client.get("/dashboard")
    html = resposta.data.decode("utf-8")
    assert "Total de tickets" in html
    assert "Tickets abertos" in html
    assert "Taxa de cumprimento SLA" in html

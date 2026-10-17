"""Fabrica da aplicacao Flask.

Expõe `create_app()` para inicializar a aplicacao com rotas, banco de dados
e configuracao. Segue o padrao application factory para facilitar testes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from flask import Flask

from . import db as db_module


def create_app(db_path: Optional[str] = None) -> Flask:
    """Cria e configura a instancia da aplicacao Flask.

    Args:
        db_path: Caminho opcional para o banco SQLite. Se None, usa o padrao.

    Returns:
        Instancia configurada da aplicacao Flask.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-prod")
    app.config["DB_PATH"] = db_path

    # Inicializa o esquema do banco dentro do contexto da aplicacao.
    # (Flask 3 removeu before_first_request; cada rota tambem chama init_db.)
    with app.app_context():
        path = Path(app.config["DB_PATH"]) if app.config["DB_PATH"] else db_module.get_db_path()
        conn = db_module.get_connection(path)
        try:
            db_module.init_db(conn)
        finally:
            conn.close()

    from . import routes  # noqa: E402  (import apos definicao do app)
    app.register_blueprint(routes.bp)

    return app

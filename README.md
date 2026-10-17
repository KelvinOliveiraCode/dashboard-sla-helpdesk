# dashboard-sla-helpdesk

Dashboard de SLA para helpdesk de suporte TI. Fila de tickets, SLA por severidade e relatorio de desempenho com KPIs.

Stack: Python, Flask, SQLite.

Autor: Kelvin Oliveira

Licensa: MIT

---

# dashboard-sla-helpdesk

SLA dashboard for IT support helpdesk. Ticket queue, SLA by severity, and performance report with KPIs.

Stack: Python, Flask, SQLite.

Author: Kelvin Oliveira

License: MIT

---

## Portugues / Portuguese

### O que faz

O dashboard registra chamados de suporte (tickets) com severidade (critico, alta, media, baixa) e status (aberto, em andamento, resolvido, fechado). Cada severidade tem um prazo de SLA em horas:

- critico: 4 h
- alta: 8 h
- media: 24 h
- baixa: 72 h

A tela principal exibe KPIs: total de tickets, abertos, resolvidos, fechados, tempo medio de resolucao e taxa de cumplimento do SLA. Tambem mostra o SLA por severidade e a lista de tickets recentes.

### Como usar

Prerequisitos: Python 3.10+ e uv.

1. Clone o repositorio e entre na pasta do projeto.
2. Crie o ambiente virtual e instale dependencias:

   uv sync --only-dev

3. Rode a aplicacao:

   uv run python -m dashboard_sla_helpdesk.app

   (ou defina FLASK_APP e use `flask run`)

4. Acesse http://localhost:5000 no navegador.

### Como rodar os testes

   uv run python -m pytest -q

Suíte: 22 testes, todos passando.

### Estrutura de pastas

```
dashboard-sla-helpdesk/
  pyproject.toml        # dependencias e metadata do projeto
  src/dashboard_sla_helpdesk/
    __init__.py         # pacote
    app.py              # fabricacao da app Flask
    db.py               # acesso ao SQLite (tickets, SLA, KPIs)
    models.py           # dataclasses Ticket e KPIs
    routes.py           # rotas HTTP (dashboard, fila, novo ticket, status)
    templates/          # HTML Jinja2 (base, dashboard, fila, novo ticket)
  tests/
    test_db.py          # camada de banco
    test_app.py         # fabricacao da app
    test_routes.py      # rotas HTTP
  README.md
  BRIEF.md
```

### Licensa

MIT. Veja o arquivo LICENSE (nao incluso neste escopo MVP).

Autor: Kelvin Oliveira

---

## English

### What it does

The dashboard records support tickets with severity (critical, high, medium, low) and status (open, in progress, resolved, closed). Each severity has an SLA window in hours:

- critical: 4 h
- high: 8 h
- medium: 24 h
- low: 72 h

The main screen shows KPIs: total tickets, open, resolved, closed, average resolution time, and SLA compliance rate. It also shows SLA by severity and a list of recent tickets.

### How to use

Prerequisites: Python 3.10+ and uv.

1. Clone the repository and enter the project folder.
2. Create the virtual environment and install dependencies:

   uv sync --only-dev

3. Run the application:

   uv run python -m dashboard_sla_helpdesk.app

   (or set FLASK_APP and use `flask run`)

4. Open http://localhost:5000 in your browser.

### How to run the tests

   uv run python -m pytest -q

Suite: 22 tests, all passing.

### Folder layout

```
dashboard-sla-helpdesk/
  pyproject.toml        # dependencies and project metadata
  src/dashboard_sla_helpdesk/
    __init__.py         # package
    app.py              # Flask app factory
    db.py               # SQLite access (tickets, SLA, KPIs)
    models.py           # Ticket and KPIs dataclasses
    routes.py           # HTTP routes (dashboard, queue, new ticket, status)
    templates/          # Jinja2 HTML (base, dashboard, queue, new ticket)
  tests/
    test_db.py          # database layer
    test_app.py         # app factory
    test_routes.py      # HTTP routes
  README.md
  BRIEF.md
```

### License

MIT. See LICENSE file (not included in this MVP scope).

Author: Kelvin Oliveira

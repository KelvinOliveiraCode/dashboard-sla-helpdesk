# BRIEF — dashboard-sla-helpdesk

Projeto: dashboard de SLA para helpdesk de suporte TI (area Suporte TI)
Proprietário da validacao: workflow manager (solicitante)
Pasta de saida: C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\dashboard-sla-helpdesk\

## Entregas

| Arquivo | Descricao |
|---------|-----------|
| pyproject.toml | Dependencias (Flask) e metadata do projeto (hatchling build) |
| src/dashboard_sla_helpdesk/__init__.py | Pacote Python (versao 0.1.0) |
| src/dashboard_sla_helpdesk/app.py | Fabricacao da app Flask (application factory) |
| src/dashboard_sla_helpdesk/db.py | Acesso ao SQLite: tickets, SLA por severidade, KPIs |
| src/dashboard_sla_helpdesk/models.py | Dataclasses Ticket e KPIs |
| src/dashboard_sla_helpdesk/routes.py | Rotas HTTP: dashboard, fila, novo ticket, atualizacao de status |
| src/dashboard_sla_helpdesk/templates/base.html | Template base HTML |
| src/dashboard_sla_helpdesk/templates/dashboard.html | Dashboard com KPIs e SLA por severidade |
| src/dashboard_sla_helpdesk/templates/tickets.html | Fila de tickets com filtros |
| src/dashboard_sla_helpdesk/templates/new_ticket.html | Formulario de novo ticket |
| tests/test_db.py | Testes da camada de banco |
| tests/test_app.py | Testes da fabricacao da app |
| tests/test_routes.py | Testes de integracao das rotas HTTP |
| tests/__init__.py | Pacote de testes |
| README.md | Documentacao bilíngue PT-BR + EN |
| BRIEF.md | Este arquivo |

## Critérios de aceitação (MVP)

- [x] Dashboard com KPIs: total de tickets, abertos, resolvidos, fechados, tempo medio de resolucao, taxa de cumplimento SLA
- [x] Fila de tickets com filtros por status e severidade
- [x] SLA por severidade (critico 4h, alta 8h, media 24h, baixa 72h)
- [x] Relatorio de desempenho (KPIs + SLA por severidade)
- [x] Suíte pytest passando
- [x] README bilíngue PT-BR + EN completo (titulo, descricao, como usar, testes, licensa MIT, autor Kelvin Oliveira)
- [x] BRIEF.md resumindo entregas e como verificar

## Como verificar

### 1. Instalar dependencias

```bash
cd C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\dashboard-sla-helpdesk
uv sync --only-dev
```

### 2. Rodar os testes

```bash
uv run python -m pytest -q
```

Resultado esperado: 22 passed, 0 failed.

### 3. Rodar a aplicacao

```bash
uv run python -m dashboard_sla_helpdesk.app
```

Acesse http://localhost:5000 no navegador.

## Resultado dos testes

Comando: `uv run python -m pytest -q`
Resultado: 22 passed, 16 warnings (apenas DeprecationWarning de datetime.utcnow, sem falhas)

## Caminhos dos artefatos

- README: C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\dashboard-sla-helpdesk\README.md
- BRIEF: C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\dashboard-sla-helpdesk\BRIEF.md

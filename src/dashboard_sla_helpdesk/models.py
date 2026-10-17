"""Modelos de dados do dominio de helpdesk.

Registros imutaveis (dataclasses) usados para transferir dados entre a camada
de banco e as rotas/templates, sem acoplamento direto com linhas do SQLite.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Ticket:
    """Representa um chamado de suporte."""

    id: Optional[int]
    title: str
    description: str
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    @property
    def sla_hours(self) -> int:
        """Prazo de SLA em horas para a severidade do ticket."""
        from .db import SLA_HOURS_BY_SEVERITY

        return SLA_HOURS_BY_SEVERITY[self.severity]

    @property
    def is_within_sla(self) -> bool:
        """True se o ticket foi resolvido dentro do prazo de SLA."""
        if self.resolved_at is None:
            return False
        from .db import is_within_sla

        return is_within_sla(
            self.created_at.isoformat(),
            self.resolved_at.isoformat(),
            self.severity,
        )


@dataclass(frozen=True)
class KPIs:
    """Indicadores-chave de desempenho do dashboard."""

    total_tickets: int
    tickets_abertos: int
    tickets_resolvidos: int
    tickets_fechados: int
    tempo_medio_resolucao_horas: float
    taxa_cumprimento_sla: float
    sla_por_severidade: dict[str, dict[str, object]]

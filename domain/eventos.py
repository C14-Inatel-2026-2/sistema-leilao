"""
domain/eventos.py

Eventos de dominio: fatos que ja aconteceram e que outras partes do sistema
(historico, auditoria, notificacoes) podem querer saber, sem que o caso de uso
que os origina precise conhece-las.

Sao dados puros e imutaveis - quem entrega o evento aos interessados e o
publicador em adapters/events/publisher.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class LanceRealizado:
    """Publicado depois que um lance e aceito e persistido."""

    leilao_id: UUID
    lance_id: UUID
    comprador_id: UUID | int
    valor: Decimal
    ocorrido_em: datetime

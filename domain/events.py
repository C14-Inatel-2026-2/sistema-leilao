from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LanceRealizado:
    leilao_id: UUID
    lance_id: UUID
    usuario_id: UUID
    valor: Decimal
    data_hora: datetime


@dataclass(frozen=True, slots=True)
class LeilaoEncerrado:
    leilao_id: UUID
    vencedor_id: UUID | None
    valor_final: Decimal | None
    data_encerramento: datetime
    motivo: str | None = None

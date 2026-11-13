from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from domain.leilao import StatusLeilao


class LeilaoDetalheResponse(BaseModel):
    id: UUID
    anuncio_id: UUID
    vendedor_id: UUID
    preco_inicial: Decimal
    incremento_minimo: Decimal
    data_inicio: datetime
    data_final: datetime
    status: StatusLeilao
    maior_lance: Decimal | None = None
    vencedor_id: UUID | None = None
    valor_arremate: Decimal | None = None

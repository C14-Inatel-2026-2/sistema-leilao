from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DarLanceRequest(BaseModel):
    valor: Decimal


class LanceResponse(BaseModel):
    id: UUID
    leilao_id: UUID
    comprador_id: UUID
    valor: Decimal
    criado_em: datetime

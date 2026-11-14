from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from domain.venda import MetodoPagamento, StatusPagamento


class PagamentoRequest(BaseModel):
    metodo: MetodoPagamento


class VendaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    anuncio_id: UUID
    comprador_id: UUID
    leilao_id: UUID | None
    valor: Decimal
    metodo: MetodoPagamento | None
    status: StatusPagamento
    criado_em: datetime

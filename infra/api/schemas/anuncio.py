from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from domain.anuncio import StatusAnuncio, TipoAnuncio
from domain.leilao import StatusLeilao


class CriarAnuncioRequest(BaseModel):
    titulo: str
    descricao: str
    preco_referencia: Decimal
    categoria_id: UUID
    vendedor_id: UUID
    preco_inicial: Decimal
    incremento_minimo: Decimal
    data_inicio: datetime
    data_final: datetime


class AnuncioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    descricao: str
    preco_referencia: Decimal
    categoria_id: UUID
    vendedor_id: UUID
    tipo: TipoAnuncio
    status: StatusAnuncio
    leilao_atual_id: UUID | None
    criado_em: datetime


class LeilaoDoAnuncioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    anuncio_id: UUID
    vendedor_id: UUID
    preco_inicial: Decimal
    incremento_minimo: Decimal
    data_inicio: datetime
    data_final: datetime
    status: StatusLeilao


class EditarAnuncioRequest(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    preco_referencia: Decimal | None = None


class AnuncioCriadoResponse(BaseModel):
    anuncio: AnuncioResponse
    leilao: LeilaoDoAnuncioResponse

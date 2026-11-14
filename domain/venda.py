from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from domain.exceptions import VendaInvalidaError


class StatusPagamento(str, Enum):
    PENDENTE = 'PENDENTE'
    APROVADO = 'APROVADO'
    CANCELADO = 'CANCELADO'


class MetodoPagamento(str, Enum):
    PIX = 'PIX'
    CARTAO = 'CARTAO'
    BOLETO = 'BOLETO'


@dataclass
class Venda:
    anuncio_id: UUID
    comprador_id: UUID
    valor: Decimal
    leilao_id: UUID | None = None
    metodo: MetodoPagamento | None = None
    status: StatusPagamento = StatusPagamento.PENDENTE
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise VendaInvalidaError('valor da venda deve ser positivo')

    def aprovar(self, metodo: MetodoPagamento) -> None:
        if self.status != StatusPagamento.PENDENTE:
            raise VendaInvalidaError('apenas venda pendente pode ser aprovada')
        self.metodo = metodo
        self.status = StatusPagamento.APROVADO

    def cancelar(self) -> None:
        if self.status != StatusPagamento.PENDENTE:
            raise VendaInvalidaError(
                'apenas venda pendente pode ser cancelada'
            )
        self.status = StatusPagamento.CANCELADO

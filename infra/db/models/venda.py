from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from domain.venda import MetodoPagamento, StatusPagamento
from infra.db.base import Base


class VendaModel(Base):
    __tablename__ = 'vendas'

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    anuncio_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('anuncios.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    comprador_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    leilao_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('leiloes.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    metodo: Mapped[MetodoPagamento | None] = mapped_column(
        SAEnum(MetodoPagamento, native_enum=False, length=20),
        nullable=True,
    )
    status: Mapped[StatusPagamento] = mapped_column(
        SAEnum(StatusPagamento, native_enum=False, length=20),
        nullable=False,
        default=StatusPagamento.PENDENTE,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

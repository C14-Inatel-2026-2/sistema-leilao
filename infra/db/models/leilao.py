from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    Uuid,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from domain.leilao import StatusLeilao
from infra.db.base import Base

if TYPE_CHECKING:
    from infra.db.models.lance import LanceModel


class LeilaoModel(Base):
    __tablename__ = 'leiloes'

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    anuncio_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('anuncios.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    vendedor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    preco_inicial: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    incremento_minimo: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    data_inicio: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_final: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[StatusLeilao] = mapped_column(
        SAEnum(StatusLeilao, native_enum=False, length=20),
        nullable=False,
        default=StatusLeilao.AGENDADO,
        index=True,
    )
    vencedor_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    valor_arremate: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    lances: Mapped[list[LanceModel]] = relationship(
        'LanceModel',
        back_populates='leilao',
        cascade='all, delete-orphan',
        order_by='LanceModel.criado_em',
    )

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.db.base import Base

if TYPE_CHECKING:
    from infra.db.models.leilao import LeilaoModel


class LanceModel(Base):
    __tablename__ = 'lances'

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    leilao_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('leiloes.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    comprador_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    leilao: Mapped[LeilaoModel] = relationship(
        'LeilaoModel', back_populates='lances'
    )

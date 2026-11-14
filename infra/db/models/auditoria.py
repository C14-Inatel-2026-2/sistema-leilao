from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from infra.db.base import Base


class AuditoriaLeilaoModel(Base):
    __tablename__ = 'auditoria_leiloes'

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    leilao_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    tipo_evento: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )
    lance_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    usuario_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    valor: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    data_evento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

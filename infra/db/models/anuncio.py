from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from domain.anuncio import StatusAnuncio, TipoAnuncio
from infra.db.base import Base


class AnuncioModel(Base):
    __tablename__ = 'anuncios'

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    preco_referencia: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    categoria_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('categorias.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
    )
    vendedor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), nullable=False, index=True
    )
    tipo: Mapped[TipoAnuncio] = mapped_column(
        SAEnum(TipoAnuncio, native_enum=False, length=20),
        nullable=False,
        default=TipoAnuncio.VENDA_DIRETA,
    )
    status: Mapped[StatusAnuncio] = mapped_column(
        SAEnum(StatusAnuncio, native_enum=False, length=20),
        nullable=False,
        default=StatusAnuncio.ATIVO,
    )
    leilao_atual_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            'leiloes.id',
            use_alter=True,
            name='fk_anuncios_leilao_atual_id',
            ondelete='SET NULL',
        ),
        nullable=True,
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

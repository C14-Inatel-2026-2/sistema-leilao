from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class StatusAnuncio(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    VENDIDO = "VENDIDO"


class TipoAnuncio(str, Enum):
    VENDA_DIRETA = "VENDA_DIRETA"
    LEILAO = "LEILAO"


class AnuncioError(ValueError):
    """Erro de regra de negócio do anúncio."""


@dataclass
class Anuncio:
    titulo: str
    descricao: str
    preco_referencia: Decimal
    categoria_id: UUID
    vendedor_id: UUID
    tipo: TipoAnuncio = TipoAnuncio.VENDA_DIRETA
    status: StatusAnuncio = StatusAnuncio.ATIVO
    leilao_atual_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        self._validar_campos_basicos()

    def _validar_campos_basicos(self) -> None:
        if not self.titulo or not self.titulo.strip():
            raise AnuncioError("titulo obrigatorio")
        if not self.descricao or not self.descricao.strip():
            raise AnuncioError("descricao obrigatoria")
        if self.preco_referencia <= 0:
            raise AnuncioError("preco_referencia deve ser positivo")

    def esta_ativo(self) -> bool:
        return self.status == StatusAnuncio.ATIVO

    def pode_iniciar_leilao(self) -> bool:
        return (
            self.esta_ativo()
            and self.leilao_atual_id is None
            # opcional: exigir tipo LEILAO, ou permitir mudar tipo ao iniciar
        )

    def associar_leilao(self, leilao_id: UUID) -> None:
        if not self.pode_iniciar_leilao():
            raise AnuncioError("anuncio nao elegivel para leilao")
        self.leilao_atual_id = leilao_id
        self.tipo = TipoAnuncio.LEILAO

    def pode_editar(self, *, leilao_com_lances: bool = False) -> bool:
        if self.status != StatusAnuncio.ATIVO:
            return False
        if leilao_com_lances:
            return False
        return True

    def editar(
        self,
        *,
        titulo: str | None = None,
        descricao: str | None = None,
        preco_referencia: Decimal | None = None,
        leilao_com_lances: bool = False,
    ) -> None:
        if not self.pode_editar(leilao_com_lances=leilao_com_lances):
            raise AnuncioError("anuncio nao pode ser editado")
        if titulo is not None:
            self.titulo = titulo
        if descricao is not None:
            self.descricao = descricao
        if preco_referencia is not None:
            self.preco_referencia = preco_referencia
        self._validar_campos_basicos()

    def inativar(self) -> None:
        if self.status == StatusAnuncio.VENDIDO:
            raise AnuncioError("anuncio vendido nao pode ser inativado")
        self.status = StatusAnuncio.INATIVO

    def marcar_vendido(self) -> None:
        if not self.esta_ativo():
            raise AnuncioError("apenas anuncio ativo pode ser vendido")
        self.status = StatusAnuncio.VENDIDO
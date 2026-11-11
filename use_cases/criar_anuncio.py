from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from domain.anuncio import Anuncio
from domain.exceptions import AnuncioInvalidoError, CategoriaInvalidaError
from domain.leilao import Leilao
from use_cases.interfaces import (
    AnuncioRepository,
    CategoriaRepository,
    LeilaoRepository,
    UsuarioRepository,
)


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DadosNovoAnuncio:
    titulo: str
    descricao: str
    preco_referencia: Decimal
    categoria_id: UUID
    vendedor_id: UUID
    preco_inicial: Decimal
    incremento_minimo: Decimal
    data_inicio: datetime
    data_final: datetime


def _dentro_da_janela(leilao: Leilao, momento: datetime) -> bool:
    return leilao.data_inicio <= momento < leilao.data_final


class CriarAnuncio:
    def __init__(
        self,
        anuncios: AnuncioRepository,
        categorias: CategoriaRepository,
        leiloes: LeilaoRepository,
        usuarios: UsuarioRepository,
        relogio: Callable[[], datetime] = _agora_utc,
    ) -> None:
        self._anuncios = anuncios
        self._categorias = categorias
        self._leiloes = leiloes
        self._usuarios = usuarios
        self._relogio = relogio

    def executar(self, dados: DadosNovoAnuncio) -> tuple[Anuncio, Leilao]:
        anuncio = Anuncio(
            titulo=dados.titulo,
            descricao=dados.descricao,
            preco_referencia=dados.preco_referencia,
            categoria_id=dados.categoria_id,
            vendedor_id=dados.vendedor_id,
        )
        leilao = Leilao(
            anuncio_id=anuncio.id,
            vendedor_id=dados.vendedor_id,
            preco_inicial=dados.preco_inicial,
            incremento_minimo=dados.incremento_minimo,
            data_inicio=dados.data_inicio,
            data_final=dados.data_final,
        )

        vendedor = self._usuarios.buscar_por_id(dados.vendedor_id)
        if vendedor is None:
            raise AnuncioInvalidoError('vendedor nao encontrado')
        if not vendedor.pode_criar_anuncio():
            raise AnuncioInvalidoError('vendedor nao pode criar anuncio')

        categoria = self._categorias.buscar_por_id(dados.categoria_id)
        if categoria is None or not categoria.esta_ativa():
            raise CategoriaInvalidaError('categoria inexistente ou inativa')

        momento = self._relogio()
        if _dentro_da_janela(leilao, momento):
            leilao.abrir(momento)

        self._anuncios.salvar(anuncio)
        self._leiloes.salvar(leilao)
        anuncio.associar_leilao(leilao.id)
        self._anuncios.salvar(anuncio)
        return anuncio, leilao

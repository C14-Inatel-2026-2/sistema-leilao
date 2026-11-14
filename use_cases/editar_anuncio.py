from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from domain.anuncio import Anuncio
from domain.exceptions import AcessoNegadoError, AnuncioNaoEncontradoError
from use_cases.interfaces import AnuncioRepository, LeilaoRepository


class EditarAnuncio:
    def __init__(
        self, anuncios: AnuncioRepository, leiloes: LeilaoRepository
    ) -> None:
        self._anuncios = anuncios
        self._leiloes = leiloes

    def executar(
        self,
        anuncio_id: UUID,
        vendedor_id: UUID,
        *,
        titulo: str | None = None,
        descricao: str | None = None,
        preco_referencia: Decimal | None = None,
    ) -> Anuncio:
        anuncio = self._anuncios.buscar_por_id(anuncio_id)
        if anuncio is None:
            raise AnuncioNaoEncontradoError(
                f'anuncio {anuncio_id} nao encontrado'
            )
        if anuncio.vendedor_id != vendedor_id:
            raise AcessoNegadoError('somente o vendedor pode editar o anuncio')

        leilao_com_lances = False
        if anuncio.leilao_atual_id is not None:
            leilao = self._leiloes.buscar_por_id(anuncio.leilao_atual_id)
            leilao_com_lances = leilao is not None and bool(leilao.lances)

        anuncio.editar(
            titulo=titulo,
            descricao=descricao,
            preco_referencia=preco_referencia,
            leilao_com_lances=leilao_com_lances,
        )
        self._anuncios.salvar(anuncio)
        return anuncio

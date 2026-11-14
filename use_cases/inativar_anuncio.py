from __future__ import annotations

from uuid import UUID

from domain.anuncio import Anuncio
from domain.exceptions import AcessoNegadoError, AnuncioNaoEncontradoError
from use_cases.interfaces import AnuncioRepository


class InativarAnuncio:
    def __init__(self, anuncios: AnuncioRepository) -> None:
        self._anuncios = anuncios

    def executar(self, anuncio_id: UUID, vendedor_id: UUID) -> Anuncio:
        anuncio = self._anuncios.buscar_por_id(anuncio_id)
        if anuncio is None:
            raise AnuncioNaoEncontradoError(
                f'anuncio {anuncio_id} nao encontrado'
            )
        if anuncio.vendedor_id != vendedor_id:
            raise AcessoNegadoError(
                'somente o vendedor pode inativar o anuncio'
            )
        anuncio.inativar()
        self._anuncios.salvar(anuncio)
        return anuncio

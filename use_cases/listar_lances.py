from __future__ import annotations

from uuid import UUID

from domain.exceptions import LeilaoNaoEncontradoError
from domain.lance import Lance
from use_cases.interfaces import LeilaoRepository


class ListarLances:
    def __init__(self, leiloes: LeilaoRepository) -> None:
        self._leiloes = leiloes

    def executar(self, leilao_id: UUID) -> list[Lance]:
        leilao = self._leiloes.buscar_por_id(leilao_id)
        if leilao is None:
            raise LeilaoNaoEncontradoError(
                f'leilao {leilao_id} nao encontrado'
            )
        return sorted(leilao.lances, key=lambda x: x.criado_em, reverse=True)

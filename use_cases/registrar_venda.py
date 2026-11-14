from __future__ import annotations

from uuid import UUID

from domain.exceptions import LeilaoNaoEncontradoError, VendaInvalidaError
from domain.leilao import StatusLeilao
from domain.venda import Venda
from use_cases.interfaces import LeilaoRepository, VendaRepository


class RegistrarVenda:
    def __init__(
        self, leiloes: LeilaoRepository, vendas: VendaRepository
    ) -> None:
        self._leiloes = leiloes
        self._vendas = vendas

    def executar(self, leilao_id: UUID) -> Venda:
        existente = self._vendas.buscar_por_leilao(leilao_id)
        if existente is not None:
            return existente

        leilao = self._leiloes.buscar_por_id(leilao_id)
        if leilao is None:
            raise LeilaoNaoEncontradoError(
                f'leilao {leilao_id} nao encontrado'
            )
        if (
            leilao.status != StatusLeilao.ENCERRADO
            or leilao.vencedor_id is None
            or leilao.valor_arremate is None
        ):
            raise VendaInvalidaError(
                'somente leilao encerrado com vencedor gera venda'
            )

        venda = Venda(
            anuncio_id=leilao.anuncio_id,
            comprador_id=leilao.vencedor_id,
            leilao_id=leilao.id,
            valor=leilao.valor_arremate,
        )
        self._vendas.salvar(venda)
        return venda

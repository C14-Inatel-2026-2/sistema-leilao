from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from domain.exceptions import AcessoNegadoError, VendaNaoEncontradaError
from domain.venda import MetodoPagamento, Venda
from use_cases.interfaces import (
    AnuncioRepository,
    LeilaoRepository,
    VendaRepository,
)


class SimularPagamento:
    def __init__(
        self,
        vendas: VendaRepository,
        leiloes: LeilaoRepository,
        anuncios: AnuncioRepository,
        confirmar: Callable[[], None],
    ) -> None:
        self._vendas = vendas
        self._leiloes = leiloes
        self._anuncios = anuncios
        self._confirmar = confirmar

    def executar(
        self,
        venda_id: UUID,
        comprador_id: UUID,
        metodo: MetodoPagamento,
    ) -> Venda:
        venda = self._vendas.buscar_por_id(venda_id)
        if venda is None:
            raise VendaNaoEncontradaError(f'venda {venda_id} nao encontrada')
        if venda.comprador_id != comprador_id:
            raise AcessoNegadoError('somente o vencedor pode pagar a venda')

        leilao = self._leiloes.buscar_por_id(venda.leilao_id)
        anuncio = self._anuncios.buscar_por_id(venda.anuncio_id)
        venda.aprovar(metodo)
        leilao.marcar_como_pago()
        anuncio.marcar_vendido()
        self._vendas.salvar(venda)
        self._leiloes.salvar(leilao)
        self._anuncios.salvar(anuncio)
        self._confirmar()
        return venda

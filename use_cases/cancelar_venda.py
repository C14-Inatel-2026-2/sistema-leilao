from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from domain.exceptions import AcessoNegadoError, VendaNaoEncontradaError
from domain.venda import Venda
from use_cases.interfaces import VendaRepository


class CancelarVenda:
    def __init__(
        self, vendas: VendaRepository, confirmar: Callable[[], None]
    ) -> None:
        self._vendas = vendas
        self._confirmar = confirmar

    def executar(self, venda_id: UUID, comprador_id: UUID) -> Venda:
        venda = self._vendas.buscar_por_id(venda_id)
        if venda is None:
            raise VendaNaoEncontradaError(f'venda {venda_id} nao encontrada')
        if venda.comprador_id != comprador_id:
            raise AcessoNegadoError('somente o vencedor pode cancelar a venda')
        venda.cancelar()
        self._vendas.salvar(venda)
        self._confirmar()
        return venda

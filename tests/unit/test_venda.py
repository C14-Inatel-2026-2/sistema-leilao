from decimal import Decimal
from uuid import uuid4

import pytest

from domain.exceptions import VendaInvalidaError
from domain.venda import MetodoPagamento, StatusPagamento, Venda


def _venda(**overrides) -> Venda:
    dados = dict(
        anuncio_id=uuid4(),
        comprador_id=uuid4(),
        leilao_id=uuid4(),
        valor=Decimal('150.00'),
    )
    dados.update(overrides)
    return Venda(**dados)


def test_venda_nasce_pendente_sem_metodo():
    venda = _venda()

    assert venda.status == StatusPagamento.PENDENTE
    assert venda.metodo is None


def test_aprovar_grava_metodo_e_conclui():
    venda = _venda()

    venda.aprovar(MetodoPagamento.PIX)

    assert venda.status == StatusPagamento.APROVADO
    assert venda.metodo == MetodoPagamento.PIX


def test_cancelar_pendente():
    venda = _venda()

    venda.cancelar()

    assert venda.status == StatusPagamento.CANCELADO


@pytest.mark.parametrize('valor', [Decimal('0'), Decimal('-1')])
def test_rejeita_valor_nao_positivo(valor):
    with pytest.raises(VendaInvalidaError):
        _venda(valor=valor)


def test_aprovar_de_novo_e_recusado():
    venda = _venda()
    venda.aprovar(MetodoPagamento.CARTAO)

    with pytest.raises(VendaInvalidaError):
        venda.aprovar(MetodoPagamento.BOLETO)

    assert venda.metodo == MetodoPagamento.CARTAO


def test_cancelar_aprovada_e_recusado():
    venda = _venda()
    venda.aprovar(MetodoPagamento.PIX)

    with pytest.raises(VendaInvalidaError):
        venda.cancelar()

    assert venda.status == StatusPagamento.APROVADO

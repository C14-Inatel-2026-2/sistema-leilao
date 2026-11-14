from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from domain.anuncio import Anuncio, StatusAnuncio
from domain.exceptions import (
    AcessoNegadoError,
    LeilaoNaoEncontradoError,
    VendaInvalidaError,
    VendaNaoEncontradaError,
)
from domain.leilao import Leilao, StatusLeilao
from domain.venda import MetodoPagamento, StatusPagamento, Venda
from use_cases.cancelar_venda import CancelarVenda
from use_cases.interfaces import (
    AnuncioRepository,
    LeilaoRepository,
    VendaRepository,
)
from use_cases.registrar_venda import RegistrarVenda
from use_cases.simular_pagamento import SimularPagamento

INICIO = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def _leilao_encerrado() -> tuple[Leilao, UUID]:
    leilao = Leilao(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=INICIO,
        data_final=INICIO + timedelta(hours=2),
        status=StatusLeilao.ABERTO,
    )
    comprador = uuid4()
    leilao.receber_lance(comprador, Decimal('100.00'), INICIO)
    leilao.encerrar(INICIO + timedelta(hours=2))
    return leilao, comprador


def _anuncio(leilao: Leilao) -> Anuncio:
    return Anuncio(
        id=leilao.anuncio_id,
        titulo='Notebook',
        descricao='Usado',
        preco_referencia=Decimal('1500.00'),
        categoria_id=uuid4(),
        vendedor_id=leilao.vendedor_id,
    )


def _venda(leilao: Leilao) -> Venda:
    return Venda(
        anuncio_id=leilao.anuncio_id,
        comprador_id=leilao.vencedor_id,
        leilao_id=leilao.id,
        valor=leilao.valor_arremate,
    )


def test_registra_venda_pendente_do_vencedor():
    leilao, comprador = _leilao_encerrado()
    leiloes = Mock(spec=LeilaoRepository)
    vendas = Mock(spec=VendaRepository)
    leiloes.buscar_por_id.return_value = leilao
    vendas.buscar_por_leilao.return_value = None

    venda = RegistrarVenda(leiloes, vendas).executar(leilao.id)

    assert venda.status == StatusPagamento.PENDENTE
    assert venda.comprador_id == comprador
    assert venda.anuncio_id == leilao.anuncio_id
    assert venda.valor == Decimal('100.00')
    assert venda.leilao_id == leilao.id
    vendas.salvar.assert_called_once_with(venda)


def test_registrar_de_novo_devolve_a_venda_existente():
    leilao, _comprador = _leilao_encerrado()
    existente = _venda(leilao)
    leiloes = Mock(spec=LeilaoRepository)
    vendas = Mock(spec=VendaRepository)
    vendas.buscar_por_leilao.return_value = existente

    venda = RegistrarVenda(leiloes, vendas).executar(leilao.id)

    assert venda is existente
    vendas.salvar.assert_not_called()
    leiloes.buscar_por_id.assert_not_called()


def test_leilao_sem_vencedor_nao_gera_venda():
    leilao, _comprador = _leilao_encerrado()
    leilao.status = StatusLeilao.CANCELADO
    leilao.vencedor_id = None
    leiloes = Mock(spec=LeilaoRepository)
    vendas = Mock(spec=VendaRepository)
    leiloes.buscar_por_id.return_value = leilao
    vendas.buscar_por_leilao.return_value = None

    with pytest.raises(VendaInvalidaError):
        RegistrarVenda(leiloes, vendas).executar(leilao.id)

    vendas.salvar.assert_not_called()


def test_registrar_leilao_inexistente():
    leiloes = Mock(spec=LeilaoRepository)
    vendas = Mock(spec=VendaRepository)
    leiloes.buscar_por_id.return_value = None
    vendas.buscar_por_leilao.return_value = None

    with pytest.raises(LeilaoNaoEncontradoError):
        RegistrarVenda(leiloes, vendas).executar(uuid4())


def test_vencedor_simula_pagamento_e_conclui_leilao_e_anuncio():
    leilao, comprador = _leilao_encerrado()
    anuncio = _anuncio(leilao)
    venda = _venda(leilao)
    confirmar = Mock()
    leiloes = Mock(spec=LeilaoRepository)
    anuncios = Mock(spec=AnuncioRepository)
    vendas = Mock(spec=VendaRepository)
    vendas.buscar_por_id.return_value = venda
    leiloes.buscar_por_id.return_value = leilao
    anuncios.buscar_por_id.return_value = anuncio

    resultado = SimularPagamento(
        vendas, leiloes, anuncios, confirmar=confirmar
    ).executar(venda.id, comprador, MetodoPagamento.PIX)

    assert resultado.status == StatusPagamento.APROVADO
    assert resultado.metodo == MetodoPagamento.PIX
    assert leilao.status == StatusLeilao.PAGO
    assert anuncio.status == StatusAnuncio.VENDIDO
    vendas.salvar.assert_called_once_with(venda)
    leiloes.salvar.assert_called_once_with(leilao)
    anuncios.salvar.assert_called_once_with(anuncio)
    confirmar.assert_called_once_with()


def test_outro_usuario_nao_simula_pagamento():
    leilao, _comprador = _leilao_encerrado()
    venda = _venda(leilao)
    vendas = Mock(spec=VendaRepository)
    vendas.buscar_por_id.return_value = venda
    leiloes = Mock(spec=LeilaoRepository)
    anuncios = Mock(spec=AnuncioRepository)

    with pytest.raises(AcessoNegadoError):
        SimularPagamento(vendas, leiloes, anuncios, confirmar=Mock()).executar(
            venda.id, uuid4(), MetodoPagamento.BOLETO
        )

    assert venda.status == StatusPagamento.PENDENTE
    assert leilao.status == StatusLeilao.ENCERRADO
    vendas.salvar.assert_not_called()


def test_simular_pagamento_de_venda_inexistente():
    vendas = Mock(spec=VendaRepository)
    vendas.buscar_por_id.return_value = None

    with pytest.raises(VendaNaoEncontradaError):
        SimularPagamento(
            vendas,
            Mock(spec=LeilaoRepository),
            Mock(spec=AnuncioRepository),
            confirmar=Mock(),
        ).executar(uuid4(), uuid4(), MetodoPagamento.PIX)


def test_vencedor_cancela_venda_pendente():
    leilao, comprador = _leilao_encerrado()
    venda = _venda(leilao)
    confirmar = Mock()
    vendas = Mock(spec=VendaRepository)
    vendas.buscar_por_id.return_value = venda

    resultado = CancelarVenda(vendas, confirmar=confirmar).executar(
        venda.id, comprador
    )

    assert resultado.status == StatusPagamento.CANCELADO
    assert leilao.status == StatusLeilao.ENCERRADO
    vendas.salvar.assert_called_once_with(venda)
    confirmar.assert_called_once_with()


def test_outro_usuario_nao_cancela():
    leilao, _comprador = _leilao_encerrado()
    venda = _venda(leilao)
    vendas = Mock(spec=VendaRepository)
    vendas.buscar_por_id.return_value = venda

    with pytest.raises(AcessoNegadoError):
        CancelarVenda(vendas, confirmar=Mock()).executar(venda.id, uuid4())

    assert venda.status == StatusPagamento.PENDENTE
    vendas.salvar.assert_not_called()

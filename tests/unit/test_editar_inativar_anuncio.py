from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.anuncio import Anuncio, StatusAnuncio
from domain.exceptions import (
    AcessoNegadoError,
    AnuncioInvalidoError,
    AnuncioNaoEncontradoError,
)
from domain.lance import Lance
from domain.leilao import Leilao
from use_cases.editar_anuncio import EditarAnuncio
from use_cases.inativar_anuncio import InativarAnuncio
from use_cases.interfaces import AnuncioRepository, LeilaoRepository


def _anuncio(**overrides) -> Anuncio:
    dados = dict(
        titulo='Notebook usado',
        descricao='16 GB RAM',
        preco_referencia=Decimal('1500.00'),
        categoria_id=uuid4(),
        vendedor_id=uuid4(),
    )
    dados.update(overrides)
    return Anuncio(**dados)


def _leilao(anuncio: Anuncio, *, com_lances: bool) -> Leilao:
    agora = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    leilao = Leilao(
        id=anuncio.leilao_atual_id,
        anuncio_id=anuncio.id,
        vendedor_id=anuncio.vendedor_id,
        preco_inicial=Decimal('500.00'),
        incremento_minimo=Decimal('50.00'),
        data_inicio=agora,
        data_final=agora + timedelta(hours=2),
    )
    if com_lances:
        leilao.lances.append(
            Lance(
                comprador_id=uuid4(),
                valor=Decimal('500.00'),
                leilao_id=leilao.id,
                criado_em=agora,
            )
        )
    return leilao


@pytest.fixture
def anuncios():
    return Mock(spec=AnuncioRepository)


@pytest.fixture
def leiloes():
    return Mock(spec=LeilaoRepository)


def test_dono_edita_titulo_descricao_e_preco(anuncios, leiloes):
    anuncio = _anuncio()
    anuncios.buscar_por_id.return_value = anuncio

    editado = EditarAnuncio(anuncios, leiloes).executar(
        anuncio.id,
        anuncio.vendedor_id,
        titulo='Notebook revisado',
        descricao='SSD 512 GB',
        preco_referencia=Decimal('1400.00'),
    )

    assert editado.titulo == 'Notebook revisado'
    assert editado.descricao == 'SSD 512 GB'
    assert editado.preco_referencia == Decimal('1400.00')
    anuncios.salvar.assert_called_once_with(anuncio)
    leiloes.buscar_por_id.assert_not_called()


def test_edicao_de_outro_usuario_nega_acesso(anuncios, leiloes):
    anuncio = _anuncio()
    anuncios.buscar_por_id.return_value = anuncio

    with pytest.raises(AcessoNegadoError):
        EditarAnuncio(anuncios, leiloes).executar(
            anuncio.id, uuid4(), titulo='Outro titulo'
        )

    assert anuncio.titulo == 'Notebook usado'
    anuncios.salvar.assert_not_called()


def test_editar_anuncio_inexistente(anuncios, leiloes):
    anuncios.buscar_por_id.return_value = None

    with pytest.raises(AnuncioNaoEncontradoError):
        EditarAnuncio(anuncios, leiloes).executar(
            uuid4(), uuid4(), titulo='Nao existe'
        )


def test_editar_recusa_quando_leilao_tem_lances(anuncios, leiloes):
    anuncio = _anuncio(leilao_atual_id=uuid4())
    anuncios.buscar_por_id.return_value = anuncio
    leiloes.buscar_por_id.return_value = _leilao(anuncio, com_lances=True)

    with pytest.raises(AnuncioInvalidoError):
        EditarAnuncio(anuncios, leiloes).executar(
            anuncio.id, anuncio.vendedor_id, titulo='Mudou no meio'
        )

    assert anuncio.titulo == 'Notebook usado'
    anuncios.salvar.assert_not_called()


def test_dono_inativa_anuncio_ativo(anuncios):
    anuncio = _anuncio()
    anuncios.buscar_por_id.return_value = anuncio

    inativado = InativarAnuncio(anuncios).executar(
        anuncio.id, anuncio.vendedor_id
    )

    assert inativado.status == StatusAnuncio.INATIVO
    anuncios.salvar.assert_called_once_with(anuncio)


def test_inativar_vendido_e_recusado(anuncios):
    anuncio = _anuncio(status=StatusAnuncio.VENDIDO)
    anuncios.buscar_por_id.return_value = anuncio

    with pytest.raises(AnuncioInvalidoError):
        InativarAnuncio(anuncios).executar(anuncio.id, anuncio.vendedor_id)

    assert anuncio.status == StatusAnuncio.VENDIDO
    anuncios.salvar.assert_not_called()


def test_inativar_de_outro_usuario_nega_acesso(anuncios):
    anuncio = _anuncio()
    anuncios.buscar_por_id.return_value = anuncio

    with pytest.raises(AcessoNegadoError):
        InativarAnuncio(anuncios).executar(anuncio.id, uuid4())

    anuncios.salvar.assert_not_called()


def test_inativar_anuncio_inexistente(anuncios):
    anuncios.buscar_por_id.return_value = None

    with pytest.raises(AnuncioNaoEncontradoError):
        InativarAnuncio(anuncios).executar(uuid4(), uuid4())

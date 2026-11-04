"""
tests/unit/test_criar_anuncio.py

Fase red do caso de uso CriarAnuncio.

CriarAnuncio(anuncio_repo, categoria_repo, leilao_repo=None)
executar(
    *,
    titulo,
    descricao,
    preco_referencia,
    categoria_id,
    vendedor_id,
    dados_leilao=None,
) -> Anuncio

dados_leilao, quando informado, e um dict com preco_inicial,
incremento_minimo, data_inicio e data_final. O caso de uso cria o
Leilao em AGENDADO, associa via Anuncio.associar_leilao e persiste
os dois. Sem dados_leilao, o anuncio fica em VENDA_DIRETA e o
repositorio de leilao nao e chamado.

Categoria inexistente ou inativa levanta CategoriaInvalidaError
antes de salvar. Dados de leilao invalidos propagam
LeilaoInvalidoError e tambem nao salvam.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from domain.categoria import Categoria
from domain.exceptions import CategoriaInvalidaError, LeilaoInvalidoError
from domain.leilao import Leilao, StatusLeilao
from use_cases.criar_anuncio import CriarAnuncio
from use_cases.interfaces import (
    AnuncioRepository,
    CategoriaRepository,
    LeilaoRepository,
)

_INICIO = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
_FIM = _INICIO + timedelta(hours=2)


@pytest.fixture
def anuncio_repo():
    return Mock(spec=AnuncioRepository)


@pytest.fixture
def categoria_repo():
    return Mock(spec=CategoriaRepository)


@pytest.fixture
def leilao_repo():
    return Mock(spec=LeilaoRepository)


def _executar(caso, categoria_id, vendedor_id, **extras):
    dados = dict(
        titulo='Notebook',
        descricao='Usado, funcionando',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria_id,
        vendedor_id=vendedor_id,
    )
    dados.update(extras)
    return caso.executar(**dados)


def test_cria_anuncio_venda_direta_quando_sem_dados_leilao(
    anuncio_repo, categoria_repo, leilao_repo
):
    categoria = Categoria(nome='Eletronicos')
    categoria_repo.buscar_por_id.return_value = categoria
    vendedor_id = uuid4()
    caso = CriarAnuncio(anuncio_repo, categoria_repo, leilao_repo)

    anuncio = _executar(caso, categoria.id, vendedor_id)

    assert isinstance(anuncio, Anuncio)
    assert anuncio.tipo is TipoAnuncio.VENDA_DIRETA
    assert anuncio.status is StatusAnuncio.ATIVO
    assert anuncio.leilao_atual_id is None
    assert anuncio.categoria_id == categoria.id
    assert anuncio.vendedor_id == vendedor_id
    assert anuncio.titulo == 'Notebook'
    assert anuncio.preco_referencia == Decimal('1500.00')
    categoria_repo.buscar_por_id.assert_called_once_with(categoria.id)
    anuncio_repo.salvar.assert_called_once_with(anuncio)
    leilao_repo.salvar.assert_not_called()


def test_cria_anuncio_com_leilao_agendado_e_associa_leilao_atual_id(
    anuncio_repo, categoria_repo, leilao_repo
):
    categoria = Categoria(nome='Eletronicos')
    categoria_repo.buscar_por_id.return_value = categoria
    vendedor_id = uuid4()
    dados_leilao = {
        'preco_inicial': Decimal('100.00'),
        'incremento_minimo': Decimal('5.00'),
        'data_inicio': _INICIO,
        'data_final': _FIM,
    }
    caso = CriarAnuncio(anuncio_repo, categoria_repo, leilao_repo)

    anuncio = _executar(
        caso, categoria.id, vendedor_id, dados_leilao=dados_leilao
    )

    assert anuncio.tipo is TipoAnuncio.LEILAO
    assert anuncio.status is StatusAnuncio.ATIVO
    assert anuncio.leilao_atual_id is not None
    anuncio_repo.salvar.assert_called_once_with(anuncio)
    leilao_repo.salvar.assert_called_once()
    (leilao_salvo,) = leilao_repo.salvar.call_args.args
    assert isinstance(leilao_salvo, Leilao)
    assert leilao_salvo.id == anuncio.leilao_atual_id
    assert leilao_salvo.anuncio_id == anuncio.id
    assert leilao_salvo.vendedor_id == vendedor_id
    assert leilao_salvo.status is StatusLeilao.AGENDADO
    assert leilao_salvo.preco_inicial == Decimal('100.00')
    assert leilao_salvo.incremento_minimo == Decimal('5.00')
    assert leilao_salvo.data_inicio == _INICIO
    assert leilao_salvo.data_final == _FIM
    assert leilao_salvo.lances == []


def test_rejeita_criacao_quando_categoria_nao_existe(
    anuncio_repo, categoria_repo, leilao_repo
):
    categoria_repo.buscar_por_id.return_value = None
    caso = CriarAnuncio(anuncio_repo, categoria_repo, leilao_repo)

    with pytest.raises(CategoriaInvalidaError):
        _executar(caso, uuid4(), uuid4())

    anuncio_repo.salvar.assert_not_called()
    leilao_repo.salvar.assert_not_called()


def test_rejeita_criacao_quando_categoria_inativa(
    anuncio_repo, categoria_repo, leilao_repo
):
    categoria = Categoria(nome='Eletronicos', ativa=False)
    categoria_repo.buscar_por_id.return_value = categoria
    caso = CriarAnuncio(anuncio_repo, categoria_repo, leilao_repo)

    with pytest.raises(CategoriaInvalidaError):
        _executar(caso, categoria.id, uuid4())

    categoria_repo.buscar_por_id.assert_called_once_with(categoria.id)
    anuncio_repo.salvar.assert_not_called()
    leilao_repo.salvar.assert_not_called()


@pytest.mark.parametrize(
    'dados_leilao',
    [
        {
            'preco_inicial': Decimal('0'),
            'incremento_minimo': Decimal('5.00'),
            'data_inicio': _INICIO,
            'data_final': _FIM,
        },
        {
            'preco_inicial': Decimal('100.00'),
            'incremento_minimo': Decimal('5.00'),
            'data_inicio': _FIM,
            'data_final': _INICIO,
        },
    ],
    ids=['preco_inicial_nao_positivo', 'data_final_antes_do_inicio'],
)
def test_propaga_erro_de_dominio_quando_dados_do_leilao_invalidos(
    anuncio_repo, categoria_repo, leilao_repo, dados_leilao
):
    categoria = Categoria(nome='Eletronicos')
    categoria_repo.buscar_por_id.return_value = categoria
    caso = CriarAnuncio(anuncio_repo, categoria_repo, leilao_repo)

    with pytest.raises(LeilaoInvalidoError):
        _executar(
            caso,
            categoria.id,
            uuid4(),
            dados_leilao=dados_leilao,
        )

    anuncio_repo.salvar.assert_not_called()
    leilao_repo.salvar.assert_not_called()

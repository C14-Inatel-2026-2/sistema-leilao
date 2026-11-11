from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.anuncio import TipoAnuncio
from domain.categoria import Categoria
from domain.exceptions import (
    AnuncioInvalidoError,
    CategoriaInvalidaError,
    LeilaoInvalidoError,
)
from domain.leilao import StatusLeilao
from domain.usuario import PapelUsuario, Usuario
from use_cases.criar_anuncio import CriarAnuncio, DadosNovoAnuncio
from use_cases.interfaces import (
    AnuncioRepository,
    CategoriaRepository,
    LeilaoRepository,
    UsuarioRepository,
)

AGORA = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


def _vendedor(**overrides):
    dados = dict(
        nome='Ana Vendedora',
        email='ana@example.com',
        senha_hash='hash',
        papel=PapelUsuario.VENDEDOR,
    )
    dados.update(overrides)
    return Usuario(**dados)


def _dados(**overrides):
    vendedor_id = overrides.pop('vendedor_id', uuid4())
    categoria_id = overrides.pop('categoria_id', uuid4())
    dados = dict(
        titulo='Notebook',
        descricao='Usado, funcionando',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria_id,
        vendedor_id=vendedor_id,
        preco_inicial=Decimal('500.00'),
        incremento_minimo=Decimal('50.00'),
        data_inicio=AGORA + timedelta(days=1),
        data_final=AGORA + timedelta(days=2),
    )
    dados.update(overrides)
    return DadosNovoAnuncio(**dados)


@pytest.fixture
def anuncios():
    return Mock(spec=AnuncioRepository)


@pytest.fixture
def categorias():
    repositorio = Mock(spec=CategoriaRepository)
    repositorio.buscar_por_id.return_value = Categoria(nome='Eletronicos')
    return repositorio


@pytest.fixture
def leiloes():
    return Mock(spec=LeilaoRepository)


@pytest.fixture
def usuarios():
    repositorio = Mock(spec=UsuarioRepository)
    repositorio.buscar_por_id.return_value = _vendedor()
    return repositorio


@pytest.fixture
def caso_de_uso(anuncios, categorias, leiloes, usuarios):
    return CriarAnuncio(
        anuncios,
        categorias,
        leiloes,
        usuarios,
        relogio=lambda: AGORA,
    )


def test_agenda_anuncio_com_leilao_quando_inicio_e_futuro(
    caso_de_uso, anuncios, leiloes, usuarios
):
    vinculos = []
    anuncios.salvar.side_effect = lambda anuncio: vinculos.append(
        anuncio.leilao_atual_id
    )
    dados = _dados(vendedor_id=usuarios.buscar_por_id.return_value.id)

    anuncio, leilao = caso_de_uso.executar(dados)

    assert leilao.status == StatusLeilao.AGENDADO
    assert anuncio.tipo == TipoAnuncio.LEILAO
    assert anuncio.leilao_atual_id == leilao.id
    assert leilao.anuncio_id == anuncio.id
    assert vinculos == [None, leilao.id]
    leiloes.salvar.assert_called_once_with(leilao)
    usuarios.buscar_por_id.assert_called_once_with(dados.vendedor_id)


def test_abre_leilao_quando_inicio_ja_caiu_na_janela(caso_de_uso, leiloes):
    dados = _dados(
        data_inicio=AGORA - timedelta(hours=1),
        data_final=AGORA + timedelta(hours=2),
    )

    _anuncio, leilao = caso_de_uso.executar(dados)

    assert leilao.status == StatusLeilao.ABERTO
    leiloes.salvar.assert_called_once_with(leilao)


def test_mantem_agendado_quando_a_janela_ja_encerrou(caso_de_uso):
    dados = _dados(
        data_inicio=AGORA - timedelta(days=2),
        data_final=AGORA - timedelta(days=1),
    )

    _anuncio, leilao = caso_de_uso.executar(dados)

    assert leilao.status == StatusLeilao.AGENDADO


@pytest.mark.parametrize(
    ('vendedor', 'mensagem'),
    [
        (None, 'vendedor nao encontrado'),
        (
            _vendedor(papel=PapelUsuario.COMPRADOR),
            'vendedor nao pode criar anuncio',
        ),
        (_vendedor(ativo=False), 'vendedor nao pode criar anuncio'),
    ],
)
def test_rejeita_vendedor_inelegivel_sem_persistir(
    caso_de_uso, usuarios, vendedor, mensagem
):
    usuarios.buscar_por_id.return_value = vendedor

    with pytest.raises(AnuncioInvalidoError, match=mensagem):
        caso_de_uso.executar(_dados())

    caso_de_uso._anuncios.salvar.assert_not_called()
    caso_de_uso._leiloes.salvar.assert_not_called()


def test_rejeita_categoria_inexistente_ou_inativa_sem_persistir(
    caso_de_uso, anuncios, leiloes, categorias
):
    categorias.buscar_por_id.return_value = None

    with pytest.raises(CategoriaInvalidaError):
        caso_de_uso.executar(_dados())

    inativa = Categoria(nome='Arquivo')
    inativa.inativar()
    categorias.buscar_por_id.return_value = inativa

    with pytest.raises(CategoriaInvalidaError):
        caso_de_uso.executar(_dados())

    anuncios.salvar.assert_not_called()
    leiloes.salvar.assert_not_called()


def test_rejeita_dados_invalidos_sem_consultar_repositorios(
    caso_de_uso, usuarios, categorias, anuncios, leiloes
):
    with pytest.raises(AnuncioInvalidoError):
        caso_de_uso.executar(_dados(titulo='  '))

    with pytest.raises(LeilaoInvalidoError):
        caso_de_uso.executar(
            _dados(
                data_inicio=AGORA + timedelta(days=2),
                data_final=AGORA + timedelta(days=1),
            )
        )

    usuarios.buscar_por_id.assert_not_called()
    categorias.buscar_por_id.assert_not_called()
    anuncios.salvar.assert_not_called()
    leiloes.salvar.assert_not_called()

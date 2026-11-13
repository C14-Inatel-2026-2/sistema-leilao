from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from adapters.repositories.anuncio_repository import (
    SQLAlchemyAnuncioRepository,
)
from adapters.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)
from adapters.repositories.leilao_repository import SQLAlchemyLeilaoRepository
from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from domain.categoria import Categoria
from domain.leilao import Leilao

INICIO = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


def _categoria(session, nome='Eletronicos'):
    categoria = Categoria(nome=nome)
    SQLAlchemyCategoriaRepository(session).salvar(categoria)
    return categoria


def _anuncio(categoria, **overrides):
    dados = dict(
        titulo='Notebook',
        descricao='Usado',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria.id,
        vendedor_id=uuid4(),
        criado_em=INICIO,
    )
    dados.update(overrides)
    return Anuncio(**dados)


def test_salva_e_busca_por_id_com_todos_os_campos(session):
    categoria = _categoria(session)
    repositorio = SQLAlchemyAnuncioRepository(session)
    anuncio = _anuncio(categoria, tipo=TipoAnuncio.VENDA_DIRETA)
    repositorio.salvar(anuncio)
    session.expunge_all()

    encontrado = repositorio.buscar_por_id(anuncio.id)

    assert encontrado == anuncio
    assert encontrado.criado_em.tzinfo is not None


def test_vincula_leilao_atual_depois_de_persistir_o_leilao(session):
    categoria = _categoria(session)
    anuncios = SQLAlchemyAnuncioRepository(session)
    anuncio = _anuncio(categoria)
    anuncios.salvar(anuncio)
    leilao = Leilao(
        anuncio_id=anuncio.id,
        vendedor_id=anuncio.vendedor_id,
        preco_inicial=Decimal('500.00'),
        incremento_minimo=Decimal('50.00'),
        data_inicio=INICIO,
        data_final=INICIO + timedelta(days=1),
    )
    SQLAlchemyLeilaoRepository(session).salvar(leilao)
    anuncio.associar_leilao(leilao.id)
    anuncios.salvar(anuncio)
    session.expunge_all()

    encontrado = anuncios.buscar_por_id(anuncio.id)

    assert encontrado.leilao_atual_id == leilao.id
    assert encontrado.tipo == TipoAnuncio.LEILAO


def test_listar_filtra_e_ordena_do_mais_recente(session):
    eletronicos = _categoria(session, 'Eletronicos')
    livros = _categoria(session, 'Livros')
    anuncios = SQLAlchemyAnuncioRepository(session)
    antigo = _anuncio(
        eletronicos,
        titulo='Tablet antigo',
        descricao='Riscado',
        criado_em=INICIO,
    )
    recente = _anuncio(
        eletronicos,
        titulo='Notebook gamer',
        descricao='Novo',
        criado_em=INICIO + timedelta(days=1),
        tipo=TipoAnuncio.LEILAO,
    )
    inativo = _anuncio(
        livros,
        titulo='Livro de python',
        descricao='Capa dura',
        criado_em=INICIO + timedelta(days=2),
    )
    inativo.inativar()
    for anuncio in (antigo, recente, inativo):
        anuncios.salvar(anuncio)

    assert [item.titulo for item in anuncios.listar()] == [
        'Livro de python',
        'Notebook gamer',
        'Tablet antigo',
    ]
    assert anuncios.listar(categoria_id=eletronicos.id) == [recente, antigo]
    assert anuncios.listar(status=StatusAnuncio.INATIVO) == [inativo]
    assert anuncios.listar(tipo=TipoAnuncio.LEILAO) == [recente]
    assert anuncios.listar(texto='PYTHON') == [inativo]
    assert anuncios.listar(texto='riscado') == [antigo]
    assert anuncios.listar(texto='   ') == [inativo, recente, antigo]
    assert (
        anuncios.listar(categoria_id=livros.id, status=StatusAnuncio.ATIVO)
        == []
    )


def test_retorna_none_quando_anuncio_nao_existe(session):
    assert SQLAlchemyAnuncioRepository(session).buscar_por_id(uuid4()) is None


def test_salvar_de_novo_atualiza_o_anuncio(session):
    categoria = _categoria(session)
    repositorio = SQLAlchemyAnuncioRepository(session)
    anuncio = _anuncio(categoria)
    repositorio.salvar(anuncio)
    anuncio.editar(titulo='Notebook revisado')
    repositorio.salvar(anuncio)
    session.expunge_all()

    assert repositorio.buscar_por_id(anuncio.id).titulo == 'Notebook revisado'

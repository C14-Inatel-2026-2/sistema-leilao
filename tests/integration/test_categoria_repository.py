from datetime import datetime, timezone
from uuid import uuid4

from adapters.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)
from domain.categoria import Categoria


def _nova(**overrides):
    dados = dict(nome='Eletronicos')
    dados.update(overrides)
    return Categoria(**dados)


def test_salva_e_busca_por_id_com_todos_os_campos(session):
    repositorio = SQLAlchemyCategoriaRepository(session)
    categoria = _nova()
    repositorio.salvar(categoria)
    session.expunge_all()

    encontrada = repositorio.buscar_por_id(categoria.id)

    assert encontrada == categoria
    assert encontrada.criado_em.tzinfo is not None


def test_listar_ativas_omite_inativas_e_ordena_por_nome(session):
    repositorio = SQLAlchemyCategoriaRepository(session)
    livros = _nova(nome='Livros')
    casa = _nova(nome='Casa')
    arquivo = _nova(nome='Arquivo')
    arquivo.inativar()
    for categoria in (livros, casa, arquivo):
        repositorio.salvar(categoria)

    assert [item.nome for item in repositorio.listar_ativas()] == [
        'Casa',
        'Livros',
    ]


def test_retorna_none_quando_categoria_nao_existe(session):
    repositorio = SQLAlchemyCategoriaRepository(session)

    assert repositorio.buscar_por_id(uuid4()) is None


def test_salvar_de_novo_atualiza_a_categoria(session):
    repositorio = SQLAlchemyCategoriaRepository(session)
    categoria = _nova()
    repositorio.salvar(categoria)
    categoria.inativar()
    repositorio.salvar(categoria)
    session.expunge_all()

    assert repositorio.buscar_por_id(categoria.id).ativa is False


def test_criado_em_sem_fuso_volta_com_utc(session):
    repositorio = SQLAlchemyCategoriaRepository(session)
    categoria = _nova(
        criado_em=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
    )
    repositorio.salvar(categoria)
    session.expunge_all()

    encontrada = repositorio.buscar_por_id(categoria.id)

    assert encontrada.criado_em == categoria.criado_em

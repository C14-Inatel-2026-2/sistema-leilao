"""
tests/integration/test_usuario_repository.py

Testes de integracao do SQLAlchemyUsuarioRepository (e do UsuarioModel),
com SQLite em memoria. As fixtures engine e session vem do conftest.
"""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from adapters.repositories.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from domain.usuario import PapelUsuario, Usuario


def novo_usuario(email='teo@example.com', **overrides):
    dados = dict(
        nome='Teo Marques',
        email=email,
        senha_hash='hash-fake',
        papel=PapelUsuario.COMPRADOR,
    )
    dados.update(overrides)
    return Usuario(**dados)


@pytest.fixture
def repositorio(session):
    return SQLAlchemyUsuarioRepository(session)


def test_salva_e_busca_por_id_com_todos_os_campos(repositorio, session):
    usuario = novo_usuario(papel=PapelUsuario.VENDEDOR)
    repositorio.salvar(usuario)
    session.expunge_all()

    encontrado = repositorio.buscar_por_id(usuario.id)

    assert encontrado == usuario
    assert encontrado.criado_em.tzinfo is not None


def test_busca_por_email(repositorio):
    usuario = novo_usuario()
    repositorio.salvar(usuario)

    assert repositorio.buscar_por_email('teo@example.com') == usuario


def test_retorna_none_quando_usuario_nao_existe(repositorio):
    assert repositorio.buscar_por_id(uuid4()) is None
    assert repositorio.buscar_por_email('ninguem@example.com') is None


def test_salvar_de_novo_atualiza_o_usuario_existente(repositorio, session):
    usuario = novo_usuario()
    repositorio.salvar(usuario)
    usuario.desativar()
    repositorio.salvar(usuario)
    session.expunge_all()

    assert repositorio.buscar_por_id(usuario.id).ativo is False


def test_rejeita_email_duplicado(repositorio):
    repositorio.salvar(novo_usuario())

    with pytest.raises(IntegrityError):
        repositorio.salvar(novo_usuario(nome='Outra Pessoa'))

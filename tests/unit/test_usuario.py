"""
tests/unit/test_usuario.py

Testes unitarios da entidade de dominio Usuario.
Sem Flask, sem banco, sem mocks - apenas o dominio isolado.
"""

import pytest

from domain.exceptions import UsuarioInvalidoError
from domain.usuario import PapelUsuario, Usuario


def usuario_valido(**overrides):
    dados = dict(
        nome="Teo Marques",
        email="teo@example.com",
        senha_hash="hash-fake-vindo-da-infra",
        papel=PapelUsuario.COMPRADOR,
        ativo=True
    )
    dados.update(overrides)
    return Usuario(**dados)


@pytest.mark.parametrize(
    "papel, ativo, esperado",
    [
        (PapelUsuario.VENDEDOR, True, True),
        (PapelUsuario.VENDEDOR, False, False),
        (PapelUsuario.COMPRADOR, True, False),
    ],
    ids=["vendedor-ativo", "vendedor-desativado", "comprador"],
)
def test_apenas_vendedor_ativo_pode_criar_anuncio(papel, ativo, esperado):
    usuario = usuario_valido(papel=papel, ativo=ativo)
    assert usuario.pode_criar_anuncio() is esperado

def test_funcao_desativar():
    usuario = usuario_valido(ativo=True)
    usuario.desativar()
    assert usuario.ativo is False

@pytest.mark.parametrize(
    "senha",
    ["abc12345678", "somenteletrasaqui", "123456789012"],
    ids=["curta", "somente-letras", "somente-numeros"],
)
def test_rejeita_senha_fraca(senha):
    with pytest.raises(UsuarioInvalidoError):
        Usuario.validar_senha_em_texto_puro(senha)


def test_rejeita_email_invalido():
    with pytest.raises(UsuarioInvalidoError):
        usuario_valido(email="nao-e-um-email")


def test_rejeita_usuario_sem_senha_hash():
    with pytest.raises(UsuarioInvalidoError):
        usuario_valido(senha_hash="")

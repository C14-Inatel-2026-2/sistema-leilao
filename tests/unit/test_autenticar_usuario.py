"""
tests/unit/test_autenticar_usuario.py

Testes unitarios do caso de uso AutenticarUsuario, com repositorio e hasher
substituidos por Mocks.
"""

from unittest.mock import Mock

import pytest

from domain.exceptions import CredenciaisInvalidasError
from domain.usuario import PapelUsuario, Usuario
from use_cases.autenticar_usuario import AutenticarUsuario
from use_cases.interfaces import PasswordHasher, UsuarioRepository

EMAIL = 'teo@example.com'
SENHA = 'senhaForte123'
MENSAGEM = 'Email ou senha invalidos.'


def usuario_cadastrado(**overrides):
    dados = dict(
        nome='Teo Marques',
        email=EMAIL,
        senha_hash='hash-salvo',
        papel=PapelUsuario.COMPRADOR,
    )
    dados.update(overrides)
    return Usuario(**dados)


@pytest.fixture
def repositorio():
    return Mock(spec=UsuarioRepository)


@pytest.fixture
def hasher():
    return Mock(spec=PasswordHasher)


def test_autentica_usuario_ativo_com_credenciais_validas(repositorio, hasher):
    usuario = usuario_cadastrado()
    repositorio.buscar_por_email.return_value = usuario
    hasher.verificar.return_value = True

    resultado = AutenticarUsuario(repositorio, hasher).executar(EMAIL, SENHA)

    assert resultado is usuario
    repositorio.buscar_por_email.assert_called_once_with(EMAIL)
    hasher.verificar.assert_called_once_with(SENHA, 'hash-salvo')


def test_busca_o_email_normalizado(repositorio, hasher):
    repositorio.buscar_por_email.return_value = usuario_cadastrado()
    hasher.verificar.return_value = True

    AutenticarUsuario(repositorio, hasher).executar(' Teo@Example.com', SENHA)

    repositorio.buscar_por_email.assert_called_once_with(EMAIL)


def test_recusa_email_mal_formado_sem_consultar_o_banco(repositorio, hasher):
    with pytest.raises(CredenciaisInvalidasError, match=MENSAGEM):
        AutenticarUsuario(repositorio, hasher).executar('nao-e-email', SENHA)

    repositorio.buscar_por_email.assert_not_called()


def test_recusa_email_inexistente(repositorio, hasher):
    repositorio.buscar_por_email.return_value = None

    with pytest.raises(CredenciaisInvalidasError, match=MENSAGEM):
        AutenticarUsuario(repositorio, hasher).executar(EMAIL, SENHA)

    hasher.verificar.assert_not_called()


def test_recusa_senha_incorreta_com_a_mesma_mensagem(repositorio, hasher):
    repositorio.buscar_por_email.return_value = usuario_cadastrado()
    hasher.verificar.return_value = False

    with pytest.raises(CredenciaisInvalidasError, match=MENSAGEM):
        AutenticarUsuario(repositorio, hasher).executar(EMAIL, SENHA)


def test_recusa_usuario_desativado_com_a_mesma_mensagem(repositorio, hasher):
    repositorio.buscar_por_email.return_value = usuario_cadastrado(ativo=False)
    hasher.verificar.return_value = True

    with pytest.raises(CredenciaisInvalidasError, match=MENSAGEM):
        AutenticarUsuario(repositorio, hasher).executar(EMAIL, SENHA)

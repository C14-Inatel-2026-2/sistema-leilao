"""
tests/unit/test_cadastrar_usuario.py

Testes unitarios do caso de uso CadastrarUsuario.

Repositorio e hasher sao substituidos por Mocks: o teste verifica a
orquestracao do caso de uso (o que e chamado, com quais argumentos e o que
NAO e chamado) sem banco de dados e sem bcrypt.
"""

from unittest.mock import Mock

import pytest

from domain.exceptions import EmailJaCadastradoError
from domain.usuario import PapelUsuario, Usuario
from use_cases.cadastrar_usuario import CadastrarUsuario
from use_cases.interfaces import PasswordHasher, UsuarioRepository

SENHA_VALIDA = "senhaForte123"


@pytest.fixture
def repositorio():
    return Mock(spec=UsuarioRepository)


@pytest.fixture
def hasher():
    return Mock(spec=PasswordHasher)


def test_cadastra_usuario_salvando_apenas_o_hash_da_senha(repositorio, hasher):
    repositorio.buscar_por_email.return_value = None
    hasher.gerar_hash.return_value = "hash-gerado"
    caso_de_uso = CadastrarUsuario(repositorio, hasher)

    usuario = caso_de_uso.executar(
        nome="Teo Marques", email="teo@example.com", senha=SENHA_VALIDA
    )

    hasher.gerar_hash.assert_called_once_with(SENHA_VALIDA)
    repositorio.salvar.assert_called_once_with(usuario)
    assert usuario.senha_hash == "hash-gerado"
    assert usuario.papel == PapelUsuario.COMPRADOR


def test_rejeita_email_ja_cadastrado_sem_gerar_hash_nem_salvar(repositorio, hasher):
    repositorio.buscar_por_email.return_value = Usuario(
        nome="Outra Pessoa",
        email="teo@example.com",
        senha_hash="hash-existente",
        papel=PapelUsuario.VENDEDOR,
    )
    caso_de_uso = CadastrarUsuario(repositorio, hasher)

    with pytest.raises(EmailJaCadastradoError):
        caso_de_uso.executar(
            nome="Teo Marques", email="teo@example.com", senha=SENHA_VALIDA
        )

    hasher.gerar_hash.assert_not_called()
    repositorio.salvar.assert_not_called()

"""
tests/unit/test_email.py

Testes unitarios do Value Object Email.
"""

import pytest

from domain.email import Email
from domain.exceptions import UsuarioInvalidoError


def test_normaliza_maiusculas_e_espacos_nas_pontas():
    assert Email('  Teo@Example.COM ') == 'teo@example.com'


def test_continua_sendo_str():
    email = Email('teo@example.com')

    assert isinstance(email, str)
    assert email.split('@')[1] == 'example.com'


def test_criar_a_partir_de_outro_email_mantem_o_valor():
    assert Email(Email('Teo@Example.com')) == 'teo@example.com'


@pytest.mark.parametrize(
    'valor',
    ['', 'nao-e-um-email', 'teo@', '@example.com', 'teo @example.com', None],
    ids=[
        'vazio',
        'sem-arroba',
        'sem-dominio',
        'sem-usuario',
        'com-espaco',
        'none',
    ],
)
def test_rejeita_email_invalido(valor):
    with pytest.raises(UsuarioInvalidoError):
        Email(valor)

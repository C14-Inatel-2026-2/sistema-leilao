"""
tests/unit/test_password_hasher.py

Testes unitarios do BcryptPasswordHasher. Usa o custo minimo do bcrypt,
para os testes continuarem rapidos.
"""

import pytest

from adapters.security.password_hasher import BcryptPasswordHasher

SENHA = 'senhaForte123'


@pytest.fixture
def hasher():
    return BcryptPasswordHasher(rounds=4)


def test_hash_nao_contem_a_senha_em_texto_puro(hasher):
    assert SENHA not in hasher.gerar_hash(SENHA)


def test_verifica_senha_correta(hasher):
    assert hasher.verificar(SENHA, hasher.gerar_hash(SENHA)) is True


def test_recusa_senha_incorreta(hasher):
    assert hasher.verificar('outraSenha456', hasher.gerar_hash(SENHA)) is False


def test_recusa_sem_erro_senha_acima_de_72_bytes(hasher):
    assert hasher.verificar('a' * 73, hasher.gerar_hash(SENHA)) is False


def test_mesma_senha_gera_hashes_diferentes(hasher):
    assert hasher.gerar_hash(SENHA) != hasher.gerar_hash(SENHA)

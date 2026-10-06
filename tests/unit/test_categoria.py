"""
tests/unit/test_categoria.py

Testes unitarios da entidade de dominio Categoria.
Sem Flask, sem banco, sem mocks - apenas o dominio isolado.
"""

from domain.categoria import Categoria


def categoria_valida(**overrides):
    dados = dict(nome="Eletronicos", ativa=True)
    dados.update(overrides)
    return Categoria(**dados)


def test_inativar_e_ativar_categoria():
    categoria = categoria_valida()
    assert categoria.esta_ativa() is True

    categoria.inativar()
    assert categoria.esta_ativa() is False

    categoria.ativar()
    assert categoria.esta_ativa() is True

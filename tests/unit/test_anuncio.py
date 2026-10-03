"""
tests/unit/test_anuncio.py

Testes unitarios da entidade de dominio Anuncio.
Sem Flask e sem banco. Mocks apenas nos colaboradores
(repositorio de categoria e verificacao de lances).
"""

from decimal import Decimal
from typing import Protocol
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest

from domain.anuncio import Anuncio, TipoAnuncio
from domain.categoria import Categoria
from domain.exceptions import AnuncioInvalidoError


class CategoriaRepository(Protocol):
    def buscar_por_id(self, categoria_id: UUID) -> Categoria | None:
        """Retorna a Categoria com o id informado, ou None se nao existir."""
        ...


def anuncio_valido(**overrides):
    dados = dict(
        titulo="Notebook usado",
        descricao="16 GB RAM, SSD 512 GB",
        preco_referencia=Decimal("1500.00"),
        categoria_id=uuid4(),
        vendedor_id=uuid4(),
    )
    dados.update(overrides)
    return Anuncio(**dados)


@pytest.mark.parametrize(
    "preco",
    [Decimal("0"), Decimal("-1.00")],
    ids=["zero", "negativo"],
)
def test_rejeita_preco_referencia_nao_positivo(preco):
    with pytest.raises(AnuncioInvalidoError):
        anuncio_valido(preco_referencia=preco)


def test_associar_leilao_quando_categoria_ativa():
    categoria = Categoria(nome="Eletronicos", ativa=True)
    repositorio = Mock(spec=CategoriaRepository)
    repositorio.buscar_por_id.return_value = categoria

    anuncio = anuncio_valido(categoria_id=categoria.id)
    categoria_encontrada = repositorio.buscar_por_id(anuncio.categoria_id)

    assert categoria_encontrada.esta_ativa() is True

    leilao_id = uuid4()
    anuncio.associar_leilao(leilao_id)

    assert anuncio.tipo == TipoAnuncio.LEILAO
    assert anuncio.leilao_atual_id == leilao_id
    repositorio.buscar_por_id.assert_called_once_with(anuncio.categoria_id)


def test_rejeita_editar_anuncio_quando_leilao_tem_lances():
    anuncio = anuncio_valido()
    titulo_original = anuncio.titulo
    leilao = Mock()
    leilao.possui_lances.return_value = True

    with pytest.raises(AnuncioInvalidoError):
        anuncio.editar(titulo="Titulo alterado", leilao_com_lances=leilao.possui_lances())

    leilao.possui_lances.assert_called_once()
    assert anuncio.titulo == titulo_original

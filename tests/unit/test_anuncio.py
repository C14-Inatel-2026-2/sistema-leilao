import pytest
from uuid import uuid4
from decimal import Decimal

from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from domain.exceptions import AnuncioInvalidoError

def test_anuncio_valido():
    anuncio = Anuncio(
        titulo="Anuncio de teste",
        descricao="Descricao de teste",
        preco_referencia=Decimal(100.00),
        categoria_id=uuid4(),
        vendedor_id=uuid4(),
    )

    assert anuncio.titulo == "Anuncio de teste"
    assert anuncio.descricao == "Descricao de teste"
    assert anuncio.preco_referencia == 100.00
    assert anuncio.categoria_id == uuid4()
    assert anuncio.vendedor_id == uuid4()
    assert anuncio.status == StatusAnuncio.ATIVO
    assert anuncio.tipo == TipoAnuncio.VENDA_DIRETA
    assert anuncio.criado_em is not None


def test_anuncio_invalido_sem_titulo():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        Anuncio(
            titulo="",
            descricao="Descricao de teste",
            preco_referencia=Decimal(100.00),
            categoria_id=uuid4(),
            vendedor_id=uuid4(),
        )
    assert str(exc_info.value) == "titulo obrigatorio"


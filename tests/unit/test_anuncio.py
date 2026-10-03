import pytest
from uuid import uuid4
from decimal import Decimal

from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from domain.exceptions import AnuncioInvalidoError

def anuncio_valido(**overrides):
    dados = dict(
        titulo="Anuncio de teste",
        descricao="Descricao de teste",
        preco_referencia=Decimal('100.00'),
        categoria_id=uuid4(),
        vendedor_id=uuid4(),
    )
    dados.update(overrides)
    return Anuncio(**dados)

def test_anuncio_valido():
    anuncio = Anuncio(
        titulo="Anuncio de teste",
        descricao="Descricao de teste",
        preco_referencia=Decimal('100.00'),
        categoria_id=uuid4(),
        vendedor_id=uuid4(),
    )

    assert anuncio == anuncio_valido()


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

def test_anuncio_invalido_sem_descricao():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(descricao="")
    assert str(exc_info.value) == "descricao obrigatoria"

def test_anuncio_invalido_sem_preco_referencia():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(preco_referencia=None)
    assert str(exc_info.value) == "preco_referencia obrigatorio"

def test_anuncio_invalido_sem_categoria_id():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(categoria_id=None)
    assert str(exc_info.value) == "categoria_id obrigatoria"
    
def test_anuncio_invalido_sem_vendedor_id():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(vendedor_id=None)
    assert str(exc_info.value) == "vendedor_id obrigatorio"

def test_anuncio_invalido_sem_status():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(status=None)
    assert str(exc_info.value) == "status obrigatorio"

def test_anuncio_invalido_sem_tipo():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(tipo=None)
    assert str(exc_info.value) == "tipo obrigatorio"

def test_anuncio_invalido_sem_criado_em():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(criado_em=None)
    assert str(exc_info.value) == "criado_em obrigatorio"

def test_anuncio_invalido_com_preco_referencia_negativo():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(preco_referencia=Decimal(-100.00))
    assert str(exc_info.value) == "preco_referencia nao pode ser negativo"

def test_anuncio_invalido_com_preco_referencia_zero():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(preco_referencia=Decimal(0.00))
    assert str(exc_info.value) == "preco_referencia nao pode ser zero"

def test_anuncio_invalido_com_preco_referencia_decimal():
    with pytest.raises(AnuncioInvalidoError) as exc_info:
        anuncio_valido(preco_referencia=Decimal(100.001))
    assert str(exc_info.value) == "preco_referencia nao pode ser decimal"

def test_anuncio_invalido_com_preco_referencia_string():
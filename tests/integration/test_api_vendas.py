from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http import HTTPStatus
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.repositories.anuncio_repository import (
    SQLAlchemyAnuncioRepository,
)
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from adapters.repositories.venda_repository import (
    SQLAlchemyVendaRepository,
)
from domain.anuncio import StatusAnuncio
from domain.leilao import Leilao, StatusLeilao
from domain.venda import MetodoPagamento, StatusPagamento
from infra.api.app import create_app
from infra.api.dependencies import get_current_user, get_session
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel
from use_cases.encerrar_leilao import EncerrarLeilao
from use_cases.registrar_venda import RegistrarVenda

INICIO = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
FIM = INICIO + timedelta(hours=2)


def _preparar(session):
    categoria = CategoriaModel(nome='Eletronicos')
    session.add(categoria)
    session.flush()
    anuncio = AnuncioModel(
        titulo='Notebook',
        descricao='Usado',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria.id,
        vendedor_id=uuid4(),
    )
    session.add(anuncio)
    session.flush()
    leilao = Leilao(
        anuncio_id=anuncio.id,
        vendedor_id=anuncio.vendedor_id,
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=INICIO,
        data_final=FIM,
        status=StatusLeilao.ABERTO,
    )
    comprador = uuid4()
    leilao.receber_lance(comprador, Decimal('120.00'), INICIO)
    SQLAlchemyLeilaoRepository(session).salvar(leilao)
    anuncio.leilao_atual_id = leilao.id
    session.commit()
    EncerrarLeilao(
        SQLAlchemyLeilaoRepository(session),
        confirmar=session.commit,
        publicar=lambda _evento: None,
        relogio=lambda: FIM,
    ).executar(leilao.id)
    venda = RegistrarVenda(
        SQLAlchemyLeilaoRepository(session),
        SQLAlchemyVendaRepository(session),
    ).executar(leilao.id)
    session.commit()
    return leilao, venda, comprador


@pytest.fixture
def client(session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _autenticar(client, usuario_id):
    usuario = SimpleNamespace(id=usuario_id)
    client.app.dependency_overrides[get_current_user] = lambda: usuario


def test_pagamento_aprova_venda_leilao_e_anuncio(client, session):
    leilao, venda, comprador = _preparar(session)
    _autenticar(client, comprador)

    resposta = client.post(
        f'/vendas/{venda.id}/pagamento',
        json={'metodo': MetodoPagamento.PIX.value},
    )

    assert resposta.status_code == HTTPStatus.OK
    corpo = resposta.json()
    assert corpo['status'] == StatusPagamento.APROVADO.value
    assert corpo['metodo'] == MetodoPagamento.PIX.value
    assert Decimal(corpo['valor']) == Decimal('120.00')
    session.expire_all()
    assert (
        SQLAlchemyLeilaoRepository(session).buscar_por_id(leilao.id).status
        == StatusLeilao.PAGO
    )
    anuncio = SQLAlchemyAnuncioRepository(session).buscar_por_id(
        leilao.anuncio_id
    )
    assert anuncio.status == StatusAnuncio.VENDIDO


def test_pagamento_de_outro_usuario_retorna_403(client, session):
    _leilao, venda, _comprador = _preparar(session)
    _autenticar(client, uuid4())

    resposta = client.post(
        f'/vendas/{venda.id}/pagamento',
        json={'metodo': MetodoPagamento.CARTAO.value},
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN
    assert venda.status == StatusPagamento.PENDENTE


def test_pagamento_sem_token_retorna_401(client, session):
    _leilao, venda, _comprador = _preparar(session)

    resposta = client.post(
        f'/vendas/{venda.id}/pagamento',
        json={'metodo': MetodoPagamento.PIX.value},
    )

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_cancelar_mantem_leilao_encerrado_e_anuncio_ativo(client, session):
    leilao, venda, comprador = _preparar(session)
    _autenticar(client, comprador)

    resposta = client.post(f'/vendas/{venda.id}/cancelar')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['status'] == StatusPagamento.CANCELADO.value
    session.expire_all()
    assert (
        SQLAlchemyLeilaoRepository(session).buscar_por_id(leilao.id).status
        == StatusLeilao.ENCERRADO
    )
    anuncio = SQLAlchemyAnuncioRepository(session).buscar_por_id(
        leilao.anuncio_id
    )
    assert anuncio.status == StatusAnuncio.ATIVO


def test_get_venda_para_vendedor_e_vencedor(client, session):
    leilao, venda, comprador = _preparar(session)

    _autenticar(client, comprador)
    do_vencedor = client.get(f'/leiloes/{leilao.id}/venda')
    _autenticar(client, leilao.vendedor_id)
    do_vendedor = client.get(f'/leiloes/{leilao.id}/venda')

    assert do_vencedor.status_code == HTTPStatus.OK
    assert do_vendedor.status_code == HTTPStatus.OK
    assert do_vencedor.json()['id'] == str(venda.id)
    assert do_vendedor.json()['comprador_id'] == str(comprador)


def test_get_venda_de_terceiro_retorna_403(client, session):
    leilao, _venda, _comprador = _preparar(session)
    _autenticar(client, uuid4())

    resposta = client.get(f'/leiloes/{leilao.id}/venda')

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_get_venda_inexistente_retorna_404(client):
    _autenticar(client, uuid4())

    resposta = client.get(f'/leiloes/{uuid4()}/venda')

    assert resposta.status_code == HTTPStatus.NOT_FOUND

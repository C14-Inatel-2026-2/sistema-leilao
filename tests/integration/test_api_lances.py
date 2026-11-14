from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http import HTTPStatus
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.leilao import Leilao, StatusLeilao
from infra.api.app import create_app
from infra.api.dependencies import get_current_user, get_session
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel
from use_cases.dar_lance import DarLance

INICIO = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def _novo_leilao(session, inicio) -> Leilao:
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
        data_inicio=inicio,
        data_final=inicio + timedelta(hours=2),
        status=StatusLeilao.ABERTO,
    )
    SQLAlchemyLeilaoRepository(session).salvar(leilao)
    return leilao


@pytest.fixture
def leilao(session) -> Leilao:
    return _novo_leilao(session, INICIO)


@pytest.fixture
def leilao_aberto(session) -> Leilao:
    # Janela em volta do relogio real: o endpoint usa a hora do servidor.
    return _novo_leilao(
        session, datetime.now(timezone.utc) - timedelta(hours=1)
    )


@pytest.fixture
def client(session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _dar_lances(session, leilao, valores):
    publicados = []
    for minuto, valor in enumerate(valores, start=1):
        DarLance(
            SQLAlchemyLeilaoRepository(session),
            confirmar=session.commit,
            publicar=publicados.append,
            relogio=lambda m=minuto: INICIO + timedelta(minutes=m),
        ).executar(leilao.id, uuid4(), Decimal(valor))
    return publicados


def test_dar_lance_persiste_e_reconstroi_o_leilao(session, leilao):
    publicados = _dar_lances(session, leilao, ['100.00', '110.00'])
    session.expire_all()

    lido = SQLAlchemyLeilaoRepository(session).buscar_com_lock(leilao.id)

    assert [lance.valor for lance in lido.lances] == [
        Decimal('100.00'),
        Decimal('110.00'),
    ]
    assert lido.valor_minimo_proximo_lance() == Decimal('120.00')
    assert [ev.lance_id for ev in publicados] == [
        lance.id for lance in lido.lances
    ]


def test_get_lances_retorna_do_mais_recente_ao_mais_antigo(
    client, session, leilao
):
    _dar_lances(session, leilao, ['100.00', '110.00', '125.00'])

    resposta = client.get(f'/leiloes/{leilao.id}/lances')

    assert resposta.status_code == HTTPStatus.OK
    corpo = resposta.json()
    assert [Decimal(lance['valor']) for lance in corpo] == [
        Decimal('125.00'),
        Decimal('110.00'),
        Decimal('100.00'),
    ]
    assert set(corpo[0]) == {
        'id',
        'leilao_id',
        'comprador_id',
        'valor',
        'criado_em',
    }
    assert corpo[0]['leilao_id'] == str(leilao.id)


def test_get_lances_de_leilao_sem_lances_retorna_lista_vazia(client, leilao):
    resposta = client.get(f'/leiloes/{leilao.id}/lances')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == []


def test_get_lances_de_leilao_inexistente_retorna_404(client):
    resposta = client.get(f'/leiloes/{uuid4()}/lances')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_get_lances_com_id_invalido_retorna_422(client):
    assert (
        client.get('/leiloes/abc/lances').status_code
        == HTTPStatus.UNPROCESSABLE_ENTITY
    )


def _autenticar(client, usuario_id=None):
    usuario = SimpleNamespace(id=usuario_id or uuid4())
    client.app.dependency_overrides[get_current_user] = lambda: usuario
    return usuario


def test_post_lance_registra_lance_do_usuario_autenticado(
    client, leilao_aberto
):
    comprador = _autenticar(client)

    resposta = client.post(
        f'/leiloes/{leilao_aberto.id}/lances', json={'valor': '150.00'}
    )

    assert resposta.status_code == HTTPStatus.CREATED
    corpo = resposta.json()
    assert corpo['comprador_id'] == str(comprador.id)
    assert Decimal(corpo['valor']) == Decimal('150.00')
    historico = client.get(f'/leiloes/{leilao_aberto.id}/lances').json()
    assert [lance['id'] for lance in historico] == [corpo['id']]


def test_post_lance_sem_token_retorna_401(client, leilao_aberto):
    resposta = client.post(
        f'/leiloes/{leilao_aberto.id}/lances', json={'valor': '150.00'}
    )

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_post_lance_abaixo_do_minimo_retorna_400(client, leilao_aberto):
    _autenticar(client)

    resposta = client.post(
        f'/leiloes/{leilao_aberto.id}/lances', json={'valor': '99.99'}
    )

    assert resposta.status_code == HTTPStatus.BAD_REQUEST


def test_post_lance_do_vendedor_no_proprio_leilao_retorna_400(
    client, leilao_aberto
):
    _autenticar(client, usuario_id=leilao_aberto.vendedor_id)

    resposta = client.post(
        f'/leiloes/{leilao_aberto.id}/lances', json={'valor': '150.00'}
    )

    assert resposta.status_code == HTTPStatus.BAD_REQUEST


def test_post_lance_fora_da_janela_retorna_400(client, leilao):
    _autenticar(client)

    resposta = client.post(
        f'/leiloes/{leilao.id}/lances', json={'valor': '150.00'}
    )

    assert resposta.status_code == HTTPStatus.BAD_REQUEST


def test_post_lance_em_leilao_inexistente_retorna_404(client):
    _autenticar(client)

    resposta = client.post(f'/leiloes/{uuid4()}/lances', json={'valor': '1'})

    assert resposta.status_code == HTTPStatus.NOT_FOUND

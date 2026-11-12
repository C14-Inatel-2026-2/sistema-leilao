from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)
from adapters.repositories.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from domain.categoria import Categoria
from domain.usuario import PapelUsuario, Usuario
from infra.api.app import create_app
from infra.api.dependencies import get_session


@pytest.fixture
def vendedor(session):
    usuario = Usuario(
        nome='Ana Vendedora',
        email=f'{uuid4()}@example.com',
        senha_hash='hash',
        papel=PapelUsuario.VENDEDOR,
    )
    SQLAlchemyUsuarioRepository(session).salvar(usuario)
    return usuario


@pytest.fixture
def categoria(session):
    item = Categoria(nome='Eletronicos')
    SQLAlchemyCategoriaRepository(session).salvar(item)
    return item


@pytest.fixture
def client(session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _corpo(vendedor, categoria, **overrides):
    inicio = datetime.now(timezone.utc) + timedelta(days=1)
    corpo = {
        'titulo': 'Notebook',
        'descricao': 'Usado',
        'preco_referencia': '1500.00',
        'categoria_id': str(categoria.id),
        'vendedor_id': str(vendedor.id),
        'preco_inicial': '500.00',
        'incremento_minimo': '50.00',
        'data_inicio': inicio.isoformat(),
        'data_final': (inicio + timedelta(days=1)).isoformat(),
    }
    corpo.update(overrides)
    return corpo


def test_post_cria_anuncio_agendado_e_get_lista(client, vendedor, categoria):
    resposta = client.post('/anuncios', json=_corpo(vendedor, categoria))

    assert resposta.status_code == HTTPStatus.CREATED
    corpo = resposta.json()
    assert corpo['anuncio']['tipo'] == 'LEILAO'
    assert corpo['leilao']['status'] == 'AGENDADO'
    assert corpo['anuncio']['leilao_atual_id'] == corpo['leilao']['id']
    assert corpo['anuncio']['vendedor_id'] == str(vendedor.id)

    listagem = client.get('/anuncios')

    assert listagem.status_code == HTTPStatus.OK
    assert [item['titulo'] for item in listagem.json()] == ['Notebook']


def test_post_abre_leilao_quando_inicio_ja_caiu_na_janela(
    client, vendedor, categoria
):
    inicio = datetime.now(timezone.utc) - timedelta(minutes=5)
    fim = datetime.now(timezone.utc) + timedelta(hours=2)

    resposta = client.post(
        '/anuncios',
        json=_corpo(
            vendedor,
            categoria,
            data_inicio=inicio.isoformat(),
            data_final=fim.isoformat(),
        ),
    )

    assert resposta.status_code == HTTPStatus.CREATED
    assert resposta.json()['leilao']['status'] == 'ABERTO'


def test_post_rejeita_vendedor_inexistente(client, categoria):
    inexistente = Usuario(
        nome='Ninguem Silva',
        email='ninguem@example.com',
        senha_hash='hash',
        papel=PapelUsuario.VENDEDOR,
    )

    resposta = client.post('/anuncios', json=_corpo(inexistente, categoria))

    assert resposta.status_code == HTTPStatus.BAD_REQUEST
    assert resposta.json()['detail'] == 'vendedor nao encontrado'


def test_post_rejeita_preco_inicial_invalido(client, vendedor, categoria):
    resposta = client.post(
        '/anuncios',
        json=_corpo(vendedor, categoria, preco_inicial='0'),
    )

    assert resposta.status_code == HTTPStatus.BAD_REQUEST


def test_post_sem_titulo_retorna_422(client, vendedor, categoria):
    corpo = _corpo(vendedor, categoria)
    del corpo['titulo']

    resposta = client.post('/anuncios', json=corpo)

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_filtra_por_texto_e_rejeita_status_invalido(
    client, vendedor, categoria
):
    client.post(
        '/anuncios',
        json=_corpo(vendedor, categoria, titulo='Notebook'),
    )
    client.post(
        '/anuncios',
        json=_corpo(
            vendedor,
            categoria,
            titulo='Cadeira',
            descricao='Escritorio',
        ),
    )

    por_texto = client.get('/anuncios', params={'texto': 'cadeira'})
    invalido = client.get('/anuncios', params={'status': 'nope'})

    assert por_texto.status_code == HTTPStatus.OK
    assert [item['titulo'] for item in por_texto.json()] == ['Cadeira']
    assert invalido.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_get_categoria_inexistente_retorna_lista_vazia(client):
    resposta = client.get('/anuncios', params={'categoria_id': str(uuid4())})

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json() == []

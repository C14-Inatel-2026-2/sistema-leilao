from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http import HTTPStatus
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.repositories.anuncio_repository import (
    SQLAlchemyAnuncioRepository,
)
from adapters.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)
from adapters.repositories.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from domain.anuncio import StatusAnuncio
from domain.categoria import Categoria
from domain.usuario import PapelUsuario, Usuario
from infra.api.app import create_app
from infra.api.dependencies import get_current_user, get_session


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


def _autenticar(client, usuario_id):
    usuario = SimpleNamespace(id=usuario_id)
    client.app.dependency_overrides[get_current_user] = lambda: usuario


def _criar(client, vendedor, categoria, **overrides):
    resposta = client.post(
        '/anuncios', json=_corpo(vendedor, categoria, **overrides)
    )
    assert resposta.status_code == HTTPStatus.CREATED
    return resposta.json()


def test_patch_dono_atualiza_anuncio(client, vendedor, categoria):
    criado = _criar(client, vendedor, categoria)
    anuncio_id = criado['anuncio']['id']
    _autenticar(client, vendedor.id)

    resposta = client.patch(
        f'/anuncios/{anuncio_id}',
        json={
            'titulo': 'Notebook revisado',
            'descricao': 'SSD 512 GB',
            'preco_referencia': '1400.00',
        },
    )

    assert resposta.status_code == HTTPStatus.OK
    corpo = resposta.json()
    assert corpo['titulo'] == 'Notebook revisado'
    assert corpo['descricao'] == 'SSD 512 GB'
    assert Decimal(corpo['preco_referencia']) == Decimal('1400.00')
    assert corpo['vendedor_id'] == str(vendedor.id)


def test_patch_de_outro_usuario_retorna_403(client, vendedor, categoria):
    criado = _criar(client, vendedor, categoria)
    _autenticar(client, uuid4())

    resposta = client.patch(
        f'/anuncios/{criado["anuncio"]["id"]}',
        json={'titulo': 'Tomado'},
    )

    assert resposta.status_code == HTTPStatus.FORBIDDEN


def test_patch_anuncio_inexistente_retorna_404(client, vendedor):
    _autenticar(client, vendedor.id)

    resposta = client.patch(
        f'/anuncios/{uuid4()}', json={'titulo': 'Nao existe'}
    )

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_patch_sem_token_retorna_401(client, vendedor, categoria):
    criado = _criar(client, vendedor, categoria)

    resposta = client.patch(
        f'/anuncios/{criado["anuncio"]["id"]}',
        json={'titulo': 'Sem login'},
    )

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED


def test_patch_com_lances_retorna_400(client, session, vendedor, categoria):
    inicio = datetime.now(timezone.utc) - timedelta(minutes=5)
    criado = _criar(
        client,
        vendedor,
        categoria,
        data_inicio=inicio.isoformat(),
        data_final=(inicio + timedelta(hours=2)).isoformat(),
    )
    leilao_id = criado['leilao']['id']
    _autenticar(client, uuid4())
    lance = client.post(
        f'/leiloes/{leilao_id}/lances', json={'valor': '500.00'}
    )
    assert lance.status_code == HTTPStatus.CREATED
    _autenticar(client, vendedor.id)

    resposta = client.patch(
        f'/anuncios/{criado["anuncio"]["id"]}',
        json={'titulo': 'Mudou no meio'},
    )

    assert resposta.status_code == HTTPStatus.BAD_REQUEST


def test_post_inativar_marca_anuncio_inativo(client, vendedor, categoria):
    criado = _criar(client, vendedor, categoria)
    _autenticar(client, vendedor.id)

    resposta = client.post(f'/anuncios/{criado["anuncio"]["id"]}/inativar')

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['status'] == 'INATIVO'


def test_post_inativar_vendido_retorna_400(
    client, session, vendedor, categoria
):
    criado = _criar(client, vendedor, categoria)
    anuncio_id = UUID(criado['anuncio']['id'])
    repositorio = SQLAlchemyAnuncioRepository(session)
    anuncio = repositorio.buscar_por_id(anuncio_id)
    anuncio.status = StatusAnuncio.VENDIDO
    repositorio.salvar(anuncio)
    session.commit()
    _autenticar(client, vendedor.id)

    resposta = client.post(f'/anuncios/{anuncio_id}/inativar')

    assert resposta.status_code == HTTPStatus.BAD_REQUEST


def test_post_inativar_de_outro_usuario_retorna_403(
    client, vendedor, categoria
):
    criado = _criar(client, vendedor, categoria)
    _autenticar(client, uuid4())

    resposta = client.post(f'/anuncios/{criado["anuncio"]["id"]}/inativar')

    assert resposta.status_code == HTTPStatus.FORBIDDEN

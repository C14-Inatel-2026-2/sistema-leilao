"""
tests/integration/test_api_auth.py

Testes de integracao das rotas /auth (cadastro, login e perfil), com SQLite
em memoria. Hasher com custo minimo e TokenService com chave de teste.
"""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from adapters.security.password_hasher import BcryptPasswordHasher
from adapters.security.token_service import TokenService
from infra.api.app import create_app
from infra.api.dependencies import (
    get_password_hasher,
    get_session,
    get_token_service,
)

SENHA = 'senhaForte123'
CADASTRO = {
    'nome': 'Teo Marques',
    'email': 'teo@example.com',
    'senha': SENHA,
}


@pytest.fixture
def client(session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_password_hasher] = lambda: (
        BcryptPasswordHasher(rounds=4)
    )
    app.dependency_overrides[get_token_service] = lambda: TokenService(
        'chave-de-teste-com-tamanho-suficiente-32b', 'HS256', 60
    )
    return TestClient(app)


def _cadastrar(client, **overrides):
    return client.post('/auth/register', json={**CADASTRO, **overrides})


def _login(client, email='teo@example.com', senha=SENHA):
    return client.post(
        '/auth/login', data={'username': email, 'password': senha}
    )


def test_cadastro_retorna_201_sem_expor_a_senha(client):
    resposta = _cadastrar(client)

    assert resposta.status_code == HTTPStatus.CREATED
    corpo = resposta.json()
    assert corpo['email'] == 'teo@example.com'
    assert corpo['papel'] == 'comprador'
    assert 'senha' not in corpo
    assert 'senha_hash' not in corpo


def test_cadastro_com_email_repetido_retorna_409(client):
    _cadastrar(client)

    assert _cadastrar(client).status_code == HTTPStatus.CONFLICT


@pytest.mark.parametrize(
    'campo',
    [{'senha': 'curta1'}, {'email': 'nao-e-um-email'}, {'nome': 'T'}],
    ids=['senha-fraca', 'email-invalido', 'nome-curto'],
)
def test_cadastro_com_dados_invalidos_retorna_400(client, campo):
    assert _cadastrar(client, **campo).status_code == HTTPStatus.BAD_REQUEST


def test_login_retorna_token_bearer(client):
    _cadastrar(client)

    resposta = _login(client)

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['token_type'] == 'bearer'
    assert resposta.json()['access_token']


@pytest.mark.parametrize(
    ('email', 'senha'),
    [('teo@example.com', 'senhaErrada456'), ('ninguem@example.com', SENHA)],
    ids=['senha-errada', 'email-inexistente'],
)
def test_login_com_credenciais_invalidas_retorna_401(client, email, senha):
    _cadastrar(client)

    assert _login(client, email, senha).status_code == HTTPStatus.UNAUTHORIZED


def test_perfil_com_token_valido_retorna_o_usuario(client):
    _cadastrar(client)
    token = _login(client).json()['access_token']

    resposta = client.get(
        '/auth/me', headers={'Authorization': f'Bearer {token}'}
    )

    assert resposta.status_code == HTTPStatus.OK
    assert resposta.json()['email'] == 'teo@example.com'


@pytest.mark.parametrize(
    'headers',
    [{}, {'Authorization': 'Bearer token-invalido'}],
    ids=['sem-token', 'token-invalido'],
)
def test_perfil_sem_token_valido_retorna_401(client, headers):
    resposta = client.get('/auth/me', headers=headers)

    assert resposta.status_code == HTTPStatus.UNAUTHORIZED

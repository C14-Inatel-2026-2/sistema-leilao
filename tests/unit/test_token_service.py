"""
tests/unit/test_token_service.py

Testes unitarios do TokenService, sem banco e sem framework web.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from adapters.security.token_service import TokenInvalidoError, TokenService
from domain.usuario import PapelUsuario, Usuario

CHAVE = 'chave-de-teste-com-tamanho-suficiente-32b'
ALGORITMO = 'HS256'


@pytest.fixture
def usuario():
    return Usuario(
        nome='Teo Marques',
        email='teo@example.com',
        senha_hash='hash-fake',
        papel=PapelUsuario.VENDEDOR,
    )


@pytest.fixture
def servico():
    return TokenService(CHAVE, ALGORITMO, expiracao_minutos=60)


def test_token_contem_sub_role_e_exp(servico, usuario):
    claims = jwt.decode(servico.gerar(usuario), CHAVE, algorithms=[ALGORITMO])

    assert claims['sub'] == str(usuario.id)
    assert claims['role'] == 'vendedor'
    assert 'exp' in claims


def test_valida_token_e_devolve_os_dados_do_usuario(servico, usuario):
    dados = servico.validar(servico.gerar(usuario))

    assert dados.usuario_id == usuario.id
    assert dados.papel == PapelUsuario.VENDEDOR


def test_rejeita_token_expirado(usuario):
    servico = TokenService(CHAVE, ALGORITMO, expiracao_minutos=-1)

    with pytest.raises(TokenInvalidoError):
        servico.validar(servico.gerar(usuario))


def test_rejeita_token_adulterado(servico, usuario):
    cabecalho, _, assinatura = servico.gerar(usuario).split('.')
    outro = jwt.encode(
        {'sub': 'outro', 'role': 'vendedor'}, CHAVE, ALGORITMO
    ).split('.')[1]

    with pytest.raises(TokenInvalidoError):
        servico.validar(f'{cabecalho}.{outro}.{assinatura}')


def test_rejeita_token_assinado_com_outra_chave(servico, usuario):
    outro_servico = TokenService(
        'outra-chave-de-teste-com-tamanho-suficiente', ALGORITMO, 60
    )

    with pytest.raises(TokenInvalidoError):
        servico.validar(outro_servico.gerar(usuario))


def test_rejeita_token_sem_assinatura(servico, usuario):
    claims = {
        'sub': str(usuario.id),
        'role': 'vendedor',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    token = jwt.encode(claims, key=None, algorithm='none')

    with pytest.raises(TokenInvalidoError):
        servico.validar(token)


@pytest.mark.parametrize(
    'claims',
    [
        {'sub': 'nao-e-uuid', 'role': 'vendedor'},
        {'sub': '6f1c2c1e-0000-4000-8000-000000000000', 'role': 'rei'},
    ],
    ids=['sub-invalido', 'role-invalido'],
)
def test_rejeita_token_com_conteudo_inesperado(servico, claims):
    expiracao = datetime.now(timezone.utc) + timedelta(minutes=5)
    token = jwt.encode({**claims, 'exp': expiracao}, CHAVE, ALGORITMO)

    with pytest.raises(TokenInvalidoError):
        servico.validar(token)


def test_from_env_usa_as_variaveis_de_ambiente(monkeypatch, usuario):
    monkeypatch.setenv('JWT_SECRET_KEY', CHAVE)
    monkeypatch.setenv('JWT_ALGORITHM', ALGORITMO)
    monkeypatch.setenv('ACCESS_TOKEN_EXPIRE_MINUTES', '-1')
    servico = TokenService.from_env()

    with pytest.raises(TokenInvalidoError):
        servico.validar(servico.gerar(usuario))


def test_from_env_exige_a_chave_secreta(monkeypatch):
    monkeypatch.delenv('JWT_SECRET_KEY', raising=False)

    with pytest.raises(RuntimeError):
        TokenService.from_env()

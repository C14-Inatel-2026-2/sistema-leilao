"""
tests/integration/test_api_catalogo.py

Fase red das rotas de catalogo.

Dependencias em infra.api.dependencies:
- get_db: gera a Session usada pelos repositorios
- get_vendedor_id: UUID do vendedor autenticado

O vendedor nao vai no corpo. Os testes trocam as duas dependencias
com app.dependency_overrides.

POST /anuncios -> 201
Corpo: titulo, descricao, preco_referencia, categoria_id.
Opcional: leilao = {preco_inicial, incremento_minimo, data_inicio,
data_final}. Sem leilao, tipo VENDA_DIRETA e leilao_atual_id nulo.
Com leilao, tipo LEILAO, leilao_atual_id preenchido e objeto leilao
com id, status AGENDADO, precos e datas.

GET /anuncios -> 200, lista JSON.
Query: categoria_id, tipo, status.

DomainError vira HTTP 400:
{"codigo": "<str nao vazia>", "mensagem": "<str nao vazia>"}.
Categoria inativa rejeita o POST e nao grava anuncio.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from domain.anuncio import StatusAnuncio, TipoAnuncio
from domain.leilao import StatusLeilao
from infra.api.app import create_app
from infra.api.dependencies import get_db, get_vendedor_id
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel
from infra.db.models.leilao import LeilaoModel

_INICIO = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
_FIM = _INICIO + timedelta(hours=2)


@pytest.fixture
def vendedor_id():
    return uuid4()


def _categoria(session, nome, *, ativa=True) -> CategoriaModel:
    categoria = CategoriaModel(nome=nome, ativa=ativa)
    session.add(categoria)
    session.flush()
    return categoria


def _anuncio(session, categoria, **overrides) -> AnuncioModel:
    dados = dict(
        titulo='Notebook',
        descricao='Usado, funcionando',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria.id,
        vendedor_id=UUID(int=1),
        tipo=TipoAnuncio.VENDA_DIRETA,
        status=StatusAnuncio.ATIVO,
    )
    dados.update(overrides)
    anuncio = AnuncioModel(**dados)
    session.add(anuncio)
    session.flush()
    return anuncio


def _corpo(categoria, **extras):
    corpo = {
        'titulo': 'Notebook',
        'descricao': 'Usado, funcionando',
        'preco_referencia': '1500.00',
        'categoria_id': str(categoria.id),
    }
    corpo.update(extras)
    return corpo


def _decimal(valor) -> Decimal:
    return Decimal(str(valor))


def _instante(valor: str) -> datetime:
    return datetime.fromisoformat(valor.replace('Z', '+00:00'))


def _client(session, vendedor_id):
    app = create_app()

    def _db():
        yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_vendedor_id] = lambda: vendedor_id
    return app


def test_post_anuncios_cria_venda_direta_retorna_201(session, vendedor_id):
    categoria = _categoria(session, 'Eletronicos')
    app = _client(session, vendedor_id)

    with TestClient(app) as api:
        response = api.post('/anuncios', json=_corpo(categoria))

    assert response.status_code == HTTPStatus.CREATED
    body = response.json()
    assert body['titulo'] == 'Notebook'
    assert body['descricao'] == 'Usado, funcionando'
    assert _decimal(body['preco_referencia']) == Decimal('1500.00')
    assert body['categoria_id'] == str(categoria.id)
    assert body['vendedor_id'] == str(vendedor_id)
    assert body['tipo'] == TipoAnuncio.VENDA_DIRETA.value
    assert body['status'] == StatusAnuncio.ATIVO.value
    assert body['leilao_atual_id'] is None
    assert isinstance(_instante(body['criado_em']), datetime)

    session.expire_all()
    gravado = session.get(AnuncioModel, UUID(body['id']))
    assert gravado is not None
    assert gravado.vendedor_id == vendedor_id
    assert gravado.tipo is TipoAnuncio.VENDA_DIRETA
    assert gravado.leilao_atual_id is None


def test_post_anuncios_com_leilao_cria_anuncio_e_leilao_retorna_201(
    session, vendedor_id
):
    categoria = _categoria(session, 'Eletronicos')
    app = _client(session, vendedor_id)
    leilao = {
        'preco_inicial': '100.00',
        'incremento_minimo': '5.00',
        'data_inicio': _INICIO.isoformat(),
        'data_final': _FIM.isoformat(),
    }

    with TestClient(app) as api:
        response = api.post(
            '/anuncios',
            json=_corpo(categoria, leilao=leilao),
        )

    assert response.status_code == HTTPStatus.CREATED
    body = response.json()
    assert body['tipo'] == TipoAnuncio.LEILAO.value
    assert body['vendedor_id'] == str(vendedor_id)
    assert body['leilao_atual_id'] == body['leilao']['id']
    assert body['leilao']['status'] == StatusLeilao.AGENDADO.value
    assert _decimal(body['leilao']['preco_inicial']) == Decimal('100.00')
    assert _decimal(body['leilao']['incremento_minimo']) == Decimal('5.00')
    assert _instante(body['leilao']['data_inicio']) == _INICIO
    assert _instante(body['leilao']['data_final']) == _FIM
    assert body['leilao']['anuncio_id'] == body['id']
    assert body['leilao']['vendedor_id'] == str(vendedor_id)

    session.expire_all()
    anuncio = session.get(AnuncioModel, UUID(body['id']))
    gravado = session.get(LeilaoModel, UUID(body['leilao']['id']))
    assert anuncio is not None
    assert gravado is not None
    assert anuncio.leilao_atual_id == gravado.id
    assert anuncio.tipo is TipoAnuncio.LEILAO
    assert gravado.anuncio_id == anuncio.id
    assert gravado.status is StatusLeilao.AGENDADO
    assert gravado.vendedor_id == vendedor_id
    assert gravado.preco_inicial == Decimal('100.00')


def test_post_anuncios_com_categoria_inativa_retorna_400_domain_error(
    session, vendedor_id
):
    categoria = _categoria(session, 'Arquivo', ativa=False)
    app = _client(session, vendedor_id)

    with TestClient(app) as api:
        response = api.post('/anuncios', json=_corpo(categoria))

    assert response.status_code == HTTPStatus.BAD_REQUEST
    body = response.json()
    assert isinstance(body['codigo'], str)
    assert body['codigo']
    assert isinstance(body['mensagem'], str)
    assert body['mensagem']
    session.expire_all()
    gravados = list(session.scalars(select(AnuncioModel)))
    assert gravados == []


def test_get_anuncios_filtra_por_categoria_tipo_e_status(session, vendedor_id):
    categoria_a = _categoria(session, 'Eletronicos')
    categoria_b = _categoria(session, 'Moveis')
    alvo = _anuncio(session, categoria_a, titulo='Notebook alvo')
    _anuncio(
        session,
        categoria_a,
        titulo='Notebook leilao',
        tipo=TipoAnuncio.LEILAO,
    )
    _anuncio(
        session,
        categoria_a,
        titulo='Notebook inativo',
        status=StatusAnuncio.INATIVO,
    )
    _anuncio(session, categoria_b, titulo='Cadeira')
    app = _client(session, vendedor_id)

    with TestClient(app) as api:
        response = api.get(
            '/anuncios',
            params={
                'categoria_id': str(categoria_a.id),
                'tipo': TipoAnuncio.VENDA_DIRETA.value,
                'status': StatusAnuncio.ATIVO.value,
            },
        )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert [item['id'] for item in body] == [str(alvo.id)]
    assert body[0]['titulo'] == 'Notebook alvo'
    assert body[0]['tipo'] == TipoAnuncio.VENDA_DIRETA.value
    assert body[0]['status'] == StatusAnuncio.ATIVO.value
    assert body[0]['categoria_id'] == str(categoria_a.id)

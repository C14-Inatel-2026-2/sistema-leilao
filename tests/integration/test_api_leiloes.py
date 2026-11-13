from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http import HTTPStatus
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from adapters.events import publish, register_auditoria_handlers
from adapters.repositories.auditoria_repository import (
    SQLAlchemyAuditoriaRepository,
)
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.events import LanceRealizado, LeilaoEncerrado
from domain.lance import Lance
from domain.leilao import Leilao, StatusLeilao
from infra.api.app import create_app
from infra.api.dependencies import get_session
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel

INICIO = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def leilao(session) -> Leilao:
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
        data_final=INICIO + timedelta(hours=2),
        status=StatusLeilao.ABERTO,
    )
    SQLAlchemyLeilaoRepository(session).salvar(leilao)
    return leilao


@pytest.fixture
def client(session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def test_get_leilao_ativo_sem_lances_retorna_detalhes(client, leilao):
    resposta = client.get(f'/leiloes/{leilao.id}')

    assert resposta.status_code == HTTPStatus.OK
    corpo = resposta.json()
    assert corpo['id'] == str(leilao.id)
    assert corpo['status'] == 'ABERTO'
    assert Decimal(corpo['preco_inicial']) == Decimal('100.00')
    assert Decimal(corpo['incremento_minimo']) == Decimal('10.00')
    assert corpo['maior_lance'] is None
    assert corpo['vencedor_id'] is None
    assert corpo['valor_arremate'] is None


def test_get_leilao_ativo_com_lances_retorna_maior_lance(
    client, session, leilao
):
    repo = SQLAlchemyLeilaoRepository(session)
    leilao.lances.append(
        Lance(
            id=uuid4(),
            leilao_id=leilao.id,
            comprador_id=uuid4(),
            valor=Decimal('110.00'),
            criado_em=INICIO + timedelta(minutes=1),
        )
    )
    leilao.lances.append(
        Lance(
            id=uuid4(),
            leilao_id=leilao.id,
            comprador_id=uuid4(),
            valor=Decimal('150.00'),
            criado_em=INICIO + timedelta(minutes=2),
        )
    )
    repo.salvar(leilao)
    session.flush()

    resposta = client.get(f'/leiloes/{leilao.id}')

    assert resposta.status_code == HTTPStatus.OK
    corpo = resposta.json()
    assert Decimal(corpo['maior_lance']) == Decimal('150.00')


def test_get_leilao_encerrado_com_vencedor(client, session, leilao):
    repo = SQLAlchemyLeilaoRepository(session)
    vencedor_id = uuid4()
    leilao.status = StatusLeilao.ENCERRADO
    leilao.vencedor_id = vencedor_id
    leilao.valor_arremate = Decimal('200.00')
    repo.salvar(leilao)
    session.flush()

    resposta = client.get(f'/leiloes/{leilao.id}')

    assert resposta.status_code == HTTPStatus.OK
    corpo = resposta.json()
    assert corpo['status'] == 'ENCERRADO'
    assert corpo['vencedor_id'] == str(vencedor_id)
    assert Decimal(corpo['valor_arremate']) == Decimal('200.00')


def test_get_leilao_inexistente_retorna_404(client):
    resposta = client.get(f'/leiloes/{uuid4()}')

    assert resposta.status_code == HTTPStatus.NOT_FOUND


def test_get_leilao_id_invalido_retorna_422(client):
    resposta = client.get('/leiloes/invalido')

    assert resposta.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_auditoria_via_eventos_sem_acoplar_rota_de_consulta(
    client, session, leilao
):
    auditoria_repo = SQLAlchemyAuditoriaRepository(session)
    register_auditoria_handlers(auditoria_repo)

    lance_id = uuid4()
    comprador_id = uuid4()
    publish(
        LanceRealizado(
            leilao_id=leilao.id,
            lance_id=lance_id,
            usuario_id=comprador_id,
            valor=Decimal('180.00'),
            data_hora=INICIO + timedelta(minutes=5),
        )
    )
    publish(
        LeilaoEncerrado(
            leilao_id=leilao.id,
            vencedor_id=comprador_id,
            valor_final=Decimal('180.00'),
            data_encerramento=INICIO + timedelta(minutes=10),
            motivo='tempo_esgotado',
        )
    )

    # A rota de consulta continua funcionando sem depender de auditoria
    resposta = client.get(f'/leiloes/{leilao.id}')
    assert resposta.status_code == HTTPStatus.OK

    # E os eventos foram gravados na auditoria com fidelidade
    registros = auditoria_repo.listar_por_leilao(leilao.id)
    esperados = ['LANCE_REALIZADO', 'LEILAO_ENCERRADO']
    assert len(registros) == len(esperados)
    assert [r.tipo_evento for r in registros] == esperados
    assert registros[0].valor == Decimal('180.00')
    assert registros[1].valor == Decimal('180.00')
    assert registros[1].motivo == 'tempo_esgotado'

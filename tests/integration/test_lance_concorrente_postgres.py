import os
import threading
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.exceptions import LanceInvalidoError
from domain.leilao import Leilao, StatusLeilao
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel
from use_cases.dar_lance import DarLance

DATABASE_URL = os.getenv('DATABASE_URL', '')

pytestmark = pytest.mark.skipif(
    not DATABASE_URL.startswith('postgresql'),
    reason='FOR UPDATE so e exercitado no PostgreSQL (alembic upgrade head)',
)


@pytest.fixture
def fabrica():
    engine = create_engine(DATABASE_URL)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def leilao(fabrica):
    agora = datetime.now(timezone.utc)
    with fabrica() as session:
        categoria = CategoriaModel(nome='Teste concorrencia')
        session.add(categoria)
        session.flush()
        anuncio = AnuncioModel(
            titulo='Item',
            descricao='Item',
            preco_referencia=Decimal('100.00'),
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
            data_inicio=agora - timedelta(hours=1),
            data_final=agora + timedelta(hours=1),
            status=StatusLeilao.ABERTO,
        )
        SQLAlchemyLeilaoRepository(session).salvar(leilao)
        session.commit()

    yield leilao

    with fabrica() as session:
        session.execute(delete(AnuncioModel).filter_by(id=anuncio.id))
        session.execute(delete(CategoriaModel).filter_by(id=categoria.id))
        session.commit()


def _relogio_lento():
    # Alarga a janela entre ler e gravar: sem o lock, os dois lances passam.
    time.sleep(0.2)
    return datetime.now(timezone.utc)


def test_lances_simultaneos_de_mesmo_valor_so_um_e_aceito(fabrica, leilao):
    largada = threading.Barrier(2)
    aceitos, rejeitados = [], []

    def dar_lance():
        with fabrica() as session:
            caso_de_uso = DarLance(
                SQLAlchemyLeilaoRepository(session),
                confirmar=session.commit,
                publicar=aceitos.append,
                relogio=_relogio_lento,
            )
            largada.wait()
            try:
                caso_de_uso.executar(leilao.id, uuid4(), Decimal('100.00'))
            except LanceInvalidoError as erro:
                rejeitados.append(erro)

    threads = [threading.Thread(target=dar_lance) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    with fabrica() as session:
        salvo = SQLAlchemyLeilaoRepository(session).buscar_por_id(leilao.id)
    assert len(salvo.lances) == 1
    assert len(aceitos) == 1
    assert len(rejeitados) == 1

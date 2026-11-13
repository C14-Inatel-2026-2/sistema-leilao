from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

import infra.jobs.leiloes as job
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.leilao import Leilao, StatusLeilao
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel

AGORA = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def publicados(monkeypatch):
    eventos = []
    monkeypatch.setattr(job, 'publish', eventos.append)
    return eventos


@pytest.fixture
def criar(session):
    categoria = CategoriaModel(nome='Eletronicos')
    session.add(categoria)
    session.flush()

    def _criar(status, inicio, fim, lances=()):
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
            data_inicio=AGORA + inicio,
            data_final=AGORA + fim,
            status=StatusLeilao.ABERTO,
        )
        for valor in lances:
            leilao.receber_lance(uuid4(), Decimal(valor), leilao.data_inicio)
        leilao.status = status
        SQLAlchemyLeilaoRepository(session).salvar(leilao)
        session.commit()
        return leilao.id

    return _criar


def _rodar(session):
    job.processar_leiloes(lambda: nullcontext(session), relogio=lambda: AGORA)
    session.expire_all()
    return SQLAlchemyLeilaoRepository(session)


H = timedelta(hours=1)


def test_abre_agendados_na_janela_e_mantem_os_futuros(session, criar):
    na_janela = criar(StatusLeilao.AGENDADO, -H, H)
    futuro = criar(StatusLeilao.AGENDADO, H, 2 * H)

    repositorio = _rodar(session)

    assert repositorio.buscar_por_id(na_janela).status == StatusLeilao.ABERTO
    assert repositorio.buscar_por_id(futuro).status == StatusLeilao.AGENDADO


def test_encerra_vencidos_e_mantem_os_em_andamento(session, criar, publicados):
    com_lances = criar(StatusLeilao.ABERTO, -2 * H, -H, ['100', '120'])
    sem_lances = criar(StatusLeilao.ABERTO, -2 * H, -H)
    em_andamento = criar(StatusLeilao.ABERTO, -H, H)

    repositorio = _rodar(session)

    vencido = repositorio.buscar_por_id(com_lances)
    assert vencido.status == StatusLeilao.ENCERRADO
    assert vencido.valor_arremate == Decimal('120.00')
    assert repositorio.buscar_por_id(sem_lances).status == (
        StatusLeilao.CANCELADO
    )
    assert repositorio.buscar_por_id(em_andamento).status == (
        StatusLeilao.ABERTO
    )
    assert {ev.leilao_id for ev in publicados} == {com_lances, sem_lances}


def test_falha_em_um_leilao_nao_impede_os_demais(
    session, criar, publicados, monkeypatch
):
    primeiro = criar(StatusLeilao.ABERTO, -2 * H, -H)
    segundo = criar(StatusLeilao.ABERTO, -2 * H, -H)
    encerrar = job._encerrar

    def _encerrar_falhando_no_primeiro(sessao, leilao_id, agora):
        if leilao_id == primeiro:
            raise RuntimeError('falha simulada')
        encerrar(sessao, leilao_id, agora)

    monkeypatch.setattr(job, '_encerrar', _encerrar_falhando_no_primeiro)

    repositorio = _rodar(session)

    assert repositorio.buscar_por_id(primeiro).status == StatusLeilao.ABERTO
    assert repositorio.buscar_por_id(segundo).status == StatusLeilao.CANCELADO


def test_agendador_desligado_sem_database_url(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)

    assert job.iniciar_agendador() is None

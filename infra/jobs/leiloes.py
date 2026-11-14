"""
infra/jobs/leiloes.py

Job periodico que abre leiloes agendados, encerra os vencidos e registra
a venda quando ha vencedor. Nao tem regra de negocio: so escolhe os
leiloes e dispara os casos de uso.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from uuid import UUID

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from adapters.events import publish
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from adapters.repositories.venda_repository import (
    SQLAlchemyVendaRepository,
)
from domain.leilao import StatusLeilao
from use_cases.encerrar_leilao import EncerrarLeilao
from use_cases.iniciar_leilao import IniciarLeilao
from use_cases.registrar_venda import RegistrarVenda

logger = logging.getLogger(__name__)

AbrirSessao = Callable[[], AbstractContextManager[Session]]


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _abrir(session: Session, leilao_id: UUID, agora: datetime) -> None:
    repositorio = SQLAlchemyLeilaoRepository(session)
    IniciarLeilao(repositorio, relogio=lambda: agora).executar(leilao_id)
    session.commit()


def _registrar(session: Session, leilao_id: UUID) -> None:
    RegistrarVenda(
        SQLAlchemyLeilaoRepository(session),
        SQLAlchemyVendaRepository(session),
    ).executar(leilao_id)
    session.commit()


def _encerrar(session: Session, leilao_id: UUID, agora: datetime) -> None:
    EncerrarLeilao(
        SQLAlchemyLeilaoRepository(session),
        confirmar=session.commit,
        publicar=publish,
        relogio=lambda: agora,
    ).executar(leilao_id)


def processar_leiloes(
    abrir_sessao: AbrirSessao, relogio: Callable[[], datetime] = _agora_utc
) -> None:
    agora = relogio()
    with abrir_sessao() as session:
        repositorio = SQLAlchemyLeilaoRepository(session)
        # shortcut: agendado que perdeu a janela inteira fica agendado;
        # cancelar esses exige regra nova no dominio.
        a_abrir = [
            leilao.id
            for leilao in repositorio.listar_por_status(StatusLeilao.AGENDADO)
            if leilao.esta_na_janela(agora)
        ]
        a_encerrar = [
            leilao.id
            for leilao in repositorio.listar_por_status(StatusLeilao.ABERTO)
            if leilao.data_final <= agora
        ]

    for acao, ids in ((_abrir, a_abrir), (_encerrar, a_encerrar)):
        for leilao_id in ids:
            # Uma transacao por leilao: a falha de um nao impede os demais.
            try:
                with abrir_sessao() as session:
                    acao(session, leilao_id, agora)
            except Exception:
                logger.exception('falha ao processar o leilao %s', leilao_id)

    with abrir_sessao() as session:
        leiloes = SQLAlchemyLeilaoRepository(session)
        vendas = SQLAlchemyVendaRepository(session)
        a_registrar = [
            leilao.id
            for leilao in leiloes.listar_por_status(StatusLeilao.ENCERRADO)
            if leilao.vencedor_id is not None
            and vendas.buscar_por_leilao(leilao.id) is None
        ]

    for leilao_id in a_registrar:
        try:
            with abrir_sessao() as session:
                _registrar(session, leilao_id)
        except Exception:
            logger.exception(
                'falha ao registrar a venda do leilao %s', leilao_id
            )


def iniciar_agendador() -> BackgroundScheduler | None:
    if not os.getenv('DATABASE_URL'):
        logger.warning('DATABASE_URL ausente: job de leiloes desligado')
        return None
    # Import tardio: infra.db.session exige DATABASE_URL ao ser importado.
    from infra.db.session import SessionLocal  # noqa: PLC0415

    agendador = BackgroundScheduler(timezone=timezone.utc)
    agendador.add_job(
        processar_leiloes,
        'interval',
        minutes=1,
        args=[SessionLocal],
        id='processar_leiloes',
        max_instances=1,
        coalesce=True,
    )
    agendador.start()
    return agendador

"""tests/unit/test_event_handlers.py

Testes unitários dos handlers de auditoria e do barramento de eventos.
Valida o comportamento isolado de cada handler utilizando mocks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from adapters.events import (
    EVENT_HANDLERS,
    publish,
    register_auditoria_handlers,
)
from adapters.events.handlers.lance_realizado_handler import (
    handle_lance_realizado,
)
from adapters.events.handlers.leilao_encerrado_handler import (
    handle_leilao_encerrado,
)
from domain.events import LanceRealizado, LeilaoEncerrado
from use_cases.interfaces import AuditoriaRepository

AGORA = datetime(2026, 11, 11, 15, 30, tzinfo=timezone.utc)


@pytest.fixture
def repo_auditoria():
    return Mock(spec=AuditoriaRepository)


@pytest.fixture(autouse=True)
def _limpar_handlers():
    """Garante barramento limpo antes e depois de cada teste."""
    EVENT_HANDLERS.clear()
    yield
    EVENT_HANDLERS.clear()


def test_handle_lance_realizado_delega_para_repositorio(repo_auditoria):
    evento = LanceRealizado(
        leilao_id=uuid4(),
        lance_id=uuid4(),
        usuario_id=uuid4(),
        valor=Decimal('250.00'),
        data_hora=AGORA,
    )

    handle_lance_realizado(evento, repo_auditoria)

    repo_auditoria.salvar_lance.assert_called_once_with(
        leilao_id=evento.leilao_id,
        lance_id=evento.lance_id,
        usuario_id=evento.usuario_id,
        valor=evento.valor,
        data_hora=evento.data_hora,
    )
    repo_auditoria.salvar_encerramento.assert_not_called()


def test_handle_leilao_encerrado_com_vencedor_delega_para_repositorio(
    repo_auditoria,
):
    evento = LeilaoEncerrado(
        leilao_id=uuid4(),
        vencedor_id=uuid4(),
        valor_final=Decimal('500.00'),
        data_encerramento=AGORA,
        motivo='tempo_esgotado',
    )

    handle_leilao_encerrado(evento, repo_auditoria)

    repo_auditoria.salvar_encerramento.assert_called_once_with(
        leilao_id=evento.leilao_id,
        vencedor_id=evento.vencedor_id,
        valor_final=evento.valor_final,
        data_encerramento=evento.data_encerramento,
        motivo='tempo_esgotado',
    )
    repo_auditoria.salvar_lance.assert_not_called()


def test_handle_leilao_encerrado_sem_vencedor_delega_para_repositorio(
    repo_auditoria,
):
    evento = LeilaoEncerrado(
        leilao_id=uuid4(),
        vencedor_id=None,
        valor_final=None,
        data_encerramento=AGORA,
        motivo=None,
    )

    handle_leilao_encerrado(evento, repo_auditoria)

    repo_auditoria.salvar_encerramento.assert_called_once_with(
        leilao_id=evento.leilao_id,
        vencedor_id=None,
        valor_final=None,
        data_encerramento=AGORA,
        motivo=None,
    )
    repo_auditoria.salvar_lance.assert_not_called()


def test_barramento_publica_e_dispara_handlers_registrados(repo_auditoria):
    register_auditoria_handlers(repo_auditoria)

    evento_lance = LanceRealizado(
        leilao_id=uuid4(),
        lance_id=uuid4(),
        usuario_id=uuid4(),
        valor=Decimal('150.00'),
        data_hora=AGORA,
    )
    evento_encerramento = LeilaoEncerrado(
        leilao_id=uuid4(),
        vencedor_id=uuid4(),
        valor_final=Decimal('150.00'),
        data_encerramento=AGORA,
    )

    publish(evento_lance)
    publish(evento_encerramento)

    repo_auditoria.salvar_lance.assert_called_once_with(
        leilao_id=evento_lance.leilao_id,
        lance_id=evento_lance.lance_id,
        usuario_id=evento_lance.usuario_id,
        valor=evento_lance.valor,
        data_hora=evento_lance.data_hora,
    )
    repo_auditoria.salvar_encerramento.assert_called_once_with(
        leilao_id=evento_encerramento.leilao_id,
        vencedor_id=evento_encerramento.vencedor_id,
        valor_final=evento_encerramento.valor_final,
        data_encerramento=evento_encerramento.data_encerramento,
        motivo=None,
    )


def test_barramento_ignora_evento_sem_handler(repo_auditoria):
    register_auditoria_handlers(repo_auditoria)

    class EventoDesconhecido:
        pass

    publish(EventoDesconhecido())

    repo_auditoria.salvar_lance.assert_not_called()
    repo_auditoria.salvar_encerramento.assert_not_called()


def test_register_auditoria_handlers_eh_idempotente(repo_auditoria):
    register_auditoria_handlers(repo_auditoria)
    register_auditoria_handlers(repo_auditoria)

    evento = LanceRealizado(
        leilao_id=uuid4(),
        lance_id=uuid4(),
        usuario_id=uuid4(),
        valor=Decimal('200.00'),
        data_hora=AGORA,
    )
    publish(evento)

    assert repo_auditoria.salvar_lance.call_count == 1

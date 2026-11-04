"""
tests/unit/test_iniciar_leilao.py

Fase red do caso de uso IniciarLeilao.

IniciarLeilao(leilao_repo)
executar(leilao_id, momento=None) -> Leilao

Busca com leilao_repo.buscar_por_id. Leilao ausente levanta
LeilaoInvalidoError. Em seguida chama Leilao.abrir(momento) e
persiste o mesmo objeto. Fora da janela, ou em status diferente de
AGENDADO, propaga EstadoLeilaoInvalidoError e nao salva.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.exceptions import (
    EstadoLeilaoInvalidoError,
    LeilaoInvalidoError,
)
from domain.leilao import Leilao, StatusLeilao
from use_cases.iniciar_leilao import IniciarLeilao
from use_cases.interfaces import LeilaoRepository

_INICIO = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
_FIM = _INICIO + timedelta(hours=2)
_DENTRO = _INICIO + timedelta(minutes=30)


@pytest.fixture
def leilao_repo():
    return Mock(spec=LeilaoRepository)


def _leilao(**overrides) -> Leilao:
    dados = dict(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('5.00'),
        data_inicio=_INICIO,
        data_final=_FIM,
    )
    dados.update(overrides)
    return Leilao(**dados)


def test_inicia_leilao_agendado_dentro_da_janela(leilao_repo):
    leilao = _leilao()
    leilao_repo.buscar_por_id.return_value = leilao
    caso = IniciarLeilao(leilao_repo)

    resultado = caso.executar(leilao.id, momento=_DENTRO)

    assert resultado is leilao
    assert resultado.status is StatusLeilao.ABERTO
    leilao_repo.buscar_por_id.assert_called_once_with(leilao.id)
    leilao_repo.salvar.assert_called_once_with(leilao)


def test_rejeita_iniciar_leilao_inexistente(leilao_repo):
    leilao_repo.buscar_por_id.return_value = None
    caso = IniciarLeilao(leilao_repo)
    leilao_id = uuid4()

    with pytest.raises(LeilaoInvalidoError):
        caso.executar(leilao_id, momento=_DENTRO)

    leilao_repo.buscar_por_id.assert_called_once_with(leilao_id)
    leilao_repo.salvar.assert_not_called()


@pytest.mark.parametrize(
    ('status', 'momento'),
    [
        (
            StatusLeilao.AGENDADO,
            _INICIO - timedelta(minutes=1),
        ),
        (StatusLeilao.ABERTO, _DENTRO),
    ],
    ids=['fora_da_janela', 'ja_aberto'],
)
def test_rejeita_iniciar_leilao_fora_da_janela_ou_ja_aberto(
    leilao_repo, status, momento
):
    leilao = _leilao(status=status)
    leilao_repo.buscar_por_id.return_value = leilao
    caso = IniciarLeilao(leilao_repo)

    with pytest.raises(EstadoLeilaoInvalidoError):
        caso.executar(leilao.id, momento=momento)

    leilao_repo.salvar.assert_not_called()

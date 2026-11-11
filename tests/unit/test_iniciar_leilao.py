from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.exceptions import (
    EstadoLeilaoInvalidoError,
    LeilaoNaoEncontradoError,
)
from domain.leilao import Leilao, StatusLeilao
from use_cases.iniciar_leilao import IniciarLeilao
from use_cases.interfaces import LeilaoRepository

AGORA = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


def _leilao(**overrides):
    dados = dict(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=AGORA - timedelta(minutes=5),
        data_final=AGORA + timedelta(hours=2),
    )
    dados.update(overrides)
    return Leilao(**dados)


@pytest.fixture
def leiloes():
    return Mock(spec=LeilaoRepository)


@pytest.fixture
def caso_de_uso(leiloes):
    return IniciarLeilao(leiloes, relogio=lambda: AGORA)


def test_abre_leilao_agendado_dentro_da_janela(caso_de_uso, leiloes):
    leilao = _leilao()
    leiloes.buscar_por_id.return_value = leilao

    aberto = caso_de_uso.executar(leilao.id)

    assert aberto.status == StatusLeilao.ABERTO
    leiloes.salvar.assert_called_once_with(leilao)


def test_rejeita_leilao_inexistente_sem_salvar(caso_de_uso, leiloes):
    leiloes.buscar_por_id.return_value = None

    with pytest.raises(LeilaoNaoEncontradoError):
        caso_de_uso.executar(uuid4())

    leiloes.salvar.assert_not_called()


def test_rejeita_abertura_fora_da_janela_sem_salvar(caso_de_uso, leiloes):
    leilao = _leilao(data_inicio=AGORA + timedelta(hours=1))
    leiloes.buscar_por_id.return_value = leilao

    with pytest.raises(EstadoLeilaoInvalidoError):
        caso_de_uso.executar(leilao.id)

    assert leilao.status == StatusLeilao.AGENDADO
    leiloes.salvar.assert_not_called()

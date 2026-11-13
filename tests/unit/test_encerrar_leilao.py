from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, call
from uuid import uuid4

import pytest

from domain.events import LeilaoEncerrado
from domain.exceptions import (
    EstadoLeilaoInvalidoError,
    LeilaoNaoEncontradoError,
)
from domain.leilao import Leilao, StatusLeilao
from use_cases.encerrar_leilao import EncerrarLeilao
from use_cases.interfaces import LeilaoRepository

FIM = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def _leilao() -> Leilao:
    return Leilao(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=FIM - timedelta(hours=2),
        data_final=FIM,
        status=StatusLeilao.ABERTO,
    )


@pytest.fixture
def chamadas():
    return Mock()


def _caso_de_uso(leilao, chamadas, agora=FIM):
    repositorio = Mock(spec=LeilaoRepository)
    repositorio.buscar_com_lock.return_value = leilao
    chamadas.attach_mock(repositorio.salvar, 'salvar')
    return EncerrarLeilao(
        repositorio,
        confirmar=chamadas.confirmar,
        publicar=chamadas.publicar,
        relogio=lambda: agora,
    )


def test_com_lances_define_vencedor_salva_confirma_e_publica(chamadas):
    leilao = _leilao()
    comprador = uuid4()
    leilao.receber_lance(uuid4(), Decimal('100.00'), FIM - timedelta(hours=1))
    leilao.receber_lance(
        comprador, Decimal('150.00'), FIM - timedelta(minutes=1)
    )

    _caso_de_uso(leilao, chamadas).executar(leilao.id)

    assert leilao.status == StatusLeilao.ENCERRADO
    assert leilao.vencedor_id == comprador
    assert chamadas.mock_calls == [
        call.salvar(leilao),
        call.confirmar(),
        call.publicar(
            LeilaoEncerrado(
                leilao_id=leilao.id,
                vencedor_id=comprador,
                valor_final=Decimal('150.00'),
                data_encerramento=FIM,
            )
        ),
    ]


def test_sem_lances_cancela_e_publica_motivo(chamadas):
    leilao = _leilao()

    _caso_de_uso(leilao, chamadas).executar(leilao.id)

    assert leilao.status == StatusLeilao.CANCELADO
    evento = chamadas.publicar.call_args.args[0]
    assert evento.vencedor_id is None
    assert evento.motivo == 'sem_lances'


def test_antes_da_data_final_nao_salva_nem_publica(chamadas):
    leilao = _leilao()

    with pytest.raises(EstadoLeilaoInvalidoError):
        _caso_de_uso(
            leilao, chamadas, agora=FIM - timedelta(seconds=1)
        ).executar(leilao.id)

    assert chamadas.mock_calls == []


def test_leilao_inexistente_levanta_erro(chamadas):
    with pytest.raises(LeilaoNaoEncontradoError):
        _caso_de_uso(None, chamadas).executar(uuid4())

"""
Caso de uso DarLance com repositorio e publicador em memoria: persistencia do
lance, publicacao de LanceRealizado, erros e concorrencia entre lances.
"""

import threading
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from adapters.events.publisher import PublicadorEmMemoria
from adapters.repositories.leilao_repository import LeilaoRepositoryEmMemoria
from domain.eventos import LanceRealizado
from domain.exceptions import (
    EstadoLeilaoInvalidoError,
    LanceInvalidoError,
    LeilaoNaoEncontradoError,
)
from domain.leilao import Leilao
from use_cases.dar_lance import DarLance

INICIO = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
FIM = INICIO + timedelta(hours=24)
DURANTE = INICIO + timedelta(hours=1)
VENDEDOR = uuid4()
COMPRADOR_A = uuid4()
COMPRADOR_B = uuid4()


def novo_leilao_aberto() -> Leilao:
    leilao = Leilao(
        anuncio_id=uuid4(),
        vendedor_id=VENDEDOR,
        preco_inicial=Decimal("500"),
        incremento_minimo=Decimal("50"),
        data_inicio=INICIO,
        data_final=FIM,
    )
    leilao.abrir(momento=INICIO)
    return leilao


@pytest.fixture
def repositorio():
    return LeilaoRepositoryEmMemoria()


@pytest.fixture
def publicador():
    return PublicadorEmMemoria()


@pytest.fixture
def leilao(repositorio):
    leilao = novo_leilao_aberto()
    repositorio.adicionar(leilao)
    return leilao


@pytest.fixture
def dar_lance(repositorio, publicador):
    return DarLance(repositorio, publicador, relogio=lambda: DURANTE)


# --- caminho feliz -----------------------------------------------------------------


def test_lance_aceito_e_persistido(dar_lance, repositorio, leilao):
    lance = dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("550"))

    salvo = repositorio.obter(leilao.id)
    assert salvo.lances == [lance]
    assert salvo.maior_lance().valor == Decimal("550")


def test_lance_usa_o_momento_do_relogio(dar_lance, leilao):
    lance = dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("550"))

    assert lance.criado_em == DURANTE


def test_sem_relogio_injetado_usa_o_horario_atual_em_utc(repositorio, publicador):
    agora = datetime.now(timezone.utc)
    leilao = Leilao(
        anuncio_id=uuid4(),
        vendedor_id=VENDEDOR,
        preco_inicial=Decimal("500"),
        incremento_minimo=Decimal("50"),
        data_inicio=agora - timedelta(hours=1),
        data_final=agora + timedelta(hours=1),
    )
    leilao.abrir(momento=agora)
    repositorio.adicionar(leilao)

    lance = DarLance(repositorio, publicador).executar(leilao.id, COMPRADOR_A, Decimal("500"))

    assert lance.criado_em.tzinfo is not None
    assert agora <= lance.criado_em <= datetime.now(timezone.utc)


def test_lance_aceito_publica_lance_realizado(dar_lance, publicador, leilao):
    lance = dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("550"))

    assert publicador.publicados == [
        LanceRealizado(
            leilao_id=leilao.id,
            lance_id=lance.id,
            comprador_id=COMPRADOR_A,
            valor=Decimal("550"),
            ocorrido_em=DURANTE,
        )
    ]


def test_handler_inscrito_recebe_o_evento(dar_lance, publicador, leilao):
    recebidos = []
    publicador.inscrever(LanceRealizado, recebidos.append)

    dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("550"))

    assert len(recebidos) == 1
    assert recebidos[0].valor == Decimal("550")


def test_segundo_lance_respeita_o_lance_ja_persistido(dar_lance, repositorio, leilao):
    dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("550"))

    with pytest.raises(LanceInvalidoError):
        dar_lance.executar(leilao.id, COMPRADOR_B, Decimal("599"))

    dar_lance.executar(leilao.id, COMPRADOR_B, Decimal("600"))
    assert repositorio.obter(leilao.id).maior_lance().comprador_id == COMPRADOR_B


# --- erros -------------------------------------------------------------------------


def test_lance_invalido_nao_persiste_nem_publica(dar_lance, repositorio, publicador, leilao):
    with pytest.raises(LanceInvalidoError):
        dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("499"))

    assert repositorio.obter(leilao.id).lances == []
    assert publicador.publicados == []


def test_vendedor_dando_lance_e_rejeitado(dar_lance, publicador, leilao):
    with pytest.raises(LanceInvalidoError, match="vendedor"):
        dar_lance.executar(leilao.id, VENDEDOR, Decimal("550"))

    assert publicador.publicados == []


def test_lance_depois_do_fim_e_rejeitado(repositorio, publicador, leilao):
    dar_lance = DarLance(repositorio, publicador, relogio=lambda: FIM)

    with pytest.raises(LanceInvalidoError, match="periodo"):
        dar_lance.executar(leilao.id, COMPRADOR_A, Decimal("550"))


def test_lance_em_leilao_agendado_e_rejeitado(dar_lance, repositorio):
    agendado = Leilao(
        anuncio_id=uuid4(),
        vendedor_id=VENDEDOR,
        preco_inicial=Decimal("500"),
        incremento_minimo=Decimal("50"),
        data_inicio=INICIO,
        data_final=FIM,
    )
    repositorio.adicionar(agendado)

    with pytest.raises(EstadoLeilaoInvalidoError):
        dar_lance.executar(agendado.id, COMPRADOR_A, Decimal("500"))


def test_leilao_inexistente_gera_erro_e_nao_publica(dar_lance, publicador):
    with pytest.raises(LeilaoNaoEncontradoError):
        dar_lance.executar(uuid4(), COMPRADOR_A, Decimal("550"))

    assert publicador.publicados == []


# --- concorrencia ------------------------------------------------------------------


def test_lances_simultaneos_de_mesmo_valor_so_um_prevalece(repositorio, publicador, leilao):
    # O relogio "demora" de proposito: sem a trava, todas as threads leriam o
    # leilao ainda sem lances e todas teriam o lance de R$ 550 aceito.
    def relogio_lento():
        time.sleep(0.01)
        return DURANTE

    dar_lance = DarLance(repositorio, publicador, relogio=relogio_lento)
    participantes = 8
    largada = threading.Barrier(participantes)
    aceitos, rejeitados = [], []

    def disputar():
        largada.wait()
        try:
            aceitos.append(dar_lance.executar(leilao.id, uuid4(), Decimal("550")))
        except LanceInvalidoError:
            rejeitados.append(1)

    threads = [threading.Thread(target=disputar) for _ in range(participantes)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(aceitos) == 1
    assert len(rejeitados) == participantes - 1
    assert repositorio.obter(leilao.id).lances == aceitos
    assert len(publicador.publicados) == 1

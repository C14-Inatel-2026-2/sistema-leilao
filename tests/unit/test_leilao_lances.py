"""
Regras de lance do Leilao: status, janela temporal, incremento minimo, vendedor
dando lance e apuracao do vencedor no encerramento.

Os valores seguem os exemplos do README: preco inicial R$ 500, incremento R$ 50.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.exceptions import EstadoLeilaoInvalidoError, LanceInvalidoError
from domain.lance import Lance
from domain.leilao import Leilao, StatusLeilao

INICIO = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
FIM = INICIO + timedelta(hours=24)
DURANTE = INICIO + timedelta(hours=1)
VENDEDOR = uuid4()
COMPRADOR_A = uuid4()
COMPRADOR_B = uuid4()


def novo_leilao(**sobrescrever) -> Leilao:
    dados = dict(
        anuncio_id=uuid4(),
        vendedor_id=VENDEDOR,
        preco_inicial=Decimal("500"),
        incremento_minimo=Decimal("50"),
        data_inicio=INICIO,
        data_final=FIM,
    )
    dados.update(sobrescrever)
    return Leilao(**dados)


@pytest.fixture
def leilao_aberto() -> Leilao:
    leilao = novo_leilao()
    leilao.abrir(momento=INICIO)
    return leilao


# --- valor minimo e incremento -------------------------------------------------


def test_sem_lances_o_minimo_e_o_preco_inicial(leilao_aberto):
    assert leilao_aberto.maior_lance() is None
    assert leilao_aberto.valor_minimo_proximo_lance() == Decimal("500")


def test_primeiro_lance_igual_ao_preco_inicial_e_aceito(leilao_aberto):
    lance = leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=DURANTE)

    assert leilao_aberto.maior_lance() is lance


def test_primeiro_lance_abaixo_do_preco_inicial_e_rejeitado(leilao_aberto):
    with pytest.raises(LanceInvalidoError, match="minmo exigido"):
        leilao_aberto.receber_lance(COMPRADOR_A, Decimal("499.99"), momento=DURANTE)


def test_com_lances_o_minimo_e_maior_lance_mais_incremento(leilao_aberto):
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("550"), momento=DURANTE)

    assert leilao_aberto.valor_minimo_proximo_lance() == Decimal("600")


def test_lance_exatamente_no_incremento_minimo_e_aceito(leilao_aberto):
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("550"), momento=DURANTE)
    leilao_aberto.receber_lance(COMPRADOR_B, Decimal("600"), momento=DURANTE)

    assert leilao_aberto.maior_lance().valor == Decimal("600")


def test_lance_abaixo_do_incremento_minimo_e_rejeitado(leilao_aberto):
    # Exemplo 3 do README: com lance atual de R$ 550, R$ 520 nao passa.
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("550"), momento=DURANTE)

    with pytest.raises(LanceInvalidoError):
        leilao_aberto.receber_lance(COMPRADOR_B, Decimal("520"), momento=DURANTE)


def test_lance_rejeitado_nao_altera_o_leilao(leilao_aberto):
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("550"), momento=DURANTE)

    with pytest.raises(LanceInvalidoError):
        leilao_aberto.receber_lance(COMPRADOR_B, Decimal("599.99"), momento=DURANTE)

    assert len(leilao_aberto.lances) == 1
    assert leilao_aberto.maior_lance().comprador_id == COMPRADOR_A


@pytest.mark.parametrize("valor", [600.0, Decimal("NaN")])
def test_leilao_rejeita_valor_invalido_como_lance_invalido(leilao_aberto, valor):
    with pytest.raises(LanceInvalidoError):
        leilao_aberto.receber_lance(COMPRADOR_A, valor, momento=DURANTE)


# --- quem pode dar lance -------------------------------------------------------


def test_vendedor_nao_pode_dar_lance_no_proprio_leilao(leilao_aberto):
    with pytest.raises(LanceInvalidoError, match="vendedor"):
        leilao_aberto.receber_lance(VENDEDOR, Decimal("500"), momento=DURANTE)


def test_receber_lance_devolve_o_lance_registrado(leilao_aberto):
    lance = leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=DURANTE)

    assert isinstance(lance, Lance)
    assert lance.leilao_id == leilao_aberto.id
    assert lance.comprador_id == COMPRADOR_A
    assert lance.criado_em == DURANTE
    assert leilao_aberto.lances == [lance]


# --- status do leilao ------------------------------------------------------------


def test_lance_em_leilao_agendado_e_rejeitado():
    leilao = novo_leilao()

    with pytest.raises(EstadoLeilaoInvalidoError, match="nao esta aberto"):
        leilao.receber_lance(COMPRADOR_A, Decimal("500"), momento=DURANTE)


def test_lance_em_leilao_cancelado_e_rejeitado(leilao_aberto):
    leilao_aberto.cancelar()

    with pytest.raises(EstadoLeilaoInvalidoError):
        leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=DURANTE)


def test_lance_em_leilao_encerrado_e_rejeitado(leilao_aberto):
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=DURANTE)
    leilao_aberto.encerrar(momento=FIM)

    with pytest.raises(EstadoLeilaoInvalidoError):
        leilao_aberto.receber_lance(COMPRADOR_B, Decimal("550"), momento=FIM)


# --- janela temporal -------------------------------------------------------------


def test_lance_antes_do_inicio_e_rejeitado(leilao_aberto):
    with pytest.raises(LanceInvalidoError, match="periodo"):
        leilao_aberto.receber_lance(
            COMPRADOR_A, Decimal("500"), momento=INICIO - timedelta(seconds=1)
        )


def test_lance_no_instante_de_inicio_e_aceito(leilao_aberto):
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=INICIO)

    assert len(leilao_aberto.lances) == 1


def test_lance_um_instante_antes_do_fim_e_aceito(leilao_aberto):
    leilao_aberto.receber_lance(
        COMPRADOR_A, Decimal("500"), momento=FIM - timedelta(microseconds=1)
    )

    assert len(leilao_aberto.lances) == 1


def test_lance_no_instante_do_fim_e_rejeitado(leilao_aberto):
    # No instante data_final o leilao ja pode ser encerrado; aceitar lance ali
    # deixaria lance e encerramento disputando o mesmo momento.
    with pytest.raises(LanceInvalidoError, match="periodo"):
        leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=FIM)


def test_lance_depois_do_fim_e_rejeitado(leilao_aberto):
    with pytest.raises(LanceInvalidoError, match="periodo"):
        leilao_aberto.receber_lance(
            COMPRADOR_A, Decimal("500"), momento=FIM + timedelta(minutes=5)
        )


# --- apuracao no encerramento ----------------------------------------------------


def test_encerrar_com_lances_define_vencedor_pelo_maior_lance(leilao_aberto):
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("500"), momento=DURANTE)
    leilao_aberto.receber_lance(COMPRADOR_B, Decimal("550"), momento=DURANTE)
    leilao_aberto.receber_lance(COMPRADOR_A, Decimal("700"), momento=DURANTE)

    leilao_aberto.encerrar(momento=FIM)

    assert leilao_aberto.status == StatusLeilao.ENCERRADO
    assert leilao_aberto.vencedor_id == COMPRADOR_A
    assert leilao_aberto.valor_arremate == Decimal("700")


def test_encerrar_sem_lances_cancela_o_leilao(leilao_aberto):
    leilao_aberto.encerrar(momento=FIM)

    assert leilao_aberto.status == StatusLeilao.CANCELADO
    assert leilao_aberto.vencedor_id is None
    assert leilao_aberto.valor_arremate is None


def test_encerrar_antes_do_fim_e_rejeitado(leilao_aberto):
    with pytest.raises(EstadoLeilaoInvalidoError, match="antes da data final"):
        leilao_aberto.encerrar(momento=FIM - timedelta(seconds=1))

    assert leilao_aberto.status == StatusLeilao.ABERTO


def test_lance_e_excecoes_continuam_importaveis_de_domain_leilao():
    # Compatibilidade: antes deste PR, Lance e as excecoes viviam em domain/leilao.py.
    from domain import leilao

    assert leilao.Lance is Lance
    assert leilao.LanceInvalidoError is LanceInvalidoError
    assert leilao.EstadoLeilaoInvalidoError is EstadoLeilaoInvalidoError

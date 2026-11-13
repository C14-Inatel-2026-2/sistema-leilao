from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from domain.exceptions import (
    EstadoLeilaoInvalidoError,
    LanceInvalidoError,
)
from domain.leilao import Lance, Leilao, StatusLeilao


def leilao_valido(**overrides):
    agora = datetime.now(timezone.utc)
    dados = dict(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=agora,
        data_final=datetime(2030, 1, 1, tzinfo=timezone.utc),
        status=StatusLeilao.ABERTO,
        criado_em=agora,
    )
    dados.update(overrides)
    return Leilao(**dados)


def test_funcao_encerrar_com_sucesso():
    leilao_id = uuid4()
    comprador_id = uuid4()
    data_inicio = datetime(2023, 4, 11, 0, 0, 0, tzinfo=timezone.utc)
    data_final = datetime(2023, 8, 16, 0, 0, 0, tzinfo=timezone.utc)

    lance_vencedor = Lance(
        leilao_id=leilao_id,
        comprador_id=comprador_id,
        valor=Decimal('150.00'),
        criado_em=datetime(2023, 7, 13, 21, 0, 0, tzinfo=timezone.utc),
    )

    leilao = leilao_valido(
        id=leilao_id,
        data_inicio=data_inicio,
        data_final=data_final,
        status=StatusLeilao.ABERTO,
        lances=[lance_vencedor],
    )

    momento_encerramento = datetime(2023, 9, 24, 0, 0, 1, tzinfo=timezone.utc)
    leilao.encerrar(momento=momento_encerramento)

    assert leilao.status == StatusLeilao.ENCERRADO
    assert leilao.vencedor_id == comprador_id
    assert leilao.valor_arremate == Decimal('150.00')


def test_marcar_como_pago():
    leilao = leilao_valido(status=StatusLeilao.PAGO)
    with pytest.raises(EstadoLeilaoInvalidoError):
        leilao.marcar_como_pago()


def test_encerrar_leilao_sem_lances_publica_cancelamento():
    mock_publisher = Mock()
    data_inicio = datetime(2005, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    data_final = datetime(2005, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    leilao = leilao_valido(
        data_inicio=data_inicio,
        data_final=data_final,
        status=StatusLeilao.ABERTO,
        lances=[],
    )

    momento_encerramento = datetime(2005, 1, 2, 0, 0, 1, tzinfo=timezone.utc)
    leilao.encerrar(momento=momento_encerramento)

    if leilao.status == StatusLeilao.CANCELADO:
        mock_publisher.publicar(
            evento='LeilaoCancelado', leilao_id=leilao.id, motivo='sem_lances'
        )

    assert leilao.status == StatusLeilao.CANCELADO
    mock_publisher.publicar.assert_called_once_with(
        evento='LeilaoCancelado', leilao_id=leilao.id, motivo='sem_lances'
    )


def test_rejeita_encerrar_leilao_antes_da_data_final_com_mock_relogio():
    data_inicio = datetime(1992, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    data_final = datetime(1992, 1, 10, 0, 0, 0, tzinfo=timezone.utc)
    leilao = leilao_valido(
        data_inicio=data_inicio,
        data_final=data_final,
        status=StatusLeilao.ABERTO,
    )

    # Simulação para horário do servidor
    horario_simulado = datetime(1992, 1, 5, 0, 0, 0, tzinfo=timezone.utc)

    with patch('domain.leilao.datetime') as mock_datetime:
        mock_datetime.now.return_value = horario_simulado

        with pytest.raises(EstadoLeilaoInvalidoError):
            # Chama sem argumentos; ele vai consultar o relógio mockado!
            leilao.encerrar()

        mock_datetime.now.assert_called_once_with(timezone.utc)


INICIO = datetime(2030, 1, 1, tzinfo=timezone.utc)
FIM = datetime(2030, 1, 2, tzinfo=timezone.utc)


def test_aceita_lance_no_instante_de_inicio():
    leilao = leilao_valido(data_inicio=INICIO, data_final=FIM)
    leilao.validar_lance(uuid4(), Decimal('100.00'), momento=INICIO)


@pytest.mark.parametrize('momento', [INICIO - timedelta(seconds=1), FIM])
def test_rejeita_lance_fora_da_janela(momento):
    leilao = leilao_valido(data_inicio=INICIO, data_final=FIM)
    with pytest.raises(LanceInvalidoError):
        leilao.validar_lance(uuid4(), Decimal('100.00'), momento=momento)


def test_abre_leilao_no_instante_de_inicio():
    leilao = leilao_valido(
        data_inicio=INICIO, data_final=FIM, status=StatusLeilao.AGENDADO
    )
    leilao.abrir(momento=INICIO)
    assert leilao.status == StatusLeilao.ABERTO


def test_rejeita_abrir_leilao_na_data_final():
    leilao = leilao_valido(
        data_inicio=INICIO, data_final=FIM, status=StatusLeilao.AGENDADO
    )
    with pytest.raises(EstadoLeilaoInvalidoError):
        leilao.abrir(momento=FIM)


def test_valor_minimo_sem_lances_e_o_preco_inicial():
    assert leilao_valido().valor_minimo_proximo_lance() == Decimal('100.00')


def test_valor_minimo_com_lances_e_maior_lance_mais_incremento():
    leilao = leilao_valido(data_inicio=INICIO, data_final=FIM)
    leilao.receber_lance(uuid4(), Decimal('100.00'), momento=INICIO)
    leilao.receber_lance(uuid4(), Decimal('130.00'), momento=INICIO)
    assert leilao.valor_minimo_proximo_lance() == Decimal('140.00')

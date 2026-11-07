from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.exceptions import LeilaoNaoEncontradoError
from domain.lance import Lance
from domain.leilao import Leilao, StatusLeilao
from use_cases.interfaces import LeilaoRepository
from use_cases.listar_lances import ListarLances

INICIO = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def test_retorna_lances_do_mais_recente_ao_mais_antigo():
    leilao = Leilao(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=INICIO,
        data_final=INICIO + timedelta(hours=2),
        status=StatusLeilao.ABERTO,
    )
    antigo, meio, recente = (
        Lance(
            leilao_id=leilao.id,
            comprador_id=uuid4(),
            valor=Decimal(valor),
            criado_em=INICIO + timedelta(minutes=minuto),
        )
        for valor, minuto in (('100', 1), ('110', 2), ('120', 3))
    )
    leilao.lances = [meio, recente, antigo]
    repositorio = Mock(spec=LeilaoRepository)
    repositorio.buscar_por_id.return_value = leilao

    assert ListarLances(repositorio).executar(leilao.id) == [
        recente,
        meio,
        antigo,
    ]


def test_leilao_inexistente_levanta_erro():
    repositorio = Mock(spec=LeilaoRepository)
    repositorio.buscar_por_id.return_value = None

    with pytest.raises(LeilaoNaoEncontradoError):
        ListarLances(repositorio).executar(uuid4())

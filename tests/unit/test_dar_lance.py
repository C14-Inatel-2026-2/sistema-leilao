import threading
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from domain.events import LanceRealizado
from domain.exceptions import (
    EstadoLeilaoInvalidoError,
    LanceInvalidoError,
    LeilaoNaoEncontradoError,
)
from domain.leilao import Leilao, StatusLeilao
from use_cases.dar_lance import DarLance
from use_cases.interfaces import LeilaoRepository

AGORA = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)


def _leilao(**overrides) -> Leilao:
    dados = dict(
        anuncio_id=uuid4(),
        vendedor_id=uuid4(),
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('10.00'),
        data_inicio=AGORA - timedelta(hours=1),
        data_final=AGORA + timedelta(hours=1),
        status=StatusLeilao.ABERTO,
    )
    dados.update(overrides)
    return Leilao(**dados)


@pytest.fixture
def chamadas():
    return Mock()


@pytest.fixture
def repositorio(chamadas):
    repo = Mock(spec=LeilaoRepository)
    chamadas.attach_mock(repo.salvar, 'salvar')
    return repo


@pytest.fixture
def caso_de_uso(repositorio, chamadas):
    return DarLance(
        repositorio,
        confirmar=chamadas.confirmar,
        publicar=chamadas.publicar,
        relogio=lambda: AGORA,
    )


def test_lance_valido_salva_confirma_e_publica_nessa_ordem(
    caso_de_uso, repositorio, chamadas
):
    leilao = _leilao()
    repositorio.buscar_com_lock.return_value = leilao
    comprador = uuid4()

    lance = caso_de_uso.executar(leilao.id, comprador, Decimal('100.00'))

    assert leilao.lances == [lance]
    assert lance.criado_em == AGORA
    assert [c[0] for c in chamadas.mock_calls] == [
        'salvar',
        'confirmar',
        'publicar',
    ]
    chamadas.publicar.assert_called_once_with(
        LanceRealizado(
            leilao_id=leilao.id,
            lance_id=lance.id,
            usuario_id=comprador,
            valor=Decimal('100.00'),
            data_hora=AGORA,
        )
    )


def test_leilao_inexistente_levanta_erro(caso_de_uso, repositorio, chamadas):
    repositorio.buscar_com_lock.return_value = None

    with pytest.raises(LeilaoNaoEncontradoError):
        caso_de_uso.executar(uuid4(), uuid4(), Decimal('100.00'))

    assert chamadas.mock_calls == []


@pytest.mark.parametrize(
    'cenario',
    [
        (
            {'status': StatusLeilao.AGENDADO},
            '100.00',
            EstadoLeilaoInvalidoError,
        ),
        (
            {'status': StatusLeilao.ENCERRADO},
            '100.00',
            EstadoLeilaoInvalidoError,
        ),
        ({}, '99.99', LanceInvalidoError),
        (
            {
                'data_inicio': AGORA - timedelta(hours=2),
                'data_final': AGORA - timedelta(minutes=1),
            },
            '100.00',
            LanceInvalidoError,
        ),
    ],
)
def test_lance_rejeitado_nao_salva_nem_publica(
    caso_de_uso, repositorio, chamadas, cenario
):
    leilao_kwargs, valor, erro = cenario
    repositorio.buscar_com_lock.return_value = _leilao(**leilao_kwargs)

    with pytest.raises(erro):
        caso_de_uso.executar(uuid4(), uuid4(), Decimal(valor))

    assert chamadas.mock_calls == []


def test_vendedor_nao_pode_dar_lance_no_proprio_leilao(
    caso_de_uso, repositorio, chamadas
):
    leilao = _leilao()
    repositorio.buscar_com_lock.return_value = leilao

    with pytest.raises(LanceInvalidoError):
        caso_de_uso.executar(leilao.id, leilao.vendedor_id, Decimal('100.00'))

    assert chamadas.mock_calls == []


def test_lance_abaixo_do_incremento_minimo_e_rejeitado(
    caso_de_uso, repositorio
):
    leilao = _leilao()
    repositorio.buscar_com_lock.return_value = leilao
    caso_de_uso.executar(leilao.id, uuid4(), Decimal('100.00'))

    with pytest.raises(LanceInvalidoError):
        caso_de_uso.executar(leilao.id, uuid4(), Decimal('109.99'))


class _RepositorioComTrava:
    """Simula o FOR UPDATE: a trava vai de buscar_com_lock ate o commit."""

    def __init__(self, leilao: Leilao) -> None:
        self._salvo = deepcopy(leilao)
        self._trava = threading.Lock()

    def buscar_com_lock(self, leilao_id):
        self._trava.acquire()
        return deepcopy(self._salvo)

    def salvar(self, leilao):
        self._pendente = deepcopy(leilao)

    def confirmar(self):
        self._salvo = self._pendente
        self._trava.release()

    def desfazer(self):
        self._trava.release()

    def lances(self):
        return self._salvo.lances


def test_lances_simultaneos_de_mesmo_valor_so_um_e_aceito():
    leilao = _leilao()
    repo = _RepositorioComTrava(leilao)
    publicados = []
    caso_de_uso = DarLance(
        repo, repo.confirmar, publicados.append, relogio=lambda: AGORA
    )
    largada = threading.Barrier(2)
    erros = []

    def dar_lance():
        largada.wait()
        try:
            caso_de_uso.executar(leilao.id, uuid4(), Decimal('100.00'))
        except LanceInvalidoError as erro:
            erros.append(erro)
            repo.desfazer()

    threads = [threading.Thread(target=dar_lance) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert len(repo.lances()) == 1
    assert len(publicados) == 1
    assert len(erros) == 1

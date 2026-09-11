from dataclasses import dataclass

from adapters.events.publisher import PublicadorEmMemoria


@dataclass(frozen=True)
class EventoA:
    valor: int


@dataclass(frozen=True)
class EventoB:
    valor: int


def test_publicador_registra_eventos_publicados_em_ordem():
    publicador = PublicadorEmMemoria()

    publicador.publicar(EventoA(1))
    publicador.publicar(EventoB(2))

    assert publicador.publicados == [EventoA(1), EventoB(2)]


def test_handler_so_recebe_eventos_do_tipo_inscrito():
    publicador = PublicadorEmMemoria()
    recebidos = []
    publicador.inscrever(EventoA, recebidos.append)

    publicador.publicar(EventoA(1))
    publicador.publicar(EventoB(2))

    assert recebidos == [EventoA(1)]


def test_varios_handlers_recebem_o_mesmo_evento():
    publicador = PublicadorEmMemoria()
    historico, auditoria = [], []
    publicador.inscrever(EventoA, historico.append)
    publicador.inscrever(EventoA, auditoria.append)

    publicador.publicar(EventoA(7))

    assert historico == auditoria == [EventoA(7)]


def test_publicar_sem_handlers_nao_falha():
    publicador = PublicadorEmMemoria()

    publicador.publicar(EventoA(1))

    assert publicador.publicados == [EventoA(1)]

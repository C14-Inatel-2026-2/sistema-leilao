"""adapters/events/__init__.py

Barramento interno de eventos de domínio em memória.
Permite registrar handlers consumidores e despachar eventos publicados.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from adapters.events.handlers.lance_realizado_handler import (
    handle_lance_realizado,
)
from adapters.events.handlers.leilao_encerrado_handler import (
    handle_leilao_encerrado,
)
from domain.events import LanceRealizado, LeilaoEncerrado
from use_cases.interfaces import AuditoriaRepository

# 1. Dicionário global de handlers por tipo de evento
EVENT_HANDLERS: dict[type, list[Callable[[Any], None]]] = defaultdict(list)


# 2. Registra os handlers no dicionário adaptando para 1 argumento
def register_auditoria_handlers(repo: AuditoriaRepository) -> None:
    """Registra os handlers de auditoria injetando a implementação concreta

    do repositório de auditoria.
    """

    def on_lance_realizado(ev: LanceRealizado) -> None:
        handle_lance_realizado(ev, repo)

    def on_leilao_encerrado(ev: LeilaoEncerrado) -> None:
        handle_leilao_encerrado(ev, repo)

    EVENT_HANDLERS[LanceRealizado].append(on_lance_realizado)
    EVENT_HANDLERS[LeilaoEncerrado].append(on_leilao_encerrado)


# 3. Dispara os eventos para os handlers registrados
def publish(event: Any) -> None:
    """Publica um evento de domínio no barramento.

    Executa todos os handlers registrados para o tipo do evento.
    """
    handlers = EVENT_HANDLERS.get(type(event), [])
    for handler in handlers:
        handler(event)

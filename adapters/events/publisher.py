"""
adapters/events/publisher.py

Publicacao de eventos de dominio.

Os casos de uso dependem apenas do contrato `PublicadorEventos`. A implementacao
`PublicadorEmMemoria` e um event bus sincrono, suficiente para o MVP e para os
testes: novos consumidores (historico, auditoria) se inscrevem sem que o caso
de uso que publica precise mudar.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Protocol


class PublicadorEventos(Protocol):
    def publicar(self, evento: object) -> None:
        ...


class PublicadorEmMemoria:
    """Entrega cada evento, na hora, aos handlers inscritos para o tipo dele."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[object], None]]] = defaultdict(list)
        self.publicados: list[object] = []

    def inscrever(self, tipo_evento: type, handler: Callable[[object], None]) -> None:
        self._handlers[tipo_evento].append(handler)

    def publicar(self, evento: object) -> None:
        self.publicados.append(evento)
        for handler in self._handlers[type(evento)]:
            handler(evento)

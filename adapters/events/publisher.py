"""adapters/events/publisher.py

Módulo do publicador de eventos de domínio, reexportando a infraestrutura
do barramento de eventos para compatibilidade com o padrão do projeto.
"""

from __future__ import annotations

from adapters.events import EVENT_HANDLERS, publish

__all__ = ['EVENT_HANDLERS', 'publish']

"""
adapters/repositories/leilao_repository.py

Contrato de persistencia de leiloes consumido pelos casos de uso, e uma
implementacao em memoria usada nos testes.

Aqui fica apenas o que o motor de lances precisa (carregar com trava e salvar).
As operacoes de CRUD e filtros do catalogo entram neste mesmo contrato no PR de
repositories de catalogo.

Concorrencia: `travar_para_lance` e o ponto em que dois lances simultaneos no
mesmo leilao sao serializados. Na implementacao SQLAlchemy ele abre a transacao
e faz `SELECT ... FOR UPDATE` no registro do leilao; ao sair do bloco sem
excecao faz commit, com excecao faz rollback (ver docs/arquitetura.md).
"""

from __future__ import annotations

import threading
from contextlib import AbstractContextManager, contextmanager
from copy import deepcopy
from typing import Iterator, Protocol
from uuid import UUID

from domain.leilao import Leilao


class LeilaoRepository(Protocol):
    def travar_para_lance(self, leilao_id: UUID) -> AbstractContextManager[Leilao | None]:
        """Carrega o leilao com trava exclusiva ate o fim do bloco `with`."""
        ...

    def salvar(self, leilao: Leilao) -> None:
        """Persiste o estado do leilao (inclusive lances novos) na transacao aberta."""
        ...


class LeilaoRepositoryEmMemoria:
    """
    Implementacao em memoria com trava por leilao.

    Devolve sempre copias: alterar o objeto recebido so tem efeito depois de
    `salvar`, como aconteceria com um banco de verdade.
    """

    def __init__(self) -> None:
        self._leiloes: dict[UUID, Leilao] = {}
        self._travas: dict[UUID, threading.Lock] = {}
        self._guarda = threading.Lock()

    def adicionar(self, leilao: Leilao) -> None:
        self._leiloes[leilao.id] = deepcopy(leilao)

    def obter(self, leilao_id: UUID) -> Leilao | None:
        leilao = self._leiloes.get(leilao_id)
        return deepcopy(leilao) if leilao is not None else None

    @contextmanager
    def travar_para_lance(self, leilao_id: UUID) -> Iterator[Leilao | None]:
        with self._trava_do(leilao_id):
            yield self.obter(leilao_id)

    def salvar(self, leilao: Leilao) -> None:
        self._leiloes[leilao.id] = deepcopy(leilao)

    def _trava_do(self, leilao_id: UUID) -> threading.Lock:
        with self._guarda:
            return self._travas.setdefault(leilao_id, threading.Lock())

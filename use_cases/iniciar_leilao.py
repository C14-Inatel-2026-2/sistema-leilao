from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from domain.exceptions import LeilaoNaoEncontradoError
from domain.leilao import Leilao
from use_cases.interfaces import LeilaoRepository


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class IniciarLeilao:
    def __init__(
        self,
        leiloes: LeilaoRepository,
        relogio: Callable[[], datetime] = _agora_utc,
    ) -> None:
        self._leiloes = leiloes
        self._relogio = relogio

    def executar(self, leilao_id: UUID) -> Leilao:
        leilao = self._leiloes.buscar_por_id(leilao_id)
        if leilao is None:
            raise LeilaoNaoEncontradoError(
                f'leilao {leilao_id} nao encontrado'
            )
        leilao.abrir(self._relogio())
        self._leiloes.salvar(leilao)
        return leilao

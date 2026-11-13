from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from uuid import UUID

from domain.events import LeilaoEncerrado
from domain.exceptions import LeilaoNaoEncontradoError
from domain.leilao import Leilao, StatusLeilao
from use_cases.interfaces import LeilaoRepository


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class EncerrarLeilao:
    def __init__(
        self,
        leiloes: LeilaoRepository,
        confirmar: Callable[[], None],
        publicar: Callable[[object], None],
        relogio: Callable[[], datetime] = _agora_utc,
    ) -> None:
        self._leiloes = leiloes
        self._confirmar = confirmar
        self._publicar = publicar
        self._relogio = relogio

    def executar(self, leilao_id: UUID) -> Leilao:
        # Lock: um lance concorrente nao entra depois da apuracao.
        leilao = self._leiloes.buscar_com_lock(leilao_id)
        if leilao is None:
            raise LeilaoNaoEncontradoError(
                f'leilao {leilao_id} nao encontrado'
            )

        momento = self._relogio()
        leilao.encerrar(momento)
        self._leiloes.salvar(leilao)
        # Publica so apos o commit, como em DarLance.
        self._confirmar()

        cancelado = leilao.status == StatusLeilao.CANCELADO
        self._publicar(
            LeilaoEncerrado(
                leilao_id=leilao.id,
                vencedor_id=leilao.vencedor_id,
                valor_final=leilao.valor_arremate,
                data_encerramento=momento,
                motivo='sem_lances' if cancelado else None,
            )
        )
        return leilao

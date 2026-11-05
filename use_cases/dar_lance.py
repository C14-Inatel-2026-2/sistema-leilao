from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from domain.events import LanceRealizado
from domain.exceptions import LeilaoNaoEncontradoError
from domain.lance import Lance
from use_cases.interfaces import LeilaoRepository


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class DarLance:
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

    def executar(
        self, leilao_id: UUID, comprador_id: UUID, valor: Decimal
    ) -> Lance:
        leilao = self._leiloes.buscar_com_lock(leilao_id)
        if leilao is None:
            raise LeilaoNaoEncontradoError(
                f'leilao {leilao_id} nao encontrado'
            )

        lance = leilao.receber_lance(
            comprador_id=comprador_id, valor=valor, momento=self._relogio()
        )
        self._leiloes.salvar(leilao)
        # Publica so apos o commit: lance desfeito no rollback nao vira evento.
        self._confirmar()

        self._publicar(
            LanceRealizado(
                leilao_id=lance.leilao_id,
                lance_id=lance.id,
                usuario_id=lance.comprador_id,
                valor=lance.valor,
                data_hora=lance.criado_em,
            )
        )
        return lance

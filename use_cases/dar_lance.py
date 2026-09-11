"""
use_cases/dar_lance.py

Caso de uso: um comprador da um lance em um leilao aberto.

Fluxo:
1. trava o leilao - dois lances simultaneos no mesmo leilao sao serializados aqui;
2. o dominio valida e registra o lance (status, janela, incremento, vendedor);
3. salva o leilao dentro da mesma transacao;
4. so depois de sair da transacao publica LanceRealizado, para que um lance
   desfeito por rollback nunca vire evento.

Nao importa Flask nem SQLAlchemy: repositorio, publicador e relogio chegam por
injecao de dependencia.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable
from uuid import UUID

from adapters.events.publisher import PublicadorEventos
from adapters.repositories.leilao_repository import LeilaoRepository
from domain.eventos import LanceRealizado
from domain.exceptions import LeilaoNaoEncontradoError
from domain.lance import Lance


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


class DarLance:
    def __init__(
        self,
        leiloes: LeilaoRepository,
        publicador: PublicadorEventos,
        relogio: Callable[[], datetime] = _agora_utc,
    ) -> None:
        self._leiloes = leiloes
        self._publicador = publicador
        self._relogio = relogio

    def executar(self, leilao_id: UUID, comprador_id: UUID | int, valor: Decimal) -> Lance:
        with self._leiloes.travar_para_lance(leilao_id) as leilao:
            if leilao is None:
                raise LeilaoNaoEncontradoError(f"leilao {leilao_id} nao encontrado")
            # O momento e lido com a trava na mao: a ordem dos lances aceitos
            # e a mesma ordem dos seus timestamps.
            lance = leilao.receber_lance(
                comprador_id=comprador_id, valor=valor, momento=self._relogio()
            )
            self._leiloes.salvar(leilao)

        self._publicador.publicar(
            LanceRealizado(
                leilao_id=lance.leilao_id,
                lance_id=lance.id,
                comprador_id=lance.comprador_id,
                valor=lance.valor,
                ocorrido_em=lance.criado_em,
            )
        )
        return lance

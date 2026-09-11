"""
domain/lance.py

Entidade de dominio: Lance.

Um Lance e um fato imutavel: depois de aceito por um Leilao, valor, comprador e
momento nao mudam mais - e isso que torna o historico de lances auditavel.

Este modulo valida apenas o que torna um Lance valido *por si so* (valor
positivo e finito, momento com fuso horario). As regras que dependem do estado
do leilao (status aberto, janela temporal, incremento minimo, vendedor nao pode
dar lance) vivem em `Leilao.validar_lance`, porque so o leilao conhece esse
contexto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from domain.exceptions import LanceInvalidoError


@dataclass(frozen=True)
class Lance:
    leilao_id: UUID
    comprador_id: UUID | int
    valor: Decimal
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.validar_valor(self.valor)
        if self.comprador_id is None:
            raise LanceInvalidoError("o lance precisa de um comprador")
        if self.criado_em.tzinfo is None:
            raise LanceInvalidoError(
                "o momento do lance precisa ter fuso horario (use datetime com tzinfo)"
            )

    @staticmethod
    def validar_valor(valor: Decimal) -> None:
        """Usado tambem por Leilao.validar_lance, antes de comparar com o minimo exigido."""
        # float e rejeitado de proposito: 0.1 + 0.2 != 0.3 nao pode decidir leilao.
        if not isinstance(valor, Decimal):
            raise LanceInvalidoError("o valor do lance deve ser Decimal")
        if not valor.is_finite():
            raise LanceInvalidoError("o valor do lance deve ser um numero finito")
        if valor <= Decimal("0"):
            raise LanceInvalidoError("o valor do lance deve ser maior que 0")

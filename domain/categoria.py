from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


class CategoriaError(ValueError):
    """Erro de regra de negócio da categoria."""


@dataclass
class Categoria:
    nome: str
    ativa: bool = True
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        self._validar_campos_basicos()

    def _validar_campos_basicos(self) -> None:
        if not self.nome or not self.nome.strip():
            raise CategoriaError("nome obrigatorio")
        self.nome = self.nome.strip()

    def esta_ativa(self) -> bool:
        return self.ativa

    def inativar(self) -> None:
        self.ativa = False

    def ativar(self) -> None:
        self.ativa = True

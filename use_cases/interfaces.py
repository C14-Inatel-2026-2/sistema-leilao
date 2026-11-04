"""use_cases/interfaces.py

Contratos (interfaces) de que os casos de uso dependem.

Ficam na camada de casos de uso porque sao eles que os definem e consomem.
As implementacoes concretas (banco, bcrypt...) vivem em adapters/ e infra/ e
importam estes contratos - nunca o contrario (must-read, secao 3.1).
Nos testes unitarios, Mocks ocupam o lugar das implementacoes.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from domain.usuario import Usuario


class UsuarioRepository(Protocol):
    def buscar_por_email(self, email: str) -> Usuario | None:
        """Retorna o Usuario com o email informado, ou None se nao existir."""
        ...

    def salvar(self, usuario: Usuario) -> None:
        """Persiste um Usuario novo ou atualizado."""
        ...


class PasswordHasher(Protocol):
    def gerar_hash(self, senha: str) -> str:
        """Gera o hash da senha em texto puro; o algoritmo fica na infra."""
        ...


class AuditoriaRepository(Protocol):
    """Porta para auditoria de leilões."""

    def salvar_lance(
        self,
        leilao_id: UUID,
        lance_id: UUID,
        usuario_id: UUID,
        valor: Decimal,
        data_hora: datetime,
    ) -> None:
        """Registra uma ação de lance realizado para auditoria/histórico."""
        ...

    def salvar_encerramento(
        self,
        leilao_id: UUID,
        vencedor_id: UUID | None,
        valor_final: Decimal | None,
        data_encerramento: datetime,
        motivo: str | None = None,
    ) -> None:
        """Registra o encerramento do leilão e o resultado da apuração."""
        ...

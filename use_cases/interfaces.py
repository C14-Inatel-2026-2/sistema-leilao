"""
use_cases/interfaces.py

Contratos (interfaces) de que os casos de uso dependem.

Ficam na camada de casos de uso porque sao eles que os definem e consomem.
As implementacoes concretas (banco, bcrypt...) vivem em adapters/ e infra/ e
importam estes contratos - nunca o contrario (must-read, secao 3.1).
Nos testes unitarios, Mocks ocupam o lugar das implementacoes.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from domain.leilao import Leilao
from domain.usuario import Usuario


class UsuarioRepository(Protocol):
    def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        """Retorna o Usuario com o id informado, ou None se nao existir."""
        ...

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

    def verificar(self, senha: str, senha_hash: str) -> bool:
        """Indica se a senha em texto puro corresponde ao hash."""
        ...


class LeilaoRepository(Protocol):
    def buscar_por_id(self, leilao_id: UUID) -> Leilao | None: ...

    def buscar_com_lock(self, leilao_id: UUID) -> Leilao | None:
        """Carrega o leilao travado (SELECT ... FOR UPDATE) ate o commit."""
        ...

    def salvar(self, leilao: Leilao) -> None: ...

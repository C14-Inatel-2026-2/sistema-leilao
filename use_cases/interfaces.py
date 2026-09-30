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
        """Retorna o hash da senha em texto puro (bcrypt, argon2... e detalhe da infra)."""
        ...

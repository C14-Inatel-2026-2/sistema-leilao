"""
use_cases/interfaces.py

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

from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from domain.categoria import Categoria
from domain.leilao import Leilao, StatusLeilao
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

    def listar_por_status(self, status: StatusLeilao) -> list[Leilao]: ...

    def salvar(self, leilao: Leilao) -> None: ...


class CategoriaRepository(Protocol):
    def buscar_por_id(self, categoria_id: UUID) -> Categoria | None: ...

    def listar_ativas(self) -> list[Categoria]: ...


class AnuncioRepository(Protocol):
    def buscar_por_id(self, anuncio_id: UUID) -> Anuncio | None: ...

    def listar(
        self,
        *,
        categoria_id: UUID | None = None,
        status: StatusAnuncio | None = None,
        tipo: TipoAnuncio | None = None,
        texto: str | None = None,
    ) -> list[Anuncio]: ...

    def salvar(self, anuncio: Anuncio) -> None: ...


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

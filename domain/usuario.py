"""
domain/usuario.py

Entidade de dominio: Usuario.

Regra de ouro deste modulo: SEM imports de FastAPI, SQLAlchemy, PyJWT
ou qualquer biblioteca de infraestrutura. Aqui vive somente a regra de
negocio - o que torna um Usuario valido e o que ele pode ou nao fazer.

A geracao do hash de senha (bcrypt, argon2...) e responsabilidade da camada de
infra/use_cases. O dominio so valida a POLITICA da senha em texto puro, antes
do hash ser gerado, e depois armazena apenas o hash.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from domain.exceptions import UsuarioInvalidoError


class PapelUsuario(str, Enum):
    COMPRADOR = 'comprador'
    VENDEDOR = 'vendedor'


_EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
NOME_TAMANHO_MINIMO = 2
SENHA_TAMANHO_MINIMO = 12


@dataclass
class Usuario:
    nome: str
    email: str
    senha_hash: str
    papel: PapelUsuario
    id: UUID = field(default_factory=uuid4)
    ativo: bool = True
    criado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        self._validar_nome(self.nome)
        self._validar_email(self.email)
        if not self.senha_hash:
            raise UsuarioInvalidoError(
                'Usuario precisa de senha_hash definido '
                '(o hash, nunca a senha em texto puro).'
            )

    @staticmethod
    def _validar_nome(nome: str) -> None:
        if not nome or not nome.strip():
            raise UsuarioInvalidoError('Nome nao pode ser vazio.')
        if len(nome.strip()) < NOME_TAMANHO_MINIMO:
            raise UsuarioInvalidoError(
                f'Nome precisa ter ao menos {NOME_TAMANHO_MINIMO} caracteres.'
            )

    @staticmethod
    def _validar_email(email: str) -> None:
        if not email or not _EMAIL_REGEX.match(email):
            raise UsuarioInvalidoError(f'Email invalido: {email!r}')

    @staticmethod
    def validar_senha_em_texto_puro(senha: str) -> None:
        """
        Valida a politica de senha ANTES do hash ser gerado.

        Quem efetivamente gera o hash (bcrypt/argon2) e a camada de
        infraestrutura - este metodo so garante que a senha em texto puro
        cumpre as regras de negocio antes de chegar la.
        """
        if senha is None or len(senha) < SENHA_TAMANHO_MINIMO:
            raise UsuarioInvalidoError(
                'Senha precisa ter ao menos '
                f'{SENHA_TAMANHO_MINIMO} caracteres.'
            )
        if senha.isalpha() or senha.isdigit():
            raise UsuarioInvalidoError(
                'Senha precisa combinar letras e numeros.'
            )

    def promover_a_vendedor(self) -> None:
        self.papel = PapelUsuario.VENDEDOR

    def desativar(self) -> None:
        self.ativo = False

    def pode_criar_anuncio(self) -> bool:
        """Regra usada pelo Catalogo: so vendedor ativo cria anuncio."""
        return self.ativo and self.papel == PapelUsuario.VENDEDOR

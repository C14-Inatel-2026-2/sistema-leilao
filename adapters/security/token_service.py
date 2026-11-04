"""
adapters/security/token_service.py

Geracao e validacao dos tokens JWT de acesso (must-read, secao 4.1).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from domain.usuario import PapelUsuario, Usuario


class TokenInvalidoError(Exception):
    """Token adulterado, expirado ou com conteudo inesperado."""


@dataclass(frozen=True)
class DadosToken:
    usuario_id: UUID
    papel: PapelUsuario


class TokenService:
    def __init__(
        self, chave_secreta: str, algoritmo: str, expiracao_minutos: int
    ) -> None:
        self._chave_secreta = chave_secreta
        self._algoritmo = algoritmo
        self._expiracao_minutos = expiracao_minutos

    @classmethod
    def from_env(cls) -> TokenService:
        chave_secreta = os.getenv('JWT_SECRET_KEY')
        if not chave_secreta:
            raise RuntimeError(
                'JWT_SECRET_KEY is not set, '
                'Copy it from .env.example and add it to .env'
            )
        return cls(
            chave_secreta=chave_secreta,
            algoritmo=os.getenv('JWT_ALGORITHM', 'HS256'),
            expiracao_minutos=int(
                os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '60')
            ),
        )

    def gerar(self, usuario: Usuario) -> str:
        expiracao = datetime.now(timezone.utc) + timedelta(
            minutes=self._expiracao_minutos
        )
        claims = {
            'sub': str(usuario.id),
            'role': usuario.papel.value,
            'exp': expiracao,
        }
        return jwt.encode(claims, self._chave_secreta, self._algoritmo)

    def validar(self, token: str) -> DadosToken:
        try:
            claims = jwt.decode(
                token,
                self._chave_secreta,
                algorithms=[self._algoritmo],
                options={'require': ['sub', 'role', 'exp']},
            )
            return DadosToken(
                usuario_id=UUID(claims['sub']),
                papel=PapelUsuario(claims['role']),
            )
        except (jwt.InvalidTokenError, ValueError) as exc:
            raise TokenInvalidoError('Token invalido ou expirado.') from exc

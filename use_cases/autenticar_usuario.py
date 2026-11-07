"""
use_cases/autenticar_usuario.py

Caso de uso: AutenticarUsuario.

Confere as credenciais de login e devolve o usuario autenticado. A geracao do
token fica na camada de API. Toda recusa levanta o mesmo erro, para a resposta
nao revelar quais emails estao cadastrados nem quais contas estao ativas.
"""

from __future__ import annotations

from domain.exceptions import CredenciaisInvalidasError
from domain.usuario import Usuario
from use_cases.interfaces import PasswordHasher, UsuarioRepository


class AutenticarUsuario:
    def __init__(
        self, repositorio: UsuarioRepository, hasher: PasswordHasher
    ) -> None:
        self._repositorio = repositorio
        self._hasher = hasher

    def executar(self, email: str, senha: str) -> Usuario:
        usuario = self._repositorio.buscar_por_email(email)

        if (
            usuario is None
            or not self._hasher.verificar(senha, usuario.senha_hash)
            or not usuario.ativo
        ):
            raise CredenciaisInvalidasError('Email ou senha invalidos.')

        return usuario

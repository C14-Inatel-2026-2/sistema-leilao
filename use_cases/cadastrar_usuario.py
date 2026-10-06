"""
use_cases/cadastrar_usuario.py

Caso de uso: CadastrarUsuario.

Orquestra o cadastro de uma conta nova. As dependencias (repositorio e hasher)
chegam pelo construtor - o caso de uso conhece apenas os contratos, nunca o
banco nem o algoritmo de hash concretos.
"""

from __future__ import annotations

from domain.exceptions import EmailJaCadastradoError
from domain.usuario import PapelUsuario, Usuario
from use_cases.interfaces import PasswordHasher, UsuarioRepository


class CadastrarUsuario:
    def __init__(self, repositorio: UsuarioRepository, hasher: PasswordHasher) -> None:
        self._repositorio = repositorio
        self._hasher = hasher

    def executar(
        self,
        nome: str,
        email: str,
        senha: str,
        papel: PapelUsuario = PapelUsuario.COMPRADOR,
    ) -> Usuario:
        Usuario.validar_senha_em_texto_puro(senha)

        # Checado antes do hash: gerar hash e caro de proposito (bcrypt).
        if self._repositorio.buscar_por_email(email) is not None:
            raise EmailJaCadastradoError(f"Email ja cadastrado: {email!r}")

        senha_hash = self._hasher.gerar_hash(senha)
        usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash, papel=papel)

        self._repositorio.salvar(usuario)
        return usuario

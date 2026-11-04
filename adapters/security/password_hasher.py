"""
adapters/security/password_hasher.py

Implementacao do contrato PasswordHasher com bcrypt.
"""

from __future__ import annotations

import bcrypt

from domain.usuario import SENHA_BYTES_MAXIMO


class BcryptPasswordHasher:
    def __init__(self, rounds: int = 12) -> None:
        self._rounds = rounds

    def gerar_hash(self, senha: str) -> str:
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verificar(senha: str, senha_hash: str) -> bool:
        senha_bytes = senha.encode('utf-8')
        # O bcrypt levanta erro acima do limite. No login, isso e apenas uma
        # senha incorreta, pois nenhuma conta pode ter senha desse tamanho.
        if len(senha_bytes) > SENHA_BYTES_MAXIMO:
            return False
        return bcrypt.checkpw(senha_bytes, senha_hash.encode('utf-8'))

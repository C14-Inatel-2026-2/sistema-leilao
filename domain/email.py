"""
domain/email.py

Value Object: Email.

Concentra num lugar so a regra do que e um e-mail valido e a sua forma
canonica (sem espacos nas pontas e em minusculas). Assim, 'Teo@Example.com'
e 'teo@example.com' viram o mesmo e-mail, e nao duas contas diferentes.

Herda de str de proposito: depois de validado, o Email continua sendo texto
para o resto do sistema (banco, schemas da API, comparacoes), sem conversao.
"""

from __future__ import annotations

import re

from domain.exceptions import UsuarioInvalidoError

_EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class Email(str):
    __slots__ = ()

    def __new__(cls, valor: str) -> Email:
        if not isinstance(valor, str):
            raise UsuarioInvalidoError(f'Email invalido: {valor!r}')
        normalizado = valor.strip().lower()
        if not _EMAIL_REGEX.match(normalizado):
            raise UsuarioInvalidoError(f'Email invalido: {valor!r}')
        return super().__new__(cls, normalizado)

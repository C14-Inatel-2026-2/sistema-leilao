from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.usuario import Usuario
from infra.db.models.usuario import UsuarioModel

_CAMPOS = ('nome', 'email', 'senha_hash', 'papel', 'ativo', 'criado_em')


def _com_fuso(momento: datetime) -> datetime:
    # SQLite devolve datetime sem fuso; o PostgreSQL ja devolve em UTC.
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


def _para_dominio(model: UsuarioModel) -> Usuario:
    dados = {campo: getattr(model, campo) for campo in _CAMPOS}
    dados['criado_em'] = _com_fuso(dados['criado_em'])
    return Usuario(id=model.id, **dados)


class SQLAlchemyUsuarioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, usuario_id: UUID) -> Usuario | None:
        model = self._session.get(UsuarioModel, usuario_id)
        return _para_dominio(model) if model is not None else None

    def buscar_por_email(self, email: str) -> Usuario | None:
        consulta = select(UsuarioModel).where(UsuarioModel.email == email)
        model = self._session.scalars(consulta).first()
        return _para_dominio(model) if model is not None else None

    def salvar(self, usuario: Usuario) -> None:
        model = self._session.get(UsuarioModel, usuario.id)
        if model is None:
            model = UsuarioModel(id=usuario.id)
            self._session.add(model)
        for campo in _CAMPOS:
            setattr(model, campo, getattr(usuario, campo))
        self._session.flush()

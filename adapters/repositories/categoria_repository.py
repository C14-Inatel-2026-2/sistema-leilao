from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.categoria import Categoria
from infra.db.models.categoria import CategoriaModel

_CAMPOS = ('nome', 'ativa', 'criado_em')


def _com_fuso(momento: datetime) -> datetime:
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


def _para_dominio(model: CategoriaModel) -> Categoria:
    dados = {campo: getattr(model, campo) for campo in _CAMPOS}
    dados['criado_em'] = _com_fuso(dados['criado_em'])
    return Categoria(id=model.id, **dados)


class SQLAlchemyCategoriaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, categoria_id: UUID) -> Categoria | None:
        model = self._session.get(CategoriaModel, categoria_id)
        return _para_dominio(model) if model is not None else None

    def listar_ativas(self) -> list[Categoria]:
        consulta = (
            select(CategoriaModel)
            .where(CategoriaModel.ativa.is_(True))
            .order_by(CategoriaModel.nome)
        )
        return [_para_dominio(m) for m in self._session.scalars(consulta)]

    def salvar(self, categoria: Categoria) -> None:
        model = self._session.get(CategoriaModel, categoria.id)
        if model is None:
            model = CategoriaModel(id=categoria.id)
            self._session.add(model)
        for campo in _CAMPOS:
            setattr(model, campo, getattr(categoria, campo))
        self._session.flush()

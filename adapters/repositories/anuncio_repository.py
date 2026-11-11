from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from infra.db.models.anuncio import AnuncioModel

_CAMPOS = (
    'titulo',
    'descricao',
    'preco_referencia',
    'categoria_id',
    'vendedor_id',
    'tipo',
    'status',
    'leilao_atual_id',
    'criado_em',
)


def _com_fuso(momento: datetime) -> datetime:
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


def _para_dominio(model: AnuncioModel) -> Anuncio:
    dados = {campo: getattr(model, campo) for campo in _CAMPOS}
    dados['criado_em'] = _com_fuso(dados['criado_em'])
    return Anuncio(id=model.id, **dados)


class SQLAlchemyAnuncioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, anuncio_id: UUID) -> Anuncio | None:
        model = self._session.get(AnuncioModel, anuncio_id)
        return _para_dominio(model) if model is not None else None

    def listar(
        self,
        *,
        categoria_id: UUID | None = None,
        status: StatusAnuncio | None = None,
        tipo: TipoAnuncio | None = None,
        texto: str | None = None,
    ) -> list[Anuncio]:
        consulta = select(AnuncioModel)
        if categoria_id is not None:
            consulta = consulta.where(
                AnuncioModel.categoria_id == categoria_id
            )
        if status is not None:
            consulta = consulta.where(AnuncioModel.status == status)
        if tipo is not None:
            consulta = consulta.where(AnuncioModel.tipo == tipo)
        termo = texto.strip() if texto else ''
        if termo:
            padrao = f'%{termo}%'
            consulta = consulta.where(
                or_(
                    AnuncioModel.titulo.ilike(padrao),
                    AnuncioModel.descricao.ilike(padrao),
                )
            )
        consulta = consulta.order_by(AnuncioModel.criado_em.desc())
        return [_para_dominio(m) for m in self._session.scalars(consulta)]

    def salvar(self, anuncio: Anuncio) -> None:
        model = self._session.get(AnuncioModel, anuncio.id)
        if model is None:
            model = AnuncioModel(id=anuncio.id)
            self._session.add(model)
        for campo in _CAMPOS:
            setattr(model, campo, getattr(anuncio, campo))
        self._session.flush()

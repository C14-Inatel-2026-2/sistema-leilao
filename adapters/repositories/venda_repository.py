from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.repositories.tempo import com_fuso
from domain.venda import Venda
from infra.db.models.venda import VendaModel

_CAMPOS = (
    'anuncio_id',
    'comprador_id',
    'leilao_id',
    'valor',
    'metodo',
    'status',
    'criado_em',
)


def _para_dominio(model: VendaModel) -> Venda:
    dados = {campo: getattr(model, campo) for campo in _CAMPOS}
    dados['criado_em'] = com_fuso(dados['criado_em'])
    return Venda(id=model.id, **dados)


class SQLAlchemyVendaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, venda_id: UUID) -> Venda | None:
        model = self._session.get(VendaModel, venda_id)
        return _para_dominio(model) if model is not None else None

    def buscar_por_leilao(self, leilao_id: UUID) -> Venda | None:
        consulta = select(VendaModel).where(VendaModel.leilao_id == leilao_id)
        model = self._session.scalars(consulta).first()
        return _para_dominio(model) if model is not None else None

    def salvar(self, venda: Venda) -> None:
        model = self._session.get(VendaModel, venda.id)
        if model is None:
            model = VendaModel(id=venda.id)
            self._session.add(model)
        for campo in _CAMPOS:
            setattr(model, campo, getattr(venda, campo))
        self._session.flush()

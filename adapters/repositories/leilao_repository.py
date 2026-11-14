from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.repositories.tempo import com_fuso
from domain.lance import Lance
from domain.leilao import Leilao, StatusLeilao
from infra.db.models.lance import LanceModel
from infra.db.models.leilao import LeilaoModel

_CAMPOS = (
    'anuncio_id',
    'vendedor_id',
    'preco_inicial',
    'incremento_minimo',
    'data_inicio',
    'data_final',
    'status',
    'vencedor_id',
    'valor_arremate',
    'criado_em',
)


def _para_dominio(model: LeilaoModel) -> Leilao:
    dados = {campo: getattr(model, campo) for campo in _CAMPOS}
    for campo in ('data_inicio', 'data_final', 'criado_em'):
        dados[campo] = com_fuso(dados[campo])
    lances = [
        Lance(
            id=lance.id,
            leilao_id=lance.leilao_id,
            comprador_id=lance.comprador_id,
            valor=lance.valor,
            criado_em=com_fuso(lance.criado_em),
        )
        for lance in model.lances
    ]
    return Leilao(id=model.id, lances=lances, **dados)


class SQLAlchemyLeilaoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def buscar_por_id(self, leilao_id: UUID) -> Leilao | None:
        model = self._session.get(LeilaoModel, leilao_id)
        return _para_dominio(model) if model is not None else None

    def buscar_com_lock(self, leilao_id: UUID) -> Leilao | None:
        consulta = (
            select(LeilaoModel)
            .where(LeilaoModel.id == leilao_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        model = self._session.scalars(consulta).first()
        return _para_dominio(model) if model is not None else None

    def listar_por_status(self, status: StatusLeilao) -> list[Leilao]:
        consulta = select(LeilaoModel).where(LeilaoModel.status == status)
        return [_para_dominio(m) for m in self._session.scalars(consulta)]

    def salvar(self, leilao: Leilao) -> None:
        model = self._session.get(LeilaoModel, leilao.id)
        if model is None:
            model = LeilaoModel(id=leilao.id)
            self._session.add(model)
        for campo in _CAMPOS:
            setattr(model, campo, getattr(leilao, campo))

        existentes = {lance.id for lance in model.lances}
        model.lances.extend(
            LanceModel(
                id=lance.id,
                leilao_id=lance.leilao_id,
                comprador_id=lance.comprador_id,
                valor=lance.valor,
                criado_em=lance.criado_em,
            )
            for lance in leilao.lances
            if lance.id not in existentes
        )
        self._session.flush()

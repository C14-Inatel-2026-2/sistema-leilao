from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from infra.db.models.auditoria import AuditoriaLeilaoModel


def _com_fuso(momento: datetime) -> datetime:
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


class SQLAlchemyAuditoriaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def salvar_lance(
        self,
        leilao_id: UUID,
        lance_id: UUID,
        usuario_id: UUID,
        valor: Decimal,
        data_hora: datetime,
    ) -> None:
        registro = AuditoriaLeilaoModel(
            leilao_id=leilao_id,
            tipo_evento='LANCE_REALIZADO',
            lance_id=lance_id,
            usuario_id=usuario_id,
            valor=valor,
            data_evento=_com_fuso(data_hora),
        )
        self._session.add(registro)
        self._session.flush()

    def salvar_encerramento(
        self,
        leilao_id: UUID,
        vencedor_id: UUID | None,
        valor_final: Decimal | None,
        data_encerramento: datetime,
        motivo: str | None = None,
    ) -> None:
        registro = AuditoriaLeilaoModel(
            leilao_id=leilao_id,
            tipo_evento='LEILAO_ENCERRADO',
            lance_id=None,
            usuario_id=vencedor_id,
            valor=valor_final,
            data_evento=_com_fuso(data_encerramento),
            motivo=motivo,
        )
        self._session.add(registro)
        self._session.flush()

    def listar_por_leilao(self, leilao_id: UUID) -> list[AuditoriaLeilaoModel]:
        consulta = (
            select(AuditoriaLeilaoModel)
            .where(AuditoriaLeilaoModel.leilao_id == leilao_id)
            .order_by(AuditoriaLeilaoModel.data_evento.asc())
        )
        registros = list(self._session.scalars(consulta).all())
        for r in registros:
            r.data_evento = _com_fuso(r.data_evento)
            r.criado_em = _com_fuso(r.criado_em)
        return registros

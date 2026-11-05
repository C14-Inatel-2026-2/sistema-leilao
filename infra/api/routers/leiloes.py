from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.exceptions import LeilaoNaoEncontradoError
from infra.api.dependencies import get_session
from infra.api.schemas.lance import LanceResponse
from use_cases.listar_lances import ListarLances

router = APIRouter(prefix='/leiloes', tags=['leiloes'])


@router.get('/{leilao_id}/lances', response_model=list[LanceResponse])
def listar_lances(leilao_id: UUID, session: Session = Depends(get_session)):
    repositorio = SQLAlchemyLeilaoRepository(session)
    try:
        return ListarLances(repositorio).executar(leilao_id)
    except LeilaoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro

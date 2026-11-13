from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from adapters.events import publish
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.exceptions import DomainError, LeilaoNaoEncontradoError
from domain.usuario import Usuario
from infra.api.dependencies import get_current_user, get_session
from infra.api.schemas.lance import DarLanceRequest, LanceResponse
from use_cases.dar_lance import DarLance
from use_cases.listar_lances import ListarLances

router = APIRouter(prefix='/leiloes', tags=['leiloes'])


@router.get('/{leilao_id}/lances', response_model=list[LanceResponse])
def listar_lances(leilao_id: UUID, session: Session = Depends(get_session)):
    repositorio = SQLAlchemyLeilaoRepository(session)
    try:
        return ListarLances(repositorio).executar(leilao_id)
    except LeilaoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro


@router.post(
    '/{leilao_id}/lances', response_model=LanceResponse, status_code=201
)
def dar_lance(
    leilao_id: UUID,
    corpo: DarLanceRequest,
    session: Session = Depends(get_session),
    comprador: Usuario = Depends(get_current_user),
):
    caso_de_uso = DarLance(
        SQLAlchemyLeilaoRepository(session),
        confirmar=session.commit,
        publicar=publish,
    )
    try:
        return caso_de_uso.executar(leilao_id, comprador.id, corpo.valor)
    except LeilaoNaoEncontradoError as erro:
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    except DomainError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro

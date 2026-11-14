from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from adapters.repositories.anuncio_repository import (
    SQLAlchemyAnuncioRepository,
)
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from adapters.repositories.venda_repository import (
    SQLAlchemyVendaRepository,
)
from domain.usuario import Usuario
from infra.api.dependencies import get_current_user, get_session
from infra.api.schemas.venda import PagamentoRequest, VendaResponse
from use_cases.cancelar_venda import CancelarVenda
from use_cases.simular_pagamento import SimularPagamento

router = APIRouter(prefix='/vendas', tags=['vendas'])


@router.post('/{venda_id}/pagamento', response_model=VendaResponse)
def simular_pagamento(
    venda_id: UUID,
    corpo: PagamentoRequest,
    session: Session = Depends(get_session),
    comprador: Usuario = Depends(get_current_user),
):
    venda = SimularPagamento(
        SQLAlchemyVendaRepository(session),
        SQLAlchemyLeilaoRepository(session),
        SQLAlchemyAnuncioRepository(session),
        confirmar=session.commit,
    ).executar(venda_id, comprador.id, corpo.metodo)
    return venda


@router.post('/{venda_id}/cancelar', response_model=VendaResponse)
def cancelar_venda(
    venda_id: UUID,
    session: Session = Depends(get_session),
    comprador: Usuario = Depends(get_current_user),
):
    return CancelarVenda(
        SQLAlchemyVendaRepository(session), confirmar=session.commit
    ).executar(venda_id, comprador.id)

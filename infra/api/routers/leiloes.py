from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from adapters.events import publish
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from adapters.repositories.venda_repository import (
    SQLAlchemyVendaRepository,
)
from domain.exceptions import (
    AcessoNegadoError,
    LeilaoNaoEncontradoError,
    VendaNaoEncontradaError,
)
from domain.usuario import Usuario
from infra.api.dependencies import get_current_user, get_session
from infra.api.schemas.lance import DarLanceRequest, LanceResponse
from infra.api.schemas.leilao import LeilaoDetalheResponse
from infra.api.schemas.venda import VendaResponse
from use_cases.dar_lance import DarLance
from use_cases.listar_lances import ListarLances

router = APIRouter(prefix='/leiloes', tags=['leiloes'])


@router.get('/{leilao_id}', response_model=LeilaoDetalheResponse)
def obter_leilao(leilao_id: UUID, session: Session = Depends(get_session)):
    repositorio = SQLAlchemyLeilaoRepository(session)
    leilao = repositorio.buscar_por_id(leilao_id)
    if leilao is None:
        raise LeilaoNaoEncontradoError(f'leilao {leilao_id} nao encontrado')

    maior = leilao.maior_lance()
    return LeilaoDetalheResponse(
        id=leilao.id,
        anuncio_id=leilao.anuncio_id,
        vendedor_id=leilao.vendedor_id,
        preco_inicial=leilao.preco_inicial,
        incremento_minimo=leilao.incremento_minimo,
        data_inicio=leilao.data_inicio,
        data_final=leilao.data_final,
        status=leilao.status,
        maior_lance=maior.valor if maior is not None else None,
        vencedor_id=leilao.vencedor_id,
        valor_arremate=leilao.valor_arremate,
    )


@router.get('/{leilao_id}/venda', response_model=VendaResponse)
def obter_venda(
    leilao_id: UUID,
    session: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
):
    venda = SQLAlchemyVendaRepository(session).buscar_por_leilao(leilao_id)
    if venda is None:
        raise VendaNaoEncontradaError(
            f'venda do leilao {leilao_id} nao encontrada'
        )
    leilao = SQLAlchemyLeilaoRepository(session).buscar_por_id(leilao_id)
    if leilao is None or usuario.id not in {
        venda.comprador_id,
        leilao.vendedor_id,
    }:
        raise AcessoNegadoError(
            'somente o vendedor ou o vencedor pode ver a venda'
        )
    return venda


@router.get('/{leilao_id}/lances', response_model=list[LanceResponse])
def listar_lances(leilao_id: UUID, session: Session = Depends(get_session)):
    repositorio = SQLAlchemyLeilaoRepository(session)
    return ListarLances(repositorio).executar(leilao_id)


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
    return caso_de_uso.executar(leilao_id, comprador.id, corpo.valor)

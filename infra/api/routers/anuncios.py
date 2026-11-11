from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from adapters.repositories.anuncio_repository import (
    SQLAlchemyAnuncioRepository,
)
from adapters.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from adapters.repositories.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from domain.anuncio import StatusAnuncio, TipoAnuncio
from domain.exceptions import DomainError
from infra.api.dependencies import get_session
from infra.api.schemas.anuncio import (
    AnuncioCriadoResponse,
    AnuncioResponse,
    CriarAnuncioRequest,
)
from use_cases.criar_anuncio import CriarAnuncio, DadosNovoAnuncio

router = APIRouter(prefix='/anuncios', tags=['anuncios'])


def _dados(corpo: CriarAnuncioRequest) -> DadosNovoAnuncio:
    return DadosNovoAnuncio(
        titulo=corpo.titulo,
        descricao=corpo.descricao,
        preco_referencia=corpo.preco_referencia,
        categoria_id=corpo.categoria_id,
        vendedor_id=corpo.vendedor_id,
        preco_inicial=corpo.preco_inicial,
        incremento_minimo=corpo.incremento_minimo,
        data_inicio=corpo.data_inicio,
        data_final=corpo.data_final,
    )


@router.post('', response_model=AnuncioCriadoResponse, status_code=201)
def criar_anuncio(
    corpo: CriarAnuncioRequest,
    session: Session = Depends(get_session),
):
    caso_de_uso = CriarAnuncio(
        SQLAlchemyAnuncioRepository(session),
        SQLAlchemyCategoriaRepository(session),
        SQLAlchemyLeilaoRepository(session),
        SQLAlchemyUsuarioRepository(session),
    )
    try:
        anuncio, leilao = caso_de_uso.executar(_dados(corpo))
    except DomainError as erro:
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    session.commit()
    return {'anuncio': anuncio, 'leilao': leilao}


@router.get('', response_model=list[AnuncioResponse])
def listar_anuncios(
    session: Session = Depends(get_session),
    categoria_id: UUID | None = None,
    status: StatusAnuncio | None = None,
    tipo: TipoAnuncio | None = None,
    texto: str | None = None,
):
    return SQLAlchemyAnuncioRepository(session).listar(
        categoria_id=categoria_id,
        status=status,
        tipo=tipo,
        texto=texto,
    )

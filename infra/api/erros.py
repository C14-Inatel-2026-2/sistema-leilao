from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from domain.exceptions import (
    AcessoNegadoError,
    AnuncioNaoEncontradoError,
    CredenciaisInvalidasError,
    DomainError,
    EmailJaCadastradoError,
    LeilaoNaoEncontradoError,
)


def registrar_erros(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    def tratar_erro_de_dominio(_pedido, erro: DomainError) -> JSONResponse:
        codigo = status.HTTP_400_BAD_REQUEST
        headers = None
        if isinstance(erro, CredenciaisInvalidasError):
            codigo = status.HTTP_401_UNAUTHORIZED
            headers = {'WWW-Authenticate': 'Bearer'}
        elif isinstance(erro, EmailJaCadastradoError):
            codigo = status.HTTP_409_CONFLICT
        elif isinstance(
            erro, (LeilaoNaoEncontradoError, AnuncioNaoEncontradoError)
        ):
            codigo = status.HTTP_404_NOT_FOUND
        elif isinstance(erro, AcessoNegadoError):
            codigo = status.HTTP_403_FORBIDDEN
        return JSONResponse(
            status_code=codigo,
            content={'detail': str(erro)},
            headers=headers,
        )

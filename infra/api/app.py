"""Factory da aplicação FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import DomainError


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # APScheduler liga no startup em feature/jobs-leilao; aqui só o gancho.
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sistema de Leilão",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    @app.exception_handler(DomainError)
    def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "codigo": getattr(exc, "codigo", "ERRO_DOMINIO"),
                "mensagem": str(exc),
            },
        )

    return app

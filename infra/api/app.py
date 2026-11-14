# implementação básica para teste de pipeline no deploy
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infra.api.erros import registrar_erros
from infra.api.routers import anuncios, auth, leiloes, vendas
from infra.jobs.leiloes import iniciar_agendador


@asynccontextmanager
async def lifespan(_app: FastAPI):
    agendador = iniciar_agendador()
    yield
    if agendador is not None:
        agendador.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title='Sistema de Leilão', lifespan=lifespan)
    registrar_erros(app)

    @app.get('/')
    def health():
        return {'status': 'ok'}

    app.include_router(auth.router)
    app.include_router(leiloes.router)
    app.include_router(anuncios.router)
    app.include_router(vendas.router)
    return app

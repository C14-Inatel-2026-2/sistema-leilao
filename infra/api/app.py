# implementação básica para teste de pipeline no deploy
from fastapi import FastAPI

from infra.api.routers import anuncios, leiloes


def create_app() -> FastAPI:
    app = FastAPI(title='Sistema de Leilão')

    @app.get('/')
    def health():
        return {'status': 'ok'}

    app.include_router(anuncios.router)
    app.include_router(leiloes.router)
    return app

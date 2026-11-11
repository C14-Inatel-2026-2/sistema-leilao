# implementação básica para teste de pipeline no deploy
from fastapi import FastAPI

from infra.api.routers import auth, leiloes


def create_app() -> FastAPI:
    app = FastAPI(title='Sistema de Leilão')

    @app.get('/')
    def health():
        return {'status': 'ok'}

    app.include_router(auth.router)
    app.include_router(leiloes.router)
    return app

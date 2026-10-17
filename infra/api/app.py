#implementação básica para teste de pipeline no deploy
from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="Sistema de Leilão")
    @app.get("/")
    def health():
        return {"status": "ok"}
    return app

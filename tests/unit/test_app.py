"""Smoke tests da factory FastAPI (OpenAPI e handler de DomainError)."""

from fastapi.testclient import TestClient

from domain.exceptions import DomainError
from infra.api.app import create_app


def test_docs_e_openapi_disponiveis() -> None:
    client = TestClient(create_app())

    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_domain_error_vira_payload_400() -> None:
    app = create_app()

    @app.get("/_teste-erro")
    def _boom() -> None:
        raise DomainError("lance abaixo do incremento minimo")

    client = TestClient(app)
    response = client.get("/_teste-erro")

    assert response.status_code == 400
    assert response.json() == {
        "codigo": "ERRO_DOMINIO",
        "mensagem": "lance abaixo do incremento minimo",
    }

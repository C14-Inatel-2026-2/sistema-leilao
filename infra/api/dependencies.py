"""Provedores FastAPI Depends() — sessão, repositórios e usuário autenticado."""

from infra.db.session import get_db

__all__ = ["get_db"]

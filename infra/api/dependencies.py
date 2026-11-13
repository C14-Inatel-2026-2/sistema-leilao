from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from adapters.repositories.usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from adapters.security.password_hasher import BcryptPasswordHasher
from adapters.security.token_service import TokenInvalidoError, TokenService
from domain.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def get_session() -> Iterator[Session]:
    # Import tardio: infra.db.session exige DATABASE_URL ao ser importado.
    from infra.db.session import SessionLocal  # noqa: PLC0415

    with SessionLocal() as session:
        yield session


def get_usuario_repository(
    session: Session = Depends(get_session),
) -> SQLAlchemyUsuarioRepository:
    return SQLAlchemyUsuarioRepository(session)


UsuarioRepositoryDep = Annotated[
    SQLAlchemyUsuarioRepository, Depends(get_usuario_repository)
]


def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    # Le as variaveis de ambiente uma vez so (JWT_SECRET_KEY e obrigatoria).
    return TokenService.from_env()


def get_current_user(
    repositorio: UsuarioRepositoryDep,
    token: str = Depends(oauth2_scheme),
    tokens: TokenService = Depends(get_token_service),
) -> Usuario:
    nao_autenticado = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Token invalido ou expirado.',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        dados = tokens.validar(token)
    except TokenInvalidoError as erro:
        raise nao_autenticado from erro

    # O token pode ser valido e a conta ter sido removida ou desativada.
    usuario = repositorio.buscar_por_id(dados.usuario_id)
    if usuario is None or not usuario.ativo:
        raise nao_autenticado
    return usuario

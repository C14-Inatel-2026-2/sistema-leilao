from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from adapters.security.password_hasher import BcryptPasswordHasher
from adapters.security.token_service import TokenService
from domain.exceptions import (
    CredenciaisInvalidasError,
    EmailJaCadastradoError,
    UsuarioInvalidoError,
)
from domain.usuario import Usuario
from infra.api.dependencies import (
    UsuarioRepositoryDep,
    get_current_user,
    get_password_hasher,
    get_session,
    get_token_service,
)
from infra.api.schemas.usuario import (
    CadastroRequest,
    TokenResponse,
    UsuarioResponse,
)
from use_cases.autenticar_usuario import AutenticarUsuario
from use_cases.cadastrar_usuario import CadastrarUsuario

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post(
    '/register',
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar(
    dados: CadastroRequest,
    repositorio: UsuarioRepositoryDep,
    session: Session = Depends(get_session),
    hasher: BcryptPasswordHasher = Depends(get_password_hasher),
):
    try:
        usuario = CadastrarUsuario(repositorio, hasher).executar(
            nome=dados.nome,
            email=dados.email,
            senha=dados.senha,
            papel=dados.papel,
        )
    except UsuarioInvalidoError as erro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)
        ) from erro
    except EmailJaCadastradoError as erro:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(erro)
        ) from erro
    session.commit()
    return usuario


@router.post('/login', response_model=TokenResponse)
def login(
    repositorio: UsuarioRepositoryDep,
    form: OAuth2PasswordRequestForm = Depends(),
    hasher: BcryptPasswordHasher = Depends(get_password_hasher),
    tokens: TokenService = Depends(get_token_service),
):
    # Padrao OAuth2: o campo se chama "username", mas recebe o e-mail.
    try:
        usuario = AutenticarUsuario(repositorio, hasher).executar(
            form.username, form.password
        )
    except CredenciaisInvalidasError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(erro),
            headers={'WWW-Authenticate': 'Bearer'},
        ) from erro
    return TokenResponse(access_token=tokens.gerar(usuario))


@router.get('/me', response_model=UsuarioResponse)
def perfil(usuario: Usuario = Depends(get_current_user)):
    return usuario

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from domain.usuario import PapelUsuario


class CadastroRequest(BaseModel):
    # Sem validacao de formato aqui: as regras ficam no dominio (Usuario).
    nome: str
    email: str
    senha: str
    papel: PapelUsuario = PapelUsuario.COMPRADOR


class UsuarioResponse(BaseModel):
    # Nunca expor senha_hash: o schema de saida lista so o que e publico.
    id: UUID
    nome: str
    email: str
    papel: PapelUsuario
    ativo: bool
    criado_em: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'

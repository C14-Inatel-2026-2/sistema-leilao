"""
domain/exceptions.py

Excecoes de dominio, compartilhadas entre as entidades (Usuario, Anuncio, Leilao...).

Usar excecoes especificas (em vez de ValueError generico) deixa explicito, no
bloco except da camada de infra/Flask, que a rejeicao veio de uma regra de
negocio violada - e nao de um bug ou erro tecnico.
"""


class DomainError(Exception):
    """Excecao base para qualquer violacao de regra de negocio do dominio."""


class UsuarioInvalidoError(DomainError):
    """Levantada quando os dados de um Usuario violam uma regra de negocio."""


class AnuncioInvalidoError(DomainError):
    """Levantada quando os dados de um Anuncio violam uma regra de negocio."""


class CategoriaInvalidaError(DomainError):
    """Levantada quando os dados de uma Categoria violam uma regra de negocio."""


# As excecoes de Leilao/Lance tambem herdam de ValueError para nao quebrar quem
# ja as capturava assim quando viviam em domain/leilao.py.


class LeilaoInvalidoError(DomainError, ValueError):
    """Dados de criacao do leilao invalidos (preco negativo, datas incorretas, etc.)."""


class EstadoLeilaoInvalidoError(DomainError, ValueError):
    """Tentativa de transicao de estado proibida (ex: lance em leilao cancelado)."""


class LanceInvalidoError(DomainError, ValueError):
    """Lance rejeitado por regras de negocio (valor baixo, vendedor dando lance, etc.)."""


class LeilaoNaoEncontradoError(DomainError):
    """O leilao informado nao existe (a camada HTTP traduz para 404)."""

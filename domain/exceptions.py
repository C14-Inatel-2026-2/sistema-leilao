"""
domain/exceptions.py

Excecoes de dominio, compartilhadas entre as entidades (Usuario, Anuncio,
Leilao...).

Usar excecoes especificas (em vez de ValueError generico) deixa explicito, no
handler HTTP da camada de infra, que a rejeicao veio de uma regra de
negocio violada - e nao de um bug ou erro tecnico.
"""


class DomainError(Exception):
    """Excecao base para qualquer violacao de regra de negocio do dominio."""


class UsuarioInvalidoError(DomainError):
    """Levantada quando os dados de um Usuario violam uma regra de negocio."""


class EmailJaCadastradoError(DomainError):
    """Levantada ao cadastrar um Usuario com email ja usado por outra conta."""


class CredenciaisInvalidasError(DomainError):
    """Login recusado, sem revelar se o email existe ou a conta esta ativa."""


class AnuncioInvalidoError(DomainError):
    """Levantada quando os dados de um Anuncio violam uma regra de negocio."""


class CategoriaInvalidaError(DomainError):
    """Levantada quando os dados de uma Categoria violam regra de negocio."""


class LeilaoInvalidoError(DomainError):
    """Dados de criacao do leilao invalidos (preco negativo, datas, etc.)."""


class EstadoLeilaoInvalidoError(DomainError):
    """Transicao de estado proibida (ex: lance em leilao cancelado)."""


class LanceInvalidoError(DomainError):
    """Lance rejeitado por regra de negocio (valor baixo, vendedor, etc.)."""


class LeilaoNaoEncontradoError(DomainError):
    """O leilao informado nao existe (a camada HTTP traduz para 404)."""


class AnuncioNaoEncontradoError(DomainError):
    """O anuncio informado nao existe (a camada HTTP traduz para 404)."""


class AcessoNegadoError(DomainError):
    """O usuario autenticado nao pode executar a operacao (HTTP 403)."""


class VendaInvalidaError(DomainError):
    """Venda recusada por valor, estado ou leilao sem vencedor."""


class VendaNaoEncontradaError(DomainError):
    """A venda informada nao existe (a camada HTTP traduz para 404)."""

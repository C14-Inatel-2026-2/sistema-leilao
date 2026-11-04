"""
tests/integration/test_catalogo_repositories.py

Fase red: persistencia dos repositorios de catalogo.

Contrato (use_cases.interfaces + adapters.repositories):

- SQLAlchemyCategoriaRepository(session)
  salvar(categoria) -> None
  buscar_por_id(categoria_id) -> Categoria | None
  listar_ativas() -> list[Categoria]
- SQLAlchemyAnuncioRepository(session)
  salvar(anuncio) -> None  (insert ou update)
  buscar_por_id(anuncio_id) -> Anuncio | None
  listar(*, categoria_id=None, tipo=None, status=None) -> list[Anuncio]
- SQLAlchemyLeilaoRepository(session)
  salvar(leilao) -> None  (leilao e seus lances)
  buscar_por_id(leilao_id) -> Leilao | None
  buscar_com_lock(leilao_id) -> Leilao | None
  listar_por_status(status) -> list[Leilao]

salvar deixa a linha visivel na mesma sessao (flush). buscar devolve
entidade de domain/, nunca o model ORM. buscar_com_lock emite
SELECT ... FOR UPDATE nos dialetos que suportam a clausula
(PostgreSQL). Em SQLite o metodo ainda devolve a entidade.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import event

from adapters.repositories.anuncio_repository import (
    SQLAlchemyAnuncioRepository,
)
from adapters.repositories.categoria_repository import (
    SQLAlchemyCategoriaRepository,
)
from adapters.repositories.leilao_repository import (
    SQLAlchemyLeilaoRepository,
)
from domain.anuncio import Anuncio, StatusAnuncio, TipoAnuncio
from domain.categoria import Categoria
from domain.lance import Lance
from domain.leilao import Leilao, StatusLeilao


def _anuncio(categoria, **overrides) -> Anuncio:
    dados = dict(
        titulo='Notebook',
        descricao='Usado, funcionando',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria.id,
        vendedor_id=uuid4(),
    )
    dados.update(overrides)
    return Anuncio(**dados)


def _leilao(anuncio, **overrides) -> Leilao:
    inicio = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
    dados = dict(
        anuncio_id=anuncio.id,
        vendedor_id=anuncio.vendedor_id,
        preco_inicial=Decimal('100.00'),
        incremento_minimo=Decimal('5.00'),
        data_inicio=inicio,
        data_final=inicio + timedelta(hours=2),
    )
    dados.update(overrides)
    return Leilao(**dados)


def test_categoria_repository_salva_e_busca_por_id(session):
    repo = SQLAlchemyCategoriaRepository(session)
    categoria = Categoria(nome='Eletronicos')

    repo.salvar(categoria)
    lida = repo.buscar_por_id(categoria.id)

    assert isinstance(lida, Categoria)
    assert lida.id == categoria.id
    assert lida.nome == 'Eletronicos'
    assert lida.ativa is True
    assert isinstance(lida.criado_em, datetime)
    assert repo.buscar_por_id(uuid4()) is None

    categoria.nome = 'Informatica'
    repo.salvar(categoria)
    atualizada = repo.buscar_por_id(categoria.id)
    assert atualizada.nome == 'Informatica'


def test_categoria_repository_lista_apenas_ativas(session):
    repo = SQLAlchemyCategoriaRepository(session)
    ativa = Categoria(nome='Eletronicos')
    inativa = Categoria(nome='Moveis')
    repo.salvar(ativa)
    repo.salvar(inativa)
    inativa.inativar()
    repo.salvar(inativa)

    listadas = repo.listar_ativas()
    relida = repo.buscar_por_id(inativa.id)

    assert [categoria.id for categoria in listadas] == [ativa.id]
    assert listadas[0].esta_ativa() is True
    assert isinstance(listadas[0], Categoria)
    assert relida.ativa is False


def test_anuncio_repository_salva_atualiza_e_busca_por_id(session):
    categorias = SQLAlchemyCategoriaRepository(session)
    anuncios = SQLAlchemyAnuncioRepository(session)
    leiloes = SQLAlchemyLeilaoRepository(session)
    categoria = Categoria(nome='Eletronicos')
    categorias.salvar(categoria)
    anuncio = _anuncio(categoria)
    anuncios.salvar(anuncio)
    leilao = _leilao(anuncio)
    leiloes.salvar(leilao)

    anuncio.associar_leilao(leilao.id)
    anuncio.inativar()
    anuncios.salvar(anuncio)
    lido = anuncios.buscar_por_id(anuncio.id)

    assert isinstance(lido, Anuncio)
    assert lido.id == anuncio.id
    assert lido.titulo == 'Notebook'
    assert lido.descricao == 'Usado, funcionando'
    assert lido.preco_referencia == Decimal('1500.00')
    assert lido.categoria_id == categoria.id
    assert lido.vendedor_id == anuncio.vendedor_id
    assert lido.tipo is TipoAnuncio.LEILAO
    assert lido.status is StatusAnuncio.INATIVO
    assert lido.leilao_atual_id == leilao.id
    assert isinstance(lido.criado_em, datetime)
    assert anuncios.buscar_por_id(uuid4()) is None


def test_anuncio_repository_lista_com_filtros(session):
    categorias = SQLAlchemyCategoriaRepository(session)
    anuncios = SQLAlchemyAnuncioRepository(session)
    categoria_a = Categoria(nome='Eletronicos')
    categoria_b = Categoria(nome='Moveis')
    categorias.salvar(categoria_a)
    categorias.salvar(categoria_b)
    alvo = _anuncio(categoria_a, titulo='Notebook alvo')
    leilao = _anuncio(
        categoria_a,
        titulo='Notebook leilao',
        tipo=TipoAnuncio.LEILAO,
    )
    inativo = _anuncio(
        categoria_a,
        titulo='Notebook inativo',
        status=StatusAnuncio.INATIVO,
    )
    outra_categoria = _anuncio(categoria_b, titulo='Cadeira')
    for anuncio in (alvo, leilao, inativo, outra_categoria):
        anuncios.salvar(anuncio)

    encontrados = anuncios.listar(
        categoria_id=categoria_a.id,
        tipo=TipoAnuncio.VENDA_DIRETA,
        status=StatusAnuncio.ATIVO,
    )

    assert [item.id for item in encontrados] == [alvo.id]
    assert isinstance(encontrados[0], Anuncio)
    assert encontrados[0].titulo == 'Notebook alvo'


def test_leilao_repository_salva_e_reconstroi_com_lances(session):
    categorias = SQLAlchemyCategoriaRepository(session)
    anuncios = SQLAlchemyAnuncioRepository(session)
    leiloes = SQLAlchemyLeilaoRepository(session)
    categoria = Categoria(nome='Eletronicos')
    categorias.salvar(categoria)
    anuncio = _anuncio(categoria)
    anuncios.salvar(anuncio)
    leilao = _leilao(anuncio)
    tarde = datetime(2026, 11, 3, 14, 0, tzinfo=timezone.utc)
    cedo = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc)
    lance_tarde = Lance(
        leilao_id=leilao.id,
        comprador_id=uuid4(),
        valor=Decimal('20.00'),
        criado_em=tarde,
    )
    lance_cedo = Lance(
        leilao_id=leilao.id,
        comprador_id=uuid4(),
        valor=Decimal('10.00'),
        criado_em=cedo,
    )
    leilao.lances = [lance_tarde, lance_cedo]
    leiloes.salvar(leilao)

    lido = leiloes.buscar_por_id(leilao.id)

    assert isinstance(lido, Leilao)
    assert lido.id == leilao.id
    assert lido.anuncio_id == anuncio.id
    assert lido.vendedor_id == anuncio.vendedor_id
    assert lido.preco_inicial == Decimal('100.00')
    assert lido.incremento_minimo == Decimal('5.00')
    assert lido.status is StatusLeilao.AGENDADO
    assert lido.vencedor_id is None
    assert lido.valor_arremate is None
    assert [lance.id for lance in lido.lances] == [
        lance_cedo.id,
        lance_tarde.id,
    ]
    assert isinstance(lido.lances[0], Lance)
    assert lido.lances[0].valor == Decimal('10.00')
    assert lido.lances[0].comprador_id == lance_cedo.comprador_id
    assert leiloes.buscar_por_id(uuid4()) is None


def test_leilao_repository_lista_por_status(session):
    categorias = SQLAlchemyCategoriaRepository(session)
    anuncios = SQLAlchemyAnuncioRepository(session)
    leiloes = SQLAlchemyLeilaoRepository(session)
    categoria = Categoria(nome='Eletronicos')
    categorias.salvar(categoria)
    anuncio = _anuncio(categoria)
    anuncios.salvar(anuncio)
    aberto = _leilao(anuncio, status=StatusLeilao.ABERTO)
    agendado = _leilao(anuncio)
    leiloes.salvar(aberto)
    leiloes.salvar(agendado)

    listados = leiloes.listar_por_status(StatusLeilao.ABERTO)

    assert [leilao.id for leilao in listados] == [aberto.id]
    assert isinstance(listados[0], Leilao)
    assert listados[0].status is StatusLeilao.ABERTO


def test_leilao_repository_buscar_com_lock_retorna_entidade(session, engine):
    categorias = SQLAlchemyCategoriaRepository(session)
    anuncios = SQLAlchemyAnuncioRepository(session)
    leiloes = SQLAlchemyLeilaoRepository(session)
    categoria = Categoria(nome='Eletronicos')
    categorias.salvar(categoria)
    anuncio = _anuncio(categoria)
    anuncios.salvar(anuncio)
    leilao = _leilao(anuncio)
    leiloes.salvar(leilao)
    sql: list[str] = []

    def _capturar(
        _conn,
        _cursor,
        statement,
        _parameters,
        _context,
        _executemany,
    ):
        sql.append(statement)

    event.listen(engine, 'before_cursor_execute', _capturar)
    try:
        bloqueado = leiloes.buscar_com_lock(leilao.id)
    finally:
        event.remove(engine, 'before_cursor_execute', _capturar)

    assert isinstance(bloqueado, Leilao)
    assert bloqueado.id == leilao.id
    if engine.dialect.name == 'postgresql':
        assert any('FOR UPDATE' in trecho.upper() for trecho in sql)

    vencedor_id = uuid4()
    bloqueado.status = StatusLeilao.ENCERRADO
    bloqueado.vencedor_id = vencedor_id
    bloqueado.valor_arremate = Decimal('30.00')
    leiloes.salvar(bloqueado)
    session.expire_all()
    relido = leiloes.buscar_por_id(leilao.id)

    assert relido.status is StatusLeilao.ENCERRADO
    assert relido.vencedor_id == vencedor_id
    assert relido.valor_arremate == Decimal('30.00')
    assert leiloes.buscar_com_lock(uuid4()) is None

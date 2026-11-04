"""
tests/integration/test_catalogo_models.py

Persistencia dos models de catalogo em SQLite em memoria.
Nao importa infra.db.session: esse modulo exige DATABASE_URL.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, delete, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

import infra.db.models  # noqa: F401
from domain.anuncio import StatusAnuncio, TipoAnuncio
from domain.leilao import StatusLeilao
from infra.db.base import Base
from infra.db.models.anuncio import AnuncioModel
from infra.db.models.categoria import CategoriaModel
from infra.db.models.lance import LanceModel
from infra.db.models.leilao import LeilaoModel

_FK_LEILAO_ATUAL = 'fk_anuncios_leilao_atual_id'


def _fk_circular():
    tabela = AnuncioModel.__table__
    for constraint in tabela.constraints:
        if getattr(constraint, 'name', None) == _FK_LEILAO_ATUAL:
            return constraint
    return None


def _destacar_fk_circular():
    fk = _fk_circular()
    if fk is None:
        return None
    AnuncioModel.__table__.constraints.remove(fk)
    for elemento in fk.elements:
        elemento.parent.foreign_keys.discard(elemento)
    return fk


def _criar_schema(engine) -> None:
    try:
        Base.metadata.create_all(engine)
    except Exception:
        Base.metadata.drop_all(engine)
        fk = _destacar_fk_circular()
        try:
            Base.metadata.create_all(engine)
            if fk is not None and engine.dialect.name == 'postgresql':
                fk.create(bind=engine)
        finally:
            if fk is not None:
                AnuncioModel.__table__.append_constraint(fk)


def _tem_fk_circular(engine) -> bool:
    chaves = inspect(engine).get_foreign_keys('anuncios')
    return any(chave['name'] == _FK_LEILAO_ATUAL for chave in chaves)


@pytest.fixture(scope='module')
def engine():
    motor = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
    )

    @event.listens_for(motor, 'connect')
    def _ativar_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()

    _criar_schema(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def session(engine):
    conexao = engine.connect()
    transacao = conexao.begin()
    fabrica = sessionmaker(
        bind=conexao,
        expire_on_commit=False,
        autoflush=False,
    )
    sessao = fabrica()
    sessao.begin_nested()

    @event.listens_for(sessao, 'after_transaction_end')
    def _reabrir_savepoint(sessao_atual, transacao_interna):
        if conexao.closed or not transacao_interna.nested:
            return
        pai = transacao_interna.parent
        if pai is not None and not pai.nested:
            sessao_atual.begin_nested()

    yield sessao
    sessao.close()
    if transacao.is_active:
        transacao.rollback()
    conexao.close()


def _categoria(session, nome='Eletronicos') -> CategoriaModel:
    categoria = CategoriaModel(nome=nome)
    session.add(categoria)
    session.flush()
    return categoria


def _anuncio(session, categoria, **overrides) -> AnuncioModel:
    dados = dict(
        titulo='Notebook',
        descricao='Usado, funcionando',
        preco_referencia=Decimal('1500.00'),
        categoria_id=categoria.id,
        vendedor_id=uuid4(),
    )
    dados.update(overrides)
    anuncio = AnuncioModel(**dados)
    session.add(anuncio)
    session.flush()
    return anuncio


def _leilao(session, anuncio, **overrides) -> LeilaoModel:
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
    leilao = LeilaoModel(**dados)
    session.add(leilao)
    session.flush()
    return leilao


def _lance(session, leilao, valor, criado_em) -> LanceModel:
    lance = LanceModel(
        leilao_id=leilao.id,
        comprador_id=uuid4(),
        valor=valor,
        criado_em=criado_em,
    )
    session.add(lance)
    session.flush()
    return lance


def test_reler_catalogo_persiste_tipos(session):
    categoria = _categoria(session)
    anuncio = _anuncio(
        session,
        categoria,
        tipo=TipoAnuncio.LEILAO,
        status=StatusAnuncio.INATIVO,
    )
    leilao = _leilao(
        session,
        anuncio,
        status=StatusLeilao.ENCERRADO,
        vencedor_id=uuid4(),
        valor_arremate=Decimal('250.50'),
    )
    lance = _lance(
        session,
        leilao,
        Decimal('250.50'),
        datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc),
    )
    session.commit()
    session.expire_all()

    anuncio_lido = session.get(AnuncioModel, anuncio.id)
    leilao_lido = session.get(LeilaoModel, leilao.id)
    lance_lido = session.get(LanceModel, lance.id)

    assert isinstance(anuncio_lido.id, UUID)
    assert anuncio_lido.preco_referencia == Decimal('1500.00')
    assert anuncio_lido.tipo is TipoAnuncio.LEILAO
    assert anuncio_lido.status is StatusAnuncio.INATIVO
    assert isinstance(anuncio_lido.criado_em, datetime)

    assert leilao_lido.status is StatusLeilao.ENCERRADO
    assert leilao_lido.vencedor_id == leilao.vencedor_id
    assert leilao_lido.valor_arremate == Decimal('250.50')
    assert leilao_lido.incremento_minimo == Decimal('5.00')
    assert isinstance(leilao_lido.criado_em, datetime)

    assert lance_lido.valor == Decimal('250.50')
    assert lance_lido.leilao.id == leilao.id
    assert isinstance(lance_lido.criado_em, datetime)


def test_defaults_preenchem_id_status_e_criado_em(session):
    categoria = CategoriaModel(nome='Moveis')
    session.add(categoria)
    session.flush()

    anuncio = AnuncioModel(
        titulo='Cadeira',
        descricao='Madeira',
        preco_referencia=Decimal('80.00'),
        categoria_id=categoria.id,
        vendedor_id=uuid4(),
    )
    session.add(anuncio)
    session.flush()

    inicio = datetime(2026, 11, 3, 15, 0, tzinfo=timezone.utc)
    leilao = LeilaoModel(
        anuncio_id=anuncio.id,
        vendedor_id=anuncio.vendedor_id,
        preco_inicial=Decimal('80.00'),
        incremento_minimo=Decimal('1.00'),
        data_inicio=inicio,
        data_final=inicio + timedelta(hours=1),
    )
    session.add(leilao)
    session.flush()

    assert categoria.ativa is True
    assert isinstance(categoria.id, UUID)
    assert isinstance(categoria.criado_em, datetime)
    assert anuncio.tipo is TipoAnuncio.VENDA_DIRETA
    assert anuncio.status is StatusAnuncio.ATIVO
    assert isinstance(anuncio.id, UUID)
    assert isinstance(anuncio.criado_em, datetime)
    assert leilao.status is StatusLeilao.AGENDADO
    assert isinstance(leilao.id, UUID)
    assert isinstance(leilao.criado_em, datetime)


def test_lances_ordenados_por_criado_em(session):
    categoria = _categoria(session)
    anuncio = _anuncio(session, categoria)
    leilao = _leilao(session, anuncio)
    mais_tarde = datetime(2026, 11, 3, 14, 0, tzinfo=timezone.utc)
    mais_cedo = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc)
    lance_tarde = _lance(session, leilao, Decimal('20.00'), mais_tarde)
    lance_cedo = _lance(session, leilao, Decimal('10.00'), mais_cedo)
    session.commit()
    session.expire(leilao, ['lances'])

    assert [lance.id for lance in leilao.lances] == [
        lance_cedo.id,
        lance_tarde.id,
    ]


def test_apagar_leilao_apaga_lances(session):
    categoria = _categoria(session)
    anuncio = _anuncio(session, categoria)
    leilao = _leilao(session, anuncio)
    inicio = datetime(2026, 11, 3, 13, 0, tzinfo=timezone.utc)
    primeiro = _lance(session, leilao, Decimal('10.00'), inicio)
    segundo = _lance(
        session,
        leilao,
        Decimal('20.00'),
        inicio + timedelta(minutes=5),
    )
    session.expire(leilao, ['lances'])
    leilao.lances.remove(primeiro)
    session.flush()
    assert session.get(LanceModel, primeiro.id) is None

    leilao_id = leilao.id
    segundo_id = segundo.id
    session.execute(delete(LeilaoModel).where(LeilaoModel.id == leilao_id))
    session.flush()
    session.expunge_all()
    assert session.get(LanceModel, segundo_id) is None
    assert session.get(LeilaoModel, leilao_id) is None


def test_apagar_anuncio_apaga_leiloes(session):
    categoria = _categoria(session)
    anuncio = _anuncio(session, categoria)
    leilao = _leilao(session, anuncio)

    anuncio_id = anuncio.id
    leilao_id = leilao.id
    session.execute(delete(AnuncioModel).where(AnuncioModel.id == anuncio_id))
    session.flush()
    session.expunge_all()
    assert session.get(LeilaoModel, leilao_id) is None
    assert session.get(AnuncioModel, anuncio_id) is None


def test_apagar_categoria_com_anuncio_falha(session):
    categoria = _categoria(session)
    _anuncio(session, categoria)

    comando = delete(CategoriaModel).where(CategoriaModel.id == categoria.id)
    with pytest.raises(IntegrityError):
        session.execute(comando)
    session.rollback()


def test_apagar_leilao_atual_zera_referencia(session, engine):
    if not _tem_fk_circular(engine):
        pytest.skip('FK circular nao existe neste dialeto')

    categoria = _categoria(session)
    anuncio = _anuncio(session, categoria)
    leilao = _leilao(session, anuncio)
    anuncio.leilao_atual_id = leilao.id
    session.flush()

    session.execute(delete(LeilaoModel).where(LeilaoModel.id == leilao.id))
    session.flush()
    session.expire_all()
    anuncio_lido = session.get(AnuncioModel, anuncio.id)
    assert anuncio_lido is not None
    assert anuncio_lido.leilao_atual_id is None

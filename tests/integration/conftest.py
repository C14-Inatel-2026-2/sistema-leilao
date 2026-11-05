"""
tests/integration/conftest.py

SQLite em memoria para os testes de catalogo que ainda nao existem
em producao. Nao importa infra.db.session: esse modulo exige
DATABASE_URL.

test_catalogo_models.py mantem a propria copia destas fixtures.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import infra.db.models  # noqa: F401
from infra.db.base import Base
from infra.db.models.anuncio import AnuncioModel

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

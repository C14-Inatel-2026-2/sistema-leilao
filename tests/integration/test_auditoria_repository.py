from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from adapters.repositories.auditoria_repository import (
    SQLAlchemyAuditoriaRepository,
)

AGORA = datetime(2026, 11, 13, 15, 0, tzinfo=timezone.utc)


def test_salvar_lance_persiste_registro_de_auditoria(session):
    repo = SQLAlchemyAuditoriaRepository(session)
    leilao_id = uuid4()
    lance_id = uuid4()
    usuario_id = uuid4()
    valor = Decimal('250.00')

    repo.salvar_lance(
        leilao_id=leilao_id,
        lance_id=lance_id,
        usuario_id=usuario_id,
        valor=valor,
        data_hora=AGORA,
    )
    session.expire_all()

    registros = repo.listar_por_leilao(leilao_id)
    assert len(registros) == 1
    reg = registros[0]
    assert reg.leilao_id == leilao_id
    assert reg.tipo_evento == 'LANCE_REALIZADO'
    assert reg.lance_id == lance_id
    assert reg.usuario_id == usuario_id
    assert reg.valor == valor
    assert reg.data_evento.tzinfo is not None
    assert reg.motivo is None


def test_salvar_encerramento_com_vencedor(session):
    repo = SQLAlchemyAuditoriaRepository(session)
    leilao_id = uuid4()
    vencedor_id = uuid4()
    valor_final = Decimal('400.00')

    repo.salvar_encerramento(
        leilao_id=leilao_id,
        vencedor_id=vencedor_id,
        valor_final=valor_final,
        data_encerramento=AGORA,
        motivo='tempo_esgotado',
    )
    session.expire_all()

    registros = repo.listar_por_leilao(leilao_id)
    assert len(registros) == 1
    reg = registros[0]
    assert reg.leilao_id == leilao_id
    assert reg.tipo_evento == 'LEILAO_ENCERRADO'
    assert reg.lance_id is None
    assert reg.usuario_id == vencedor_id
    assert reg.valor == valor_final
    assert reg.motivo == 'tempo_esgotado'


def test_salvar_encerramento_sem_vencedor(session):
    repo = SQLAlchemyAuditoriaRepository(session)
    leilao_id = uuid4()

    repo.salvar_encerramento(
        leilao_id=leilao_id,
        vencedor_id=None,
        valor_final=None,
        data_encerramento=AGORA,
        motivo=None,
    )
    session.expire_all()

    registros = repo.listar_por_leilao(leilao_id)
    assert len(registros) == 1
    reg = registros[0]
    assert reg.leilao_id == leilao_id
    assert reg.tipo_evento == 'LEILAO_ENCERRADO'
    assert reg.usuario_id is None
    assert reg.valor is None
    assert reg.motivo is None


def test_listar_por_leilao_ordena_cronologicamente(session):
    repo = SQLAlchemyAuditoriaRepository(session)
    leilao_id = uuid4()

    repo.salvar_lance(
        leilao_id=leilao_id,
        lance_id=uuid4(),
        usuario_id=uuid4(),
        valor=Decimal('100.00'),
        data_hora=AGORA,
    )
    repo.salvar_lance(
        leilao_id=leilao_id,
        lance_id=uuid4(),
        usuario_id=uuid4(),
        valor=Decimal('120.00'),
        data_hora=AGORA + timedelta(minutes=5),
    )
    repo.salvar_encerramento(
        leilao_id=leilao_id,
        vencedor_id=uuid4(),
        valor_final=Decimal('120.00'),
        data_encerramento=AGORA + timedelta(minutes=10),
    )

    tipos_esperados = [
        'LANCE_REALIZADO',
        'LANCE_REALIZADO',
        'LEILAO_ENCERRADO',
    ]
    registros = repo.listar_por_leilao(leilao_id)
    assert len(registros) == len(tipos_esperados)
    assert [r.tipo_evento for r in registros] == tipos_esperados
    assert [r.valor for r in registros] == [
        Decimal('100.00'),
        Decimal('120.00'),
        Decimal('120.00'),
    ]

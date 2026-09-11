from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.exceptions import DomainError, LanceInvalidoError
from domain.lance import Lance


def novo_lance(**sobrescrever) -> Lance:
    dados = dict(leilao_id=uuid4(), comprador_id=uuid4(), valor=Decimal("550"))
    dados.update(sobrescrever)
    return Lance(**dados)


def test_lance_valido_recebe_id_e_momento_em_utc():
    lance = novo_lance()

    assert lance.id is not None
    assert lance.criado_em.tzinfo is not None
    assert lance.valor == Decimal("550")


def test_lance_aceita_comprador_com_id_inteiro():
    assert novo_lance(comprador_id=42).comprador_id == 42


@pytest.mark.parametrize("valor", [Decimal("0"), Decimal("-10"), Decimal("-0.01")])
def test_lance_rejeita_valor_zero_ou_negativo(valor):
    with pytest.raises(LanceInvalidoError, match="maior que 0"):
        novo_lance(valor=valor)


@pytest.mark.parametrize("valor", [550.0, 550, "550"])
def test_lance_rejeita_valor_que_nao_e_decimal(valor):
    with pytest.raises(LanceInvalidoError, match="Decimal"):
        novo_lance(valor=valor)


@pytest.mark.parametrize("valor", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_lance_rejeita_valor_nao_finito(valor):
    with pytest.raises(LanceInvalidoError, match="finito"):
        novo_lance(valor=valor)


def test_lance_rejeita_comprador_ausente():
    with pytest.raises(LanceInvalidoError, match="comprador"):
        novo_lance(comprador_id=None)


def test_lance_rejeita_momento_sem_fuso_horario():
    with pytest.raises(LanceInvalidoError, match="fuso horario"):
        novo_lance(criado_em=datetime(2026, 9, 1, 12, 0))


def test_lance_aceita_momento_informado_com_fuso_horario():
    momento = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    assert novo_lance(criado_em=momento).criado_em == momento


def test_lance_e_imutavel_depois_de_criado():
    lance = novo_lance()

    with pytest.raises(FrozenInstanceError):
        lance.valor = Decimal("1000000")


def test_lance_invalido_e_erro_de_dominio():
    # A camada Flask vai mapear DomainError -> 4xx; ValueError fica por compatibilidade.
    with pytest.raises(DomainError):
        novo_lance(valor=Decimal("0"))
    with pytest.raises(ValueError):
        novo_lance(valor=Decimal("0"))

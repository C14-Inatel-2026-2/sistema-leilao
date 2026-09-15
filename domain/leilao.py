from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

# A entidade Lance e a excecao de lance agora vivem em domain/lance.py.
from domain.lance import Lance, LanceInvalidoError

class StatusLeilao (str, Enum):
    AGENDADO = "AGENDADO"
    ABERTO = "ABERTO"
    ENCERRADO = "ENCERRADO"
    PAGO = "PAGO"
    CANCELADO = "CANCELADO"

class LeilaoInvalidoError(ValueError):
    """Dados de criacao do leilao invalidos (preco negativo, datas incorretas, etc.)."""
    pass

class EstadoLeilaoInvalidoError(ValueError):
    """Tentativa de transicao de estado proibida (ex: lance em leilao cancelado)."""
    pass

@dataclass
class Leilao:
    anuncio_id: UUID
    vendedor_id: UUID
    preco_inicial: Decimal
    incremento_minimo: Decimal
    data_inicio: datetime
    data_final: datetime
    id: UUID = field(default_factory=uuid4)
    status: StatusLeilao = StatusLeilao.AGENDADO
    lances: list[Lance] = field(default_factory=list)
    vencedor_id: UUID | int | None = None
    valor_arremate: Decimal | None = None
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validações estruturais"""
        self._validar_campos_basicos()

    def _validar_campos_basicos(self) -> None:
        if self.preco_inicial <= (Decimal("0")):
            raise LeilaoInvalidoError("o preco deve ser maior que 0")
        if self.incremento_minimo <= (Decimal("0")):
            raise LeilaoInvalidoError("o incremento deve ser maior que 0")
        if self.data_final <= self.data_inicio:
            raise LeilaoInvalidoError("o data final deve ser maior que a data de inicio")

    def esta_aberto(self) -> bool:
        return self.status == StatusLeilao.ABERTO

    def esta_agendado(self) -> bool:
        return self.status == StatusLeilao.AGENDADO

    def maior_lance(self) -> Lance | None:
        if not self.lances:
            return None
        return max(self.lances, key=lambda x: x.valor)

    def valor_minimo_proximo_lance(self) -> Decimal:
        if self.maior_lance() is None:
            return self.preco_inicial
        return self.maior_lance().valor + self.incremento_minimo

    def abrir(self, momento: datetime | None = None) -> None:
        momento = momento or datetime.now(timezone.utc)
        if self.status != StatusLeilao.AGENDADO:
            raise EstadoLeilaoInvalidoError("nao e possível abrir o leilao no status atual, apenas possivel no status agendado")
        if momento < self.data_inicio or momento >= self.data_final:
            raise EstadoLeilaoInvalidoError("nao e possivel abrir o leilão fora da janela de tempo")
        self.status = StatusLeilao.ABERTO

    def validar_lance(self,comprador_id: UUID | int,valor: Decimal,momento: datetime | None = None) -> None:
        momento = momento or datetime.now(timezone.utc)
        if self.status != StatusLeilao.ABERTO:
            raise EstadoLeilaoInvalidoError("leilao nao esta aberto para lances, apenas possível no status aberto")
        # Janela [inicio, fim): no instante data_final o leilao ja pode ser encerrado
        # (ver abrir/encerrar), entao ele nao aceita mais lance - senao lance e
        # encerramento disputam o mesmo instante.
        if momento < self.data_inicio or momento >= self.data_final:
            raise LanceInvalidoError("nao e possivel fazer lances nesse periodo de tempo")
        Lance.validar_valor(valor)
        if comprador_id == self.vendedor_id:
            raise LanceInvalidoError("o vendedor nao pode dar lances em seu proprio leilao.")
        minimo_exigido = self.valor_minimo_proximo_lance()
        if valor < minimo_exigido:
            raise LanceInvalidoError("o valor inserido e menor que o minmo exigido, verifique o valor")

    def receber_lance(self, comprador_id: UUID | int, valor: Decimal, momento: datetime | None = None) -> Lance:
        momento = momento or datetime.now(timezone.utc)
        self.validar_lance(comprador_id=comprador_id, valor=valor, momento=momento)
        novo_lance = Lance(
            comprador_id=comprador_id,
            valor=valor,
            leilao_id=self.id,
            criado_em=momento,
        )
        self.lances.append(novo_lance)
        return novo_lance

    def encerrar(self, momento: datetime | None = None) -> None:
        momento = momento or datetime.now(timezone.utc)
        if self.status != StatusLeilao.ABERTO:
            raise EstadoLeilaoInvalidoError("Apenas leiloes abertos podem ser encerrados.")
        if momento < self.data_final:
            raise EstadoLeilaoInvalidoError("O leilao nao pode ser encerrado antes da data final.")
        maior = self.maior_lance()
        if maior is not None:
            self.status = StatusLeilao.ENCERRADO
            self.vencedor_id = maior.comprador_id
            self.valor_arremate = maior.valor
        else:
            self.status = StatusLeilao.CANCELADO

    def cancelar(self, motivo: str | None = None) -> None:
        if self.status not in (StatusLeilao.AGENDADO, StatusLeilao.ABERTO):
            raise EstadoLeilaoInvalidoError("nao e possivel cancelar o leilao no status atual do leilao, verifique se esta agendado ou aberto.")
        self.status = StatusLeilao.CANCELADO

    def marcar_como_pago(self) -> None:
        if self.status != StatusLeilao.ENCERRADO:
            raise EstadoLeilaoInvalidoError("apenas leiloes encerrados podem ser marcados como pago")
        self.status = StatusLeilao.PAGO
from __future__ import annotations

from domain.events import LeilaoEncerrado
from use_cases.interfaces import AuditoriaRepository


def handle_leilao_encerrado(
    event: LeilaoEncerrado, repo: AuditoriaRepository
) -> None:
    """Handler que recebe o evento LeilaoEncerrado e delega a gravação ao repositório de auditoria."""
    repo.salvar_encerramento(
        leilao_id=event.leilao_id,
        vencedor_id=event.vencedor_id,
        valor_final=event.valor_final,
        data_encerramento=event.data_encerramento,
        motivo=event.motivo,
    )

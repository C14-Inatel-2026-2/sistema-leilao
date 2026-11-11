from __future__ import annotations

from domain.events import LanceRealizado
from use_cases.interfaces import AuditoriaRepository


def handle_lance_realizado(
    event: LanceRealizado, repo: AuditoriaRepository
) -> None:
    """Recebe LanceRealizado e delega a gravação à auditoria."""
    repo.salvar_lance(
        leilao_id=event.leilao_id,
        lance_id=event.lance_id,
        usuario_id=event.usuario_id,
        valor=event.valor,
        data_hora=event.data_hora,
    )

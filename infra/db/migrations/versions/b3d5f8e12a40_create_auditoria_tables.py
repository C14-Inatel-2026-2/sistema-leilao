"""create auditoria tables

Revision ID: b3d5f8e12a40
Revises: a1c4e7d29b30
Create Date: 2026-11-13 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3d5f8e12a40'
down_revision: Union[str, Sequence[str], None] = 'a1c4e7d29b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('auditoria_leiloes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('leilao_id', sa.Uuid(), nullable=False),
    sa.Column('tipo_evento', sa.String(length=30), nullable=False),
    sa.Column('lance_id', sa.Uuid(), nullable=True),
    sa.Column('usuario_id', sa.Uuid(), nullable=True),
    sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('data_evento', sa.DateTime(timezone=True), nullable=False),
    sa.Column('motivo', sa.String(length=255), nullable=True),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auditoria_leiloes_leilao_id'), 'auditoria_leiloes', ['leilao_id'], unique=False)
    op.create_index(op.f('ix_auditoria_leiloes_tipo_evento'), 'auditoria_leiloes', ['tipo_evento'], unique=False)
    op.create_index(op.f('ix_auditoria_leiloes_usuario_id'), 'auditoria_leiloes', ['usuario_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_auditoria_leiloes_usuario_id'), table_name='auditoria_leiloes')
    op.drop_index(op.f('ix_auditoria_leiloes_tipo_evento'), table_name='auditoria_leiloes')
    op.drop_index(op.f('ix_auditoria_leiloes_leilao_id'), table_name='auditoria_leiloes')
    op.drop_table('auditoria_leiloes')


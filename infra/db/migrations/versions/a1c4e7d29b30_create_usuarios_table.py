"""create usuarios table

Revision ID: a1c4e7d29b30
Revises: fe5b97ac3441
Create Date: 2026-11-06 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c4e7d29b30'
down_revision: Union[str, Sequence[str], None] = 'fe5b97ac3441'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('usuarios',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('senha_hash', sa.String(length=255), nullable=False),
    sa.Column('papel', sa.Enum('COMPRADOR', 'VENDEDOR', name='papelusuario', native_enum=False, length=20), nullable=False),
    sa.Column('ativo', sa.Boolean(), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_table('usuarios')

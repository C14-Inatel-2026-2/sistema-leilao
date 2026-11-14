"""create vendas table

Revision ID: c4e8a1b27d50
Revises: b3d5f8e12a40
Create Date: 2026-11-14 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4e8a1b27d50'
down_revision: Union[str, Sequence[str], None] = 'b3d5f8e12a40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vendas',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('anuncio_id', sa.Uuid(), nullable=False),
        sa.Column('comprador_id', sa.Uuid(), nullable=False),
        sa.Column('leilao_id', sa.Uuid(), nullable=False),
        sa.Column('valor', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            'metodo',
            sa.Enum(
                'PIX',
                'CARTAO',
                'BOLETO',
                name='metodopagamento',
                native_enum=False,
                length=20,
            ),
            nullable=True,
        ),
        sa.Column(
            'status',
            sa.Enum(
                'PENDENTE',
                'APROVADO',
                'CANCELADO',
                name='statuspagamento',
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column('criado_em', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['anuncio_id'], ['anuncios.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['leilao_id'], ['leiloes.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('leilao_id'),
    )
    op.create_index(
        op.f('ix_vendas_anuncio_id'), 'vendas', ['anuncio_id'], unique=False
    )
    op.create_index(
        op.f('ix_vendas_comprador_id'),
        'vendas',
        ['comprador_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_vendas_comprador_id'), table_name='vendas')
    op.drop_index(op.f('ix_vendas_anuncio_id'), table_name='vendas')
    op.drop_table('vendas')

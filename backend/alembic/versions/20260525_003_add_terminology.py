"""add_terminology

Revision ID: 20260525_003
Revises: 20260525_002
Create Date: 2026-05-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260525_003'
down_revision: Union[str, None] = '20260525_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create terminologies table
    op.create_table(
        'terminologies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Terminology entry name'),
        sa.Column('source_text', sa.Text(), nullable=False, comment='Original/source text'),
        sa.Column('translated_text', sa.Text(), nullable=False, comment='Translated text'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language code'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language code'),
        sa.Column('domain', sa.Enum('HOTEL', 'ROOM', 'AMENITY', 'GENERAL', name='terminologycategory'), nullable=False, comment='Domain category'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Additional notes'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether term is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminologies_name'), 'terminologies', ['name'], unique=False)
    op.create_index(op.f('ix_terminologies_source_lang'), 'terminologies', ['source_lang'], unique=False)
    op.create_index(op.f('ix_terminologies_target_lang'), 'terminologies', ['target_lang'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_terminologies_target_lang'), table_name='terminologies')
    op.drop_index(op.f('ix_terminologies_source_lang'), table_name='terminologies')
    op.drop_index(op.f('ix_terminologies_name'), table_name='terminologies')
    op.drop_table('terminologies')
    op.execute('DROP TYPE IF EXISTS terminologycategory')
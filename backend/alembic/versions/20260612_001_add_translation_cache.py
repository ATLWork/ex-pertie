"""add_translation_cache

Revision ID: 20260612_001
Revises: 20260525_003
Create Date: 2026-06-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260612_001'
down_revision: Union[str, None] = '20260525_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create translation_cache table
    op.create_table(
        'translation_cache',
        sa.Column('cache_key', sa.String(length=128), nullable=False, comment='Unique cache key'),
        sa.Column('text', sa.Text(), nullable=False, comment='Original source text'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language'),
        sa.Column('translated_text', sa.Text(), nullable=False, comment='Cached translation'),
        sa.Column('source', sa.String(length=20), nullable=False, comment='Translation source'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Confidence score'),
        sa.Column('metadata_json', sa.Text(), nullable=True, comment='JSON metadata'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('ttl_expires_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('cache_key'),
    )
    op.create_index('ix_translation_cache_ttl_expires_at', 'translation_cache', ['ttl_expires_at'])
    op.create_index('ix_translation_cache_lang_pair', 'translation_cache', ['source_lang', 'target_lang'])


def downgrade() -> None:
    op.drop_index('ix_translation_cache_lang_pair', table_name='translation_cache')
    op.drop_index('ix_translation_cache_ttl_expires_at', table_name='translation_cache')
    op.drop_table('translation_cache')

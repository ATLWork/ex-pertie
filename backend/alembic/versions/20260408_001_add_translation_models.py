"""add_translation_models

Revision ID: 20260408_001
Revises:
Create Date: 2026-04-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260408_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create translation_rules table
    op.create_table(
        'translation_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='Rule name'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language code (e.g., zh-CN)'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language code (e.g., en-US)'),
        sa.Column('field_name', sa.String(length=100), nullable=False, comment='Field name to apply rule'),
        sa.Column('rule_type', sa.Enum('DIRECT', 'GLOSSARY', 'AI', name='ruletype'), nullable=False, comment='Rule type'),
        sa.Column('rule_value', sa.Text(), nullable=False, comment='Rule value/mapping JSON'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether rule is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translation_rules_field_name'), 'translation_rules', ['field_name'], unique=False)
    op.create_index(op.f('ix_translation_rules_source_lang'), 'translation_rules', ['source_lang'], unique=False)
    op.create_index(op.f('ix_translation_rules_target_lang'), 'translation_rules', ['target_lang'], unique=False)

    # Create translation_references table
    op.create_table(
        'translation_references',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False, comment='Original text'),
        sa.Column('translated_text', sa.Text(), nullable=False, comment='Translated text'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language code'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language code'),
        sa.Column('context', sa.Text(), nullable=True, comment='Context information'),
        sa.Column('confidence', sa.Float(), nullable=False, comment='Confidence score (0-1)'),
        sa.Column('source', sa.Enum('MANUAL', 'IMPORTED', 'AI', name='referencesource'), nullable=False, comment='Reference source'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translation_references_source_lang'), 'translation_references', ['source_lang'], unique=False)
    op.create_index(op.f('ix_translation_references_target_lang'), 'translation_references', ['target_lang'], unique=False)

    # Create glossaries table
    op.create_table(
        'glossaries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('term', sa.String(length=255), nullable=False, comment='Term in source language'),
        sa.Column('translation', sa.String(length=255), nullable=False, comment='Standard translation'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language code'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language code'),
        sa.Column('category', sa.Enum('HOTEL', 'ROOM', 'AMENITY', 'GENERAL', name='glossarycategory'), nullable=False, comment='Term category'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Additional notes'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether term is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_glossaries_source_lang'), 'glossaries', ['source_lang'], unique=False)
    op.create_index(op.f('ix_glossaries_target_lang'), 'glossaries', ['target_lang'], unique=False)
    op.create_index(op.f('ix_glossaries_term'), 'glossaries', ['term'], unique=False)

    # Create translation_histories table
    op.create_table(
        'translation_histories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False, comment='Original text'),
        sa.Column('translated_text', sa.Text(), nullable=False, comment='Translated text'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language code'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language code'),
        sa.Column('translation_type', sa.Enum('MACHINE', 'AI', 'HYBRID', name='translationtype'), nullable=False, comment='Translation type'),
        sa.Column('reference_used', sa.Boolean(), nullable=False, comment='Whether reference library was used'),
        sa.Column('glossary_used', sa.Boolean(), nullable=False, comment='Whether glossary was used'),
        sa.Column('confidence_score', sa.Float(), nullable=True, comment='Confidence score (0-1)'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_translation_histories_created_at'), 'translation_histories', ['created_at'], unique=False)
    op.create_index(op.f('ix_translation_histories_source_lang'), 'translation_histories', ['source_lang'], unique=False)
    op.create_index(op.f('ix_translation_histories_target_lang'), 'translation_histories', ['target_lang'], unique=False)


def downgrade() -> None:
    # Drop translation_histories table
    op.drop_index(op.f('ix_translation_histories_target_lang'), table_name='translation_histories')
    op.drop_index(op.f('ix_translation_histories_source_lang'), table_name='translation_histories')
    op.drop_index(op.f('ix_translation_histories_created_at'), table_name='translation_histories')
    op.drop_table('translation_histories')
    op.execute('DROP TYPE IF EXISTS translationtype')

    # Drop glossaries table
    op.drop_index(op.f('ix_glossaries_term'), table_name='glossaries')
    op.drop_index(op.f('ix_glossaries_target_lang'), table_name='glossaries')
    op.drop_index(op.f('ix_glossaries_source_lang'), table_name='glossaries')
    op.drop_table('glossaries')
    op.execute('DROP TYPE IF EXISTS glossarycategory')

    # Drop translation_references table
    op.drop_index(op.f('ix_translation_references_target_lang'), table_name='translation_references')
    op.drop_index(op.f('ix_translation_references_source_lang'), table_name='translation_references')
    op.drop_table('translation_references')
    op.execute('DROP TYPE IF EXISTS referencesource')

    # Drop translation_rules table
    op.drop_index(op.f('ix_translation_rules_target_lang'), table_name='translation_rules')
    op.drop_index(op.f('ix_translation_rules_source_lang'), table_name='translation_rules')
    op.drop_index(op.f('ix_translation_rules_field_name'), table_name='translation_rules')
    op.drop_table('translation_rules')
    op.execute('DROP TYPE IF EXISTS ruletype')

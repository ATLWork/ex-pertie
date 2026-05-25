"""add_booking_reference

Revision ID: 20260525_002
Revises: 20260525_001
Create Date: 2026-05-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260525_002"
down_revision: Union[str, None] = "20260525_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create booking_references table
    op.create_table(
        'booking_references',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True, primary_key=True),
        sa.Column('source_text', sa.Text(), nullable=False, comment='Original text in source language'),
        sa.Column('ctrip_translation', sa.Text(), nullable=True, comment='Translation from Ctrip'),
        sa.Column('booking_translation', sa.Text(), nullable=True, comment='Translation from Booking.com'),
        sa.Column('source_lang', sa.String(length=10), nullable=False, comment='Source language code'),
        sa.Column('target_lang', sa.String(length=10), nullable=False, comment='Target language code'),
        sa.Column('hotel_name', sa.String(length=255), nullable=True, comment='Associated hotel name'),
        sa.Column('hotel_address', sa.Text(), nullable=True, comment='Associated hotel address'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='Number of times this reference was used'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether reference is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f('ix_booking_references_source_text'), 'booking_references', ['source_text'], unique=False)
    op.create_index(op.f('ix_booking_references_source_lang'), 'booking_references', ['source_lang'], unique=False)
    op.create_index(op.f('ix_booking_references_target_lang'), 'booking_references', ['target_lang'], unique=False)
    op.create_index(op.f('ix_booking_references_hotel_name'), 'booking_references', ['hotel_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_booking_references_hotel_name'), table_name='booking_references')
    op.drop_index(op.f('ix_booking_references_target_lang'), table_name='booking_references')
    op.drop_index(op.f('ix_booking_references_source_lang'), table_name='booking_references')
    op.drop_index(op.f('ix_booking_references_source_text'), table_name='booking_references')
    op.drop_table('booking_references')
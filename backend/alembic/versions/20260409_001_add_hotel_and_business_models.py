"""add_hotel_and_business_models

Revision ID: 20260409_001
Revises: 20260408_001
Create Date: 2026-04-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260409_001"
down_revision: Union[str, None] = "20260408_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE hotelbrand AS ENUM ('atour', 'atour_x', 'zhotel', 'ahaus')")
    op.execute("CREATE TYPE hotelstatus AS ENUM ('draft', 'pending_review', 'approved', 'published', 'suspended')")
    op.execute("CREATE TYPE importtype AS ENUM ('hotel', 'room', 'mixed')")
    op.execute("CREATE TYPE importstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'partial')")
    op.execute("CREATE TYPE exporttype AS ENUM ('hotel', 'room', 'mixed', 'expedia_template')")
    op.execute("CREATE TYPE exportformat AS ENUM ('excel', 'csv', 'json', 'xml')")
    op.execute("CREATE TYPE exportstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE templatetype AS ENUM ('hotel', 'room', 'rate', 'inventory')")
    op.execute("CREATE TYPE templatestatus AS ENUM ('draft', 'active', 'deprecated', 'archived')")
    op.execute("CREATE TYPE fieldmappingtype AS ENUM ('direct', 'transform', 'lookup', 'computed', 'fixed', 'null')")

    # Create hotels table
    op.create_table(
        'hotels',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name_cn', sa.String(length=255), nullable=False, comment='Hotel name in Chinese'),
        sa.Column('name_en', sa.String(length=255), nullable=True, comment='Hotel name in English'),
        sa.Column('brand', sa.Enum('atour', 'atour_x', 'zhotel', 'ahaus', name='hotelbrand'), nullable=False, comment='Hotel brand'),
        sa.Column('status', sa.Enum('draft', 'pending_review', 'approved', 'published', 'suspended', name='hotelstatus'), nullable=False, comment='Hotel status'),
        sa.Column('country_code', sa.String(length=10), nullable=False, server_default='CN', comment='Country code (ISO 3166-1)'),
        sa.Column('province', sa.String(length=100), nullable=False, comment='Province/State'),
        sa.Column('city', sa.String(length=100), nullable=False, comment='City'),
        sa.Column('district', sa.String(length=100), nullable=True, comment='District/County'),
        sa.Column('address_cn', sa.String(length=500), nullable=False, comment='Address in Chinese'),
        sa.Column('address_en', sa.String(length=500), nullable=True, comment='Address in English'),
        sa.Column('postal_code', sa.String(length=20), nullable=True, comment='Postal code'),
        sa.Column('phone', sa.String(length=50), nullable=True, comment='Phone number'),
        sa.Column('email', sa.String(length=255), nullable=True, comment='Email address'),
        sa.Column('website', sa.String(length=500), nullable=True, comment='Website URL'),
        sa.Column('latitude', sa.Float(), nullable=True, comment='Latitude'),
        sa.Column('longitude', sa.Float(), nullable=True, comment='Longitude'),
        sa.Column('expedia_hotel_id', sa.String(length=100), nullable=True, comment='Expedia Hotel ID'),
        sa.Column('expedia_chain_code', sa.String(length=50), nullable=True, comment='Expedia Chain Code'),
        sa.Column('expedia_property_code', sa.String(length=50), nullable=True, comment='Expedia Property Code'),
        sa.Column('opened_at', sa.DateTime(), nullable=True, comment='Hotel opening date'),
        sa.Column('renovated_at', sa.DateTime(), nullable=True, comment='Last renovation date'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hotels_city'), 'hotels', ['city'], unique=False)
    op.create_index(op.f('ix_hotels_expedia_hotel_id'), 'hotels', ['expedia_hotel_id'], unique=True)
    op.create_index(op.f('ix_hotels_status'), 'hotels', ['status'], unique=False)

    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('hotel_id', sa.String(length=36), nullable=False, comment='Hotel ID'),
        sa.Column('room_type_code', sa.String(length=100), nullable=False, comment='Room type code (internal)'),
        sa.Column('name_cn', sa.String(length=255), nullable=False, comment='Room name in Chinese'),
        sa.Column('name_en', sa.String(length=255), nullable=True, comment='Room name in English'),
        sa.Column('description_cn', sa.Text(), nullable=True, comment='Room description in Chinese'),
        sa.Column('description_en', sa.Text(), nullable=True, comment='Room description in English'),
        sa.Column('bed_type', sa.String(length=100), nullable=True, comment='Bed type'),
        sa.Column('max_occupancy', sa.Integer(), nullable=False, server_default='2', comment='Maximum occupancy'),
        sa.Column('standard_occupancy', sa.Integer(), nullable=False, server_default='2', comment='Standard occupancy'),
        sa.Column('room_size', sa.Float(), nullable=True, comment='Room size in square meters'),
        sa.Column('floor_range', sa.String(length=50), nullable=True, comment='Floor range'),
        sa.Column('total_rooms', sa.Integer(), nullable=False, server_default='1', comment='Total number of rooms'),
        sa.Column('expedia_room_id', sa.String(length=100), nullable=True, comment='Expedia Room ID'),
        sa.Column('expedia_room_type_code', sa.String(length=50), nullable=True, comment='Expedia Room Type Code'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether room type is active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rooms_expedia_room_id'), 'rooms', ['expedia_room_id'], unique=True)
    op.create_index(op.f('ix_rooms_hotel_id'), 'rooms', ['hotel_id'], unique=False)

    # Create room_extensions table
    op.create_table(
        'room_extensions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('room_id', sa.String(length=36), nullable=False, comment='Room ID'),
        sa.Column('amenities_cn', sa.Text(), nullable=True, comment='Room amenities in Chinese'),
        sa.Column('amenities_en', sa.Text(), nullable=True, comment='Room amenities in English'),
        sa.Column('amenity_details', sa.Text(), nullable=True, comment='Detailed amenities in JSON'),
        sa.Column('image_urls', sa.Text(), nullable=True, comment='Room image URLs in JSON'),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True, comment='Thumbnail image URL'),
        sa.Column('view_type', sa.String(length=100), nullable=True, comment='View type'),
        sa.Column('balcony', sa.Boolean(), nullable=True, server_default='false', comment='Has balcony'),
        sa.Column('smoking_policy', sa.String(length=50), nullable=True, comment='Smoking policy'),
        sa.Column('floor', sa.String(length=50), nullable=True, comment='Floor information'),
        sa.Column('bathroom_type', sa.String(length=100), nullable=True, comment='Bathroom type'),
        sa.Column('bathroom_amenities_cn', sa.Text(), nullable=True, comment='Bathroom amenities in Chinese'),
        sa.Column('bathroom_amenities_en', sa.Text(), nullable=True, comment='Bathroom amenities in English'),
        sa.Column('accessibility_features', sa.Text(), nullable=True, comment='Accessibility features'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id')
    )
    op.create_index(op.f('ix_room_extensions_room_id'), 'room_extensions', ['room_id'], unique=True)

    # Create import_histories table
    op.create_table(
        'import_histories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False, comment='Original file name'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='File storage path'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='File size in bytes'),
        sa.Column('file_hash', sa.String(length=64), nullable=True, comment='File MD5 hash'),
        sa.Column('import_type', sa.Enum('hotel', 'room', 'mixed', name='importtype'), nullable=False, comment='Import type'),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'partial', name='importstatus'), nullable=False, comment='Import status'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0', comment='Total rows'),
        sa.Column('success_rows', sa.Integer(), nullable=False, server_default='0', comment='Success rows'),
        sa.Column('failed_rows', sa.Integer(), nullable=False, server_default='0', comment='Failed rows'),
        sa.Column('skipped_rows', sa.Integer(), nullable=False, server_default='0', comment='Skipped rows'),
        sa.Column('error_log', sa.Text(), nullable=True, comment='Error log in JSON'),
        sa.Column('warning_log', sa.Text(), nullable=True, comment='Warning log in JSON'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='Processing start time'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='Processing completion time'),
        sa.Column('processing_time', sa.Float(), nullable=True, comment='Processing time in seconds'),
        sa.Column('operator_id', sa.String(length=36), nullable=True, comment='Operator user ID'),
        sa.Column('operator_name', sa.String(length=100), nullable=True, comment='Operator name'),
        sa.Column('operator_ip', sa.String(length=50), nullable=True, comment='Operator IP'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Additional notes'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_histories_operator_id'), 'import_histories', ['operator_id'], unique=False)

    # Create export_histories table
    op.create_table(
        'export_histories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False, comment='Generated file name'),
        sa.Column('file_path', sa.String(length=500), nullable=True, comment='File storage path'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='File size in bytes'),
        sa.Column('download_url', sa.String(length=500), nullable=True, comment='Download URL'),
        sa.Column('export_type', sa.Enum('hotel', 'room', 'mixed', 'expedia_template', name='exporttype'), nullable=False, comment='Export type'),
        sa.Column('export_format', sa.Enum('excel', 'csv', 'json', 'xml', name='exportformat'), nullable=False, comment='Export format'),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='exportstatus'), nullable=False, comment='Export status'),
        sa.Column('filter_criteria', sa.Text(), nullable=True, comment='Filter criteria'),
        sa.Column('hotel_ids', sa.Text(), nullable=True, comment='Selected hotel IDs'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0', comment='Total rows'),
        sa.Column('total_hotels', sa.Integer(), nullable=False, server_default='0', comment='Total hotels'),
        sa.Column('total_rooms', sa.Integer(), nullable=False, server_default='0', comment='Total rooms'),
        sa.Column('template_id', sa.String(length=36), nullable=True, comment='Template ID'),
        sa.Column('template_name', sa.String(length=255), nullable=True, comment='Template name'),
        sa.Column('template_version', sa.String(length=50), nullable=True, comment='Template version'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='Processing start time'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='Processing completion time'),
        sa.Column('processing_time', sa.Float(), nullable=True, comment='Processing time in seconds'),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0', comment='Download count'),
        sa.Column('last_downloaded_at', sa.DateTime(), nullable=True, comment='Last download time'),
        sa.Column('expires_at', sa.DateTime(), nullable=True, comment='Download link expiration'),
        sa.Column('operator_id', sa.String(length=36), nullable=True, comment='Operator user ID'),
        sa.Column('operator_name', sa.String(length=100), nullable=True, comment='Operator name'),
        sa.Column('operator_ip', sa.String(length=50), nullable=True, comment='Operator IP'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Additional notes'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_export_histories_operator_id'), 'export_histories', ['operator_id'], unique=False)

    # Create expedia_templates table
    op.create_table(
        'expedia_templates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Template name'),
        sa.Column('code', sa.String(length=100), nullable=False, comment='Template code'),
        sa.Column('description', sa.Text(), nullable=True, comment='Template description'),
        sa.Column('template_type', sa.Enum('hotel', 'room', 'rate', 'inventory', name='templatetype'), nullable=False, comment='Template type'),
        sa.Column('status', sa.Enum('draft', 'active', 'deprecated', 'archived', name='templatestatus'), nullable=False, comment='Template status'),
        sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0', comment='Template version'),
        sa.Column('parent_template_id', sa.String(length=36), nullable=True, comment='Parent template ID'),
        sa.Column('expedia_template_name', sa.String(length=255), nullable=True, comment='Expedia template name'),
        sa.Column('expedia_template_id', sa.String(length=100), nullable=True, comment='Expedia template ID'),
        sa.Column('expedia_version', sa.String(length=50), nullable=True, comment='Expedia template version'),
        sa.Column('header_row', sa.Integer(), nullable=False, server_default='1', comment='Header row'),
        sa.Column('data_start_row', sa.Integer(), nullable=False, server_default='2', comment='Data start row'),
        sa.Column('sheet_name', sa.String(length=100), nullable=True, comment='Sheet name'),
        sa.Column('config', sa.Text(), nullable=True, comment='Template config'),
        sa.Column('sample_file_path', sa.String(length=500), nullable=True, comment='Sample file path'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expedia_templates_code'), 'expedia_templates', ['code'], unique=True)

    # Create field_mappings table
    op.create_table(
        'field_mappings',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('template_id', sa.String(length=36), nullable=False, comment='Template ID'),
        sa.Column('field_order', sa.Integer(), nullable=False, comment='Field order'),
        sa.Column('source_field', sa.String(length=100), nullable=False, comment='Source field name'),
        sa.Column('source_field_cn', sa.String(length=100), nullable=True, comment='Source field Chinese'),
        sa.Column('source_field_type', sa.String(length=50), nullable=False, server_default='string', comment='Source field type'),
        sa.Column('source_model', sa.String(length=50), nullable=False, server_default='Hotel', comment='Source model'),
        sa.Column('target_field', sa.String(length=100), nullable=False, comment='Target field name'),
        sa.Column('target_field_required', sa.Boolean(), nullable=False, server_default='false', comment='Required field'),
        sa.Column('target_field_max_length', sa.Integer(), nullable=True, comment='Max length'),
        sa.Column('mapping_type', sa.Enum('direct', 'transform', 'lookup', 'computed', 'fixed', 'null', name='fieldmappingtype'), nullable=False, comment='Mapping type'),
        sa.Column('mapping_config', sa.Text(), nullable=True, comment='Mapping config'),
        sa.Column('validation_rule', sa.Text(), nullable=True, comment='Validation rule'),
        sa.Column('default_value', sa.String(length=255), nullable=True, comment='Default value'),
        sa.Column('transform_script', sa.Text(), nullable=True, comment='Transform script'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Active'),
        sa.Column('is_visible', sa.Boolean(), nullable=False, server_default='true', comment='Visible'),
        sa.Column('description', sa.Text(), nullable=True, comment='Description'),
        sa.Column('notes', sa.Text(), nullable=True, comment='Notes'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['expedia_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_field_mappings_template_id'), 'field_mappings', ['template_id'], unique=False)
    op.create_index(op.f('ix_field_mappings_source_field'), 'field_mappings', ['source_field'], unique=False)


def downgrade() -> None:
    # Drop field_mappings table
    op.drop_index(op.f('ix_field_mappings_source_field'), table_name='field_mappings')
    op.drop_index(op.f('ix_field_mappings_template_id'), table_name='field_mappings')
    op.drop_table('field_mappings')
    op.execute('DROP TYPE IF EXISTS fieldmappingtype')

    # Drop expedia_templates table
    op.drop_index(op.f('ix_expedia_templates_code'), table_name='expedia_templates')
    op.drop_table('expedia_templates')
    op.execute('DROP TYPE IF EXISTS templatestatus')
    op.execute('DROP TYPE IF EXISTS templatetype')

    # Drop export_histories table
    op.drop_index(op.f('ix_export_histories_operator_id'), table_name='export_histories')
    op.drop_table('export_histories')
    op.execute('DROP TYPE IF EXISTS exportstatus')
    op.execute('DROP TYPE IF EXISTS exportformat')
    op.execute('DROP TYPE IF EXISTS exporttype')

    # Drop import_histories table
    op.drop_index(op.f('ix_import_histories_operator_id'), table_name='import_histories')
    op.drop_table('import_histories')
    op.execute('DROP TYPE IF EXISTS importstatus')
    op.execute('DROP TYPE IF EXISTS importtype')

    # Drop room_extensions table
    op.drop_index(op.f('ix_room_extensions_room_id'), table_name='room_extensions')
    op.drop_table('room_extensions')

    # Drop rooms table
    op.drop_index(op.f('ix_rooms_hotel_id'), table_name='rooms')
    op.drop_index(op.f('ix_rooms_expedia_room_id'), table_name='rooms')
    op.drop_table('rooms')

    # Drop hotels table
    op.drop_index(op.f('ix_hotels_status'), table_name='hotels')
    op.drop_index(op.f('ix_hotels_expedia_hotel_id'), table_name='hotels')
    op.drop_index(op.f('ix_hotels_city'), table_name='hotels')
    op.drop_table('hotels')
    op.execute('DROP TYPE IF EXISTS hotelstatus')
    op.execute('DROP TYPE IF EXISTS hotelbrand')

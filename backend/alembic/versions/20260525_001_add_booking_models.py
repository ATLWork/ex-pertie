"""add_booking_models

Revision ID: 20260525_001
Revises: 20260409_001
Create Date: 2026-05-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260525_001"
down_revision: Union[str, None] = "20260409_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type for booking source
    op.execute("CREATE TYPE bookingsource AS ENUM ('booking_com', 'ctrip', 'expedia', 'other')")

    # Create booking_hotels table
    op.create_table(
        'booking_hotels',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('source', sa.Enum('booking_com', 'ctrip', 'expedia', 'other', name='bookingsource'), nullable=False, server_default='booking_com', comment='Data source'),
        sa.Column('source_hotel_id', sa.String(length=100), nullable=True, comment='Hotel ID in source system'),
        sa.Column('name_cn', sa.String(length=255), nullable=True, comment='Hotel name in Chinese'),
        sa.Column('name_en', sa.String(length=255), nullable=False, comment='Hotel name in English'),
        sa.Column('display_name', sa.String(length=255), nullable=True, comment='Display name'),
        sa.Column('brand', sa.String(length=100), nullable=True, comment='Hotel brand'),
        sa.Column('chain_name', sa.String(length=255), nullable=True, comment='Hotel chain name'),
        sa.Column('star_rating', sa.Float(), nullable=True, comment='Star rating'),
        sa.Column('country_code', sa.String(length=10), nullable=False, server_default='CN', comment='Country code'),
        sa.Column('country_name', sa.String(length=100), nullable=True, comment='Country name'),
        sa.Column('province', sa.String(length=100), nullable=True, comment='Province/State'),
        sa.Column('city', sa.String(length=100), nullable=False, comment='City'),
        sa.Column('city_id', sa.String(length=100), nullable=True, comment='City ID in source system'),
        sa.Column('district', sa.String(length=100), nullable=True, comment='District/County'),
        sa.Column('address', sa.String(length=500), nullable=False, comment='Street address'),
        sa.Column('postal_code', sa.String(length=20), nullable=True, comment='Postal code'),
        sa.Column('latitude', sa.Float(), nullable=True, comment='Latitude'),
        sa.Column('longitude', sa.Float(), nullable=True, comment='Longitude'),
        sa.Column('phone', sa.String(length=50), nullable=True, comment='Phone number'),
        sa.Column('fax', sa.String(length=50), nullable=True, comment='Fax number'),
        sa.Column('email', sa.String(length=255), nullable=True, comment='Email address'),
        sa.Column('website', sa.String(length=500), nullable=True, comment='Website URL'),
        sa.Column('check_in_time', sa.String(length=20), nullable=True, comment='Check-in time'),
        sa.Column('check_out_time', sa.String(length=20), nullable=True, comment='Check-out time'),
        sa.Column('built_year', sa.Integer(), nullable=True, comment='Year hotel was built'),
        sa.Column('renovated_year', sa.Integer(), nullable=True, comment='Last renovation year'),
        sa.Column('floor_count', sa.Integer(), nullable=True, comment='Number of floors'),
        sa.Column('room_count', sa.Integer(), nullable=True, comment='Total number of rooms'),
        sa.Column('booking_url', sa.String(length=500), nullable=True, comment='URL on Booking.com'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether hotel is active'),
        sa.Column('internal_hotel_id', sa.String(length=36), nullable=True, comment='Mapped internal hotel ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['internal_hotel_id'], ['hotels.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_booking_hotels_city'), 'booking_hotels', ['city'], unique=False)
    op.create_index(op.f('ix_booking_hotels_internal_hotel_id'), 'booking_hotels', ['internal_hotel_id'], unique=False)
    op.create_index(op.f('ix_booking_hotels_source_hotel_id'), 'booking_hotels', ['source_hotel_id'], unique=False)

    # Create booking_hotel_extensions table
    op.create_table(
        'booking_hotel_extensions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('hotel_id', sa.String(length=36), nullable=False, comment='Booking hotel ID'),
        sa.Column('description', sa.Text(), nullable=True, comment='Hotel description'),
        sa.Column('description_cn', sa.Text(), nullable=True, comment='Hotel description in Chinese'),
        sa.Column('cancellation_policy', sa.Text(), nullable=True, comment='Cancellation policy'),
        sa.Column('cancellation_policy_cn', sa.Text(), nullable=True, comment='Cancellation policy in Chinese'),
        sa.Column('prepayment_policy', sa.Text(), nullable=True, comment='Prepayment policy'),
        sa.Column('prepayment_policy_cn', sa.Text(), nullable=True, comment='Prepayment policy in Chinese'),
        sa.Column('kid_policy', sa.Text(), nullable=True, comment='Child policy'),
        sa.Column('pet_policy', sa.Text(), nullable=True, comment='Pet policy'),
        sa.Column('services', sa.Text(), nullable=True, comment='Hotel services'),
        sa.Column('services_cn', sa.Text(), nullable=True, comment='Hotel services in Chinese'),
        sa.Column('service_details', sa.Text(), nullable=True, comment='Service details in JSON'),
        sa.Column('facilities', sa.Text(), nullable=True, comment='Hotel facilities'),
        sa.Column('facilities_cn', sa.Text(), nullable=True, comment='Hotel facilities in Chinese'),
        sa.Column('facility_details', sa.Text(), nullable=True, comment='Facility details in JSON'),
        sa.Column('room_facilities', sa.Text(), nullable=True, comment='Room facilities'),
        sa.Column('room_facilities_cn', sa.Text(), nullable=True, comment='Room facilities in Chinese'),
        sa.Column('photo_urls', sa.Text(), nullable=True, comment='Hotel photo URLs in JSON'),
        sa.Column('cover_photo_url', sa.String(length=500), nullable=True, comment='Cover photo URL'),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True, comment='Thumbnail photo URL'),
        sa.Column('review_score', sa.Float(), nullable=True, comment='Review score'),
        sa.Column('review_count', sa.Integer(), nullable=True, comment='Total review count'),
        sa.Column('review_score_breakdown', sa.Text(), nullable=True, comment='Review score breakdown in JSON'),
        sa.Column('awards', sa.Text(), nullable=True, comment='Awards and certifications'),
        sa.Column('nearby_attractions', sa.Text(), nullable=True, comment='Nearby attractions in JSON'),
        sa.Column('important_notes', sa.Text(), nullable=True, comment='Important notes for guests'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['booking_hotels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('hotel_id')
    )
    op.create_index(op.f('ix_booking_hotel_extensions_hotel_id'), 'booking_hotel_extensions', ['hotel_id'], unique=True)

    # Create booking_rooms table
    op.create_table(
        'booking_rooms',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('hotel_id', sa.String(length=36), nullable=False, comment='Booking hotel ID'),
        sa.Column('source', sa.Enum('booking_com', 'ctrip', 'expedia', 'other', name='bookingsource'), nullable=False, server_default='booking_com', comment='Data source'),
        sa.Column('source_room_id', sa.String(length=100), nullable=True, comment='Room ID in source system'),
        sa.Column('room_name', sa.String(length=255), nullable=False, comment='Room name on Booking.com'),
        sa.Column('room_name_cn', sa.String(length=255), nullable=True, comment='Room name in Chinese'),
        sa.Column('room_type_code', sa.String(length=100), nullable=True, comment='Room type code'),
        sa.Column('room_type', sa.String(length=100), nullable=True, comment='Room type category'),
        sa.Column('bed_type', sa.String(length=100), nullable=True, comment='Bed type'),
        sa.Column('bed_configuration', sa.Text(), nullable=True, comment='Bed configuration details'),
        sa.Column('max_occupancy', sa.Integer(), nullable=False, server_default='2', comment='Maximum occupancy'),
        sa.Column('standard_occupancy', sa.Integer(), nullable=False, server_default='2', comment='Standard occupancy'),
        sa.Column('extra_bed_count', sa.Integer(), nullable=True, comment='Extra bed count available'),
        sa.Column('room_size', sa.Float(), nullable=True, comment='Room size in square meters'),
        sa.Column('floor', sa.String(length=50), nullable=True, comment='Floor information'),
        sa.Column('view_type', sa.String(length=100), nullable=True, comment='View type'),
        sa.Column('window_type', sa.String(length=50), nullable=True, comment='Window type'),
        sa.Column('amenities', sa.Text(), nullable=True, comment='Room amenities'),
        sa.Column('amenities_cn', sa.Text(), nullable=True, comment='Room amenities in Chinese'),
        sa.Column('amenity_details', sa.Text(), nullable=True, comment='Amenity details in JSON'),
        sa.Column('bathroom_type', sa.String(length=100), nullable=True, comment='Bathroom type'),
        sa.Column('bathroom_amenities', sa.Text(), nullable=True, comment='Bathroom amenities'),
        sa.Column('bathroom_amenities_cn', sa.Text(), nullable=True, comment='Bathroom amenities in Chinese'),
        sa.Column('photo_urls', sa.Text(), nullable=True, comment='Room photo URLs in JSON'),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True, comment='Thumbnail photo URL'),
        sa.Column('smoking_policy', sa.String(length=50), nullable=True, comment='Smoking policy'),
        sa.Column('booking_url', sa.String(length=500), nullable=True, comment='URL on Booking.com'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether room is active'),
        sa.Column('internal_room_id', sa.String(length=36), nullable=True, comment='Mapped internal room ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['hotel_id'], ['booking_hotels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['internal_room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_booking_rooms_hotel_id'), 'booking_rooms', ['hotel_id'], unique=False)
    op.create_index(op.f('ix_booking_rooms_internal_room_id'), 'booking_rooms', ['internal_room_id'], unique=False)
    op.create_index(op.f('ix_booking_rooms_source_room_id'), 'booking_rooms', ['source_room_id'], unique=False)

    # Create booking_room_extensions table
    op.create_table(
        'booking_room_extensions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('room_id', sa.String(length=36), nullable=False, comment='Booking room ID'),
        sa.Column('description', sa.Text(), nullable=True, comment='Room description'),
        sa.Column('description_cn', sa.Text(), nullable=True, comment='Room description in Chinese'),
        sa.Column('cancellation_policy', sa.Text(), nullable=True, comment='Cancellation policy'),
        sa.Column('cancellation_policy_cn', sa.Text(), nullable=True, comment='Cancellation policy in Chinese'),
        sa.Column('prepayment_policy', sa.Text(), nullable=True, comment='Prepayment policy'),
        sa.Column('prepayment_policy_cn', sa.Text(), nullable=True, comment='Prepayment policy in Chinese'),
        sa.Column('accessibility_features', sa.Text(), nullable=True, comment='Accessibility features in JSON'),
        sa.Column('additional_info', sa.Text(), nullable=True, comment='Additional room information'),
        sa.Column('additional_info_cn', sa.Text(), nullable=True, comment='Additional room information in Chinese'),
        sa.Column('important_notes', sa.Text(), nullable=True, comment='Important notes for this room'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['booking_rooms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id')
    )
    op.create_index(op.f('ix_booking_room_extensions_room_id'), 'booking_room_extensions', ['room_id'], unique=True)


def downgrade() -> None:
    # Drop booking_room_extensions table
    op.drop_index(op.f('ix_booking_room_extensions_room_id'), table_name='booking_room_extensions')
    op.drop_table('booking_room_extensions')

    # Drop booking_rooms table
    op.drop_index(op.f('ix_booking_rooms_source_room_id'), table_name='booking_rooms')
    op.drop_index(op.f('ix_booking_rooms_internal_room_id'), table_name='booking_rooms')
    op.drop_index(op.f('ix_booking_rooms_hotel_id'), table_name='booking_rooms')
    op.drop_table('booking_rooms')

    # Drop booking_hotel_extensions table
    op.drop_index(op.f('ix_booking_hotel_extensions_hotel_id'), table_name='booking_hotel_extensions')
    op.drop_table('booking_hotel_extensions')

    # Drop booking_hotels table
    op.drop_index(op.f('ix_booking_hotels_source_hotel_id'), table_name='booking_hotels')
    op.drop_index(op.f('ix_booking_hotels_internal_hotel_id'), table_name='booking_hotels')
    op.drop_index(op.f('ix_booking_hotels_city'), table_name='booking_hotels')
    op.drop_table('booking_hotels')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS bookingsource')
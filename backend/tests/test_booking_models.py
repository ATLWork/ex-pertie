"""
Tests for Booking hotel and room models.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import (
    BookingHotel,
    BookingRoom,
    BookingHotelExtension,
    BookingRoomExtension,
    BookingSource,
)
from app.services.booking_hotel_service import booking_hotel
from app.services.booking_room_service import booking_room


class TestBookingSourceEnum:
    """Test cases for BookingSource enum."""

    def test_booking_source_values(self):
        """Test BookingSource enum values."""
        assert BookingSource.BOOKING_COM.value == "booking_com"
        assert BookingSource.CTRIP.value == "ctrip"
        assert BookingSource.EXPEDIA.value == "expedia"
        assert BookingSource.OTHER.value == "other"


class TestBookingHotelModel:
    """Test cases for BookingHotel model."""

    async def test_create_booking_hotel(self, db_session: AsyncSession):
        """Test creating a booking hotel."""
        hotel = BookingHotel(
            source=BookingSource.BOOKING_COM,
            source_hotel_id="bk_test_001",
            name_en="Test Hotel Booking",
            city="Shanghai",
            address="123 Test Road, Shanghai",
            country_code="CN",
            star_rating=4.0,
            latitude=31.2304,
            longitude=121.4737,
            is_active=True,
        )
        db_session.add(hotel)
        await db_session.flush()
        await db_session.refresh(hotel)

        assert hotel.id is not None
        assert hotel.name_en == "Test Hotel Booking"
        assert hotel.city == "Shanghai"
        assert hotel.star_rating == 4.0
        assert hotel.is_active is True
        assert hotel.source == BookingSource.BOOKING_COM

    async def test_booking_hotel_with_extension(self, db_session: AsyncSession):
        """Test booking hotel with extension."""
        hotel = BookingHotel(
            source=BookingSource.BOOKING_COM,
            source_hotel_id="bk_test_002",
            name_en="Hotel With Extension",
            city="Beijing",
            address="456 Test Street",
            country_code="CN",
            is_active=True,
        )
        db_session.add(hotel)
        await db_session.flush()

        extension = BookingHotelExtension(
            hotel_id=hotel.id,
            description="A beautiful hotel in Beijing",
        )
        db_session.add(extension)
        await db_session.flush()
        await db_session.refresh(extension)

        assert extension.id is not None
        assert extension.hotel_id == hotel.id
        assert extension.description == "A beautiful hotel in Beijing"

    async def test_booking_hotel_service_create(self, db_session: AsyncSession):
        """Test creating booking hotel via service."""
        hotel = await booking_hotel.create(
            db_session,
            obj_in={
                "source": BookingSource.EXPEDIA,
                "source_hotel_id": "ex_test_001",
                "name_en": "Service Created Hotel",
                "city": "Hangzhou",
                "address": "789 Test Avenue",
                "country_code": "CN",
                "is_active": True,
            },
        )

        assert hotel.id is not None
        assert hotel.name_en == "Service Created Hotel"


class TestBookingRoomModel:
    """Test cases for BookingRoom model."""

    async def test_create_booking_room(self, db_session: AsyncSession):
        """Test creating a booking room."""
        hotel = BookingHotel(
            source=BookingSource.BOOKING_COM,
            source_hotel_id="bk_room_test",
            name_en="Room Test Hotel",
            city="Shanghai",
            address="123 Room Test Road",
            country_code="CN",
            is_active=True,
        )
        db_session.add(hotel)
        await db_session.flush()

        room = BookingRoom(
            hotel_id=hotel.id,
            source=BookingSource.BOOKING_COM,
            source_room_id="bk_rm_001",
            room_name="Standard King Room",
            room_type="1",
            bed_type="200",
            max_occupancy=2,
            is_active=True,
        )
        db_session.add(room)
        await db_session.flush()
        await db_session.refresh(room)

        assert room.id is not None
        assert room.hotel_id == hotel.id
        assert room.room_name == "Standard King Room"
        assert room.max_occupancy == 2

    async def test_booking_room_with_extension(self, db_session: AsyncSession):
        """Test booking room with extension."""
        hotel = BookingHotel(
            source=BookingSource.BOOKING_COM,
            source_hotel_id="bk_rm_ext_test",
            name_en="Room Extension Hotel",
            city="Chengdu",
            address="999 Test Road",
            country_code="CN",
            is_active=True,
        )
        db_session.add(hotel)
        await db_session.flush()

        room = BookingRoom(
            hotel_id=hotel.id,
            source=BookingSource.BOOKING_COM,
            source_room_id="bk_rm_ext_001",
            room_name="Deluxe Suite",
            room_type="4",
            bed_type="200",
            max_occupancy=3,
            is_active=True,
        )
        db_session.add(room)
        await db_session.flush()

        extension = BookingRoomExtension(
            room_id=room.id,
            description="Spacious suite with city view",
        )
        db_session.add(extension)
        await db_session.flush()
        await db_session.refresh(extension)

        assert extension.id is not None
        assert extension.room_id == room.id
        assert extension.description == "Spacious suite with city view"

    async def test_get_rooms_by_hotel(self, db_session: AsyncSession):
        """Test getting rooms by hotel."""
        hotel = BookingHotel(
            source=BookingSource.BOOKING_COM,
            source_hotel_id="bk_hotel_rooms",
            name_en="Multiple Rooms Hotel",
            city="Guangzhou",
            address="111 Test Road",
            country_code="CN",
            is_active=True,
        )
        db_session.add(hotel)
        await db_session.flush()

        room1 = BookingRoom(
            hotel_id=hotel.id,
            source=BookingSource.BOOKING_COM,
            source_room_id="bk_rm_multi_001",
            room_name="Room 1",
            room_type="1",
            bed_type="200",
            max_occupancy=2,
            is_active=True,
        )
        room2 = BookingRoom(
            hotel_id=hotel.id,
            source=BookingSource.BOOKING_COM,
            source_room_id="bk_rm_multi_002",
            room_name="Room 2",
            room_type="4",
            bed_type="200",
            max_occupancy=2,
            is_active=True,
        )
        db_session.add_all([room1, room2])
        await db_session.flush()

        rooms = await booking_room.get_by_hotel(
            db_session, hotel_id=hotel.id, skip=0, limit=100
        )

        assert len(rooms) == 2


class TestBookingLinkage:
    """Test cases for booking hotel-room linkage."""

    async def test_booking_hotel_room_relationship(self, db_session: AsyncSession):
        """Test booking hotel has rooms relationship."""
        hotel = BookingHotel(
            source=BookingSource.BOOKING_COM,
            source_hotel_id="bk_linkage_test",
            name_en="Linkage Test Hotel",
            city="Shenzhen",
            address="222 Test Road",
            country_code="CN",
            is_active=True,
        )
        db_session.add(hotel)
        await db_session.flush()

        room = BookingRoom(
            hotel_id=hotel.id,
            source=BookingSource.BOOKING_COM,
            source_room_id="bk_linkage_rm",
            room_name="Linkage Test Room",
            room_type="1",
            bed_type="200",
            max_occupancy=2,
            is_active=True,
        )
        db_session.add(room)
        await db_session.flush()

        await db_session.refresh(hotel, ["rooms"])

        assert len(hotel.rooms) == 1
        assert hotel.rooms[0].room_name == "Linkage Test Room"
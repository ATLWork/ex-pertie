"""
Test data factories using factory_boy.
"""

from tests.factories.hotel_factory import HotelFactory
from tests.factories.room_factory import RoomFactory, RoomExtensionFactory

__all__ = ["HotelFactory", "RoomFactory", "RoomExtensionFactory"]

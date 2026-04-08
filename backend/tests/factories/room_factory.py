"""
Room and RoomExtension factories for creating test room data.
"""

import factory
from factory import Faker, SubFactory
from factory_boy.factory import DjangoModelFactory

from app.models.hotel import Room, RoomExtension


class RoomFactory(DjangoModelFactory):
    """
    Factory for creating test Room instances.
    """

    class Meta:
        model = Room
        strategy = factory.BUILD_STRATEGY

    # Reference to hotel - must be set when using
    hotel_id = None

    # Basic Info
    room_type_code = Faker("bothify", text="???-###", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    name_cn = Faker("word", locale="zh_CN")
    name_en = Faker("word", locale="en_US")
    description_cn = Faker("sentence", locale="zh_CN", nb_words=10)
    description_en = Faker("sentence", locale="en_US", nb_words=10)

    # Room Configuration
    bed_type = factory.fuzzy.FuzzyChoice(["King", "Queen", "Twin", "Double", "Single"])
    max_occupancy = factory.fuzzy.FuzzyInteger(1, 6)
    standard_occupancy = factory.fuzzy.FuzzyInteger(1, 4)
    room_size = factory.fuzzy.FuzzyFloat(15.0, 100.0)
    floor_range = factory.fuzzy.FuzzyChoice(["1-5", "6-10", "11-15", "16-20", "21-25"])
    total_rooms = factory.fuzzy.FuzzyInteger(1, 100)

    # Expedia specific
    expedia_room_id = None
    expedia_room_type_code = None

    # Status
    is_active = True

    @classmethod
    def create_for_hotel(cls, hotel, **kwargs):
        """Create a room associated with a specific hotel."""
        defaults = {"hotel_id": hotel.id}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_batch_for_hotel(cls, hotel, count: int, **kwargs):
        """Create multiple rooms for a specific hotel."""
        defaults = {"hotel_id": hotel.id}
        defaults.update(kwargs)
        return cls.create_batch(count, **defaults)

    @classmethod
    def create_standard_room(cls, **kwargs):
        """Create a standard configuration room."""
        defaults = {
            "room_type_code": "STD",
            "bed_type": "King",
            "max_occupancy": 2,
            "standard_occupancy": 2,
            "room_size": 30.0,
            "total_rooms": 20,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_suite(cls, **kwargs):
        """Create a suite room type."""
        defaults = {
            "room_type_code": "STE",
            "name_cn": "套房",
            "name_en": "Suite",
            "bed_type": "King",
            "max_occupancy": 4,
            "standard_occupancy": 2,
            "room_size": 60.0,
            "total_rooms": 5,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_deluxe(cls, **kwargs):
        """Create a deluxe room type."""
        defaults = {
            "room_type_code": "DLX",
            "name_cn": "豪华房",
            "name_en": "Deluxe Room",
            "bed_type": "Queen",
            "max_occupancy": 3,
            "standard_occupancy": 2,
            "room_size": 40.0,
            "total_rooms": 15,
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class RoomExtensionFactory(DjangoModelFactory):
    """
    Factory for creating test RoomExtension instances.
    """

    class Meta:
        model = RoomExtension
        strategy = factory.BUILD_STRATEGY

    # Reference to room - must be set when using
    room_id = None

    # Amenities
    amenities_cn = "免费WiFi,空调,电视,冰箱"
    amenities_en = "Free WiFi, Air conditioning, TV, Refrigerator"
    amenity_details = '{"wifi": true, "ac": true, "tv": true, "minibar": false}'

    # Media
    image_urls = '["https://example.com/room1.jpg", "https://example.com/room2.jpg"]'
    thumbnail_url = Faker("url")

    # Physical Features
    view_type = factory.fuzzy.FuzzyChoice(["城市景观", "海景", "花园景观", "山景", "无景观"])
    balcony = factory.fuzzy.FuzzyChoice([True, False])
    smoking_policy = factory.fuzzy.FuzzyChoice(["无烟", "吸烟", "指定区域"])
    floor = factory.fuzzy.FuzzyChoice(["3", "5", "8", "12", "15"])

    # Bathroom
    bathroom_type = factory.fuzzy.FuzzyChoice(["独立卫浴", "公共卫浴", "套间卫浴"])
    bathroom_amenities_cn = "淋浴,浴缸,吹风机,洗漱用品"
    bathroom_amenities_en = "Shower, Bathtub, Hair dryer, Toiletries"

    # Accessibility
    accessibility_features = '{"wheelchair": true, "hearing_aid": false}'

    @classmethod
    def create_for_room(cls, room, **kwargs):
        """Create a room extension associated with a specific room."""
        defaults = {"room_id": room.id}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_with_amenities(cls, **kwargs):
        """Create a room extension with full amenities."""
        defaults = {
            "amenities_cn": "免费WiFi,空调,电视,冰箱,保险柜,电话",
            "amenities_en": "Free WiFi, Air conditioning, TV, Refrigerator, Safe, Phone",
            "balcony": True,
            "view_type": "城市景观",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

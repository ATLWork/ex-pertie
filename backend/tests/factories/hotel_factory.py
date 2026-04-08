"""
Hotel factory for creating test hotel data.
"""

import factory
from factory import Faker, SubFactory
from factory.alchemy import SQLAlchemyModelFactory
from factory_boy.factory import DjangoModelFactory

from app.models.hotel import Hotel, HotelBrand, HotelStatus


class HotelFactory(DjangoModelFactory):
    """
    Factory for creating test Hotel instances.
    """

    class Meta:
        model = Hotel
        strategy = factory.BUILD_STRATEGY

    # Basic Info
    name_cn = Faker("company", locale="zh_CN")
    name_en = Faker("company", locale="en_US")
    brand = factory.fuzzy.FuzzyChoice([HotelBrand.ATour, HotelBrand.ATourX, HotelBrand.ZHotel, HotelBrand.Ahaus])
    status = HotelStatus.DRAFT

    # Location Info
    country_code = "CN"
    province = Faker("administrative_unit", locale="zh_CN")
    city = Faker("city", locale="zh_CN")
    district = Faker("district", locale="zh_CN")
    address_cn = Faker("street_address", locale="zh_CN")
    address_en = Faker("street_address", locale="en_US")
    postal_code = Faker("postcode")

    # Contact Info
    phone = Faker("phone_number")
    email = Faker("company_email")
    website = Faker("url")

    # Geolocation
    latitude = Faker("latitude")
    longitude = Faker("longitude")

    # Expedia specific
    expedia_hotel_id = None
    expedia_chain_code = None
    expedia_property_code = None

    # Timestamps
    opened_at = None
    renovated_at = None

    @classmethod
    def create_with_expedia(cls, **kwargs):
        """Create a hotel with Expedia IDs."""
        defaults = {
            "expedia_hotel_id": f"EXP-{Faker('uuid4').generate()[:8]}",
            "expedia_chain_code": "ATOUR",
            "expedia_property_code": f"ATOUR-{Faker('uuid4').generate()[:6]}",
        }
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_published(cls, **kwargs):
        """Create a published hotel."""
        defaults = {"status": HotelStatus.PUBLISHED}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_draft(cls, **kwargs):
        """Create a draft hotel."""
        defaults = {"status": HotelStatus.DRAFT}
        defaults.update(kwargs)
        return cls.create(**defaults)

    @classmethod
    def create_batch_for_city(cls, city: str, count: int, **kwargs):
        """Create multiple hotels in the same city."""
        defaults = {"city": city}
        defaults.update(kwargs)
        return cls.create_batch(count, **defaults)

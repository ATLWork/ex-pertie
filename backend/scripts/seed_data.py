"""
Database seed data script.
Creates initial hotel and room data for testing and development.

Usage:
    # As standalone script
    python -m scripts.seed_data

    # Within Python code
    from scripts.seed_data import seed_database, clear_seed_data

    # Seed data
    await seed_database()

    # Clear seed data
    await clear_seed_data()
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, init_db
from app.models import (
    Hotel,
    Room,
    HotelBrand,
    HotelStatus,
)


# =============================================================================
# Seed Data Definitions
# =============================================================================

def get_seed_hotels() -> List[dict]:
    """
    Get seed hotel data.

    Returns:
        List of hotel dictionaries with all required fields.
    """
    return [
        {
            "name_cn": "上海外滩亚朵酒店",
            "name_en": "Atour Hotel Shanghai Bund",
            "brand": HotelBrand.ATour,
            "status": HotelStatus.PUBLISHED,
            "country_code": "CN",
            "province": "上海市",
            "city": "上海市",
            "district": "黄浦区",
            "address_cn": "上海市黄浦区中山东一路100号",
            "address_en": "100 Zhongshan East Road, Huangpu District, Shanghai",
            "postal_code": "200002",
            "phone": "+86-21-63298888",
            "email": "bund@atour.com",
            "website": "https://bund.atour.com",
            "latitude": 31.2405,
            "longitude": 121.4901,
            "expedia_chain_code": "ATOUR",
            "opened_at": datetime(2018, 6, 1),
            "renovated_at": datetime(2023, 12, 1),
        },
        {
            "name_cn": "杭州西湖亚朵酒店",
            "name_en": "Atour Hotel Hangzhou West Lake",
            "brand": HotelBrand.ATour,
            "status": HotelStatus.PUBLISHED,
            "country_code": "CN",
            "province": "浙江省",
            "city": "杭州市",
            "district": "西湖区",
            "address_cn": "杭州市西湖区曙光路120号",
            "address_en": "120 Shuguang Road, Xihu District, Hangzhou",
            "postal_code": "310007",
            "phone": "+86-571-87888888",
            "email": "westlake@atour.com",
            "website": "https://westlake.atour.com",
            "latitude": 30.2655,
            "longitude": 120.1487,
            "expedia_chain_code": "ATOUR",
            "opened_at": datetime(2019, 3, 15),
            "renovated_at": None,
        },
        {
            "name_cn": "北京三里屯亚朵X酒店",
            "name_en": "ATour X Beijing Sanlitun",
            "brand": HotelBrand.ATourX,
            "status": HotelStatus.PUBLISHED,
            "country_code": "CN",
            "province": "北京市",
            "city": "北京市",
            "district": "朝阳区",
            "address_cn": "北京市朝阳区工人体育场北路8号",
            "address_en": "8 Gong Ren Ti Yu Chang North Road, Chaoyang District, Beijing",
            "postal_code": "100027",
            "phone": "+86-10-84568888",
            "email": "sanlitun@atour.com",
            "website": "https://sanlitunx.atour.com",
            "latitude": 39.9357,
            "longitude": 116.4467,
            "expedia_chain_code": "ATOURX",
            "opened_at": datetime(2020, 9, 1),
            "renovated_at": None,
        },
        {
            "name_cn": "成都太古里ZHotel",
            "name_en": "ZHotel Chengdu Taikoo Li",
            "brand": HotelBrand.ZHotel,
            "status": HotelStatus.APPROVED,
            "country_code": "CN",
            "province": "四川省",
            "city": "成都市",
            "district": "锦江区",
            "address_cn": "成都市锦江区中纱帽街8号",
            "address_en": "8 Zhong Sha Mao Street, Jinjiang District, Chengdu",
            "postal_code": "610021",
            "phone": "+86-28-66888888",
            "email": "taikooli@zhotel.com",
            "website": "https://taikooli.zhotel.com",
            "latitude": 30.6598,
            "longitude": 104.0837,
            "expedia_chain_code": "ZHOTEL",
            "opened_at": datetime(2021, 5, 20),
            "renovated_at": None,
        },
        {
            "name_cn": "南京新街口Ahaus",
            "name_en": "Ahaus Nanjing Xinjiekou",
            "brand": HotelBrand.Ahaus,
            "status": HotelStatus.PENDING_REVIEW,
            "country_code": "CN",
            "province": "江苏省",
            "city": "南京市",
            "district": "鼓楼区",
            "address_cn": "南京市鼓楼区中山路100号",
            "address_en": "100 Zhongshan Road, Gulou District, Nanjing",
            "postal_code": "210005",
            "phone": "+86-25-58888888",
            "email": "xinjiekou@ahaus.com",
            "website": "https://xinjiekou.ahaus.com",
            "latitude": 32.0603,
            "longitude": 118.7833,
            "expedia_chain_code": "AHAUS",
            "opened_at": datetime(2022, 2, 14),
            "renovated_at": None,
        },
        {
            "name_cn": "深圳南山亚朵酒店",
            "name_en": "Atour Hotel Shenzhen Nanshan",
            "brand": HotelBrand.ATour,
            "status": HotelStatus.DRAFT,
            "country_code": "CN",
            "province": "广东省",
            "city": "深圳市",
            "district": "南山区",
            "address_cn": "深圳市南山区科技园南区高新南七道18号",
            "address_en": "18 Gaoxin No.7 Road, Nanshan District, Shenzhen",
            "postal_code": "518057",
            "phone": "+86-755-26888888",
            "email": "nanshan@atour.com",
            "website": "https://nanshan.atour.com",
            "latitude": 22.5312,
            "longitude": 113.9308,
            "expedia_chain_code": "ATOUR",
            "opened_at": datetime(2024, 1, 1),
            "renovated_at": None,
        },
        {
            "name_cn": "西安钟楼亚朵S酒店",
            "name_en": "Atour S Hotel Xi'an Bell Tower",
            "brand": HotelBrand.ATourX,
            "status": HotelStatus.PUBLISHED,
            "country_code": "CN",
            "province": "陕西省",
            "city": "西安市",
            "district": "莲湖区",
            "address_cn": "西安市莲湖区北大街1号",
            "address_en": "1 North Street, Lianhu District, Xi'an",
            "postal_code": "710003",
            "phone": "+86-29-88888888",
            "email": "belltower@atour.com",
            "website": "https://belltower.atour.com",
            "latitude": 34.2643,
            "longitude": 108.9423,
            "expedia_chain_code": "ATOURS",
            "opened_at": datetime(2023, 7, 1),
            "renovated_at": None,
        },
    ]


def get_seed_rooms(hotel_ids: List[str]) -> List[dict]:
    """
    Generate seed room data for given hotels.

    Args:
        hotel_ids: List of hotel IDs to create rooms for.

    Returns:
        List of room dictionaries with all required fields.
    """
    room_templates = [
        # Standard room types
        {
            "room_type_code": "STD",
            "name_cn": "标准大床房",
            "name_en": "Standard King Room",
            "description_cn": "配备1.8米大床，30平米舒适空间，包含免费早餐。",
            "description_en": "Room with 1.8m king bed, 30 sqm, includes breakfast.",
            "bed_type": "King",
            "max_occupancy": 2,
            "standard_occupancy": 2,
            "room_size": 30.0,
            "floor_range": "3-10",
            "total_rooms": 20,
        },
        {
            "room_type_code": "STD-TWIN",
            "name_cn": "标准双床房",
            "name_en": "Standard Twin Room",
            "description_cn": "配备2张1.2米单人床，32平米空间，包含免费早餐。",
            "description_en": "Room with 2x1.2m twin beds, 32 sqm, includes breakfast.",
            "bed_type": "Twin",
            "max_occupancy": 2,
            "standard_occupancy": 2,
            "room_size": 32.0,
            "floor_range": "3-10",
            "total_rooms": 15,
        },
        {
            "room_type_code": "DELUXE",
            "name_cn": "豪华大床房",
            "name_en": "Deluxe King Room",
            "description_cn": "配备1.8米大床，40平米宽敞空间，景观房，包含免费早餐。",
            "description_en": "King bed, 40 sqm, view room, includes breakfast.",
            "bed_type": "King",
            "max_occupancy": 2,
            "standard_occupancy": 2,
            "room_size": 40.0,
            "floor_range": "10-15",
            "total_rooms": 12,
        },
        {
            "room_type_code": "SUITE",
            "name_cn": "商务套房",
            "name_en": "Business Suite",
            "description_cn": "配备1.8米大床+独立客厅，55平米空间，包含早餐和下午茶。",
            "description_en": "King bed with separate living room, 55 sqm, breakfast and afternoon tea included.",
            "bed_type": "King",
            "max_occupancy": 3,
            "standard_occupancy": 2,
            "room_size": 55.0,
            "floor_range": "15-20",
            "total_rooms": 8,
        },
        {
            "room_type_code": "FAM-SUITE",
            "name_cn": "家庭套房",
            "name_en": "Family Suite",
            "description_cn": "配备主卧1.8米大床+次卧双床，75平米空间，适合家庭入住。",
            "description_en": "Master king bed + second room twin beds, 75 sqm, ideal for families.",
            "bed_type": "King+Twin",
            "max_occupancy": 4,
            "standard_occupancy": 3,
            "room_size": 75.0,
            "floor_range": "8-12",
            "total_rooms": 5,
        },
    ]

    rooms = []
    for hotel_id in hotel_ids:
        # Assign different room types based on hotel index
        num_rooms = 4 if len(hotel_ids) > 5 else 3  # Most hotels get 4 room types
        selected_templates = room_templates[:num_rooms]

        for i, template in enumerate(selected_templates):
            room = template.copy()
            room["hotel_id"] = hotel_id
            rooms.append(room)

    return rooms


# =============================================================================
# Database Operations
# =============================================================================

async def seed_database() -> dict:
    """
    Seed the database with initial data.

    Returns:
        Dictionary with seeding statistics.
    """
    stats = {
        "hotels_created": 0,
        "rooms_created": 0,
        "errors": [],
    }

    async with async_session_maker() as session:
        try:
            # Check if hotels already exist
            result = await session.execute(select(Hotel))
            existing_hotels = result.scalars().all()

            if existing_hotels:
                stats["errors"].append(f"Database already contains {len(existing_hotels)} hotels. Clear data first.")
                return stats

            # Create hotels
            hotel_data_list = get_seed_hotels()
            created_hotels = []

            for hotel_data in hotel_data_list:
                hotel = Hotel(**hotel_data)
                session.add(hotel)
                created_hotels.append(hotel)

            await session.flush()  # Get IDs without committing

            # Create rooms for each hotel
            hotel_ids = [hotel.id for hotel in created_hotels]
            room_data_list = get_seed_rooms(hotel_ids)

            for room_data in room_data_list:
                room = Room(**room_data)
                session.add(room)
                stats["rooms_created"] += 1

            await session.commit()

            stats["hotels_created"] = len(created_hotels)

            print(f"\n{'='*50}")
            print("Database seeding completed successfully!")
            print(f"{'='*50}")
            print(f"Hotels created: {stats['hotels_created']}")
            print(f"Rooms created: {stats['rooms_created']}")
            print(f"{'='*50}")

            for hotel in created_hotels:
                print(f"  - {hotel.name_cn} ({hotel.brand.value})")

        except Exception as e:
            await session.rollback()
            stats["errors"].append(str(e))
            print(f"\nError seeding database: {e}")
            raise

    return stats


async def clear_seed_data() -> dict:
    """
    Clear all seed data from the database.

    Note: This will delete all hotels and their associated rooms.

    Returns:
        Dictionary with deletion statistics.
    """
    stats = {
        "hotels_deleted": 0,
        "rooms_deleted": 0,
        "errors": [],
    }

    async with async_session_maker() as session:
        try:
            # Delete rooms first (due to foreign key)
            result = await session.execute(delete(Room))
            stats["rooms_deleted"] = result.rowcount

            # Delete hotels
            result = await session.execute(delete(Hotel))
            stats["hotels_deleted"] = result.rowcount

            await session.commit()

            print(f"\n{'='*50}")
            print("Seed data cleared successfully!")
            print(f"{'='*50}")
            print(f"Hotels deleted: {stats['hotels_deleted']}")
            print(f"Rooms deleted: {stats['rooms_deleted']}")
            print(f"{'='*50}")

        except Exception as e:
            await session.rollback()
            stats["errors"].append(str(e))
            print(f"\nError clearing seed data: {e}")
            raise

    return stats


async def reset_seed_data() -> dict:
    """
    Clear and reseed the database.

    Returns:
        Dictionary with operation statistics.
    """
    await clear_seed_data()
    return await seed_database()


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Database seed data management")
    parser.add_argument(
        "action",
        choices=["seed", "clear", "reset"],
        help="Action to perform: seed, clear, or reset"
    )

    args = parser.parse_args()

    # Run the appropriate action
    if args.action == "seed":
        asyncio.run(seed_database())
    elif args.action == "clear":
        asyncio.run(clear_seed_data())
    elif args.action == "reset":
        asyncio.run(reset_seed_data())


if __name__ == "__main__":
    main()

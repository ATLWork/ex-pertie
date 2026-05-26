"""
Booking.com 亚朵酒店数据爬虫 - 入口脚本

Usage:
    python -m backend.scripts.booking_scraper.main
    python -m backend.scripts.booking_scraper.main --cities 上海 北京 杭州
    python -m backend.scripts.booking_scraper.main --headless false
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from backend.scripts.booking_scraper.scraper import BookingScraper
from backend.scripts.booking_scraper.exporter import HotelExporter


def setup_logging():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )
    logger.add(
        "logs/booking_scraper_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
    )


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Booking.com 亚朵酒店数据爬虫")
    parser.add_argument(
        "--cities",
        nargs="+",
        default=["上海", "北京", "杭州", "成都", "西安", "南京"],
        help="要爬取的城市列表",
    )
    parser.add_argument(
        "--max-per-city",
        type=int,
        default=10,
        help="每个城市最多爬取酒店数量",
    )
    parser.add_argument(
        "--headless",
        type=lambda x: x.lower() == "true",
        default=True,
        help="是否无头模式运行",
    )
    parser.add_argument(
        "--format",
        choices=["excel", "csv", "both"],
        default="excel",
        help="导出格式",
    )
    parser.add_argument(
        "--delay",
        nargs=2,
        type=float,
        default=[2, 5],
        help="请求延迟范围（秒）",
    )

    args = parser.parse_args()

    setup_logging()
    logger.info("=" * 50)
    logger.info("Booking.com 亚朵酒店数据爬虫启动")
    logger.info(f"城市: {args.cities}")
    logger.info(f"每城市最大数量: {args.max_per_city}")
    logger.info(f"无头模式: {args.headless}")
    logger.info(f"导出格式: {args.format}")
    logger.info("=" * 50)

    all_hotels = []

    async with BookingScraper(
        headless=args.headless,
        delay_range=tuple(args.delay),
    ) as scraper:
        all_hotels = await scraper.scrape_atour_hotels(
            cities=args.cities,
            max_per_city=args.max_per_city,
        )

    logger.info(f"\n爬取完成，共获取 {len(all_hotels)} 家酒店数据")

    if all_hotels:
        exporter = HotelExporter()

        if args.format in ["excel", "both"]:
            excel_path = exporter.export_to_excel(all_hotels)
            logger.info(f"Excel 文件: {excel_path}")

        if args.format in ["csv", "both"]:
            csv_path = exporter.export_to_csv(all_hotels)
            logger.info(f"CSV 文件: {csv_path}")
    else:
        logger.warning("没有获取到任何酒店数据")

    logger.info("爬虫执行完成")


if __name__ == "__main__":
    asyncio.run(main())
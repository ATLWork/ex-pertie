"""
Booking.com Playwright 爬虫核心模块
"""

import asyncio
import random
from typing import Optional, List, Dict, Any
from loguru import logger
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout


class BookingScraper:
    """Booking.com 爬虫"""

    BASE_URL = "https://www.booking.com"
    SEARCH_URL = "https://www.booking.com/searchresults.html"

    def __init__(
        self,
        headless: bool = True,
        delay_range: tuple = (2, 5),
    ):
        """
        初始化爬虫

        Args:
            headless: 是否无头模式
            delay_range: 请求间隔范围（秒）
        """
        self.headless = headless
        self.delay_range = delay_range
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """启动浏览器"""
        logger.info("启动 Playwright 浏览器...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            user_agent=random.choice(self.user_agents),
            viewport={"width": 1280, "height": 720},
            locale="zh-CN",
            geolocation={"latitude": 31.2304, "longitude": 121.4737},  # 上海
            permissions=["geolocation"],
        )
        self.page = await context.new_page()
        # 设置语言偏好
        await self.page.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        # 禁用图片加载加速爬取
        await self.page.route("**/*.{png,jpg,jpeg,gif,svg,webp}", lambda route: route.abort())
        logger.info("浏览器启动成功")

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("浏览器已关闭")

    def _random_delay(self):
        """随机延迟"""
        return random.uniform(*self.delay_range)

    async def _accept_cookies_if_present(self):
        """处理 Cookie 弹窗 - 勾选所有选项并同意"""
        try:
            # 等待弹窗出现
            await asyncio.sleep(2)

            # 使用 JS 查找并勾选所有复选框
            await self.page.evaluate("""
                async () => {
                    // 查找所有 cookie 相关的复选框
                    const checkboxes = document.querySelectorAll(
                        'input[type="checkbox"]:not([checked]), ' +
                        '.onetrust-pc-dark-filter input[type="checkbox"], ' +
                        '#onetrust-consent-sdk input[type="checkbox"], ' +
                        '.permission-modal input[type="checkbox"]'
                    );
                    checkboxes.forEach(cb => {
                        if (!cb.checked && cb.offsetParent !== null) {
                            cb.click();
                        }
                    });
                }
            """)
            await asyncio.sleep(0.5)

            # 等待确认按钮出现
            await asyncio.sleep(1)

            # 点击"确认全部"或"同意"按钮 - 使用多个策略
            button_selectors = [
                'button[id="onetrust-accept-btn-handler"]',
                'button[data-testid="accept-all"]',
                'button:has-text("确认全部")',
                'button:has-text("同意所有")',
                '.onetrust-pc-btn-accept',
                '#cookieConsentAccept',
                'button[class*="accept"]',
            ]

            for selector in button_selectors:
                try:
                    btn = self.page.locator(selector).first
                    if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                        await btn.click()
                        logger.info(f"已点击: {selector}")
                        await asyncio.sleep(1)
                        return
                except Exception:
                    continue

            # 如果找不到按钮，尝试直接按 Escape 关闭弹窗
            try:
                await self.page.keyboard.press("Escape")
                logger.info("按 Escape 关闭弹窗")
            except Exception:
                pass

            await asyncio.sleep(2)

            # 检查页面是否还在 consent 页面
            if "pipl_consent" in self.page.url:
                # 尝试点击强制确认
                try:
                    # 查找所有按钮并尝试点击包含"确认"或"同意"的
                    buttons = await self.page.query_selector_all("button")
                    for btn in buttons:
                        text = await btn.inner_text()
                        if "确认" in text or "同意" in text or "Accept" in text or "accept" in text.lower():
                            await btn.click()
                            logger.info(f"点击了按钮: {text}")
                            await asyncio.sleep(2)
                            break
                except Exception as e:
                    logger.debug(f"额外点击尝试: {e}")

        except Exception as e:
            logger.debug(f"Cookie 弹窗处理: {e}")

    async def search_atour_hotels(self, city: str = "") -> List[Dict[str, Any]]:
        """
        搜索亚朵酒店

        Args:
            city: 城市名称（可选）

        Returns:
            酒店列表（包含基本信息）
        """
        logger.info(f"搜索亚朵酒店，城市: {city or '全国'}")

        # 构建搜索 URL - 正确编码
        import urllib.parse
        query = "Atour" + (f" {city}" if city else "")
        encoded_query = urllib.parse.quote(query)
        url = f"{self.SEARCH_URL}?ss={encoded_query}"

        logger.info(f"访问 URL: {url}")
        await self.page.goto(url, timeout=60000)
        logger.info(f"实际 URL: {self.page.url}")
        logger.info(f"页面标题: {await self.page.title()}")
        await asyncio.sleep(5)  # 等待页面加载

        # 处理 Cookie
        await self._accept_cookies_if_present()
        await asyncio.sleep(3)

        # 检查是否还在 consent 页面，如果是就尝试点击同意按钮
        if "pipl_consent" in self.page.url:
            logger.info("检测到 consent 页面，尝试点击同意按钮")
            try:
                # 尝试直接点击确认按钮
                accept_btn = self.page.locator('button[id="confirm"], button:has-text("确认"), button:has-text("同意")')
                if await accept_btn.count() > 0:
                    await accept_btn.first.click()
                    await asyncio.sleep(3)
            except Exception as e:
                logger.warning(f"点击同意按钮失败: {e}")

        hotels = []
        page_num = 1

        while True:
            logger.info(f"解析第 {page_num} 页...")

            # 等待搜索结果加载
            try:
                await self.page.wait_for_selector(
                    'div[data-testid="property-card"]',
                    timeout=15000
                )
            except PlaywrightTimeout:
                # 如果没找到，尝试截图调试
                logger.warning(f"第 {page_num} 页没有找到搜索结果，尝试其他选择器")
                logger.warning(f"当前 URL: {self.page.url}")
                logger.warning(f"当前标题: {await self.page.title()}")
                # 保存页面 HTML 用于调试
                try:
                    html = await self.page.content()
                    logger.debug(f"页面长度: {len(html)} 字符")
                    # 查找任何看起来像酒店卡片的元素
                    any_cards = await self.page.query_selector_all('[class*="property"], [class*="hotel"], [class*="card"]')
                    logger.info(f"页面中有 {len(any_cards)} 个可能相关的元素")
                except Exception as e:
                    logger.debug(f"调试获取失败: {e}")
                # 尝试其他可能的选择器
                try:
                    await self.page.wait_for_selector('.sr_property_card', timeout=5000)
                except PlaywrightTimeout:
                    logger.warning(f"第 {page_num} 页确实没有搜索结果")
                    break

            # 解析当前页的酒店列表
            cards = await self.page.query_selector_all('div[data-testid="property-card"], .sr_property_card')
            logger.info(f"第 {page_num} 页找到 {len(cards)} 个酒店")

            for card in cards:
                try:
                    hotel = await self._parse_search_card(card)
                    if hotel:
                        hotels.append(hotel)
                except Exception as e:
                    logger.warning(f"解析酒店卡片失败: {e}")

            # 检查是否有下一页
            try:
                next_button = self.page.locator('button[data-testid="pagination-next-arrow"]')
                if await next_button.count() == 0:
                    break
                if await next_button.is_disabled(timeout=3000):
                    break
            except Exception:
                break

            # 点击下一页
            try:
                await next_button.click()
                await asyncio.sleep(self._random_delay())
                page_num += 1
            except Exception:
                break

        logger.info(f"共找到 {len(hotels)} 家亚朵酒店")
        return hotels

    async def _parse_search_card(self, card) -> Optional[Dict[str, Any]]:
        """解析搜索结果卡片"""
        try:
            # 酒店名称 - 在链接文本中，格式为 "酒店名\n在新窗口中打开"
            name = ""
            booking_url = ""
            links = await card.query_selector_all('a[href*="/hotel/"]')
            for link in links:
                href = await link.get_attribute("href")
                if href and "/hotel/" in href and not booking_url:
                    booking_url = href
                text = await link.inner_text()
                # 酒店名称包含中文且不包含"在新窗口"等文字
                if text and any(c >= '\u4e00' and c <= '\u9fff' for c in text):
                    if "在" not in text and "窗口" not in text and "地图" not in text and "评分" not in text:
                        name = text.split('\n')[0]
                        break

            # 如果没找到名字，尝试从第一个酒店链接获取
            if not name and links:
                text = await links[0].inner_text()
                if text and "在" not in text and "窗口" not in text:
                    name = text.split('\n')[0]

            # 评分 - 从包含"评分"的链接文本获取
            rating = 0.0
            for link in links:
                text = await link.inner_text()
                if text and "评分" in text:
                    import re
                    numbers = re.findall(r'\d+\.\d+', text)
                    if numbers:
                        rating = float(numbers[0])
                        break

            # 简要地址 - 从包含区/路/街的链接文本获取
            address = ""
            for link in links:
                text = await link.inner_text()
                if text and ("区" in text or "路" in text or "街" in text) and "地图" not in text:
                    address = text.split('\n')[0]
                    break

            return {
                "name_cn": name,
                "booking_url": booking_url if booking_url.startswith("http") else f"{self.BASE_URL}{booking_url}",
                "rating": rating,
                "address": address,
            }
        except Exception as e:
            logger.warning(f"解析卡片失败: {e}")
            return None

    async def get_hotel_details(self, booking_url: str) -> Optional[Dict[str, Any]]:
        """
        获取酒店详情

        Args:
            booking_url: 酒店详情页 URL

        Returns:
            酒店详情数据
        """
        logger.info(f"获取详情: {booking_url}")
        await asyncio.sleep(self._random_delay())

        try:
            # 确保 URL 格式正确
            if booking_url.startswith("https://www.booking.comhttps"):
                booking_url = booking_url.replace("https://www.booking.comhttps", "https://")

            await self.page.goto(booking_url, timeout=30000)
            await asyncio.sleep(3)

            # 处理 Cookie
            await self._accept_cookies_if_present()

            details = {}

            # 酒店名称（英文名）
            try:
                name_en_elem = await self.page.query_selector(
                    'h2[data-testid="property-title"]'
                )
                details["name_en"] = await name_en_elem.inner_text() if name_en_elem else ""
            except Exception:
                details["name_en"] = ""

            # 地址
            try:
                address_elem = await self.page.query_selector(
                    'span[data-testid="address"]'
                )
                details["address"] = await address_elem.inner_text() if address_elem else ""
            except Exception:
                details["address"] = ""

            # 电话
            try:
                phone_elem = await self.page.query_selector(
                    'a[href^="tel:"]'
                )
                details["phone"] = await phone_elem.inner_text() if phone_elem else ""
            except Exception:
                details["phone"] = ""

            # 经纬度（从页面脚本获取）
            try:
                lat_elem = await self.page.query_selector(
                    '[data-testid="show-map"]'
                )
                if lat_elem:
                    href = await lat_elem.get_attribute("data-atlas-event")
                    if href:
                        import json
                        event_data = json.loads(href)
                        details["latitude"] = event_data.get("lat", 0)
                        details["longitude"] = event_data.get("lng", 0)
            except Exception:
                details["latitude"] = None
                details["longitude"] = None

            # 星级
            try:
                stars = await self.page.query_selector_all(
                    '.bui-star-score__item--active svg'
                )
                details["star_rating"] = len(stars)
            except Exception:
                details["star_rating"] = 0

            # 入住/退房时间
            try:
                check_in_elem = await self.page.query_selector(
                    '[data-testid="check-in-time"]'
                )
                details["check_in_time"] = await check_in_elem.inner_text() if check_in_elem else ""

                check_out_elem = await self.page.query_selector(
                    '[data-testid="check-out-time"]'
                )
                details["check_out_time"] = await check_out_elem.inner_text() if check_out_elem else ""
            except Exception:
                pass

            # 房间数
            try:
                rooms_elem = await self.page.query_selector(
                    '[data-testid="rooms-show"]'
                )
                rooms_text = await rooms_elem.inner_text() if rooms_elem else ""
                # 提取数字
                import re
                numbers = re.findall(r'\d+', rooms_text)
                details["room_count"] = int(numbers[0]) if numbers else 0
            except Exception:
                details["room_count"] = 0

            # 设施服务
            facilities = []
            try:
                fac_elems = await self.page.query_selector_all(
                    '[data-testid="facility-group"]'
                )
                for fac in fac_elems[:5]:  # 只取前5组
                    text = await fac.inner_text()
                    facilities.append(text.split('\n')[0])
            except Exception:
                pass
            details["facilities"] = ", ".join(facilities) if facilities else ""

            return details

        except Exception as e:
            logger.error(f"获取详情失败: {e}")
            return None

    async def scrape_atour_hotels(
        self,
        cities: List[str] = None,
        max_per_city: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        爬取亚朵酒店数据

        Args:
            cities: 城市列表
            max_per_city: 每个城市最多爬取数量

        Returns:
            酒店详情列表
        """
        all_hotels = []

        # 如果没有指定城市，使用主要城市
        if not cities:
            cities = ["上海", "北京", "杭州", "成都", "西安", "南京", "苏州", "武汉", "深圳", "广州"]

        for city in cities:
            logger.info(f"=== 爬取 {city} 的亚朵酒店 ===")

            try:
                # 搜索酒店
                search_results = await self.search_atour_hotels(city)

                # 限制数量
                for hotel in search_results[:max_per_city]:
                    # 获取详情
                    if hotel.get("booking_url"):
                        details = await self.get_hotel_details(hotel["booking_url"])
                        if details:
                            # 合并搜索结果和详情
                            hotel.update(details)
                            # 添加城市信息
                            hotel["city"] = city
                            all_hotels.append(hotel)
                        else:
                            # 即使没有详情，也保留搜索结果
                            hotel["city"] = city
                            all_hotels.append(hotel)
                    else:
                        hotel["city"] = city
                        all_hotels.append(hotel)

                # 城市间延迟
                await asyncio.sleep(self._random_delay() * 2)

            except Exception as e:
                logger.error(f"爬取 {city} 失败: {e}")

        return all_hotels
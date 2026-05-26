# Booking.com 亚朵酒店数据爬虫

## 概述

从 Booking.com 爬取亚朵（Atour）品牌酒店数据，用于导入系统作为翻译参考数据源。

## 技术架构

```
backend/scripts/booking_scraper/
├── __init__.py      # 模块初始化
├── main.py          # CLI 入口脚本
├── scraper.py        # Playwright 爬虫核心
└── exporter.py      # Excel/CSV 导出器
```

## 数据需求

根据 `BookingHotel` 模型，需要以下字段：

| 字段 | 说明 |
|------|------|
| name_cn | 酒店中文名 |
| name_en | 酒店英文名 |
| city | 城市 |
| province | 省份 |
| country_code | 国家代码 |
| address | 地址 |
| phone | 电话 |
| email | 邮箱 |
| latitude/longitude | 经纬度 |
| star_rating | 星级 |
| check_in/out_time | 入住/退房时间 |
| room_count | 房间数 |
| facilities | 设施服务 |
| booking_url | Booking.com URL |

## 使用方法

```bash
# 基本用法
PYTHONPATH=backend python3 -m backend.scripts.booking_scraper.main

# 指定城市
PYTHONPATH=backend python3 -m backend.scripts.booking_scraper.main --cities 上海 北京 杭州

# 每个城市限制数量
PYTHONPATH=backend python3 -m backend.scripts.booking_scraper.main --cities 上海 --max-per-city 5

# 非无头模式（显示浏览器）
PYTHONPATH=backend python3 -m backend.scripts.booking_scraper.main --headless false

# 调整请求延迟
PYTHONPATH=backend python3 -m backend.scripts.booking_scraper.main --delay 3 5

# 导出格式
PYTHONPATH=backend python3 -m backend.scripts.booking_scraper.main --format csv
```

## 爬虫流程

```
1. 启动 Playwright Chromium 浏览器
2. 访问 Booking.com 搜索页 (ss=Atour+城市)
3. 处理 consent 弹窗（Cookie 同意）
4. 解析搜索结果列表（酒店名称、URL、评分、地址）
5. 逐个进入酒店详情页获取完整信息
6. 处理分页（爬取多页结果）
7. 导出为 Excel/CSV 文件到 output/ 目录
```

## 关键技术点

### 1. URL 编码

搜索 URL 中的中文字符必须正确 URL 编码：

```python
import urllib.parse
query = "Atour 上海"
encoded_query = urllib.parse.quote(query)
url = f"{self.SEARCH_URL}?ss={encoded_query}"
# 结果: https://www.booking.com/searchresults.html?ss=Atour%20%E4%B8%8A%E6%B5%B7
```

### 2. Consent 弹窗处理

Booking.com 会重定向到 consent 页面，需要特殊处理：

1. 按 Escape 尝试关闭弹窗
2. 查找并点击"同意"按钮
3. 检查页面 URL 是否还在 consent 页面，如果是则再次点击确认

```python
if "pipl_consent" in self.page.url:
    buttons = await self.page.query_selector_all("button")
    for btn in buttons:
        text = await btn.inner_text()
        if "确认" in text or "同意" in text:
            await btn.click()
```

### 3. 酒店卡片解析

Booking.com 的搜索结果页面结构：

- 酒店卡片容器：`div[data-testid="property-card"]`
- 酒店名称：在链接文本中，格式为 `"酒店名\n在新窗口中打开"`
- Booking URL：`a[href*="/hotel/"]`
- 评分：在链接文本中包含"评分"字样
- 地址：在链接文本中包含"区/路/街"等关键词

```python
# 解析酒店卡片
links = await card.query_selector_all('a[href*="/hotel/"]')
for link in links:
    text = await link.inner_text()
    # 酒店名称包含中文且不包含特定排除文字
    if text and any('\u4e00' <= c <= '\u9fff' for c in text):
        if "在" not in text and "窗口" not in text:
            name = text.split('\n')[0]
```

### 4. 反爬策略

- 随机 User-Agent（Chrome/Safari 多版本）
- 请求间隔延迟（默认 2-5 秒）
- 禁用图片加载加速爬取
- 适当延长超时时间（60 秒）

### 5. 浏览器配置

```python
context = await self.browser.new_context(
    user_agent=random.choice(self.user_agents),
    viewport={"width": 1280, "height": 720},
    locale="zh-CN",
    geolocation={"latitude": 31.2304, "longitude": 121.4737},
    permissions=["geolocation"],
)
await self.page.set_extra_http_headers({
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
})
```

## 数据导出

导出的 Excel 文件包含以下列：

| 列名 | 宽度 |
|------|------|
| 酒店中文名 | 30 |
| 酒店英文名 | 35 |
| 城市 | 15 |
| 省份 | 15 |
| 国家代码 | 12 |
| 地址 | 40 |
| 电话 | 20 |
| 邮箱 | 30 |
| 纬度 | 12 |
| 经度 | 12 |
| 星级 | 10 |
| 入住时间 | 12 |
| 退房时间 | 12 |
| 房间数 | 10 |
| 设施服务 | 50 |
| Booking URL | 60 |
| 评分 | 10 |

输出文件保存在 `output/atour_hotels_YYYYMMDD_HHMMSS.xlsx`

## 注意事项

1. Booking.com 可能需要处理 Cookie consent 弹窗
2. 详情页爬取容易超时，建议增加延迟
3. 爬虫仅用于获取亚朵品牌数据，不要大规模爬取
4. 遵守 Booking.com 的 robots.txt 和使用条款
# CLI 翻译工具部署指南

> [!note] 目标读者
> 本文面向运维工程师和开发者，覆盖 CLI 翻译工具的部署、配置和故障排查。
> 命令用法和字段说明请参见 [CLI 使用手册](cli-translation-tool.md)。

---

## 1. 概述

### 1.1 工具定位

CLI 翻译工具 (`backend/scripts/translate_cli.py`) 是一个命令行程序，用于将中文酒店主数据批量翻译为英文并写回数据库。它共享 FastAPI 后端的翻译编排引擎 (`TranslationOrchestrator`)，因此 CLI 和 Web 端产出的翻译质量完全一致。

### 1.2 支持的部署拓扑

| 拓扑 | 说明 |
|------|------|
| **生产环境** | PostgreSQL + Redis，高并发高可用，适合日常运营和数据管道 |
| **开发环境** | SQLite 零配置启动，本地开发调试，无需安装外部服务 |
| **CI/CD 测试** | SQLite 内存数据库或临时文件，运行翻译测试无需持久化 |
| **离线部署** | SQLite 数据库 + SQLite 缓存，不依赖任何外部网络服务 |

### 1.3 与后端 FastAPI 服务的关系

CLI 工具**不经过 HTTP 层**。它直接连接数据库执行查询和写入，同时调用与 FastAPI 服务相同的翻译编排器。这意味着：

- CLI 不依赖后端服务进程运行。只要数据库可访问即可工作。
- 翻译缓存（Redis / SQLite）与 Web 端共享。CLI 写入的缓存可被后续 API 请求命中，反之亦然。
- 翻译历史记录 (`TranslationHistory`) 中 CLI 操作的 `operator_name` 固定为 `translate_cli`，与 Web 端用户操作区分开。

```
┌──────────────────────┐       ┌──────────────────────┐
│   CLI 翻译工具        │       │   FastAPI 后端服务    │
│   (translate_cli.py)  │       │   (app.main:app)      │
└──────────┬───────────┘       └──────────┬───────────┘
           │                              │
           │   共享 TranslationOrchestrator│
           │                              │
           v                              v
┌──────────────────────────────────────────────────────┐
│                  PostgreSQL / SQLite                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ hotels 表    │  │ rooms 表     │  │ translation_ │ │
│  │             │  │             │  │ cache 表      │ │
│  └─────────────┘  └─────────────┘  └──────────────┘ │
└──────────────────────────────────────────────────────┘
           │
           v
┌──────────────────┐     ┌──────────────────┐
│  Redis (可选)     │     │  腾讯云 MT API    │
│  翻译缓存         │     │  DeepSeek API     │
└──────────────────┘     └──────────────────┘
```

---

## 2. 环境依赖

### 2.1 必需组件

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11+ | 异步特性 (`asyncio`) 贯穿整个工具 |
| pip 依赖 | 见 `requirements.txt` | Typer, Rich, SQLAlchemy 2.0, loguru 等 |
| 腾讯云 MT 凭证 | - | `TENCENT_SECRET_ID` + `TENCENT_SECRET_KEY` |

### 2.2 可选组件

| 组件 | 用途 | 缺失时的影响 |
|------|------|-------------|
| **Redis** | 翻译缓存加速 | 自动降级到 SQLite 缓存，翻译速度略慢 |
| **PostgreSQL** | 生产数据库 | 可使用 SQLite 替代（开发/测试场景） |
| **DeepSeek API Key** | AI 翻译增强 | 使用 `--no-ai` 参数跳过，仅用机器翻译 |

### 2.3 安装命令

```bash
# 进入 backend 目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 可选：安装 Redis Python 客户端（已包含在 requirements.txt 中）
# pip install redis

# 复制环境配置模板
cp .env.example .env
```

---

## 3. 数据库配置

### 3.1 环境变量 `DATABASE_URL`

CLI 工具通过 `DATABASE_URL` 环境变量决定连接哪个数据库。支持 PostgreSQL 和 SQLite 两种后端。

**PostgreSQL（生产环境推荐）：**

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/expertie
```

**SQLite（开发 / CI/CD 推荐）：**

```bash
DATABASE_URL=sqlite+aiosqlite:///./expertie.db
```

### 3.2 数据库迁移

无论使用哪种数据库，都需要先执行 Alembic 迁移以创建表结构：

```bash
cd backend
alembic upgrade head
```

迁移会创建所有业务表（`hotels`, `rooms`, `room_extensions` 等）以及缓存表 `translation_cache`。

### 3.3 切换数据库类型

数据库切换只需修改 `.env` 文件中的 `DATABASE_URL` 一行，无需改动任何代码：

```bash
# 从 PostgreSQL 切换到 SQLite（开发测试）
# 注释掉原来的 PostgreSQL 行，启用 SQLite 行
DATABASE_URL=sqlite+aiosqlite:///./expertie.db
```

切换后重新执行迁移：

```bash
alembic upgrade head
```

### 3.4 SQLite 限制说明

SQLite 适用于开发和 CI/CD 场景，但在以下方面存在限制：

- **并发写入。** SQLite 同一时间只允许一个写入操作。`--concurrency` 参数设置过高时，写入可能因锁冲突失败。建议开发环境并发数不超过 3。
- **网络访问。** SQLite 是本地文件数据库，不支持远程连接。多台机器共享翻译缓存必须使用 PostgreSQL + Redis。
- **性能。** 大批量翻译（数千家酒店）时，PostgreSQL 的查询和写入性能明显优于 SQLite。

### 3.5 连接池配置

以下环境变量控制数据库连接池行为（仅对 PostgreSQL 生效，SQLite 忽略）：

```bash
# 连接池基础大小（默认 5）
DB_POOL_SIZE=5

# 超出 pool_size 后的最大溢出连接数（默认 10）
DB_MAX_OVERFLOW=10

# 连接回收时间，单位秒（默认 3600）
DB_POOL_RECYCLE=3600
```

---

## 4. 缓存配置

### 4.1 自动降级链

CLI 工具的翻译缓存采用责任链模式，按以下优先级自动选择后端：

```
Redis 可用  -->  使用 Redis 缓存（最快）
    │
    │ Redis 不可用
    v
SQLite 可用  -->  使用 SQLite 缓存（数据库表 translation_cache）
    │
    │ SQLite 也不可用
    v
无缓存       -->  继续运行但每次都调用翻译 API（最慢）
```

这个降级过程完全自动，不需要任何手动切换。工具启动时检测后端可用性，翻译过程中每个缓存读写操作也会逐级尝试。

### 4.2 Redis 缓存

Redis 是推荐的缓存后端，提供最快的读写性能。

**配置环境变量：**

```bash
# Redis 连接地址
REDIS_URL=redis://localhost:6379/0

# Redis 密码（可选，如果 Redis 设置了密码）
REDIS_PASSWORD=

# Redis 连接池大小（默认 10）
REDIS_POOL_SIZE=10
```

**Redis 不可用时的行为：**

- 工具启动时不报错，静默降级
- 日志中可能出现 `redis get failed` 的 warning 级别记录
- 翻译继续执行，缓存写入自动转到 SQLite

**验证 Redis 连通性：**

```bash
redis-cli -h localhost -p 6379 ping
# 预期输出: PONG
```

### 4.3 SQLite 缓存

当 Redis 不可用时，缓存数据写入数据库的 `translation_cache` 表。这个表在首次执行 `alembic upgrade head` 时自动创建。

**缓存表结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `cache_key` | String(128) | 缓存键，格式 `translation:zh:en:ai:md5hash` |
| `text` | Text | 原始中文文本 |
| `translated_text` | Text | 翻译后的英文文本 |
| `source_lang` | String(10) | 源语言（zh） |
| `target_lang` | String(10) | 目标语言（en） |
| `source` | String(20) | 翻译来源（MACHINE/AI_ENHANCED/CACHE/N/A） |
| `confidence` | Float | 置信度（0.0-1.0） |
| `metadata_json` | Text | 附加元数据 JSON |
| `created_at` | DateTime | 创建时间 |
| `ttl_expires_at` | DateTime | 过期时间 |

**缓存 TTL 配置：**

```bash
# 缓存过期时间，单位秒（默认 86400 = 24 小时）
TRANSLATION_CACHE_TTL=86400
```

### 4.4 缓存位置总结

| 缓存后端 | 存储位置 | 生命周期 | 跨进程共享 |
|----------|----------|----------|------------|
| Redis | Redis 服务器内存 | 受 TTL 控制，重启丢失（除非持久化） | 是 |
| SQLite | 数据库 `translation_cache` 表 | 受 TTL 控制，数据库文件持久化 | 是（同一数据库） |
| 无缓存 | 不存储 | 每次翻译实时调用 API | 不适用 |

### 4.5 缓存行为细节

- 缓存键包含源文本、语言对以及是否使用了 AI 增强。启用 AI 增强时的缓存条目不会在 `--no-ai` 模式下命中，反之亦然。
- 过期缓存条目不会被自动清理。SQLite 缓存的过期条目在查询时被过滤掉（WHERE `ttl_expires_at > now()`），但不删除物理行。如需清理，可使用 FAQ 中提供的方法。
- Redis 缓存的 TTL 由 Redis 自身管理，过期后自动删除。

---

## 5. 推荐场景配置

### 5.1 场景对照表

| 场景 | 数据库 | 缓存 | 并发建议 | 理由 |
|------|--------|------|----------|------|
| **生产环境** | PostgreSQL | Redis | 5-10 | 高并发写入安全，Redis 提供最快缓存响应，多实例共享缓存 |
| **开发环境** | SQLite | SQLite（自动） | 1-3 | 零外部依赖，`pip install` 后即可运行，SQLite 文件即数据库 |
| **CI/CD** | SQLite | 无缓存 | 1 | 每次运行全新环境，缓存无意义，翻译结果通过 `--dry-run` 验证 |
| **离线 / 隔离环境** | SQLite | SQLite | 1-3 | 无需 Redis、无需外网（缓存命中时），仅首次翻译需 API 访问 |

### 5.2 生产环境完整 `.env` 示例

```bash
# ===== 数据库 =====
DATABASE_URL=postgresql+asyncpg://expertie_user:strong_password@db.example.com:5432/expertie
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=1800

# ===== Redis 缓存 =====
REDIS_URL=redis://redis.example.com:6379/0
REDIS_PASSWORD=redis_strong_password
REDIS_POOL_SIZE=20

# ===== 腾讯云机器翻译 =====
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxx
TENCENT_REGION=ap-guangzhou

# ===== DeepSeek AI 增强 =====
AI_API_KEY=sk-xxxxxxxxxxxxxxxx
AI_API_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

# ===== 翻译设置 =====
TRANSLATION_CACHE_TTL=86400
TRANSLATION_MAX_RETRIES=3
TRANSLATION_TIMEOUT=30

# ===== 应用设置 =====
APP_ENV=production
LOG_LEVEL=INFO
```

### 5.3 开发环境完整 `.env` 示例

```bash
# ===== 数据库（SQLite 零配置） =====
DATABASE_URL=sqlite+aiosqlite:///./expertie.db

# ===== Redis（不配置，自动降级到 SQLite 缓存） =====
# REDIS_URL 留空或不设置，工具自动使用 SQLite 缓存

# ===== 腾讯云机器翻译 =====
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxx
TENCENT_REGION=ap-guangzhou

# ===== DeepSeek AI 增强 =====
AI_API_KEY=sk-xxxxxxxxxxxxxxxx
AI_API_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat

# ===== 应用设置 =====
APP_ENV=development
LOG_LEVEL=DEBUG
```

### 5.4 CI/CD 环境完整 `.env` 示例

```bash
# ===== 数据库（SQLite 临时文件） =====
DATABASE_URL=sqlite+aiosqlite:///./test_expertie.db

# ===== 无 Redis =====
# 不配置 REDIS_URL，翻译缓存不生效，每次实时调用 API

# ===== 腾讯云机器翻译 =====
TENCENT_SECRET_ID=${CI_TENCENT_SECRET_ID}
TENCENT_SECRET_KEY=${CI_TENCENT_SECRET_KEY}
TENCENT_REGION=ap-guangzhou

# ===== AI 增强（CI 中通常跳过以节省时间） =====
# 使用 --no-ai 参数运行，无需配置 AI_API_KEY

# ===== 应用设置 =====
APP_ENV=test
LOG_LEVEL=WARNING
```

CI 中典型运行命令：

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m scripts.translate_cli by-search "测试" --dry-run --no-ai --concurrency 1
```

### 5.5 离线环境完整 `.env` 示例

```bash
# ===== 数据库（SQLite 本地文件） =====
DATABASE_URL=sqlite+aiosqlite:///./expertie.db

# ===== 无 Redis =====
# 不配置 REDIS_URL

# ===== 腾讯云 MT（首次翻译需要，缓存命中后不需要） =====
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxx
TENCENT_REGION=ap-guangzhou

# ===== AI 增强（可选） =====
# AI_API_KEY=sk-xxxxxxxxxxxxxxxx

# ===== 应用设置 =====
APP_ENV=production
LOG_LEVEL=INFO
```

离线环境的工作模式：首次翻译时调用腾讯云 MT API 获取翻译结果并写入 SQLite 缓存。后续相同文本的翻译直接从 SQLite 缓存命中，不再需要外网访问。

---

## 6. 首次运行验证清单

按以下顺序执行 5 个验证步骤，确认部署环境正确。

### 步骤 1：检查 Python 版本

```bash
python --version
# 预期输出: Python 3.11.x 或更高版本
```

如果版本低于 3.11，需要升级 Python 后再继续。

### 步骤 2：安装依赖

```bash
cd backend
pip install -r requirements.txt
```

验证关键包已安装：

```bash
python -c "import typer, rich, sqlalchemy, loguru; print('All OK')"
# 预期输出: All OK
```

### 步骤 3：运行数据库迁移

```bash
alembic upgrade head
```

验证迁移状态：

```bash
alembic current
# 预期输出: 20260612_001 (head) 或更新的版本号
```

验证缓存表已创建：

```bash
# PostgreSQL
psql "$DATABASE_URL" -c "\d translation_cache"

# SQLite
sqlite3 expertie.db ".schema translation_cache"
```

### 步骤 4：运行翻译测试（试运行模式）

```bash
# 先查找一个存在的酒店 UUID
python -c "
import asyncio
from app.core.database import get_db_context
from app.models.hotel import Hotel
from sqlalchemy import select

async def main():
    async with get_db_context() as db:
        result = await db.execute(select(Hotel).limit(1))
        hotel = result.scalar_one_or_none()
        if hotel:
            print(f'Found hotel: {hotel.id}  {hotel.name_cn}')
        else:
            print('No hotels in database')

asyncio.run(main())
"

# 用查到的 UUID 执行试运行
python -m scripts.translate_cli by-id <上面输出的UUID> --dry-run --no-ai
```

预期结果：终端显示 Rich 格式的翻译预览表格，底部显示 `Dry run - no changes made to database.`。

### 步骤 5：验证缓存写入

执行一次正式翻译（不带 `--dry-run`），然后检查缓存是否写入：

```bash
# 执行翻译
python -m scripts.translate_cli by-id <UUID> --no-ai

# 验证缓存记录（PostgreSQL）
psql "$DATABASE_URL" -c "SELECT cache_key, source, ttl_expires_at FROM translation_cache ORDER BY created_at DESC LIMIT 5;"

# 验证缓存记录（SQLite）
sqlite3 expertie.db "SELECT cache_key, source, ttl_expires_at FROM translation_cache ORDER BY created_at DESC LIMIT 5;"
```

如果看到缓存记录，说明翻译缓存写入正常。

### 验证通过标志

五项验证全部通过后，环境部署完成。可以开始正式的批量翻译工作。命令用法参见 [CLI 使用手册](cli-translation-tool.md)。

---

## 7. 常见问题 (FAQ)

### Q1：Redis 连接失败怎么办？

Redis 是可选的。工具会自动降级到 SQLite 缓存，翻译功能不受影响。日志中可能出现 warning 级别记录，但不会报错退出。

如果希望排查 Redis 连接问题：

```bash
# 检查 Redis 服务是否运行
redis-cli ping

# 检查 REDIS_URL 格式是否正确
echo $REDIS_URL

# 检查防火墙 / 网络连通性
telnet <redis_host> 6379
```

### Q2：CLI 和后端服务可以共享数据库吗？

可以。CLI 和后端 FastAPI 服务使用完全相同的数据库 schema，共享所有业务数据和翻译缓存。但需要注意：

- 两者同时大量写入时，PostgreSQL 的行锁可能导致短暂的写入等待。这是正常的数据库并发行为。
- CLI 的并发参数 `--concurrency` 不宜设置过高，避免与 Web 端请求争抢数据库连接。
- 翻译缓存 (Redis / SQLite) 天然支持共享，一端写入的缓存可被另一端命中。

### Q3：如何清空翻译缓存？

**清空 Redis 缓存：**

```bash
redis-cli KEYS "translation:*" | xargs redis-cli DEL
```

**清空 SQLite 缓存：**

```bash
sqlite3 expertie.db "DELETE FROM translation_cache;"
```

**清空 PostgreSQL 缓存：**

```bash
psql "$DATABASE_URL" -c "DELETE FROM translation_cache;"
```

也可以通过 Python 代码调用 `TranslationCacheService.clear_all()`：

```python
import asyncio
from app.services.translation.cache_service import get_cache_service

async def main():
    service = get_cache_service()
    count = await service.clear_all()
    print(f"Cleared {count} cache entries")

asyncio.run(main())
```

### Q4：并发翻译时有死锁问题吗？

SQLite 在并发写入场景下可能出现 `database is locked` 错误，因为 SQLite 同一时间只允许一个写入操作。表现为部分酒店的翻译失败，摘要行中 `ERROR` 计数增加。

解决方案：

```bash
# 降低并发数
python -m scripts.translate_cli all-untranslated --concurrency 1

# 或者切换到 PostgreSQL
DATABASE_URL=postgresql+asyncpg://...
```

PostgreSQL 使用行级锁和 MVCC，并发写入安全。生产环境建议始终使用 PostgreSQL。

### Q5：翻译缓存会占用多少磁盘空间？

SQLite 缓存的 `translation_cache` 表中每条记录约 500 字节到 2KB（取决于文本长度）。以 10,000 条缓存记录计算，约占用 5-20 MB。

Redis 缓存的内存占用类似，但受 `maxmemory` 配置和淘汰策略控制。

如果缓存表过大，可以手动清理过期记录：

```bash
# SQLite
sqlite3 expertie.db "DELETE FROM translation_cache WHERE ttl_expires_at < datetime('now');"

# PostgreSQL
psql "$DATABASE_URL" -c "DELETE FROM translation_cache WHERE ttl_expires_at < NOW();"
```

### Q6：如何查看当前使用的是哪个缓存后端？

通过 Python 代码查询：

```python
import asyncio
from app.services.translation.cache_service import get_cache_service

async def main():
    service = get_cache_service()
    backend = await service.active_backend()
    stats = await service.get_stats()
    print(f"Active backend: {backend}")
    print(f"Stats: {stats}")

asyncio.run(main())
```

输出示例：

```
Active backend: redis
Stats: {'total_cached': 1523, 'backend': 'redis', 'ttl_seconds': 86400, ...}
```

### Q7：数据库迁移报错怎么办？

常见迁移错误及解决方法：

**错误：`relation "translation_cache" already exists`**

说明缓存表已经存在。可能之前手动创建过，或迁移执行了两次。

```bash
# 查看当前迁移状态
alembic current

# 如果显示版本已是最新但表不存在，手动标记版本
alembic stamp head
```

**错误：`Can't locate revision identified by 'xxx'`**

说明迁移链断裂。检查 `alembic/versions/` 目录下的迁移文件是否完整。

```bash
# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### Q8：CLI 工具可以部署为定时任务吗？

可以。典型用法是通过 cron 定时执行增量翻译：

```bash
# 每天凌晨 2 点翻译所有未翻译酒店
0 2 * * * cd /path/to/ex-pertie/backend && /path/to/venv/bin/python -m scripts.translate_cli all-untranslated --no-ai >> /var/log/translate.log 2>&1
```

建议在 cron 脚本中加入以下内容：

```bash
#!/bin/bash
set -e
cd /path/to/ex-pertie/backend
source venv/bin/activate

# 记录开始时间
echo "=== $(date) Start translation ==="

# 执行翻译
python -m scripts.translate_cli all-untranslated --no-ai --concurrency 5

echo "=== $(date) Done ==="
```

### Q9：腾讯云 MT API 调用失败如何排查？

按以下顺序检查：

1. 验证凭证是否正确设置：

```bash
echo $TENCENT_SECRET_ID
echo $TENCENT_SECRET_KEY
```

2. 检查 `.env` 文件是否在 `backend/` 目录下，且格式正确（无多余空格、引号）。

3. 测试 API 连通性：

```bash
curl -X POST "https://tmt.tencentcloudapi.com/" \
  -H "Content-Type: application/json" \
  -d '{"Action":"TextTranslate","Version":"2018-03-21","SourceText":"测试","Source":"zh","Target":"en"}'
```

4. 检查腾讯云控制台：API 密钥是否启用，账户余额是否充足，该 Region 是否开通了机器翻译服务。

### Q10：如何在一台新机器上快速部署开发环境？

```bash
# 1. 克隆项目
git clone <repo_url> && cd ex-pertie/backend

# 2. 创建虚拟环境并安装依赖
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. 配置环境变量（使用 SQLite 零配置方案）
cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./expertie.db
TENCENT_SECRET_ID=your_secret_id
TENCENT_SECRET_KEY=your_secret_key
TENCENT_REGION=ap-guangzhou
AI_API_KEY=your_deepseek_key
AI_API_BASE_URL=https://api.deepseek.com/v1
APP_ENV=development
LOG_LEVEL=DEBUG
EOF

# 4. 数据库迁移
alembic upgrade head

# 5. 验证
python -m scripts.translate_cli --help
```

以上 5 步完成后即可开始使用。如果暂时没有腾讯云凭证，可以跳过第 3 步中凭证相关的配置，先完成环境搭建，待凭证就绪后再补充。

---

## 附录 A：环境变量速查表

| 变量名 | 默认值 | 必需 | 说明 |
|--------|--------|------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./expertie.db` | 是 | 数据库连接地址 |
| `REDIS_URL` | `redis://localhost:6379/0` | 否 | Redis 连接地址 |
| `REDIS_PASSWORD` | 空 | 否 | Redis 密码 |
| `REDIS_POOL_SIZE` | `10` | 否 | Redis 连接池大小 |
| `DB_POOL_SIZE` | `5` | 否 | 数据库连接池大小（仅 PostgreSQL） |
| `DB_MAX_OVERFLOW` | `10` | 否 | 连接池溢出上限（仅 PostgreSQL） |
| `DB_POOL_RECYCLE` | `3600` | 否 | 连接回收时间（秒） |
| `TENCENT_SECRET_ID` | 空 | 是 | 腾讯云 API 密钥 ID |
| `TENCENT_SECRET_KEY` | 空 | 是 | 腾讯云 API 密钥 Key |
| `TENCENT_REGION` | `ap-shanghai` | 否 | 腾讯云 MT 服务区域 |
| `AI_API_KEY` | 空 | 否 | DeepSeek API Key |
| `AI_API_BASE_URL` | `https://api.deepseek.com/v1` | 否 | AI API 地址 |
| `AI_MODEL` | `deepseek-chat` | 否 | AI 模型名称 |
| `TRANSLATION_CACHE_TTL` | `86400` | 否 | 缓存过期时间（秒） |
| `TRANSLATION_MAX_RETRIES` | `3` | 否 | 翻译失败重试次数 |
| `TRANSLATION_TIMEOUT` | `30` | 否 | 翻译 API 超时（秒） |
| `APP_ENV` | `development` | 否 | 运行环境 |
| `LOG_LEVEL` | `DEBUG` | 否 | 日志级别 |

## 附录 B：相关文档

- [CLI 翻译工具使用手册](cli-translation-tool.md) -- 全部 5 个子命令的详细参考
- [CLI 翻译工具（中文版）](cli-translation-tool-zh.md) -- 中文版使用手册
- [后端 README](../backend/README.md) -- 后端服务开发指南
- [AGENTS.md](../AGENTS.md) -- 项目整体知识库

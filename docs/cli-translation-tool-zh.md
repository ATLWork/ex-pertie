# CLI 翻译工具

> [!info] 本文是 [CLI Translation Tool](cli-translation-tool.md) 的中文版本

> [!note] 目标读者
> 本文面向维护 Expedia 酒店数据管道的后端开发人员和运维工程师。完整覆盖 CLI 翻译工具的各项内容：架构设计、全部五个子命令、全部十三个可翻译字段、导出格式、错误恢复以及高级脚本化模式。

---

## 1. 概述

CLI 翻译工具（`backend/scripts/translate_cli.py`）是一个命令行工具，用于将中文酒店主数据批量翻译为英文，并可选择性地将结果写回 PostgreSQL 数据库。它构建在与 FastAPI Web 应用相同的 `TranslationOrchestrator`（翻译编排器）之上，因此通过 CLI 产生的翻译质量与通过 REST API 产生的翻译质量完全一致。

### 1.1 设计目标

- **批量优先。** 单次调用即可翻译一家酒店或数百家酒店。工具通过可配置的并行度并发处理酒店。
- **提交前预览。** 每次运行都会显示一个 Rich 格式的表格预览；可以使用 `--dry-run`（试运行）来检查结果而不触碰数据库。
- **错误隔离。** 某个字段或某家酒店的翻译失败不会阻塞批次中其余部分的处理。每家酒店独立处理。
- **按酒店逐条提交（Per-Hotel Commit）。** 每家酒店独立提交；批次中途的失败不会回滚已经持久化的酒店。这是核心的恢复保障。
- **可审计。** 每个字段的翻译都会记录为一条 `TranslationHistory`（翻译历史记录），操作人（operator_name）为 `translate_cli`，从而提供完整的审计记录。
- **可导出。** 结果可导出为 CSV 或 Excel 格式，用于离线审阅、与非技术相关人员共享或输入下游数据管道。

### 1.2 核心功能一览

| 功能 | 说明 |
|---|---|
| 5 个子命令 | `by-id`、`by-search`、`by-brand`、`by-filter`、`all-untranslated` |
| 13 个可翻译字段 | 酒店级（9）、房型级（2）、房型扩展级（2） |
| AI 增强 | DeepSeek 大语言模型对机器翻译结果进行后处理优化 |
| 翻译缓存 | Redis 后端，进程重启后依然有效 |
| 并发控制 | `--concurrency` 参数，默认 5 个工作线程 |
| 试运行模式 | 完整执行翻译流水线，但不写入数据库 |
| CSV 导出 | UTF-8 BOM 编码，7 列格式 |
| Excel 导出 | 带样式表头行，自动列宽 |
| 按酒店逐条提交 | 部分失败恢复保障 |
| 翻译历史 | 带操作人跟踪的审计记录 |
| 进度显示 | Rich 进度条，完成即消失 |

### 1.3 技术栈

| 组件 | 库 | 版本要求 |
|---|---|---|
| CLI 框架 | [Typer](https://typer.tiangolo.com/) | Latest（通过 requirements.txt） |
| 终端输出 | [Rich](https://rich.readthedocs.io/) | Latest |
| 并发 | `asyncio` + `asyncio.Semaphore` | Python 3.11+ 标准库 |
| 机器翻译 | 腾讯云 MT API | 不适用（云服务） |
| AI 增强 | DeepSeek 大语言模型 | 不适用（云服务） |
| 翻译缓存 | Redis（`TranslationCacheService`） | Redis 6+ |
| 数据库 ORM | SQLAlchemy 2.0（异步） | 2.0+ |
| 数据库驱动 | asyncpg | Latest |
| Excel 导出 | `openpyxl` | Latest |
| 日志 | loguru | Latest |

### 1.4 CLI 与 REST API 对比

| 维度 | CLI 工具 | REST API |
|---|---|---|
| 调用方式 | 命令行、cron、脚本 | HTTP 请求 |
| 认证 | `.env` 中的数据库凭证 | API Key 或会话令牌 |
| 批次大小 | 无限制（实际受约束） | 分页，通常最大 100 条 |
| 进度反馈 | Rich 进度条 + 表格预览 | 带状态的 JSON 响应 |
| 并发 | 每次调用使用 `asyncio.Semaphore` | 每次请求，由服务端管理 |
| 审计记录 | `TranslationHistory`，`operator_name="translate_cli"` | `TranslationHistory`，带用户 ID |
| 使用场景 | 批量操作、数据迁移、定时任务 | 交互式 UI、按需翻译 |

---

## 2. 架构

### 2.1 模块关系图

```
┌─────────────────────────────────────────────────────────────────────┐
│  translate_cli.py（Typer 应用，662 行）                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  by-id   │ │by-search │ │ by-brand │ │by-filter │ │all-untrans│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └─────────────┴────────────┴────────────┴────────────┘        │
│                              │                                       │
│                   _translate_workflow()                              │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         v                    v                    v                  │
│   Redis 初始化          BatchHotelTranslator    Rich 预览            │
│   （可选）              .translate_batch()      + CSV/Excel          │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               v
┌──────────────────────────────────────────────────────────────────────┐
│  BatchHotelTranslator（batch_translator.py，339 行）                  │
│                                                                      │
│  translate_batch(hotel_ids, db, concurrency, progress_callback)      │
│       │                                                              │
│       │  asyncio.gather()，使用 Semaphore(concurrency)               │
│       v                                                              │
│  translate_hotel(hotel_id, db)                                       │
│       │                                                              │
│       ├── 酒店字段（9）：  _translate_model_fields(HOTEL_FIELDS)      │
│       ├── 房型字段（2）：  _translate_model_fields(ROOM_FIELDS)       │
│       └── 扩展字段（2）：  _translate_model_fields(EXT_FIELDS)        │
│              │                                                       │
│              v                                                       │
│  _translate_field(orchestrator, text, db)                            │
│       │                                                              │
└───────┼──────────────────────────────────────────────────────────────┘
        │
        v
┌──────────────────────────────────────────────────────────────────────┐
│  TranslationOrchestrator（orchestrator.py，557 行）                   │
│                                                                      │
│  translate(text, source_lang, target_lang, use_cache, use_ai)        │
│       │                                                              │
│       ├── 步骤 1：检查 Redis 缓存                                    │
│       │     └── （命中）返回 CACHE 结果                               │
│       │                                                              │
│       ├── 步骤 2：术语替换（GlossaryService）                         │
│       │     └── 按术语长度降序排列                                    │
│       │                                                              │
│       ├── 步骤 3：参考库查询（BookingReferenceService）               │
│       │     └── 精确匹配 → 相似匹配 → 无结果                          │
│       │                                                              │
│       ├── 步骤 4：腾讯云 MT API                                       │
│       │     └── TencentTranslateClient.translate()                   │
│       │                                                              │
│       ├── 步骤 5：AI 增强（DeepSeek，可选）                           │
│       │     └── DeepSeekClient.enhance_translation()                 │
│       │                                                              │
│       ├── 步骤 6：将结果缓存到 Redis                                  │
│       │                                                              │
│       └── 返回：TranslationResult                                    │
│                                                                      │
│  依赖项（懒加载 Lazy-Load）：                                        │
│       ├── TranslationCacheService（Redis）                           │
│       ├── TencentTranslateClient（腾讯云）                            │
│       ├── DeepSeekClient（DeepSeek API）                              │
│       ├── GlossaryService（术语数据库）                                │
│       └── BookingReferenceService（参考数据库）                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流（详细）

对批次中的每家酒店，工具按以下顺序执行：

1. **查询酒店**，通过 `selectinload(Hotel.rooms)` 从 PostgreSQL 中预加载 `rooms` 关系。这样可以在一次数据库往返中加载酒店及其所有房型记录。

2. **提取 13 个中文源文本**，从 `Hotel`、`Room` 和 `RoomExtension` 模型中读取。字段映射常量 `HOTEL_FIELDS`、`ROOM_FIELDS` 和 `ROOM_EXTENSION_FIELDS` 定义了要读取的属性。

3. **翻译每个文本**，通过 `TranslationOrchestrator` 流水线处理。在每家酒店内部，所有 13 个字段通过 `asyncio.gather` 并行翻译。在酒店之间，并发度由 `asyncio.Semaphore` 控制。

4. **收集结果**，附带每个字段的元数据：翻译后文本、来源枚举（`CACHE` / `MACHINE` / `AI_ENHANCED` / `ERROR`）以及层级（`hotel` / `room` / `room_extension`）。房型和扩展字段以房型 UUID 作为前缀。

5. **渲染 Rich 表格**预览到终端，来源列使用颜色编码，文本截断以保证可读性。

6. **导出为 CSV/Excel**，如果设置了 `--export-csv` 或 `--export-excel` 参数。导出操作基于内存中的结果，因此在试运行模式下也能正常工作。

7. **提示确认**（除非使用 `--dry-run`）。用户必须输入 `y` 才能继续。任何其他输入都会取消操作。

8. **写入数据库**，采用按酒店逐条提交的方式。对每家酒店：
   - 在写入会话中重新加载酒店。
   - 加载 `RoomExtension` 记录以获取设施字段。
   - 调用 `update_hotel_fields()` 设置属性值。
   - 为每个字段创建 `TranslationHistory` 记录。
   - 仅对当前酒店执行 `await db.commit()`。
   - 出现异常时：仅对当前酒店执行 `await db.rollback()`，然后继续处理下一家。

### 2.3 TranslationOrchestrator 流水线（深入）

编排器对每个源文本执行七步流水线。理解这个流水线对于解读导出文件中的 `Source`（来源）列至关重要。

#### 步骤 1：Redis 缓存检查

```python
if use_cache:
    cached_result = await self.cache_service.get(
        text=original_text, source_lang=source_lang,
        target_lang=target_lang, use_ai_enhance=use_ai_enhance)
if cached_result:
    return TranslationResult(source=TranslationSource.CACHE, cached=True, ...)
```

缓存键包含源文本、语言对以及是否使用了 AI 增强。这意味着在启用 AI 增强时，使用 `--no-ai` 参数缓存的翻译结果**不会**被返回，反之亦然。每种组合都有独立的缓存条目。

缓存命中时：`source = "CACHE"`，`cached = True`。流水线在此停止。

#### 步骤 2：术语替换

```python
processed_text, terminology_matches = await self._apply_terminology_replacements(
    original_text, db, source_lang, target_lang)
```

术语表服务检索该语言对的所有活跃术语条目。术语按长度排序（最长优先），以防止部分替换。例如，如果"大床"和"高级大床房"都是术语表条目，则先匹配"高级大床房"。这是在机器翻译之前对中文源文本进行的预处理步骤。

如果未提供 `db` 会话（CLI 使用场景中不会出现），则跳过此步骤。

#### 步骤 3：参考库查询

```python
reference_data = await self._query_reference_library(
    original_text, db, source_lang, target_lang)
```

按顺序尝试两种查询策略：

1. **精确匹配：** `booking_reference_service.find_by_source_text()` 在参考库中查找完全相同的源文本。
2. **相似匹配：** 如果没有精确匹配，`find_similar()` 返回最多 3 条相似参考记录。使用最相关的一条。

每次成功查询都会增加对应参考记录的使用计数。参考数据（携程翻译、Booking.com 翻译、酒店名称）会作为上下文传递给 AI 增强步骤。

#### 步骤 4：腾讯云机器翻译

```python
mt_result = await self.tencent_client.translate(
    text=processed_text, source_lang=source_lang, target_lang=target_lang)
translated_text = mt_result.get("translated_text", "")
source = TranslationSource.MACHINE
```

这是核心翻译步骤。输入是步骤 2 中经过术语处理的文本。腾讯云 MT API 返回机器翻译的英文文本。

如果此步骤失败，编排器返回一个空的翻译结果：
```python
return TranslationResult(translated_text="", source=TranslationSource.MACHINE, ...)
```

#### 步骤 5：AI 增强（可选）

```python
if use_ai_enhance and translated_text:
    ai_result = await self.ai_client.enhance_translation(
        original_text=original_text,
        machine_translation=translated_text,
        source_lang=source_lang, target_lang=target_lang,
        context=enhancement_context)
    enhanced_text = ai_result.get("enhanced_text", translated_text)
    if enhanced_text and enhanced_text != translated_text:
        translated_text = enhanced_text
        source = TranslationSource.AI_ENHANCED
```

DeepSeek 大语言模型接收原始中文文本、机器翻译结果以及步骤 3 中的任何参考数据作为上下文。它可能会重写翻译，以提高流畅度、准确性和自然度。

如果 AI 产生的文本与 MT 输出完全一致，来源保持为 `MACHINE`。如果 AI 产生了不同的文本，来源变为 `AI_ENHANCED`。

如果 AI 调用失败（网络错误、API 错误、超时），异常会被捕获，MT 结果按原样使用：
```python
except Exception as e:
    logger.warning(f"AI enhancement failed, using MT result: {e}")
```

这在 CLI 中由 `--no-ai` 参数控制。

#### 步骤 6：缓存结果

```python
if use_cache and translated_text:
    await self.cache_service.set(
        text=original_text, translated_text=translated_text,
        source_lang=source_lang, target_lang=target_lang,
        source=source, use_ai_enhance=use_ai_enhance, metadata={...})
```

最终翻译（无论是来自缓存、MT 还是 AI）都会存入 Redis 以供后续缓存命中。

#### 步骤 7：返回 TranslationResult

```python
return TranslationResult(
    original_text=text, translated_text=translated_text,
    source_lang=source_lang, target_lang=target_lang,
    source=source, cached=False,
    booking_reference=reference_data.get("booking_translation"),
    ctrip_reference=reference_data.get("ctrip_translation"))
```

`TranslationResult` Pydantic 模型携带原始文本、翻译后文本、来源枚举、置信度分数（如有）、缓存状态和参考数据。

### 2.4 懒加载模式

`BatchHotelTranslator` 和 `TranslationOrchestrator` 都使用懒加载（Lazy-Load）初始化：

```python
class BatchHotelTranslator:
    def __init__(self):
        self._orchestrator = None

    def _get_orchestrator(self):
        if self._orchestrator is None:
            from app.services.translation.orchestrator import get_orchestrator
            self._orchestrator = get_orchestrator()
        return self._orchestrator
```

同样，`TranslationOrchestrator` 也懒加载其术语表服务和预订参考服务。这种模式确保 API 密钥、数据库连接和服务配置在导入时不需要。CLI 脚本可以在不触发任何网络调用的情况下被导入。

### 2.5 并发模型

工具使用两个层级的并发：

**第 1 层：酒店间并发（batch_translator.py）**
```python
semaphore = asyncio.Semaphore(concurrency)

async def _translate_one(hid):
    async with semaphore:
        result = await self.translate_hotel(hid, db)
        completed += 1
        if progress_callback:
            progress_callback(completed, total)
        return result

tasks = [_translate_one(hid) for hid in hotel_ids]
results = await asyncio.gather(*tasks)
```

信号量（Semaphore）确保最多同时处理 `concurrency` 家酒店。当一家酒店完成后，队列中的下一家酒店开始处理。

**第 2 层：酒店内部并发（batch_translator.py）**
```python
tasks = [self._translate_field(orchestrator, source_text, db) for ...]
raw_results = await asyncio.gather(*tasks)
```

在每家酒店内部，所有映射的字段并行翻译。对于拥有 3 个房型的酒店，这意味着最多 `9 + (3 * 2) + (3 * 2) = 21` 个并发字段翻译。这些字段级任务不受酒店级信号量的约束。

### 2.6 房型和房型扩展字段的键命名约定

房型和扩展字段使用冒号分隔的键格式，以避免与酒店级字段冲突。例如，`name_en` 同时存在于 `Hotel` 和 `Room` 上：

| 结果中的键 | 含义 |
|---|---|
| `name_en` | 酒店级 `name_en` |
| `<room_id>:name_en` | 房型 `<room_id>` 的 `name_en` |
| `<room_id>:amenities_en` | 房型 `<room_id>` 的 RoomExtension `amenities_en` |

`translate_cli.py` 中的 `get_original_text()` 辅助函数解析这些键：

```python
if ":" in field_key:
    room_id, field = field_key.split(":", 1)
    room = next((r for r in hotel.rooms if str(r.id) == room_id), None)
    # ... 访问房型或扩展属性 ...
else:
    # 酒店级字段
    cn_field = field_key.replace("_en", "_cn") if field_key.endswith("_en") else field_key
    return str(getattr(hotel, cn_field, "") or "")
```

---

## 3. 安装与环境

### 3.1 前置条件

| 组件 | 必需 | 备注 |
|---|---|---|
| Python 3.11+ | 是 | 全部使用异步特性 |
| PostgreSQL | 是 | 包含 Expedia 模式的数据库 |
| Redis | 否 | 可选；没有 Redis 工具也能工作 |
| 腾讯云 MT 凭证 | 是 | `TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY` |
| DeepSeek API Key | 否 | 仅在不使用 `--no-ai` 时需要 |
| openpyxl | 否 | 仅在使用 `--export-excel` 时需要 |

### 3.2 逐步安装

```bash
# 1. 进入 backend 目录
cd backend

# 2. 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装所有依赖
pip install -r requirements.txt

# 4. 复制并配置环境变量
cp .env.example .env
```

编辑 `.env` 填入实际值：

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/expedia_db

# Redis（可选）
REDIS_URL=redis://localhost:6379/0

# 腾讯云机器翻译
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxx
TENCENT_REGION=ap-guangzhou

# DeepSeek AI 增强（可选，不使用 --no-ai 时需要）
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 应用设置
APP_ENV=development
LOG_LEVEL=DEBUG
```

```bash
# 5. 执行数据库迁移
alembic upgrade head

# 6. 验证工具是否可用
python -m scripts.translate_cli --help
```

预期输出：

```
Usage: python -m scripts.translate_cli [OPTIONS] COMMAND [ARGS]...

 酒店主数据翻译工具 - Translate hotel master data from Chinese to English

Options:
  --help  Show this message and exit.

Commands:
  all-untranslated  Translate all hotels where name_en IS NULL
  by-brand          Translate hotels filtered by brand
  by-filter         Translate hotels by flexible filter conditions
  by-id             Translate a single hotel by its UUID
  by-search         Search and translate hotels by keyword
```

### 3.3 安装问题排查

**问题：`ModuleNotFoundError: No module named 'typer'`**
```bash
pip install typer rich
```

**问题：`ModuleNotFoundError: No module named 'app'`**
确保从 `backend/` 目录运行。脚本使用 `sys.path.insert(0, str(Path(__file__).parent.parent))` 将 backend 目录添加到 Python 路径中。

**问题：数据库连接被拒绝**
```bash
# 验证 PostgreSQL 是否运行
pg_isready

# 测试连接
psql "$DATABASE_URL" -c "SELECT 1"
```

**问题：腾讯云 API 返回认证错误**
验证 `.env` 中的 `TENCENT_SECRET_ID` 和 `TENCENT_SECRET_KEY` 是否正确设置。工具通过 `pydantic-settings` 读取这些变量，后者会自动加载 `.env` 文件。

**问题：Redis 连接被拒绝**
Redis 是可选的。当 Redis 不可用时，工具不打印任何警告。翻译继续执行但不使用缓存。如果需要 Redis，请确保其正在运行：
```bash
redis-cli ping  # 应返回 PONG
```

---

## 4. 快速入门

### 4.1 五个核心命令

```bash
# 命令 1：通过 UUID 翻译单个酒店
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000

# 命令 2：搜索并翻译匹配关键词的酒店
python -m scripts.translate_cli by-search "亚朵"

# 命令 3：翻译指定品牌的所有酒店
python -m scripts.translate_cli by-brand atour

# 命令 4：翻译满足多个筛选条件的酒店
python -m scripts.translate_cli by-filter --brand atour --city 上海 --status approved

# 命令 5：翻译所有缺少英文名称的酒店
python -m scripts.translate_cli all-untranslated
```

### 4.2 首次运行最佳实践

> [!tip] 始终从试运行开始
> 在写入数据库之前，先预览翻译结果：
> ```bash
> python -m scripts.translate_cli by-search "测试" --dry-run
> ```
>
> 试运行会执行完整的翻译流水线（包括 API 调用），但跳过数据库写入。先查看 Rich 表格预览，然后在不带 `--dry-run` 的情况下重新运行。

> [!tip] 从小规模开始
> 先用 `by-id` 对单个酒店进行翻译，以验证你的环境配置：
> ```bash
> # 从数据库中查找一个酒店 UUID
> psql -d yourdb -c "SELECT id, name_cn FROM hotels LIMIT 1;"
>
> # 翻译它
> python -m scripts.translate_cli by-id <上面查到的uuid> --dry-run
> ```

> [!tip] 导出以进行审阅
> 对于较大批次，导出为 Excel 以便离线审阅：
> ```bash
> python -m scripts.translate_cli by-brand atour --dry-run --export-excel review.xlsx
> # 在 Excel 中打开 review.xlsx 审阅，然后不带 --dry-run 重新运行
> ```

### 4.3 常见工作流模式

**模式 1：接入新品牌**
```bash
# 步骤 1：预览新品牌的所有酒店
python -m scripts.translate_cli by-brand zhotel --dry-run --export-excel zhotel_preview.xlsx

# 步骤 2：审阅 Excel 文件

# 步骤 3：执行（先纯机器翻译以追求速度）
python -m scripts.translate_cli by-brand zhotel --no-ai

# 步骤 4：用 AI 增强进行润色
python -m scripts.translate_cli by-brand zhotel
```

**模式 2：按城市分批迁移**
```bash
python -m scripts.translate_cli by-filter --city 上海 --no-ai --export-csv shanghai.csv
python -m scripts.translate_cli by-filter --city 北京 --no-ai --export-csv beijing.csv
python -m scripts.translate_cli by-filter --city 广州 --no-ai --export-csv guangzhou.csv
```

**模式 3：增量补齐**
```bash
# 翻译所有仍然缺少英文名称的酒店
python -m scripts.translate_cli all-untranslated --no-ai
```

---

## 5. 子命令参考

每个子命令均包含参数列表、SQL 查询逻辑、行为说明以及带注释的示例。

### 5.1 `by-id` —— 翻译单个酒店

通过 UUID 主键翻译一家酒店。

```
python -m scripts.translate_cli by-id <HOTEL_ID> [OPTIONS]
```

#### 参数

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `HOTEL_ID` | `str` | 是 | 酒店 UUID（36 字符字符串，如 `550e8400-e29b-41d4-a716-446655440000`） |

#### 查询逻辑

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.id == hotel_id)
)
result = await db.execute(stmt)
hotel = result.scalar_one_or_none()
```

使用精确 UUID 匹配。加载酒店并预加载 `rooms` 关系。

#### 行为

- **找到：** 进入 `_translate_workflow`，处理单家酒店。
- **未找到：** 以红色打印 `Hotel not found: <uuid>` 并退出，退出码（Exit Code）为 1。
- **单酒店，无批处理：** 由于只处理一家酒店，并发参数实际上没有影响。

#### 示例

```bash
# 基本用法：翻译并写入数据库
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000

# 试运行：仅预览，不写入
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 --dry-run

# 纯机器翻译：跳过 AI 增强
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 --no-ai

# 同时导出为 CSV 和 Excel
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 \
    --export-csv result.csv --export-excel result.xlsx

# 组合参数
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 \
    --dry-run --no-ai --export-csv preview.csv
```

#### 如何查找酒店 UUID

```bash
# 从 PostgreSQL 查询
psql -d expedia_db -c "SELECT id, name_cn, brand, city FROM hotels WHERE name_cn ILIKE '%亚朵%' LIMIT 10;"

# 从之前的 CSV 导出文件中获取（第一列是 Hotel ID）
head -3 previous_export.csv

# 从 REST API 获取
curl -s http://localhost:8000/api/v1/hotels?search=亚朵 | jq '.items[].id'
```

### 5.2 `by-search` —— 按关键词搜索

通过关键词搜索酒店（对 `name_cn` 或 `name_en` 进行部分匹配），并翻译所有匹配结果。

```
python -m scripts.translate_cli by-search <KEYWORD> [OPTIONS]
```

#### 参数

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `KEYWORD` | `str` | 是 | 用于部分匹配的搜索关键词 |

#### 查询逻辑

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(
        (Hotel.name_cn.ilike(f"%{keyword}%"))
        | (Hotel.name_en.ilike(f"%{keyword}%"))
    )
    .order_by(Hotel.updated_at.desc())
)
```

`ILIKE` 操作符提供不区分大小写的匹配。同时搜索 `name_cn` 和 `name_en`。结果按最近更新时间降序排列。

#### 行为

- **找到匹配：** 打印 `Found N hotel(s) matching '<keyword>'` 并进入 `_translate_workflow`。
- **未找到匹配：** 以红色打印 `No hotels found matching: <keyword>` 并退出，退出码为 1。
- **部分匹配：** 关键词 `"亚朵"` 可以匹配 `"上海亚朵酒店"`、`"亚朵X酒店"`、`"Atour Hotel"`（如果 `name_en` 包含 `亚朵`）等。
- **多个匹配：** 所有匹配的酒店在单个批次中翻译。

#### 示例

```bash
# 按中文关键词搜索
python -m scripts.translate_cli by-search "南京" --dry-run

# 按英文关键词搜索（匹配 name_en）
python -m scripts.translate_cli by-search "Atour" --dry-run

# 搜索并导出
python -m scripts.translate_cli by-search "西湖" --export-csv xihu_results.csv

# 搜索并以并发数 10 写入
python -m scripts.translate_cli by-search "北京" --concurrency 10
```

> [!warning] 宽泛关键词
> 搜索单个字符如"酒"（出现在"酒店"中）可能匹配数百家酒店。对宽泛搜索始终先使用 `--dry-run`。

### 5.3 `by-brand` —— 按品牌筛选

翻译属于特定品牌的所有酒店。

```
python -m scripts.translate_cli by-brand <BRAND> [OPTIONS]
```

#### 参数

| 参数 | 类型 | 必需 | 说明 |
|---|---|---|---|
| `BRAND` | `HotelBrand` | 是 | 品牌名称（通过 Typer 不区分大小写） |

#### 有效品牌值

| CLI 值 | 枚举常量 | 中文名称 | 说明 |
|---|---|---|---|
| `atour` | `HotelBrand.ATour` | 亚朵 | 标准亚朵酒店 |
| `atour_x` | `HotelBrand.ATourX` | 亚朵X | 亚朵X 酒店 |
| `zhotel` | `HotelBrand.ZHotel` | ZHotel | ZHotel 物业 |
| `ahaus` | `HotelBrand.Ahaus` | Ahaus | Ahaus 物业 |

#### 查询逻辑

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.brand == brand)
    .order_by(Hotel.updated_at.desc())
)
```

#### 行为

- **有效品牌：** 使用精确枚举匹配查询数据库，翻译所有结果。
- **无效品牌：** Typer 在任何数据库调用之前拒绝参数。产生 Typer 错误消息，列出有效值：
  ```
  Error: Invalid value for 'BRAND:{atour|atour_x|zhotel|ahaus}': 'invalid' is not one of 'atour', 'atour_x', 'zhotel', 'ahaus'.
  ```
  退出码为 2（Typer 参数解析错误）。
- **品牌下无酒店：** 打印 `No hotels found for brand: <value>` 并退出，退出码为 1。
- **不区分大小写：** `atour`、`Atour`、`ATOUR` 都映射到 `HotelBrand.ATour`。

#### 示例

```bash
# 翻译所有亚朵酒店
python -m scripts.translate_cli by-brand atour --dry-run

# 翻译所有亚朵X 酒店，纯机器翻译
python -m scripts.translate_cli by-brand atour_x --no-ai

# 翻译所有 ZHotel 物业并导出
python -m scripts.translate_cli by-brand zhotel --export-excel zhotel_$(date +%Y%m%d).xlsx

# 以高并发翻译所有 Ahaus 物业
python -m scripts.translate_cli by-brand ahaus --concurrency 15
```

### 5.4 `by-filter` —— 灵活多条件筛选

翻译满足品牌、城市、国家和状态筛选条件任意组合的酒店。至少需要指定一个筛选条件。

```
python -m scripts.translate_cli by-filter [OPTIONS]
```

#### 选项

| 选项 | 类型 | 默认值 | SQL 列 | 说明 |
|---|---|---|---|---|
| `--brand` | `HotelBrand` | None | `Hotel.brand` | 按品牌枚举筛选 |
| `--city` | `str` | None | `Hotel.city` | 按城市名称精确匹配 |
| `--country` | `str` | None | `Hotel.country_code` | 按国家代码筛选 |
| `--status` | `str` | None | `Hotel.status` | 按状态值筛选 |

#### 有效状态值

| CLI 值 | 枚举常量 | 说明 |
|---|---|---|
| `draft` | `HotelStatus.DRAFT` | 草稿酒店，尚未提交审核 |
| `pending_review` | `HotelStatus.PENDING_REVIEW` | 等待审核 |
| `approved` | `HotelStatus.APPROVED` | 审核已通过 |
| `published` | `HotelStatus.PUBLISHED` | 已发布到 Expedia |
| `suspended` | `HotelStatus.SUSPENDED` | 暂时停用 |

#### 查询逻辑

所有指定的筛选条件通过 `AND` 组合。WHERE 子句动态构建：

```python
conditions = []
if brand is not None:
    conditions.append(Hotel.brand == brand)
if city is not None:
    conditions.append(Hotel.city == city)
if country is not None:
    conditions.append(Hotel.country_code == country)
if status is not None:
    status_enum = HotelStatus(status)
    conditions.append(Hotel.status == status_enum)

for cond in conditions:
    stmt = stmt.where(cond)

stmt = stmt.order_by(Hotel.updated_at.desc())
```

#### 行为

- **无筛选条件：** 打印 `At least one filter is required (--brand, --city, --country, --status)` 并退出，退出码为 1。
- **无效状态：** 打印 `Invalid status: '<value>'. Valid values: draft, pending_review, approved, published, suspended` 并退出，退出码为 1。
- **无效品牌：** Typer 拒绝参数并列出有效值。
- **无匹配：** 打印 `No hotels found for filter: brand=atour, city=上海` 并退出，退出码为 1。
- **单个筛选条件：** 仅需一个筛选选项即可工作。
- **四个筛选条件全部使用：** 所有条件通过 AND 组合。

#### 示例

```bash
# 单个筛选条件：上海的所有酒店
python -m scripts.translate_cli by-filter --city 上海 --dry-run

# 单个筛选条件：所有已发布的酒店
python -m scripts.translate_cli by-filter --status published --dry-run

# 两个筛选条件：北京的亚朵酒店
python -m scripts.translate_cli by-filter --brand atour --city 北京 --dry-run

# 三个筛选条件：中国的已发布亚朵酒店
python -m scripts.translate_cli by-filter --brand atour --country CN --status published

# 四个筛选条件
python -m scripts.translate_cli by-filter \
    --brand atour_x --city 杭州 --country CN --status approved

# 仅按状态筛选（需要审核的草稿酒店）
python -m scripts.translate_cli by-filter --status draft --no-ai --export-csv drafts.csv

# 无效：未指定筛选条件
python -m scripts.translate_cli by-filter
# Error: At least one filter is required (--brand, --city, --country, --status)
```

> [!note] 城市筛选是精确匹配
> `--city 上海` 仅匹配 `city = '上海'` 的酒店。它**不**像 `by-search` 那样进行部分匹配。对于模糊的城市搜索，请使用 `by-search`。

### 5.5 `all-untranslated` —— 查找缺少英文名称的酒店

翻译所有 `name_en IS NULL` 的酒店。这是为全新数据集快速生成英文翻译或补齐遗漏翻译的最快方式。

```
python -m scripts.translate_cli all-untranslated [OPTIONS]
```

#### 查询逻辑

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.name_en.is_(None))
    .order_by(Hotel.updated_at.desc())
)
```

仅检查 `name_en IS NULL`。这是一种启发式方法：如果酒店没有英文名称，那么它的其他英文字段很可能也都没有填充。

#### 行为

- **找到酒店：** 打印 `Found N hotel(s) with missing English name` 并进入 `_translate_workflow`。
- **未找到酒店：** 打印 `All hotels already have English names. Nothing to translate.` 并以退出码 0（成功，非错误）退出。
- **无参数：** 此子命令不接受位置参数，仅接受标准的全局选项。

#### 示例

```bash
# 查看有多少酒店需要翻译
python -m scripts.translate_cli all-untranslated --dry-run

# 翻译所有未翻译酒店（纯机器翻译，追求速度）
python -m scripts.translate_cli all-untranslated --no-ai

# 翻译并导出
python -m scripts.translate_cli all-untranslated --export-csv bootstrap.csv

# 大批量时使用低并发
python -m scripts.translate_cli all-untranslated --concurrency 3
```

> [!note] 为什么只检查 `name_en`？
> `name_en IS NULL` 检查是一种快速的启发式方法。检查所有 13 个字段是否为 NULL 需要一个包含 13 个 OR 条件的复杂查询。在实践中，如果酒店的 `name_en` 为 NULL，那么这家酒店从未被翻译过。如果你需要查找特定字段缺失的酒店，请使用 `by-filter` 或直接执行 SQL 查询。

---

## 6. 全局参数

所有五个子命令都接受以下共享选项。这些选项在 `translate_cli.py` 中定义为模块级 `typer.Option` 默认值，并在所有子命令中一致应用。

### 6.1 `--dry-run`

```
--dry-run / --no-dry-run    （默认：False）
```

启用后，工具执行完整的翻译流水线（包括对腾讯云 MT 和 DeepSeek 的 API 调用）并显示 Rich 表格预览，但**跳过** `_translate_workflow` 第 5 阶段中的数据库写入步骤。

**试运行模式下会发生什么：**

1. Redis 初始化正常进行（可选，失败时忽略）。
2. 翻译 API 调用正常执行（真实的 API 使用，真实的费用）。
3. 显示 Rich 表格预览，包含完整结果。
4. 如果设置了 `--export-csv` 或 `--export-excel`，则生成 CSV/Excel 导出文件。
5. 跳过确认提示。
6. 跳过数据库写入。

终端输出以以下内容结尾：
```
Dry run - no changes made to database.
```

**使用场景：**

- 提交前预览翻译结果。
- 生成导出文件以供离线审阅。
- 测试 API 连通性和翻译质量。
- 对比机器翻译和 AI 增强翻译。

```bash
# 预览一个批次
python -m scripts.translate_cli by-brand atour --dry-run

# 导出以供审阅，不写入数据库
python -m scripts.translate_cli by-search "测试" --dry-run --export-excel review.xlsx
```

### 6.2 `--no-ai`

```
--no-ai / --no-no-ai    （默认：False）
```

禁用 DeepSeek AI 增强步骤（编排器流水线的步骤 5）。设置后，翻译仅来自腾讯云 MT API，仅应用术语替换和参考库查询。

**对流水线的影响：**

| 流水线步骤 | `--no-ai`（默认） | 设置 `--no-ai` |
|---|---|---|
| 步骤 1：缓存检查 | 是 | 是 |
| 步骤 2：术语替换 | 是 | 是 |
| 步骤 3：参考库查询 | 是 | 是 |
| 步骤 4：MT API | 是 | 是 |
| 步骤 5：AI 增强 | 是 | **跳过** |
| 步骤 6：缓存结果 | 是 | 是 |

**对 TranslationHistory 的影响：**

| 参数 | 历史记录中的 `translation_type` |
|---|---|
| （默认，AI 启用） | `HYBRID` |
| `--no-ai` | `MACHINE` |

**使用场景：**

- 速度优先的初始批量翻译。
- 成本敏感的操作（避免 DeepSeek API 的 Token 费用）。
- 独立测试机器翻译质量。
- 未配置 DeepSeek API Key 的环境。

```bash
# 快速的纯机器翻译
python -m scripts.translate_cli by-brand atour --no-ai

# 对比：纯机器 vs AI 增强
python -m scripts.translate_cli by-id <UUID> --no-ai --export-csv mt.csv
python -m scripts.translate_cli by-id <UUID> --export-csv hybrid.csv
diff <(cut -d',' -f6 mt.csv) <(cut -d',' -f6 hybrid.csv)
```

### 6.3 `--concurrency`

```
--concurrency INTEGER    （默认：5）
```

控制同时翻译的最大酒店数量。底层的 `BatchHotelTranslator` 使用 `asyncio.Semaphore(concurrency)` 来限制并发酒店翻译。

**并发如何工作：**

```python
semaphore = asyncio.Semaphore(concurrency)

async def _translate_one(hid):
    async with semaphore:
        result = await self.translate_hotel(hid, db)
        # ... 进度回调 ...
        return result

tasks = [_translate_one(hid) for hid in hotel_ids]
results = await asyncio.gather(*tasks)
```

在每家酒店内部，所有 13 个字段（加上房型和扩展字段）通过 `asyncio.gather` 并行翻译。这些字段级任务不受酒店级信号量的约束。对于拥有 3 个房型的酒店，这意味着每家酒店最多 21 个并发 API 调用。

**使用指南：**

| 并发数 | 使用场景 |
|---|---|
| 1 | 调试，逐步执行翻译 |
| 3 | 保守模式，数据库/API 负载低 |
| 5 | 默认值，适用于大多数环境 |
| 10 | 中等吞吐量，注意监控 API 速率限制 |
| 20 | 高吞吐量，确保有足够的数据库连接池 |

> [!warning] 并发数限制
> 设置过高的并发数可能：
> - 超出腾讯云 MT API 的速率限制（导致 `ERROR` 结果）
> - 耗尽数据库连接池槽位（导致连接错误）
> - 增加内存使用（所有酒店结果保存在内存中直到预览完成）
>
> 从默认值 5 开始，逐步增加，同时关注摘要行中的错误计数。

```bash
# 单线程调试
python -m scripts.translate_cli by-id <UUID> --concurrency 1

# 大批量时的激进模式
python -m scripts.translate_cli all-untranslated --concurrency 15
```

### 6.4 `--export-csv`

```
--export-csv PATH
```

将翻译结果导出到指定路径的 CSV 文件。文件使用 UTF-8 BOM（`utf-8-sig`）编码写入，以兼容 Microsoft Excel。

**CSV 格式（7 列）：**

| 列 | 内容 | 示例 |
|---|---|---|
| `Hotel ID` | 酒店 UUID | `550e8400-e29b-41d4-a716-446655440000` |
| `Hotel Name` | `name_cn` 值 | `上海亚朵酒店` |
| `Level` | `hotel`、`room` 或 `room_extension` | `hotel` |
| `Field` | 字段键 | `name_en` 或 `<room_id>:name_en` |
| `Original` | 中文源文本 | `上海亚朵酒店` |
| `Translated` | 英文翻译结果 | `Shanghai Atour Hotel` |
| `Source` | 翻译来源枚举 | `AI_ENHANCED` |

**实现：**

```python
def export_results_to_csv(results, hotels, output_path):
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Hotel ID", "Hotel Name", "Level", "Field",
                          "Original", "Translated", "Source"])
        for result in results:
            hotel = _find_hotel_by_id(hotels, result["hotel_id"])
            if not hotel:
                continue
            for field_key, field_info in result["fields"].items():
                original = get_original_text(hotel, field_key)
                writer.writerow([
                    str(hotel.id), hotel.name_cn,
                    field_info["level"], field_key,
                    original, field_info["translated"],
                    field_info["source"]
                ])
```

**示例输出：**

```
Hotel ID,Hotel Name,Level,Field,Original,Translated,Source
550e8400-...,上海亚朵酒店,hotel,name_en,上海亚朵酒店,Shanghai Atour Hotel,AI_ENHANCED
550e8400-...,上海亚朵酒店,hotel,address_en,浦东新区某路123号,No. 123 Some Road Pudong,CACHE
550e8400-...,上海亚朵酒店,room,abc123:name_en,豪华大床房,Deluxe King Room,MACHINE
550e8400-...,上海亚朵酒店,room_extension,abc123:amenities_en,空调;电视;WiFi,AC; TV; WiFi,CACHE
```

### 6.5 `--export-excel`

```
--export-excel PATH
```

将翻译结果导出到指定路径的 Excel（`.xlsx`）文件。需要 `openpyxl` 包（已包含在 `requirements.txt` 中）。

**Excel 格式：**

- 与 CSV 相同的 7 列。
- **工作表名称：** `Translations`
- **表头行：** 蓝色背景（`#4472C4`），白色粗体文字，居中对齐。
- **列宽：** 根据内容自动计算，最大不超过 80 字符。

**表头样式代码：**

```python
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF")
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")
```

**列宽代码：**

```python
for col in ws.columns:
    max_length = max(len(str(cell.value or "")) for cell in col)
    ws.column_dimensions[col_letter].width = min(max_length + 4, 80)
```

**错误处理：**

如果未安装 `openpyxl`：
```
Error: openpyxl is required for Excel export. Install with: pip install openpyxl
```
退出码：1。

```bash
python -m scripts.translate_cli by-filter --city 上海 --export-excel shanghai_$(date +%Y%m%d).xlsx
```

### 6.6 参数组合

所有全局参数可以自由组合：

```bash
# 完整组合：试运行、纯机器、高并发、双导出
python -m scripts.translate_cli by-brand atour \
    --dry-run --no-ai --concurrency 10 \
    --export-csv results.csv --export-excel results.xlsx

# 最小化：仅翻译并写入
python -m scripts.translate_cli by-id <UUID>

# 仅导出：不写数据库，只生成文件
python -m scripts.translate_cli by-search "测试" --dry-run --export-excel review.xlsx
```

---

## 7. 翻译字段参考

工具精确翻译 13 个字段，分布在三个数据库模型中。每个字段都有一个中文源列和一个英文目标列。字段映射在 `batch_translator.py` 中定义为模块级常量。

### 7.1 酒店级字段（9 个）

这些字段位于 `hotels` 表（`app/models/hotel.py` 中的 `Hotel` 模型）。

| # | 目标字段 | 源字段 | 列类型 | 可为空 | 说明 |
|---|---|---|---|---|---|
| 1 | `name_en` | `name_cn` | `String(255)` | 否 | 酒店名称 |
| 2 | `address_en` | `address_cn` | `String(500)` | 否 | 街道地址 |
| 3 | `cancellation_policy_en` | `cancellation_policy` | `Text` | 是 | 取消政策 |
| 4 | `prepayment_policy_en` | `prepayment_policy` | `Text` | 是 | 预付政策 |
| 5 | `kid_policy_en` | `kid_policy` | `Text` | 是 | 儿童政策 |
| 6 | `pet_policy_en` | `pet_policy` | `Text` | 是 | 宠物政策 |
| 7 | `services_en` | `services` | `Text` | 是 | 酒店服务 |
| 8 | `facilities_en` | `facilities` | `Text` | 是 | 酒店设施 |
| 9 | `description_en` | `description` | `Text` | 是 | 酒店描述 |

**代码中的字段映射：**

```python
HOTEL_FIELDS: Dict[str, str] = {
    "name_en": "name_cn",
    "address_en": "address_cn",
    "cancellation_policy_en": "cancellation_policy",
    "prepayment_policy_en": "prepayment_policy",
    "kid_policy_en": "kid_policy",
    "pet_policy_en": "pet_policy",
    "services_en": "services",
    "facilities_en": "facilities",
    "description_en": "description",
}
```

**酒店字段的翻译过程：**

```python
hotel_fields, hotel_errors = await self._translate_model_fields(
    orchestrator, hotel, HOTEL_FIELDS, db, level="hotel"
)
all_fields.update(hotel_fields)
```

结果中每个字段的键是目标列名（例如 `name_en`），而非源列名。`level` 始终为 `"hotel"`。

> [!note] 源字段命名不一致
> 酒店级的政策字段（`cancellation_policy`、`prepayment_policy`、`kid_policy`、`pet_policy`）**没有** `_cn` 后缀。`HOTEL_FIELDS` 映射将每个 `_en` 目标映射到精确的数据库列名。CLI 中的 `get_original_text()` 辅助函数处理这种情况：
> ```python
> cn_field = field_key.replace("_en", "_cn") if field_key.endswith("_en") else field_key
> ```
> 对于 `cancellation_policy_en`，这首先产生 `cancellation_policy_cn`，然后回退到 `cancellation_policy`，因为 `_cn` 在模型上不存在。

### 7.2 房型级字段（2 个）

这些字段位于 `rooms` 表（`app/models/hotel.py` 中的 `Room` 模型）。

| # | 目标字段 | 源字段 | 列类型 | 可为空 | 说明 |
|---|---|---|---|---|---|
| 10 | `name_en` | `name_cn` | `String(255)` | 否 | 房型名称 |
| 11 | `description_en` | `description_cn` | `Text` | 是 | 房型描述 |

**代码中的字段映射：**

```python
ROOM_FIELDS: Dict[str, str] = {
    "name_en": "name_cn",
    "description_en": "description_cn",
}
```

**房型字段的翻译过程：**

```python
if hotel.rooms:
    for room in hotel.rooms:
        room_fields, room_errors = await self._translate_model_fields(
            orchestrator, room, ROOM_FIELDS, db, level="room"
        )
        for key, value in room_fields.items():
            all_fields[f"{room.id}:{key}"] = value
```

**键前缀：** 结果字典中的房型字段键以房型 UUID 为前缀，以避免与酒店级字段冲突。例如：

| 结果键 | 含义 |
|---|---|
| `name_en` | 酒店 `name_en`（level: hotel） |
| `abc123-def456:name_en` | 房型 `abc123-def456` 的 `name_en`（level: room） |
| `abc123-def456:description_en` | 房型 `abc123-def456` 的 `description_en`（level: room） |

### 7.3 房型扩展级字段（2 个）

这些字段位于 `room_extensions` 表（`app/models/room.py` 中的 `RoomExtension` 模型）。

| # | 目标字段 | 源字段 | 列类型 | 可为空 | 说明 |
|---|---|---|---|---|---|
| 12 | `amenities_en` | `amenities_cn` | `Text` | 是 | 房型设施 |
| 13 | `bathroom_amenities_en` | `bathroom_amenities_cn` | `Text` | 是 | 浴室设施 |

**代码中的字段映射：**

```python
ROOM_EXTENSION_FIELDS: Dict[str, str] = {
    "amenities_en": "amenities_cn",
    "bathroom_amenities_en": "bathroom_amenities_cn",
}
```

**扩展字段的翻译过程：**

```python
if room_ids:
    ext_stmt = select(RoomExtension).where(RoomExtension.room_id.in_(room_ids))
    ext_result = await db.execute(ext_stmt)
    extensions = ext_result.scalars().all()

    for ext in extensions:
        ext_fields, ext_errors = await self._translate_model_fields(
            orchestrator, ext, ROOM_EXTENSION_FIELDS, db, level="room_extension"
        )
        for key, value in ext_fields.items():
            all_fields[f"{ext.room_id}:{key}"] = value
```

**键前缀：** 与房型字段类似，扩展字段键以房型 UUID 为前缀：

| 结果键 | 含义 |
|---|---|
| `abc123-def456:amenities_en` | 房型 `abc123-def456` 的 RoomExtension `amenities_en` |
| `abc123-def456:bathroom_amenities_en` | 房型 `abc123-def456` 的 RoomExtension `bathroom_amenities_en` |

> [!note] RoomExtension 加载方式
> RoomExtensions 不会随酒店查询预加载。它们在 `translate_hotel()` 中收集房型 ID 后单独加载：
> ```python
> ext_stmt = select(RoomExtension).where(RoomExtension.room_id.in_(room_ids))
> ```
> 这是因为 SQLAlchemy 中没有从 `Room` 到 `RoomExtension` 的关系（`RoomExtension` 上的 `room` 关系在模型中被注释掉了）。

### 7.4 字段结果结构

结果字典中每个已翻译字段具有以下结构：

```python
{
    "translated": str,    # 英文翻译文本
    "source": str,        # "CACHE" | "MACHINE" | "AI_ENHANCED" | "ERROR" | "N/A"
    "level": str,         # "hotel" | "room" | "room_extension"
}
```

`level` 决定导出文件中 `Level` 列的值，纯粹用于分类。它不影响翻译过程。

### 7.5 来源枚举值

| 来源 | 含义 | 出现时机 |
|---|---|---|
| `CACHE` | 结果从 Redis 缓存中检索 | 编排器步骤 1 中缓存命中 |
| `MACHINE` | 结果来自腾讯云 MT API | MT 成功，未使用 AI 增强或 AI 产生了相同文本 |
| `AI_ENHANCED` | MT 结果经 DeepSeek AI 改进 | AI 增强产生了不同的文本 |
| `ERROR` | 翻译失败 | API 错误、网络错误或异常 |
| `N/A` | 没有可翻译的内容 | 源文本为空或仅包含空白字符 |

### 7.6 空/Null 源文本处理

当源字段为空（None 或仅包含空白字符）时，`_translate_field` 直接返回，不调用任何翻译 API：

```python
if not text or not text.strip():
    return (text or "", "N/A")
```

`N/A` 来源表示该字段没有内容。这些字段仍然包含在结果字典中（以原始空文本作为"翻译"值），并在导出中显示来源为 `N/A`。在数据库写入阶段，它们不会生成 `TranslationHistory` 记录：

```python
original_text = get_original_text(hotel, field_key)
if not original_text or not original_text.strip():
    continue  # 跳过 TranslationHistory 创建
```

### 7.7 完整字段计数示例

对于拥有 2 个房型的酒店，字段翻译总数为：

```
酒店字段：         9
房型 1 字段：      2
房型 2 字段：      2
房型 1 扩展字段：  2
房型 2 扩展字段：  2
                 ----
总计：            17 个字段
```

这 17 个字段中的每一个都会在 CSV/Excel 导出中产生一行，并且（如果不为空）产生一条 `TranslationHistory` 记录。

---

## 8. 导出格式

### 8.1 Rich 表格预览

每次运行都会在任何数据库写入之前在终端中显示一个 Rich 格式的表格。这是交互式使用的主要审阅机制。

#### 表格列

| 列 | 样式 | 宽度 | 说明 |
|---|---|---|---|
| `#` | `dim`，右对齐 | 4 | 每家酒店的行号 |
| `Hotel` | `cyan`，`no_wrap` | 自动 | 酒店 `name_cn` |
| `Field` | `green` | 自动 | 字段键 |
| `Original (CN)` | `yellow` | 最大 50 字符 | 截断的中文源文本 |
| `Translated (EN)` | `magenta` | 最大 50 字符 | 截断的英文翻译 |
| `Source` | 颜色编码 | 12 | 翻译来源 |
| `Status` | `bold` | 8 | 对勾或错误指示 |

#### 来源列颜色

| 来源值 | Rich 样式字符串 | 视觉效果 |
|---|---|---|
| `CACHE` | `[dim]CACHE[/dim]` | 灰色/变暗文本 |
| `MACHINE` | `[blue]MACHINE[/blue]` | 蓝色文本 |
| `AI_ENHANCED` | `[green]AI_ENHANCED[/green]` | 绿色文本 |
| `ERROR` | `[red]✗ {error_message}[/red]` | 红色文本，带错误信息 |
| （其他） | 普通文本 | 默认颜色 |

`_translate_workflow` 中的颜色逻辑：

```python
if source_value == "CACHE":
    source_display = "[dim]CACHE[/dim]"
elif source_value == "MACHINE":
    source_display = "[blue]MACHINE[/blue]"
elif source_value == "AI_ENHANCED":
    source_display = "[green]AI_ENHANCED[/green]"
else:
    source_display = source_value
```

#### 文本截断

`Original (CN)` 和 `Translated (EN)` 列均截断为 50 字符：

```python
def _truncate(text: str, max_len: int = 50) -> str:
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text
```

这样可以在显示长政策文本和描述时保持表格可读性。完整文本可在 CSV/Excel 导出中获取。

#### 错误行显示

当字段翻译失败时，会显示一个错误行：

```
│   1 │ 上海亚朵酒店 │ ERROR        │                  │                  │ ✗ Translation failed for name_en │
```

错误行跨越全宽并以红色显示。酒店名称和行号仍然显示以提供上下文。

#### 摘要行

表格之后，会显示一行摘要统计：

```
Summary: 3 hotels, 39 fields translated, 2 errors
```

- 绿色：酒店数量和字段数量。
- 红色（如果 > 0）：错误数量。

#### 完整输出示例

```
         Translation Preview
┌─────┬──────────────┬──────────────────┬──────────────────────┬──────────────────────┬──────────────┬────────┐
│   # │ Hotel        │ Field            │ Original (CN)        │ Translated (EN)      │ Source       │ Status │
├─────┼──────────────┼──────────────────┼──────────────────────┼──────────────────────┼──────────────┼────────┤
│   1 │ 上海亚朵酒店 │ name_en          │ 上海亚朵酒店         │ Shanghai Atour Hotel │ AI_ENHANCED  │ ✓      │
│     │              │ address_en       │ 上海市浦东新区...     │ Pudong New Area,...  │ CACHE        │ ✓      │
│     │              │ cancellation_... │ 入住前24小时可免费取消 │ Free cancellation... │ MACHINE      │ ✓      │
│     │              │ prepayment_po... │ 需预付全额房费        │ Full prepayment...   │ MACHINE      │ ✓      │
│     │              │ kid_policy_en    │ 12岁以下儿童免费入住   │ Children under 12... │ AI_ENHANCED  │ ✓      │
│     │              │ pet_policy_en    │                       │                      │ N/A          │ ✓      │
│     │              │ services_en      │ 洗衣服务;叫醒服务     │ Laundry; Wake-up...  │ CACHE        │ ✓      │
│     │              │ facilities_en    │ 健身房;游泳池         │ Gym; Swimming pool   │ CACHE        │ ✓      │
│     │              │ description_en   │ 酒店位于上海市中心...  │ The hotel is loca... │ AI_ENHANCED  │ ✓      │
│     │              │ abc123:name_en   │ 豪华大床房            │ Deluxe King Room     │ MACHINE      │ ✓      │
│     │              │ abc123:descri... │ 宽敞舒适的客房...      │ Spacious and comf... │ MACHINE      │ ✓      │
│     │              │ abc123:amenit... │ 空调;电视;WiFi        │ AC; TV; WiFi         │ CACHE        │ ✓      │
│     │              │ abc123:bathro... │ 淋浴;吹风机           │ Shower; Hair dryer   │ CACHE        │ ✓      │
└─────┴──────────────┴──────────────────┴──────────────────────┴──────────────────────┴──────────────┴────────┘

Summary: 1 hotels, 13 fields translated

Apply translations to database? [y/N]:
```

### 8.2 CSV 导出格式

**文件编码：** UTF-8 带 BOM（`utf-8-sig`）。

BOM（字节顺序标记）确保 Microsoft Excel 在打开文件时正确检测 UTF-8 编码。没有 BOM，Excel 可能会错误解读中文字符。

**表头行：**
```
Hotel ID,Hotel Name,Level,Field,Original,Translated,Source
```

**数据行：** 每个翻译字段一行。对于拥有 N 个房型的酒店：

```
总行数 = 1（表头）+ 9（酒店字段）+ (N * 2)（房型字段）+ (N * 2)（扩展字段）
```

**CSV 内容示例：**
```csv
Hotel ID,Hotel Name,Level,Field,Original,Translated,Source
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,hotel,name_en,上海亚朵酒店,Shanghai Atour Hotel,AI_ENHANCED
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,hotel,address_en,上海市浦东新区某路123号,"No. 123 Some Road, Pudong New Area, Shanghai",CACHE
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,hotel,cancellation_policy_en,入住前24小时可免费取消,Free cancellation up to 24 hours before check-in,MACHINE
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,hotel,prepayment_policy_en,需预付全额房费,Full prepayment required,MACHINE
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,hotel,kid_policy_en,12岁以下儿童免费入住,Children under 12 stay free,AI_ENHANCED
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,hotel,pet_policy_en,,,N/A
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,room,abc123-def456:name_en,豪华大床房,Deluxe King Room,MACHINE
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,room,abc123-def456:description_en,宽敞舒适的客房,Spacious and comfortable room,MACHINE
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,room_extension,abc123-def456:amenities_en,"空调;电视;WiFi","AC; TV; WiFi",CACHE
550e8400-e29b-41d4-a716-446655440000,上海亚朵酒店,room_extension,abc123-def456:bathroom_amenities_en,"淋浴;吹风机","Shower; Hair dryer",CACHE
```

**CSV 格式注意事项：**
- 包含逗号的字段会被 Python 的 `csv.writer` 正确引用。
- `Hotel Name` 列始终使用 `name_cn`，无论 `name_en` 是否存在。
- 空字段在 CSV 中显示为两个连续逗号。
- 房型和扩展字段键包含房型 UUID 以便追溯。

### 8.3 Excel 导出格式

**文件格式：** `.xlsx`（Office Open XML 电子表格）

**工作表名称：** `Translations`

**表头行样式：**

| 属性 | 值 |
|---|---|
| 背景色 | `#4472C4`（中蓝色） |
| 字体颜色 | `#FFFFFF`（白色） |
| 字体粗细 | 粗体 |
| 水平对齐 | 居中 |

**数据行：** 不应用特殊样式。

**列宽：** 根据每列中最长内容自动计算，最大不超过 80 字符：

```python
max_length = max(len(str(cell.value or "")) for cell in col)
ws.column_dimensions[col_letter].width = min(max_length + 4, 80)
```

`+ 4` 添加填充，使文本不会紧贴列边缘。80 字符的上限防止长政策文本导致列过宽。

**Excel 结构示例：**

| Hotel ID (A) | Hotel Name (B) | Level (C) | Field (D) | Original (E) | Translated (F) | Source (G) |
|---|---|---|---|---|---|---|
| *（蓝色表头行，白色粗体文字）* |
| 550e... | 上海亚朵酒店 | hotel | name_en | 上海亚朵酒店 | Shanghai Atour Hotel | AI_ENHANCED |
| 550e... | 上海亚朵酒店 | hotel | address_en | 浦东新区... | Pudong New Area... | CACHE |

**Excel 导出的错误处理：**

```python
try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:
    console.print("[red]Error: openpyxl is required for Excel export...[/red]")
    raise typer.Exit(1)
```

如果未安装 `openpyxl`，工具打印清晰的错误信息并以退出码 1 退出。不会创建不完整的文件。

---

## 9. 工作流详情

`translate_cli.py` 中的 `_translate_workflow` 函数是所有五个子命令的共享执行路径。它经历五个不同的阶段。

### 阶段 1：Redis 初始化（可选）

```python
try:
    from app.core.redis import RedisService
    await RedisService.init()
    RedisService.get_client()
except Exception:
    pass
```

Redis 在工作流开始时初始化一次。如果 Redis 不可用（连接被拒绝、错误的 URL、未安装），异常会被静默捕获，工作流继续执行。翻译仍然通过直接 API 调用工作；缓存仅在此次调用中被禁用。

**为什么 Redis 初始化与编排器分离：**
编排器懒加载其 `TranslationCacheService`，后者又连接到 Redis。CLI 中的显式初始化确保 Redis 在任何翻译调用之前就绪，避免每次调用的连接开销。

### 阶段 2：翻译

```python
async with get_db_context() as db:
    translator = BatchHotelTranslator()
    with Progress(transient=True) as progress:
        task_id = progress.add_task("[cyan]Translating...", total=len(hotel_ids))
        def on_progress(done, total):
            progress.update(task_id, completed=done)
        results = await translator.translate_batch(
            hotel_ids, db, concurrency=concurrency, progress_callback=on_progress)
```

关键细节：

- 通过 `get_db_context()` 创建新的数据库会话。
- `BatchHotelTranslator` 全新实例化（不携带之前调用的状态）。
- Rich `Progress` 进度条显示 `Translating...` 及完成百分比。
- `transient=True` 表示进度条在完成后消失，只保留结果表格可见。
- `progress_callback` 在每家酒店完成后被调用（无论成功或失败），更新进度条。
- `translate_batch` 返回结果字典列表，每家酒店一个。

**`translate_batch` 内部发生什么：**

```python
semaphore = asyncio.Semaphore(concurrency)
completed = 0
total = len(hotel_ids)

async def _translate_one(hid):
    async with semaphore:
        try:
            result = await self.translate_hotel(hid, db)
            return result
        except Exception as exc:
            return {"hotel_id": hid, "fields": {}, "errors": [f"Unexpected error: {exc}"]}
        finally:
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

tasks = [_translate_one(hid) for hid in hotel_ids]
results = await asyncio.gather(*tasks)
```

### 阶段 3：Rich 表格预览

工具构建一个 `rich.table.Table`，标题为 `"Translation Preview"`，并遍历结果来填充行。

对每个酒店结果：
1. 通过 `hotel_id` 在 `hotels_for_display` 中查找酒店。
2. 如果存在错误，添加错误行（每个错误一行）。
3. 对每个字段，添加一个带颜色编码来源的数据行。

表格通过 `console.print(table)` 打印到控制台。

表格之后，打印摘要行：

```python
summary_parts = [f"{len(results)} hotels, {total_fields} fields translated"]
if total_errors:
    summary_parts.append(f"[red]{total_errors} errors[/red]")
console.print(f"\n[bold]Summary:[/bold] {', '.join(summary_parts)}")
```

### 阶段 4：导出（如果请求）

```python
if export_csv:
    export_results_to_csv(results, hotels_for_display, export_csv)
if export_excel:
    export_results_to_excel(results, hotels_for_display, export_excel)
```

两种导出都基于内存中的 `results` 列表生成，而非从数据库读取。这意味着：
- 导出在 `--dry-run` 模式下也可用。
- 导出精确反映 Rich 表格预览中显示的内容。
- 失败的字段（来源 `ERROR`）在导出中显示，翻译文本为空。

成功消息以绿色打印：
```
✓ CSV exported to /path/to/file.csv
✓ Excel exported to /path/to/file.xlsx
```

### 阶段 5：数据库写入（非试运行模式）

这是最复杂的阶段。仅当**未**设置 `--dry-run` 时运行。

#### 5a. 错误警告

```python
if not dry_run:
    if total_errors > 0:
        console.print("[yellow]⚠ There are translation errors. Review carefully before applying.[/yellow]")
```

如果有任何字段翻译失败（来源 `ERROR`），会显示黄色警告。鼓励用户审阅，但仍可继续。

#### 5b. 确认提示

```python
if not typer.confirm("\nApply translations to database?"):
    console.print("[yellow]Cancelled. No changes were made.[/yellow]")
    return
```

提示显示 `Apply translations to database? [y/N]:`。用户必须输入 `y`（或 `yes`）并按 Enter。任何其他输入（包括直接按 Enter）都会取消操作。不会对数据库做任何更改。

> [!warning] 非交互式环境
> `typer.confirm()` 调用从标准输入读取。在 CI/CD 管道或定时任务中，这会一直挂起等待输入。通过管道传入 `yes` 来处理：
> ```bash
> yes | python -m scripts.translate_cli by-brand atour --no-ai
> ```

#### 5c. 在写入会话中重新加载酒店

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.id.in_(hotel_ids))
)
r = await db.execute(stmt)
hotels_in_session = list(r.scalars().all())
hotel_map = {str(h.id): h for h in hotels_in_session}
```

酒店在写入会话中重新查询，以确保 ORM 对象附加到当前会话。`hotel_map` 字典提供按酒店 ID 的 O(1) 查找。

#### 5d. 加载 RoomExtensions

```python
all_room_ids = []
for h in hotels_in_session:
    for room in h.rooms:
        all_room_ids.append(room.id)

ext_map = {}
if all_room_ids:
    ext_stmt = select(RoomExtension).where(RoomExtension.room_id.in_(all_room_ids))
    ext_result = await db.execute(ext_stmt)
    for ext in ext_result.scalars().all():
        ext_map[ext.room_id] = ext
```

RoomExtensions 单独加载，并按 `room_id` 索引，以便在字段写入期间高效查找。`ext_map` 传递给 `update_hotel_fields()`。

#### 5e. 确定翻译类型

```python
translation_type = TranslationType.MACHINE if no_ai else TranslationType.HYBRID
```

存储在 `TranslationHistory` 中的翻译类型取决于 `--no-ai` 参数。

#### 5f. 按酒店逐条提交循环

```python
succeeded_hotels = []
failed_hotels = []

for result in results:
    hotel = hotel_map.get(result["hotel_id"])
    if not hotel:
        failed_hotels.append((result["hotel_id"], "Hotel not reloaded in session"))
        continue

    try:
        # 将字段值写入 ORM 对象
        update_hotel_fields(hotel, result["fields"], ext_map)

        # 创建 TranslationHistory 记录
        for field_key, field_info in result["fields"].items():
            translated_value = field_info["translated"]
            original_text = get_original_text(hotel, field_key)
            if not original_text or not original_text.strip():
                continue  # 跳过空字段

            db.add(TranslationHistory(
                source_text=original_text,
                translated_text=translated_value,
                source_lang="zh",
                target_lang="en",
                translation_type=translation_type,
                reference_used=False,
                glossary_used=False,
                confidence_score=None,
                review_status=ReviewStatus.PENDING,
                booking_reference=None,
                operator_name="translate_cli",
            ))

        await db.commit()          # 提交「当前」酒店
        succeeded_hotels.append(result["hotel_id"])
    except Exception as e:
        await db.rollback()        # 仅回滚「当前」酒店
        failed_hotels.append((result["hotel_id"], str(e)))
```

**提交保障：** 每家酒店独立提交。如果 10 家酒店中的第 3 家在写入时失败，酒店 1 和 2 保持已提交状态。酒店 3 被回滚。酒店 4-10 继续正常处理。

**TranslationHistory 字段：**

| 字段 | 值 | 备注 |
|---|---|---|
| `source_text` | 中文原始文本 | 来自 `get_original_text()` |
| `translated_text` | 英文结果 | 来自字段信息 |
| `source_lang` | `"zh"` | 硬编码 |
| `target_lang` | `"en"` | 硬编码 |
| `translation_type` | `HYBRID` 或 `MACHINE` | 取决于 `--no-ai` |
| `reference_used` | `False` | CLI 中始终为 false（未跟踪） |
| `glossary_used` | `False` | CLI 中始终为 false（未跟踪） |
| `confidence_score` | `None` | MT/AI API 不返回逐字段置信度 |
| `review_status` | `PENDING` | 所有 CLI 翻译初始为待审核 |
| `booking_reference` | `None` | CLI 不填充此字段 |
| `operator_name` | `"translate_cli"` | 标识工具为操作人 |

> [!note] 为什么 `reference_used` 和 `glossary_used` 始终为 `False`
> 编排器的术语和参考查询在内部进行，不暴露在字段级结果中。跟踪这些信息需要修改编排器的返回类型。目前，CLI 始终将这些记录为 `False`。

#### 5g. 摘要输出

```python
console.print(
    f"\n[bold]Result:[/bold] [green]✓ {len(succeeded_hotels)} succeeded[/green], "
    f"[red]✗ {len(failed_hotels)} failed[/red]"
)
if failed_hotels:
    console.print("[red]Failed hotels:[/red]")
    for hid, err in failed_hotels:
        console.print(f"  - {hid}: {err}")
if succeeded_hotels:
    console.print("[green]✓ Translations applied successfully![/green]")
```

示例输出：
```
Result: ✓ 3 succeeded, ✗ 1 failed
Failed hotels:
  - abc-def-ghi: IntegrityError: duplicate key value violates unique constraint
✓ Translations applied successfully!
```

### 阶段 5（替代）：试运行终止

```python
else:
    console.print("\n[blue]Dry run - no changes made to database.[/blue]")
```

当设置 `--dry-run` 时，工作流在此结束。没有确认提示，没有数据库写入。

---

## 10. 错误处理与恢复

### 10.1 错误隔离层级

工具在三个粒度上实现错误隔离，确保单次失败永远不会级联为整个批次的失败。

| 层级 | 位置 | 机制 | 失败影响 |
|---|---|---|---|
| **字段级** | `batch_translator.py` 中的 `_translate_field()` | 对编排器调用使用 `try/except` | 一个字段返回来源 `ERROR`；同一酒店的其他字段继续处理 |
| **酒店级** | `batch_translator.py` 中的 `_translate_one()` | 对 `translate_hotel()` 使用 `try/except` | 一家酒店返回带零字段的错误字典；批次中的其他酒店继续处理 |
| **数据库写入** | `translate_cli.py` 中的 `_translate_workflow()` | 按酒店 `commit`/`rollback` | 失败的酒店回滚；已成功的酒店保持已提交 |

### 10.2 字段级错误处理

在 `BatchHotelTranslator._translate_field()` 中：

```python
@staticmethod
async def _translate_field(orchestrator, text, db):
    if not text or not text.strip():
        return (text or "", "N/A")

    try:
        result = await orchestrator.translate(
            text=text.strip(),
            source_lang=DEFAULT_SOURCE_LANG,
            target_lang=DEFAULT_TARGET_LANG,
            use_cache=True,
            use_ai_enhance=True,
            db=db,
        )
        return (result.translated_text, result.source.name)
    except Exception as exc:
        logger.warning(f"Translation failed: {exc}")
        return (None, "ERROR")
```

该方法是 `@staticmethod`，永不抛出异常。始终返回 `(text, source)` 元组。当翻译失败时：
- 翻译后文本为 `None`。
- 来源为 `"ERROR"`。
- 通过 loguru 记录一条警告。
- 同一酒店的其他字段继续处理。

在 `_translate_model_fields()` 中，`None` 翻译被检测到：

```python
if translated is not None:
    fields[key] = {"translated": translated, "source": source, "level": level}
else:
    errors.append(f"Translation failed for {key}")
```

该字段被排除在 `fields` 字典之外，并添加到 `errors` 列表中。在 Rich 表格预览中，错误字段显示为错误行。在导出中，错误字段被省略（不在 `fields` 字典中）。

### 10.3 酒店级错误处理

在 `BatchHotelTranslator.translate_batch()` 中：

```python
async def _translate_one(hid):
    async with semaphore:
        try:
            result = await self.translate_hotel(hid, db)
            return result
        except Exception as exc:
            logger.error(f"Hotel translation raised exception", ...)
            return {
                "hotel_id": hid,
                "fields": {},
                "errors": [f"Unexpected error: {exc}"],
            }
        finally:
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
```

如果 `translate_hotel()` 抛出异常（不只是字段错误，而是整个酒店翻译崩溃），该酒店被记录为：
- 零个已翻译字段。
- 一条包含异常消息的错误条目。
- 进度回调仍然触发（通过 `finally` 块）。

批次中的其他酒店正常继续。异常以 ERROR 级别记录。

### 10.4 按酒店逐条提交与回滚

这是最关键的恢复机制。在数据库写入阶段，每家酒店独立提交：

```
酒店 1：更新 → commit ✓
酒店 2：更新 → commit ✓
酒店 3：更新 → 异常 → rollback ✗  （仅酒店 3 回滚）
酒店 4：更新 → commit ✓
酒店 5：更新 → commit ✓
```

保障：酒店 1、2、4 和 5 保持已提交状态。仅酒店 3 被回滚。这意味着 100 家酒店的批次中 1 家失败，仍有 99 家酒店成功翻译。

**实现：**

```python
for result in results:
    hotel = hotel_map.get(result["hotel_id"])
    try:
        update_hotel_fields(hotel, result["fields"], ext_map)
        # ... 创建 TranslationHistory 记录 ...
        await db.commit()          # ← 仅提交「当前」酒店
        succeeded_hotels.append(result["hotel_id"])
    except Exception as e:
        await db.rollback()        # ← 仅回滚「当前」酒店
        failed_hotels.append((result["hotel_id"], str(e)))
```

### 10.5 边缘情况：酒店未在会话中重新加载

如果翻译结果中的酒店在会话重新加载中找不到：

```python
hotel = hotel_map.get(result["hotel_id"])
if not hotel:
    failed_hotels.append((result["hotel_id"], "Hotel not reloaded in session"))
    continue
```

这处理了酒店在预览阶段和写入阶段之间被从数据库删除，或酒店 ID 被某种方式损坏的边缘情况。

### 10.6 边缘情况：空的原始文本

在 `TranslationHistory` 创建期间，原始文本为空或仅包含空白字符的字段被跳过：

```python
original_text = get_original_text(hotel, field_key)
if not original_text or not original_text.strip():
    continue  # 不为空字段创建 TranslationHistory
```

这避免为像 `pet_policy_en` 这样的字段创建审计记录，当酒店没有宠物政策时。这些字段仍然出现在导出中，来源为 `N/A`。

### 10.7 中断批次的恢复策略

如果批次被中断（写入过程中进程被杀死、`Ctrl+C`、断电）：

1. **已提交的酒店**在数据库中保留其英文翻译。
2. **尚未提交的酒店**不受影响（由于按酒店逐条提交，没有部分写入）。
3. **TranslationHistory**仅包含已提交字段的记录，`operator_name = "translate_cli"`。
4. **恢复：** 重新运行相同的命令。已翻译的字段将命中 Redis 缓存（来源 `CACHE`），或在缓存不可用时重新翻译。`all-untranslated` 中的 `name_en IS NULL` 筛选条件将排除已成功提交的酒店。

### 10.8 常见错误场景

| 错误 | 原因 | 解决方案 |
|---|---|---|
| `Translation failed for name_en` | 腾讯 MT API 错误或网络超时 | 检查 API 凭证和网络；重试 |
| `Hotel not reloaded in session` | 酒店在预览和写入之间被删除 | 忽略；酒店已不存在 |
| `IntegrityError` | 数据库约束冲突 | 检查重复的 `expedia_hotel_id` 或其他唯一约束 |
| `ConnectionRefusedError`（Redis） | Redis 未运行 | 静默忽略；翻译继续但不使用缓存 |
| `ImportError: openpyxl` | 未安装 `openpyxl` 用于 Excel 导出 | `pip install openpyxl` 或使用 `--export-csv` |
| `Hotel not found: <uuid>` | UUID 在数据库中不存在 | 验证 UUID；使用 `by-search` 查找正确的酒店 |
| `No hotels found matching: <keyword>` | 没有酒店匹配搜索词 | 扩大搜索关键词或使用 `by-filter` |

---

## 11. 高级技巧

### 11.1 先试运行再执行

任何批次的标准安全工作流：

```bash
# 步骤 1：预览
python -m scripts.translate_cli by-search "南京" --dry-run --export-csv preview.csv

# 步骤 2：在 Excel 或文本编辑器中审阅 preview.csv

# 步骤 3：如果满意，执行
python -m scripts.translate_cli by-search "南京"
```

### 11.2 按状态增量翻译

根据审核状态分阶段处理酒店：

```bash
# 阶段 1：草稿酒店（新建，可能未翻译）- 快速纯机器翻译
python -m scripts.translate_cli by-filter --status draft --no-ai

# 阶段 2：待审核酒店 - 纯机器翻译
python -m scripts.translate_cli by-filter --status pending_review --no-ai

# 阶段 3：已审核酒店（可能需要润色）- 带 AI
python -m scripts.translate_cli by-filter --status approved

# 阶段 4：已发布酒店（最终质量）- 带 AI
python -m scripts.translate_cli by-filter --status published
```

### 11.3 按品牌迁移

在接入新品牌或进行完整重翻译时：

```bash
#!/bin/bash
# translate_all_brands.sh

BRANDS=("atour" "atour_x" "zhotel" "ahaus")
DATE=$(date +%Y%m%d)

for brand in "${BRANDS[@]}"; do
    echo "=== Processing brand: $brand ==="
    python -m scripts.translate_cli by-brand "$brand" \
        --export-excel "${brand}_${DATE}.xlsx"
    echo ""
done

echo "All brands processed."
```

### 11.4 按城市处理

用于大规模按城市拆分的迁移：

```bash
#!/bin/bash
# translate_by_city.sh

CITIES=("上海" "北京" "广州" "深圳" "杭州" "成都" "南京" "武汉" "西安" "重庆")

for city in "${CITIES[@]}"; do
    echo "=== $(date): Processing $city ==="
    python -m scripts.translate_cli by-filter --city "$city" --no-ai \
        --export-csv "city_exports/${city}_$(date +%Y%m%d).csv"
    echo ""
done
```

### 11.5 用于定时翻译的 Cron 任务

每天运行以捕获任何新的未翻译酒店：

```bash
# crontab 条目：每天凌晨 3 点
0 3 * * * cd /path/to/backend && \
    . venv/bin/activate && \
    yes | python -m scripts.translate_cli all-untranslated --no-ai \
        --export-csv "/var/log/translations/daily_$(date +\%Y\%m\%d).csv" \
        >> /var/log/translations/cron.log 2>&1
```

> [!warning] Cron 与 `typer.confirm()`
> 确认提示从标准输入读取。在 cron 中，通过管道传入 `yes` 来自动确认：
> ```bash
> yes | python -m scripts.translate_cli all-untranslated --no-ai
> ```
> 没有 `yes`，cron 任务将无限期挂起。

### 11.6 结合 grep 进行定向审阅

```bash
# 导出所有结果
python -m scripts.translate_cli by-brand atour --dry-run --export-csv all.csv

# 筛选 AI 增强翻译进行人工审阅
grep "AI_ENHANCED" all.csv > ai_review.csv

# 筛选可能需要改进的机器翻译
grep "MACHINE" all.csv > mt_review.csv

# 筛选错误
grep "ERROR" all.csv > errors.csv

# 统计来源分布
echo "CACHE: $(grep -c 'CACHE' all.csv)"
echo "MACHINE: $(grep -c 'MACHINE' all.csv)"
echo "AI_ENHANCED: $(grep -c 'AI_ENHANCED' all.csv)"
echo "ERROR: $(grep -c 'ERROR' all.csv)"
echo "N/A: $(grep -c 'N/A' all.csv)"
```

### 11.7 对比机器翻译与 AI 增强翻译

```bash
HOTEL_ID="550e8400-e29b-41d4-a716-446655440000"

# 纯机器翻译
python -m scripts.translate_cli by-id "$HOTEL_ID" --no-ai --dry-run --export-csv mt.csv

# AI 增强翻译
python -m scripts.translate_cli by-id "$HOTEL_ID" --dry-run --export-csv ai.csv

# 对比翻译文本列（第 6 列）
echo "=== AI 修改了翻译的字段 ==="
diff <(cut -d',' -f6 mt.csv | tail -n +2) <(cut -d',' -f6 ai.csv | tail -n +2)
```

### 11.8 批量重翻译特定字段

仅重翻译所有酒店的特定字段（例如 `description_en`）：

```bash
# 1. 将数据库中的字段置为 NULL
psql -d expedia_db -c "UPDATE hotels SET description_en = NULL WHERE brand = 'atour';"

# 2. 清除这些文本的 Redis 缓存（可选，强制重新翻译）
redis-cli FLUSHDB  # 警告：清除整个 Redis 数据库

# 3. 运行 CLI（它会翻译所有字段，但只有 description_en 为 NULL）
python -m scripts.translate_cli by-brand atour
```

> [!note] CLI 始终翻译所有 13 个字段
> 即使只有 `description_en` 为 NULL，CLI 也会翻译所有字段。然而，已填充的字段可能会命中 Redis 缓存（来源 `CACHE`），不会产生 API 费用。数据库写入仅覆盖 `description_en` 列。

### 11.9 高并发调优

对于大批量（100+ 酒店），在监控的同时调优并发：

```bash
# 终端 1：监控数据库连接
watch -n 1 'psql -d expedia_db -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '\''expedia_db'\'';"'

# 终端 2：运行翻译
python -m scripts.translate_cli all-untranslated --concurrency 15 --no-ai
```

关注以下指标：
- **数据库连接错误：** 减少 `--concurrency` 或增加连接池大小。
- **腾讯 API 错误：** 缓慢增加 `--concurrency`；每家酒店内部会生成多个并行 API 调用。
- **内存使用：** 所有结果在预览完成前保存在内存中。

### 11.10 结合 jq 进行 JSON 处理

如果导出为 CSV 并需要 JSON 输出：

```bash
python -m scripts.translate_cli by-brand atour --dry-run --export-csv results.csv

# 使用 Python 将 CSV 转换为 JSON
python -c "
import csv, json, sys
reader = csv.DictReader(open('results.csv', encoding='utf-8-sig'))
data = list(reader)
print(json.dumps(data, indent=2, ensure_ascii=False))
" > results.json
```

### 11.11 基于试运行结果的条件执行

```bash
#!/bin/bash
# safe_translate.sh：仅当试运行无错误时才执行

python -m scripts.translate_cli by-brand "$1" --dry-run --no-ai --export-csv /tmp/preview.csv 2>&1 | tee /tmp/preview.log

ERROR_COUNT=$(grep -c ",ERROR," /tmp/preview.csv || true)

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "No errors in preview. Proceeding with execution."
    yes | python -m scripts.translate_cli by-brand "$1" --no-ai
else
    echo "Found $ERROR_COUNT errors in preview. Aborting."
    echo "Review /tmp/preview.csv for details."
    exit 1
fi
```

### 11.12 日志记录与审计

CLI 不产生自己的日志文件（输出到 stdout/stderr）。对于审计记录，结合 shell 重定向：

```bash
# 将所有内容记录到文件
python -m scripts.translate_cli by-brand atour 2>&1 | tee "translate_$(date +%Y%m%d_%H%M%S).log"

# 仅记录错误
python -m scripts.translate_cli by-brand atour 2> "translate_errors_$(date +%Y%m%d).log"
```

对于数据库级别的审计，查询 `TranslationHistory` 表：

```sql
SELECT
    source_text,
    translated_text,
    translation_type,
    review_status,
    operator_name,
    created_at
FROM translation_histories
WHERE operator_name = 'translate_cli'
ORDER BY created_at DESC
LIMIT 100;
```

---

## 12. 测试

### 12.1 测试文件位置

测试文件位于 `backend/tests/test_translate_cli.py`（617 行）。

### 12.2 测试基础设施

测试套件使用：

| 组件 | 库 | 用途 |
|---|---|---|
| 测试运行器 | `pytest` | 测试发现与执行 |
| CLI 调用 | `typer.testing.CliRunner` | 在测试中调用 Typer 命令 |
| 测试数据库 | `sqlite+aiosqlite:///:memory:` | 内存中的 SQLite，支持异步 |
| 模拟 | `unittest.mock`（`MagicMock`、`AsyncMock`、`patch`） | 模拟 `BatchHotelTranslator` 和 `get_db_context` |

### 12.3 测试架构

每个测试：
1. 创建一个包含完整 Expedia 模式的 SQLite 内存数据库。
2. 使用受控数据填充测试酒店。
3. 模拟 `BatchHotelTranslator.translate_batch` 返回预定义结果。
4. 模拟 `get_db_context` 提供测试数据库会话。
5. 通过 `CliRunner` 调用 CLI。
6. 断言退出码、输出文本和数据库状态。

### 12.4 测试用例（共 14 个）

| # | 测试名称 | 验证内容 | 关键断言 |
|---|---|---|---|
| 1 | `test_by_id_help` | `--help` 参数打印使用说明 | 退出码 0，输出包含 "UUID" 或 "HOTEL" |
| 2 | `test_by_id_not_found` | 无效 UUID 以退出码 1 退出 | 退出码 1，输出包含 "not found" |
| 3 | `test_by_id_dry_run` | `--dry-run` 不写入数据库 | 输出包含 "Dry run"，数据库中 `name_en` 仍为 NULL |
| 4 | `test_by_id_confirm_write` | 确认写入后数据库更新 | `name_en` 设置为翻译值，`TranslationHistory` 记录已创建 |
| 5 | `test_by_search_found` | 关键词搜索找到匹配 | 输出包含 "Found 2 hotel" |
| 6 | `test_by_search_not_found` | 无匹配以退出码 1 退出 | 退出码 1，输出包含 "No hotels found" |
| 7 | `test_by_brand_valid` | 有效品牌返回结果 | 退出码 0，输出包含品牌名称 |
| 8 | `test_by_brand_invalid` | 无效品牌被 Typer 拒绝 | 退出码 != 0 |
| 9 | `test_by_filter_multi` | 组合品牌 + 城市筛选 | 输出包含 "Found 1 hotel" |
| 10 | `test_by_filter_no_params` | 无筛选参数以退出码 1 退出 | 输出包含 "At least one filter" |
| 11 | `test_all_untranslated` | 找到 `name_en` 为 NULL 的酒店 | 输出包含 "1 hotel" 或 "missing English" |
| 12 | `test_csv_export` | CSV 具有正确的 7 列表头 | 表头匹配规范，第一行具有正确的 level 和 source |
| 13 | `test_excel_export` | Excel 具有正确的结构 | 工作表名称 "Translations"，7 列表头，带样式的表头行 |
| 14 | `test_partial_failure_recovery` | 一家酒店失败不阻塞其他酒店 | 成功酒店的翻译可见，输出中有错误计数 |

### 12.5 运行测试

```bash
# 运行所有 CLI 测试
cd backend
pytest tests/test_translate_cli.py -v

# 运行特定测试
pytest tests/test_translate_cli.py::test_by_id_dry_run -v

# 运行并显示详细输出（查看 print 语句）
pytest tests/test_translate_cli.py -v -s

# 运行并显示覆盖率
pytest tests/test_translate_cli.py --cov=scripts.translate_cli --cov-report=term-missing

# 运行并生成 HTML 覆盖率报告
pytest tests/test_translate_cli.py --cov=scripts.translate_cli --cov-report=html
open htmlcov/index.html
```

> [!note] Excel 测试依赖
> `test_excel_export` 需要 `openpyxl`。如果未安装，测试通过 `pytest.importorskip("openpyxl")` 跳过。这是安全的：当 openpyxl 缺失时，测试不计为失败。

### 12.6 测试辅助函数

测试文件定义了可复用的辅助函数：

```python
def _make_mock_db_context(session_factory):
    """返回一个模拟的 get_db_context 替代。"""
    @asynccontextmanager
    async def _mock():
        async with session_factory() as session:
            yield session
    return _mock

def _make_translate_result(hotel_id, fields=None, errors=None):
    """构建匹配 BatchHotelTranslator.translate_hotel 输出的结果字典。"""
    return {
        "hotel_id": hotel_id,
        "fields": fields or {"name_en": {"translated": "Test Hotel EN", "source": "CACHE", "level": "hotel"}},
        "errors": errors or [],
    }

async def _seed_hotel(session, **kwargs):
    """插入单个酒店并返回其 id 和 name_cn。"""
    defaults = {"name_cn": "测试酒店", "name_en": None, "brand": HotelBrand.ATour, ...}
    defaults.update(kwargs)
    hotel = Hotel(**defaults)
    session.add(hotel)
    await session.flush()
    await session.refresh(hotel)
    return {"id": str(hotel.id), "name_cn": hotel.name_cn}
```

---

## 13. 常见问题

### 通用问题

#### Q1：如果 Redis 宕机会发生什么？

工具在没有缓存的情况下继续工作。`_translate_workflow` 的阶段 1 捕获 Redis 初始化的所有异常并静默忽略。翻译仍然通过直接 API 调用工作。唯一的缺点：重复翻译相同文本时会再次调用 API 而不是命中缓存。

#### Q2：如何取消正在运行的翻译？

按下 `Ctrl+C`。进程立即终止。已提交到数据库的酒店保持已提交状态（按酒店逐条提交保障）。正在翻译中或尚未开始的酒店不受影响。重新运行命令以处理剩余酒店。

#### Q3：可以只翻译特定字段吗？

不能直接这样做。`BatchHotelTranslator` 始终为每家酒店翻译所有 13 个字段。要选择性重翻译：

1. 清除数据库中目标列（将其设置为 NULL）。
2. 运行 CLI。已填充的字段将命中 Redis 缓存。
3. 只有 NULL 字段会生成新的 API 调用。

要永久排除字段，修改 `batch_translator.py` 中的 `HOTEL_FIELDS`、`ROOM_FIELDS` 或 `ROOM_EXTENSION_FIELDS`。

#### Q4：MACHINE 和 HYBRID 翻译类型有什么区别？

| 维度 | MACHINE（`--no-ai`） | HYBRID（默认） |
|---|---|---|
| 流水线步骤 | 缓存 → 术语 → 参考 → MT | 缓存 → 术语 → 参考 → MT → AI |
| API 调用 | 仅腾讯 MT | 腾讯 MT + DeepSeek |
| 速度 | 快（每个文本一次 API 调用） | 较慢（每个文本两次 API 调用） |
| 成本 | 较低（仅 MT） | 较高（MT + AI Token） |
| 质量 | 简单文本质量好 | 细微/政策文本质量更优 |
| 结果中的来源 | `MACHINE` | `AI_ENHANCED` 或 `MACHINE` |

使用 `--no-ai` 进行初始批量处理。使用默认模式（带 AI）进行最终润色。

#### Q5：为什么有些字段显示来源 "N/A"？

中文源文本为空或仅包含空白字符的字段被 `_translate_field()` 跳过：

```python
if not text or not text.strip():
    return (text or "", "N/A")
```

不进行 API 调用。这对于像 `pet_policy`、`cancellation_policy` 或 `description` 等许多酒店留空的可选字段来说是正常的。

### 字段与导出问题

#### Q6：如何在导出中识别房型和房型扩展字段？

房型字段使用格式 `<room_id>:<field_name>`：

| 导出键 | 含义 |
|---|---|
| `abc123:name_en` | 房型 `abc123` 的 `name_en`（level: `room`） |
| `abc123:amenities_en` | 房型 `abc123` 的 RoomExtension `amenities_en`（level: `room_extension`） |

导出中的 `Level` 列也会区分它们。房型 UUID 前缀确保唯一性，因为 `name_en` 同时存在于 `Hotel` 和 `Room` 上。

#### Q7：如果 AI 增强 API 失败会发生什么？

工具回退到机器翻译结果。在编排器的 `translate()` 方法中，步骤 5 被 `try/except` 包裹：

```python
try:
    ai_result = await self.ai_client.enhance_translation(...)
    if enhanced_text and enhanced_text != translated_text:
        translated_text = enhanced_text
        source = TranslationSource.AI_ENHANCED
except Exception as e:
    logger.warning(f"AI enhancement failed, using MT result: {e}")
```

翻译继续使用 MT 输出，来源保持 `MACHINE`。该字段**不会**标记为 `ERROR`。

#### Q8：TranslationHistory 记录是如何创建的？

每个翻译字段生成一条 `TranslationHistory` 行。关键字段：

| 字段 | 值 | 备注 |
|---|---|---|
| `source_text` | 中文原文 | 来自 `get_original_text()` |
| `translated_text` | 英文结果 | 来自翻译结果 |
| `translation_type` | `HYBRID` 或 `MACHINE` | 取决于 `--no-ai` |
| `operator_name` | `"translate_cli"` | 标识 CLI 为来源 |
| `review_status` | `PENDING` | 所有 CLI 翻译初始为待审核 |
| `reference_used` | `False` | 未在字段级跟踪 |
| `glossary_used` | `False` | 未在字段级跟踪 |
| `confidence_score` | `None` | MT/AI 不返回逐字段置信度 |

### 运维问题

#### Q9：可以在 CI/CD 管道中使用此工具吗？

可以。使用 `--dry-run` 进行验证，使用 `--no-ai` 追求速度：

```bash
# 验证步骤（有错误时管道失败）
python -m scripts.translate_cli by-filter --status draft --dry-run --no-ai \
    --export-csv ci_preview.csv
if grep -q ",ERROR," ci_preview.csv; then
    echo "Translation errors detected!" >&2
    exit 1
fi

# 执行步骤（使用 yes 自动确认）
yes | python -m scripts.translate_cli by-filter --status draft --no-ai
```

#### Q10：为什么 `all-untranslated` 只检查 `name_en`？

查询 `Hotel.name_en.is_(None)` 是一种启发式方法：如果酒店没有英文名称，那么它的其他英文字段很可能也都没有填充。这避免了昂贵的多列 NULL 检查。对于有 `name_en` 但缺少其他字段的酒店，必须使用 `by-filter` 或 `by-search` 来定位。

#### Q11：如何查找酒店的 UUID？

```bash
# 从数据库查询
psql -d expedia_db -c "SELECT id, name_cn, brand, city FROM hotels WHERE name_cn ILIKE '%keyword%';"

# 从 REST API 查询
curl -s http://localhost:8000/api/v1/hotels?search=keyword | jq '.items[] | {id, name_cn}'

# 从之前的 CSV 导出文件中获取（第一列）
head -3 previous_export.csv
```

#### Q12：最大批次大小是多少？

没有硬性限制。工具处理所有匹配的酒店，无论数量多少。实际限制来自：

- **数据库连接池：** 默认通常为 10-20 个连接。每家酒店在翻译期间使用一个连接。使用 `--concurrency 15` 时，至少需要 15 个可用连接。
- **腾讯云 MT 速率限制：** 检查你的腾讯云配额。
- **内存：** 所有酒店的所有结果在预览完成前保存在内存中。对于 500 家酒店，每家 3 个房型，即 `500 * 21 = 10,500` 个字段结果，每个都是一个小字典。内存使用量可控。
- **时间：** 使用 `--concurrency 5` 和 `--no-ai`，预计每家酒店约 1-3 秒。使用 AI 增强时，每家酒店约 3-8 秒。

对于超过 500 家酒店的批次，建议按品牌或城市拆分。

#### Q13：可以从英文翻译到中文吗？

工具硬编码为中译英：

```python
DEFAULT_SOURCE_LANG = "zh"
DEFAULT_TARGET_LANG = "en"
```

编排器和腾讯客户端支持任意语言对，但 `BatchHotelTranslator` 和 CLI 工具使用这些常量。要支持反向翻译，需要将这些参数化，并且字段映射需要反转。

#### Q14：进度条完成后会发生什么？

进度条使用 `transient=True` 创建：

```python
with Progress(transient=True) as progress:
```

这意味着它在完成后从终端消失。只有最终的 Rich 表格预览和摘要保持可见。这保持了终端输出的整洁。

#### Q15：如何验证翻译是否已正确应用？

```bash
# 检查特定酒店
psql -d expedia_db -c "SELECT name_cn, name_en, address_en FROM hotels WHERE id = '<uuid>';"

# 检查今天翻译的所有酒店
psql -d expedia_db -c "
    SELECT h.name_cn, h.name_en, th.created_at
    FROM hotels h
    JOIN translation_histories th ON th.source_text = h.name_cn
    WHERE th.operator_name = 'translate_cli'
    AND th.created_at > CURRENT_DATE
    ORDER BY th.created_at DESC;
"

# 按类型统计翻译数量
psql -d expedia_db -c "
    SELECT translation_type, count(*)
    FROM translation_histories
    WHERE operator_name = 'translate_cli'
    GROUP BY translation_type;
"
```

#### Q16：如何回滚一批翻译？

没有内置的回滚命令。手动回滚选项：

```sql
-- 回滚 CLI 今天的所有翻译
UPDATE hotels SET name_en = NULL, address_en = NULL, /* ... 全部 9 个字段 ... */
WHERE id IN (
    SELECT DISTINCT h.id FROM hotels h
    JOIN translation_histories th ON th.source_text = h.name_cn
    WHERE th.operator_name = 'translate_cli' AND th.created_at > CURRENT_DATE
);

-- 删除历史记录
DELETE FROM translation_histories
WHERE operator_name = 'translate_cli' AND created_at > CURRENT_DATE;
```

> [!warning] 手动回滚具有破坏性
> 在执行手动回滚操作之前始终备份数据库。考虑使用数据库快照或事务转储。

---

## 附录 A：完整选项参考

### `by-id`

```
Usage: python -m scripts.translate_cli by-id [OPTIONS] HOTEL_ID

Arguments:
  HOTEL_ID  Hotel UUID to translate  [required]

Options:
  --dry-run / --no-dry-run      Preview only, no DB write  [default: no-dry-run]
  --no-ai / --no-no-ai          Disable AI enhancement (use machine translation only)
                                [default: no-no-ai]
  --concurrency INTEGER         Concurrent translation workers  [default: 5]
  --export-csv PATH             Export results to CSV file
  --export-excel PATH           Export results to Excel file
  --help                        Show this message and exit
```

### `by-search`

```
Usage: python -m scripts.translate_cli by-search [OPTIONS] KEYWORD

Arguments:
  KEYWORD  Search keyword (partial match on name_cn or name_en)  [required]

Options:
  --dry-run / --no-dry-run      Preview only, no DB write  [default: no-dry-run]
  --no-ai / --no-no-ai          Disable AI enhancement (use machine translation only)
                                [default: no-no-ai]
  --concurrency INTEGER         Concurrent translation workers  [default: 5]
  --export-csv PATH             Export results to CSV file
  --export-excel PATH           Export results to Excel file
  --help                        Show this message and exit
```

### `by-brand`

```
Usage: python -m scripts.translate_cli by-brand [OPTIONS] BRAND:{atour|atour_x|zhotel|ahaus}

Arguments:
  BRAND:{atour|atour_x|zhotel|ahaus}  Hotel brand  [required]

Options:
  --dry-run / --no-dry-run      Preview only, no DB write  [default: no-dry-run]
  --no-ai / --no-no-ai          Disable AI enhancement (use machine translation only)
                                [default: no-no-ai]
  --concurrency INTEGER         Concurrent translation workers  [default: 5]
  --export-csv PATH             Export results to CSV file
  --export-excel PATH           Export results to Excel file
  --help                        Show this message and exit
```

### `by-filter`

```
Usage: python -m scripts.translate_cli by-filter [OPTIONS]

Options:
  --brand [atour|atour_x|zhotel|ahaus]
                                Filter by brand
  --city TEXT                   Filter by city (exact match)
  --country TEXT                Filter by country code (e.g., CN)
  --status [draft|pending_review|approved|published|suspended]
                                Filter by status
  --dry-run / --no-dry-run      Preview only, no DB write  [default: no-dry-run]
  --no-ai / --no-no-ai          Disable AI enhancement (use machine translation only)
                                [default: no-no-ai]
  --concurrency INTEGER         Concurrent translation workers  [default: 5]
  --export-csv PATH             Export results to CSV file
  --export-excel PATH           Export results to Excel file
  --help                        Show this message and exit
```

### `all-untranslated`

```
Usage: python -m scripts.translate_cli all-untranslated [OPTIONS]

Options:
  --dry-run / --no-dry-run      Preview only, no DB write  [default: no-dry-run]
  --no-ai / --no-no-ai          Disable AI enhancement (use machine translation only)
                                [default: no-no-ai]
  --concurrency INTEGER         Concurrent translation workers  [default: 5]
  --export-csv PATH             Export results to CSV file
  --export-excel PATH           Export results to Excel file
  --help                        Show this message and exit
```

---

## 附录 B：源代码索引

| 文件 | 行数 | 用途 |
|---|---|---|
| `backend/scripts/translate_cli.py` | 662 | CLI 入口：5 个子命令、导出函数、`_translate_workflow` |
| `backend/app/services/translation/batch_translator.py` | 339 | `BatchHotelTranslator`：字段映射、并发酒店翻译 |
| `backend/app/services/translation/orchestrator.py` | 557 | `TranslationOrchestrator`：7 步翻译流水线 |
| `backend/app/models/hotel.py` | 249 | `Hotel`、`Room`、`HotelBrand`、`HotelStatus` 模型 |
| `backend/app/models/room.py` | 82 | `RoomExtension` 模型 |
| `backend/app/models/translation.py` | 267 | `TranslationHistory`、`TranslationType`、`ReviewStatus` 模型 |
| `backend/app/schemas/translation/__init__.py` | 269 | `TranslationSource`、`TranslationResult`、请求/响应模式 |
| `backend/tests/test_translate_cli.py` | 617 | CLI 工具的 14 个集成测试 |

---

## 附录 C：环境变量参考

| 变量 | 必需 | 默认值 | 说明 |
|---|---|---|---|
| `DATABASE_URL` | 是 | 无 | PostgreSQL 连接字符串（asyncpg 格式） |
| `REDIS_URL` | 否 | 无 | Redis 连接字符串 |
| `TENCENT_SECRET_ID` | 是 | 无 | 腾讯云 API Secret ID |
| `TENCENT_SECRET_KEY` | 是 | 无 | 腾讯云 API Secret Key |
| `TENCENT_REGION` | 否 | `ap-guangzhou` | 腾讯云区域 |
| `DEEPSEEK_API_KEY` | 否 | 无 | DeepSeek API Key（不使用 `--no-ai` 时需要） |
| `DEEPSEEK_BASE_URL` | 否 | `https://api.deepseek.com` | DeepSeek API 基础 URL |
| `APP_ENV` | 否 | `development` | 应用环境 |
| `LOG_LEVEL` | 否 | `DEBUG` | Loguru 日志级别 |

---

## 附录 D：退出码

| 退出码 | 含义 |
|---|---|
| 0 | 成功：所有酒店已处理，或所有酒店已有英文名称 |
| 1 | 错误：酒店未找到、没有酒店匹配查询、至少需要一个筛选条件、无效的状态值、Excel 导出失败（openpyxl 未安装） |
| 2 | 错误：Typer 参数解析错误（无效品牌、缺少必需参数） |

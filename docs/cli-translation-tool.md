# CLI Translation Tool

> [!note] Target Audience
> This document is written for backend developers and operations engineers who maintain
> the Expedia hotel data pipeline. It covers the full CLI translation tool: architecture,
> all five subcommands, all thirteen translatable fields, export formats, error recovery,
> and advanced scripting patterns.

---

## 1. Overview

The CLI Translation Tool (`backend/scripts/translate_cli.py`) is a command-line utility
that batch-translates Chinese hotel master data into English and optionally writes the
results back to the PostgreSQL database. It sits on top of the same
`TranslationOrchestrator` used by the FastAPI web application, so translations produced
via CLI are identical in quality to those produced via the REST API.

### 1.1 Design Goals

- **Batch-first.** Translate one hotel or hundreds in a single invocation. The tool
  processes hotels concurrently with configurable parallelism.
- **Preview before commit.** Every run shows a Rich-formatted table preview; you can
  use `--dry-run` to inspect results without touching the database.
- **Error isolation.** A translation failure on one field or one hotel never blocks the
  rest of the batch. Each hotel is independent.
- **Per-hotel commit.** Each hotel is committed independently; a failure mid-batch does
  not roll back hotels already persisted. This is the core recovery guarantee.
- **Auditable.** Every field translation is recorded as a `TranslationHistory` row with
  operator name `translate_cli`, enabling full audit trails.
- **Exportable.** Results can be exported to CSV or Excel for offline review,
  sharing with non-technical stakeholders, or feeding into downstream pipelines.

### 1.2 Key Features at a Glance

| Feature | Description |
|---|---|
| 5 subcommands | `by-id`, `by-search`, `by-brand`, `by-filter`, `all-untranslated` |
| 13 translatable fields | Hotel (9), Room (2), RoomExtension (2) |
| AI enhancement | DeepSeek LLM post-processes machine translations |
| Translation cache | Redis-backed, survives process restarts |
| Concurrency control | `--concurrency` flag, default 5 workers |
| Dry-run mode | Full pipeline execution without database writes |
| CSV export | UTF-8 BOM encoded, 7-column format |
| Excel export | Styled header row, auto-sized columns |
| Per-hotel commit | Partial failure recovery guarantee |
| Translation history | Audit records with operator tracking |
| Progress display | Rich progress bar with transient display |

### 1.3 Technology Stack

| Component | Library | Version Requirement |
|---|---|---|
| CLI framework | [Typer](https://typer.tiangolo.com/) | Latest (via requirements.txt) |
| Terminal output | [Rich](https://rich.readthedocs.io/) | Latest |
| Concurrency | `asyncio` + `asyncio.Semaphore` | Python 3.11+ stdlib |
| Machine translation | Tencent Cloud MT API | N/A (cloud service) |
| AI enhancement | DeepSeek LLM | N/A (cloud service) |
| Translation cache | Redis (`TranslationCacheService`) | Redis 6+ |
| Database ORM | SQLAlchemy 2.0 (async) | 2.0+ |
| Database driver | asyncpg | Latest |
| Excel export | `openpyxl` | Latest |
| Logging | loguru | Latest |

### 1.4 Comparison: CLI vs REST API

| Aspect | CLI Tool | REST API |
|---|---|---|
| Invocation | Command line, cron, scripts | HTTP requests |
| Authentication | Database credentials in `.env` | API key or session token |
| Batch size | Unlimited (practical limits apply) | Paginated, typically 100 max |
| Progress feedback | Rich progress bar + table preview | JSON response with status |
| Concurrency | `asyncio.Semaphore` per invocation | Per-request, server-managed |
| Audit trail | `TranslationHistory` with `operator_name="translate_cli"` | `TranslationHistory` with user ID |
| Use case | Bulk operations, migrations, cron jobs | Interactive UI, on-demand translation |

---

## 2. Architecture

### 2.1 Module Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  translate_cli.py (Typer app, 662 lines)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  by-id   │ │by-search │ │ by-brand │ │by-filter │ │all-untrans│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └─────────────┴────────────┴────────────┴────────────┘        │
│                              │                                       │
│                   _translate_workflow()                              │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         v                    v                    v                  │
│   Redis init          BatchHotelTranslator    Rich Preview          │
│   (optional)          .translate_batch()      + CSV/Excel           │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               v
┌──────────────────────────────────────────────────────────────────────┐
│  BatchHotelTranslator (batch_translator.py, 339 lines)               │
│                                                                      │
│  translate_batch(hotel_ids, db, concurrency, progress_callback)      │
│       │                                                              │
│       │  asyncio.gather() with Semaphore(concurrency)                │
│       v                                                              │
│  translate_hotel(hotel_id, db)                                       │
│       │                                                              │
│       ├── Hotel fields (9):    _translate_model_fields(HOTEL_FIELDS) │
│       ├── Room fields (2):     _translate_model_fields(ROOM_FIELDS)  │
│       └── RoomExt fields (2):  _translate_model_fields(EXT_FIELDS)   │
│              │                                                       │
│              v                                                       │
│  _translate_field(orchestrator, text, db)                            │
│       │                                                              │
└───────┼──────────────────────────────────────────────────────────────┘
        │
        v
┌──────────────────────────────────────────────────────────────────────┐
│  TranslationOrchestrator (orchestrator.py, 557 lines)                │
│                                                                      │
│  translate(text, source_lang, target_lang, use_cache, use_ai)        │
│       │                                                              │
│       ├── Step 1: Check Redis cache                                 │
│       │     └── (hit) return CACHE result                           │
│       │                                                              │
│       ├── Step 2: Terminology replacements (GlossaryService)        │
│       │     └── Sorts by term length descending                     │
│       │                                                              │
│       ├── Step 3: Reference library lookup (BookingReferenceService)│
│       │     └── Exact match → similar match → nothing               │
│       │                                                              │
│       ├── Step 4: Tencent Cloud MT API                              │
│       │     └── TencentTranslateClient.translate()                  │
│       │                                                              │
│       ├── Step 5: AI enhancement (DeepSeek, optional)               │
│       │     └── DeepSeekClient.enhance_translation()                │
│       │                                                              │
│       ├── Step 6: Cache result in Redis                             │
│       │                                                              │
│       └── Return: TranslationResult                                 │
│                                                                      │
│  Dependencies (lazy-loaded):                                        │
│       ├── TranslationCacheService (Redis)                           │
│       ├── TencentTranslateClient (Tencent Cloud)                     │
│       ├── DeepSeekClient (DeepSeek API)                              │
│       ├── GlossaryService (terminology DB)                           │
│       └── BookingReferenceService (reference DB)                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow (Detailed)

For each hotel in the batch, the tool performs this sequence:

1. **Query hotel** with eager-loaded `rooms` from PostgreSQL using
   `selectinload(Hotel.rooms)`. This loads the hotel and all its room records in
   a single database round-trip.

2. **Extract 13 Chinese source texts** from `Hotel`, `Room`, and `RoomExtension`
   models. The field mappings `HOTEL_FIELDS`, `ROOM_FIELDS`, and
   `ROOM_EXTENSION_FIELDS` define which attributes to read.

3. **Translate each text** through the `TranslationOrchestrator` pipeline. Within
   each hotel, all 13 fields are translated in parallel via `asyncio.gather`.
   Between hotels, concurrency is controlled by `asyncio.Semaphore`.

4. **Collect results** with per-field metadata: translated text, source enum
   (`CACHE` / `MACHINE` / `AI_ENHANCED` / `ERROR`), and level (`hotel` / `room`
   / `room_extension`). Room and extension fields are prefixed with the room UUID.

5. **Render Rich Table** preview to the terminal with color-coded source columns
   and truncated text for readability.

6. **Export to CSV/Excel** if `--export-csv` or `--export-excel` flags are set.
   Exports happen from in-memory results, so they work in dry-run mode too.

7. **Prompt for confirmation** (unless `--dry-run`). The user must type `y` to
   proceed. Any other input cancels the operation.

8. **Write to database** with per-hotel commit. For each hotel:
   - Reload the hotel in the write session.
   - Load `RoomExtension` records for amenities fields.
   - Call `update_hotel_fields()` to set attribute values.
   - Create `TranslationHistory` records for each field.
   - `await db.commit()` for this hotel only.
   - On exception: `await db.rollback()` for this hotel only, continue to next.

### 2.3 TranslationOrchestrator Pipeline (In Depth)

The orchestrator executes a seven-step pipeline for each source text. Understanding
this pipeline is essential for interpreting the `Source` column in exports.

#### Step 1: Redis Cache Check

```python
if use_cache:
    cached_result = await self.cache_service.get(
        text=original_text, source_lang=source_lang,
        target_lang=target_lang, use_ai_enhance=use_ai_enhance)
if cached_result:
    return TranslationResult(source=TranslationSource.CACHE, cached=True, ...)
```

The cache key includes the source text, language pair, and whether AI enhancement
was used. This means a translation cached with `--no-ai` will NOT be returned when
AI enhancement is enabled, and vice versa. Each combination has its own cache entry.

Cache hit: `source = "CACHE"`, `cached = True`. The pipeline stops here.

#### Step 2: Terminology Replacements

```python
processed_text, terminology_matches = await self._apply_terminology_replacements(
    original_text, db, source_lang, target_lang)
```

The glossary service retrieves all active terminology entries for the language pair.
Terms are sorted by length (longest first) to prevent partial replacements. For
example, if both "大床" and "高级大床房" are glossary terms, "高级大床房" is matched
first. This is a pre-processing step applied to the Chinese source text before
machine translation.

If no `db` session is provided (not the case in CLI usage), this step is skipped.

#### Step 3: Reference Library Lookup

```python
reference_data = await self._query_reference_library(
    original_text, db, source_lang, target_lang)
```

Two lookup strategies are tried in order:

1. **Exact match:** `booking_reference_service.find_by_source_text()` looks for an
   identical source text in the reference library.
2. **Similar match:** If no exact match, `find_similar()` returns up to 3 similar
   references. The most relevant one is used.

Each successful lookup increments a usage counter on the reference record. The
reference data (Ctrip translation, Booking.com translation, hotel name) is passed
to the AI enhancement step as context.

#### Step 4: Tencent Cloud Machine Translation

```python
mt_result = await self.tencent_client.translate(
    text=processed_text, source_lang=source_lang, target_lang=target_lang)
translated_text = mt_result.get("translated_text", "")
source = TranslationSource.MACHINE
```

This is the core translation step. The input is the terminology-processed text
from step 2. The Tencent Cloud MT API returns the machine-translated English text.

If this step fails, the orchestrator returns an empty translation result:
```python
return TranslationResult(translated_text="", source=TranslationSource.MACHINE, ...)
```

#### Step 5: AI Enhancement (Optional)

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

The DeepSeek LLM receives the original Chinese text, the machine translation, and
any reference data from step 3 as context. It may rewrite the translation for
better fluency, accuracy, and naturalness.

If the AI produces text identical to the MT output, the source remains `MACHINE`.
If the AI produces different text, the source changes to `AI_ENHANCED`.

If the AI call fails (network error, API error, timeout), the exception is caught
and the MT result is used as-is:
```python
except Exception as e:
    logger.warning(f"AI enhancement failed, using MT result: {e}")
```

This is controlled by the `--no-ai` flag in the CLI.

#### Step 6: Cache the Result

```python
if use_cache and translated_text:
    await self.cache_service.set(
        text=original_text, translated_text=translated_text,
        source_lang=source_lang, target_lang=target_lang,
        source=source, use_ai_enhance=use_ai_enhance, metadata={...})
```

The final translation (whether from cache, MT, or AI) is stored in Redis for future
cache hits.

#### Step 7: Return TranslationResult

```python
return TranslationResult(
    original_text=text, translated_text=translated_text,
    source_lang=source_lang, target_lang=target_lang,
    source=source, cached=False,
    booking_reference=reference_data.get("booking_translation"),
    ctrip_reference=reference_data.get("ctrip_translation"))
```

The `TranslationResult` Pydantic model carries the original text, translated text,
source enum, confidence score (if available), caching status, and reference data.

### 2.4 Lazy-Load Pattern

Both `BatchHotelTranslator` and `TranslationOrchestrator` use lazy initialization:

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

Similarly, `TranslationOrchestrator` lazy-loads its glossary and booking reference
services. This pattern ensures that API keys, database connections, and service
configurations are not required at import time. The CLI script can be imported
without triggering any network calls.

### 2.5 Concurrency Model

The tool uses two levels of concurrency:

**Level 1: Inter-hotel (batch_translator.py)**
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

The semaphore ensures at most `concurrency` hotels are processed simultaneously.
When one hotel completes, the next hotel in the queue starts.

**Level 2: Intra-hotel (batch_translator.py)**
```python
tasks = [self._translate_field(orchestrator, source_text, db) for ...]
raw_results = await asyncio.gather(*tasks)
```

Within each hotel, all mapped fields are translated in parallel. For a hotel with
3 rooms, this means up to `9 + (3 * 2) + (3 * 2) = 21` concurrent field
translations. These field-level tasks are NOT subject to the hotel-level semaphore.

### 2.6 Room and RoomExtension Field Key Convention

Room and extension fields use a colon-separated key format to avoid collisions with
hotel-level fields. For example, `name_en` exists on both `Hotel` and `Room`:

| Key in results | Meaning |
|---|---|
| `name_en` | Hotel-level `name_en` |
| `<room_id>:name_en` | Room-level `name_en` for room `<room_id>` |
| `<room_id>:amenities_en` | RoomExtension `amenities_en` for room `<room_id>` |

The `get_original_text()` helper in `translate_cli.py` parses these keys:

```python
if ":" in field_key:
    room_id, field = field_key.split(":", 1)
    room = next((r for r in hotel.rooms if str(r.id) == room_id), None)
    # ... access room or extension attribute ...
else:
    # Hotel-level field
    cn_field = field_key.replace("_en", "_cn") if field_key.endswith("_en") else field_key
    return str(getattr(hotel, cn_field, "") or "")
```

---

## 3. Installation and Environment

### 3.1 Prerequisites

| Component | Required | Notes |
|---|---|---|
| Python 3.11+ | Yes | Async features used throughout |
| PostgreSQL | Yes | Database with Expedia schema |
| Redis | No | Optional; tool works without it |
| Tencent Cloud MT credentials | Yes | `TENCENT_SECRET_ID`, `TENCENT_SECRET_KEY` |
| DeepSeek API key | No | Only needed without `--no-ai` |
| openpyxl | No | Only needed for `--export-excel` |

### 3.2 Step-by-Step Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Copy and configure environment variables
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/expedia_db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# Tencent Cloud Machine Translation
TENCENT_SECRET_ID=AKIDxxxxxxxxxxxxxxxx
TENCENT_SECRET_KEY=xxxxxxxxxxxxxxxx
TENCENT_REGION=ap-guangzhou

# DeepSeek AI Enhancement (optional, needed without --no-ai)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Application settings
APP_ENV=development
LOG_LEVEL=DEBUG
```

```bash
# 5. Apply database migrations
alembic upgrade head

# 6. Verify the tool is functional
python -m scripts.translate_cli --help
```

Expected output:

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

### 3.3 Troubleshooting Installation

**Problem: `ModuleNotFoundError: No module named 'typer'`**
```bash
pip install typer rich
```

**Problem: `ModuleNotFoundError: No module named 'app'`**
Ensure you are running from the `backend/` directory. The script uses
`sys.path.insert(0, str(Path(__file__).parent.parent))` to add the backend
directory to the Python path.

**Problem: Database connection refused**
```bash
# Verify PostgreSQL is running
pg_isready

# Test connection
psql "$DATABASE_URL" -c "SELECT 1"
```

**Problem: Tencent Cloud API returns authentication error**
Verify that `TENCENT_SECRET_ID` and `TENCENT_SECRET_KEY` are set correctly in `.env`.
The tool reads these via `pydantic-settings` which automatically loads `.env` files.

**Problem: Redis connection refused**
Redis is optional. The tool prints no warning when Redis is unavailable. Translation
proceeds without caching. If you want Redis, ensure it is running:
```bash
redis-cli ping  # Should return PONG
```

---

## 4. Quick Start

### 4.1 Five Essential Commands

```bash
# Command 1: Translate a single hotel by its UUID
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000

# Command 2: Search and translate hotels matching a keyword
python -m scripts.translate_cli by-search "亚朵"

# Command 3: Translate all hotels of a specific brand
python -m scripts.translate_cli by-brand atour

# Command 4: Translate hotels matching multiple filter conditions
python -m scripts.translate_cli by-filter --brand atour --city 上海 --status approved

# Command 5: Translate all hotels that are missing an English name
python -m scripts.translate_cli all-untranslated
```

### 4.2 First-Run Best Practices

> [!tip] Always start with dry-run
> Before writing to the database, preview the translations:
> ```bash
> python -m scripts.translate_cli by-search "测试" --dry-run
> ```
>
> The dry-run executes the full translation pipeline (including API calls) but skips
> the database write. Review the Rich Table preview, then re-run without `--dry-run`.

> [!tip] Start small
> Begin with `by-id` on a single hotel to verify your setup:
> ```bash
> # Find a hotel UUID from the database
> psql -d yourdb -c "SELECT id, name_cn FROM hotels LIMIT 1;"
>
> # Translate it
> python -m scripts.translate_cli by-id <uuid-from-above> --dry-run
> ```

> [!tip] Export for review
> For larger batches, export to Excel for offline review:
> ```bash
> python -m scripts.translate_cli by-brand atour --dry-run --export-excel review.xlsx
> # Open review.xlsx in Excel, review, then re-run without --dry-run
> ```

### 4.3 Common Workflow Patterns

**Pattern 1: Onboarding a new brand**
```bash
# Step 1: Preview all hotels of the new brand
python -m scripts.translate_cli by-brand zhotel --dry-run --export-excel zhotel_preview.xlsx

# Step 2: Review the Excel file

# Step 3: Execute (machine-only first pass for speed)
python -m scripts.translate_cli by-brand zhotel --no-ai

# Step 4: Polish with AI enhancement
python -m scripts.translate_cli by-brand zhotel
```

**Pattern 2: City-by-city migration**
```bash
python -m scripts.translate_cli by-filter --city 上海 --no-ai --export-csv shanghai.csv
python -m scripts.translate_cli by-filter --city 北京 --no-ai --export-csv beijing.csv
python -m scripts.translate_cli by-filter --city 广州 --no-ai --export-csv guangzhou.csv
```

**Pattern 3: Incremental catch-up**
```bash
# Translate everything that is still missing an English name
python -m scripts.translate_cli all-untranslated --no-ai
```

---

## 5. Subcommand Reference

Each subcommand is documented with its argument list, SQL query logic, behavior,
and annotated examples.

### 5.1 `by-id` -- Translate a Single Hotel

Translates one hotel identified by its UUID primary key.

```
python -m scripts.translate_cli by-id <HOTEL_ID> [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `HOTEL_ID` | `str` | Yes | Hotel UUID (36-character string, e.g., `550e8400-e29b-41d4-a716-446655440000`) |

#### Query Logic

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.id == hotel_id)
)
result = await db.execute(stmt)
hotel = result.scalar_one_or_none()
```

Uses exact UUID match. Loads the hotel with eager-loaded `rooms` relationship.

#### Behavior

- **Found:** Proceeds to `_translate_workflow` with a single hotel.
- **Not found:** Prints `Hotel not found: <uuid>` in red and exits with code 1.
- **Single hotel, no batching:** Concurrency parameter has no practical effect since
  only one hotel is processed.

#### Examples

```bash
# Basic: translate and write to database
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000

# Dry-run: preview without writing
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 --dry-run

# Machine-only: skip AI enhancement
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 --no-ai

# Export to both CSV and Excel
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 \
    --export-csv result.csv --export-excel result.xlsx

# Combine flags
python -m scripts.translate_cli by-id 550e8400-e29b-41d4-a716-446655440000 \
    --dry-run --no-ai --export-csv preview.csv
```

#### How to Find a Hotel UUID

```bash
# From PostgreSQL
psql -d expedia_db -c "SELECT id, name_cn, brand, city FROM hotels WHERE name_cn ILIKE '%亚朵%' LIMIT 10;"

# From a previous CSV export (first column is Hotel ID)
head -3 previous_export.csv

# From the REST API
curl -s http://localhost:8000/api/v1/hotels?search=亚朵 | jq '.items[].id'
```

### 5.2 `by-search` -- Search by Keyword

Searches hotels by keyword (partial match on `name_cn` or `name_en`) and translates
all matches.

```
python -m scripts.translate_cli by-search <KEYWORD> [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `KEYWORD` | `str` | Yes | Search keyword for partial matching |

#### Query Logic

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

The `ILIKE` operator provides case-insensitive matching. Both `name_cn` and `name_en`
are searched. Results are ordered by most recently updated first.

#### Behavior

- **Matches found:** Prints `Found N hotel(s) matching '<keyword>'` and proceeds to
  `_translate_workflow`.
- **No matches:** Prints `No hotels found matching: <keyword>` in red and exits with
  code 1.
- **Partial matching:** The keyword `"亚朵"` matches `"上海亚朵酒店"`, `"亚朵X酒店"`,
  `"Atour Hotel"` (if `name_en` contains `亚朵`), etc.
- **Multiple matches:** All matching hotels are translated in a single batch.

#### Examples

```bash
# Search by Chinese keyword
python -m scripts.translate_cli by-search "南京" --dry-run

# Search by English keyword (matches name_en)
python -m scripts.translate_cli by-search "Atour" --dry-run

# Search with export
python -m scripts.translate_cli by-search "西湖" --export-csv xihu_results.csv

# Search and apply with concurrency 10
python -m scripts.translate_cli by-search "北京" --concurrency 10
```

> [!warning] Broad keywords
> Searching for a single character like "酒" (which appears in "酒店") may match
> hundreds of hotels. Always use `--dry-run` first with broad searches.

### 5.3 `by-brand` -- Filter by Brand

Translates all hotels belonging to a specific brand.

```
python -m scripts.translate_cli by-brand <BRAND> [OPTIONS]
```

#### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `BRAND` | `HotelBrand` | Yes | Brand name (case-insensitive via Typer) |

#### Valid Brand Values

| CLI Value | Enum Constant | Chinese Name | Description |
|---|---|---|---|
| `atour` | `HotelBrand.ATour` | 亚朵 | Standard Atour hotels |
| `atour_x` | `HotelBrand.ATourX` | 亚朵X | Atour X hotels |
| `zhotel` | `HotelBrand.ZHotel` | ZHotel | ZHotel properties |
| `ahaus` | `HotelBrand.Ahaus` | Ahaus | Ahaus properties |

#### Query Logic

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.brand == brand)
    .order_by(Hotel.updated_at.desc())
)
```

#### Behavior

- **Valid brand:** Queries database with exact enum match, translates all results.
- **Invalid brand:** Typer rejects the argument before any database call. Produces
  a Typer error message listing valid values:
  ```
  Error: Invalid value for 'BRAND:{atour|atour_x|zhotel|ahaus}': 'invalid' is not one of 'atour', 'atour_x', 'zhotel', 'ahaus'.
  ```
  Exit code is 2 (Typer argument parsing error).
- **Brand with no hotels:** Prints `No hotels found for brand: <value>` and exits
  with code 1.
- **Case-insensitive:** `atour`, `Atour`, `ATOUR` all map to `HotelBrand.ATour`.

#### Examples

```bash
# Translate all Atour hotels
python -m scripts.translate_cli by-brand atour --dry-run

# Translate all Atour X hotels with machine-only translation
python -m scripts.translate_cli by-brand atour_x --no-ai

# Translate all ZHotel properties and export
python -m scripts.translate_cli by-brand zhotel --export-excel zhotel_$(date +%Y%m%d).xlsx

# Translate all Ahaus properties with high concurrency
python -m scripts.translate_cli by-brand ahaus --concurrency 15
```

### 5.4 `by-filter` -- Flexible Multi-Condition Filter

Translates hotels matching any combination of brand, city, country, and status filters.
At least one filter must be specified.

```
python -m scripts.translate_cli by-filter [OPTIONS]
```

#### Options

| Option | Type | Default | SQL Column | Description |
|---|---|---|---|---|
| `--brand` | `HotelBrand` | None | `Hotel.brand` | Filter by brand enum |
| `--city` | `str` | None | `Hotel.city` | Filter by exact city name |
| `--country` | `str` | None | `Hotel.country_code` | Filter by country code |
| `--status` | `str` | None | `Hotel.status` | Filter by status value |

#### Valid Status Values

| CLI Value | Enum Constant | Description |
|---|---|---|
| `draft` | `HotelStatus.DRAFT` | Draft hotels, not yet submitted for review |
| `pending_review` | `HotelStatus.PENDING_REVIEW` | Awaiting review |
| `approved` | `HotelStatus.APPROVED` | Approved by reviewer |
| `published` | `HotelStatus.PUBLISHED` | Published to Expedia |
| `suspended` | `HotelStatus.SUSPENDED` | Temporarily suspended |

#### Query Logic

All specified filters are combined with `AND`. The WHERE clause is built dynamically:

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

#### Behavior

- **No filters:** Prints `At least one filter is required (--brand, --city, --country, --status)` and exits with code 1.
- **Invalid status:** Prints `Invalid status: '<value>'. Valid values: draft, pending_review, approved, published, suspended` and exits with code 1.
- **Invalid brand:** Typer rejects the argument with a list of valid values.
- **No matches:** Prints `No hotels found for filter: brand=atour, city=上海` and exits with code 1.
- **Single filter:** Works with just one filter option.
- **All four filters:** All conditions are AND-combined.

#### Examples

```bash
# Single filter: all hotels in Shanghai
python -m scripts.translate_cli by-filter --city 上海 --dry-run

# Single filter: all published hotels
python -m scripts.translate_cli by-filter --status published --dry-run

# Two filters: Atour hotels in Beijing
python -m scripts.translate_cli by-filter --brand atour --city 北京 --dry-run

# Three filters: published Atour hotels in China
python -m scripts.translate_cli by-filter --brand atour --country CN --status published

# All four filters
python -m scripts.translate_cli by-filter \
    --brand atour_x --city 杭州 --country CN --status approved

# Filter by status only (draft hotels that need review)
python -m scripts.translate_cli by-filter --status draft --no-ai --export-csv drafts.csv

# Invalid: no filters specified
python -m scripts.translate_cli by-filter
# Error: At least one filter is required (--brand, --city, --country, --status)
```

> [!note] City filter is exact match
> `--city 上海` matches only hotels where `city = '上海'`. It does NOT do partial
> matching like `by-search`. Use `by-search` for fuzzy city searches.

### 5.5 `all-untranslated` -- Find Missing English Names

Translates all hotels where `name_en IS NULL`. This is the quickest way to bootstrap
English translations for a fresh dataset or catch up on missed translations.

```
python -m scripts.translate_cli all-untranslated [OPTIONS]
```

#### Query Logic

```python
stmt = (
    select(Hotel)
    .options(selectinload(Hotel.rooms))
    .where(Hotel.name_en.is_(None))
    .order_by(Hotel.updated_at.desc())
)
```

Only checks `name_en IS NULL`. This is a heuristic: if a hotel has no English name,
it is very likely that none of its other English fields are populated either.

#### Behavior

- **Hotels found:** Prints `Found N hotel(s) with missing English name` and proceeds
  to `_translate_workflow`.
- **No hotels found:** Prints `All hotels already have English names. Nothing to translate.`
  and exits with code 0 (success, not an error).
- **No arguments:** This subcommand takes no positional arguments, only the standard
  global options.

#### Examples

```bash
# Check how many hotels need translation
python -m scripts.translate_cli all-untranslated --dry-run

# Translate all untranslated hotels (machine-only for speed)
python -m scripts.translate_cli all-untranslated --no-ai

# Translate with export
python -m scripts.translate_cli all-untranslated --export-csv bootstrap.csv

# Low concurrency for a large batch
python -m scripts.translate_cli all-untranslated --concurrency 3
```

> [!note] Why only check `name_en`?
> The `name_en IS NULL` check is a fast heuristic. Checking all 13 fields for NULL
> would require a complex query with 13 OR conditions. In practice, if a hotel's
> `name_en` is NULL, the hotel has never been translated. If you need to find hotels
> with specific fields missing, use `by-filter` or a direct SQL query.

---

## 6. Global Parameters

All five subcommands accept the following shared options. These are defined as
module-level `typer.Option` defaults in `translate_cli.py` and applied consistently
across all subcommands.

### 6.1 `--dry-run`

```
--dry-run / --no-dry-run    (default: False)
```

When enabled, the tool executes the full translation pipeline (including API calls
to Tencent Cloud MT and DeepSeek) and displays the Rich Table preview, but **skips
the database write step** in `_translate_workflow` phase 5.

**What happens in dry-run mode:**

1. Redis initialization proceeds as normal (optional, failure ignored).
2. Translation API calls are made (real API usage, real costs).
3. Rich Table preview is displayed with full results.
4. CSV/Excel exports are generated if `--export-csv` or `--export-excel` are set.
5. The confirmation prompt is skipped.
6. Database writes are skipped.

Terminal output ends with:
```
Dry run - no changes made to database.
```

**Use cases:**

- Preview translations before committing.
- Generate export files for offline review.
- Test API connectivity and translation quality.
- Compare machine vs AI-enhanced translations.

```bash
# Preview a batch
python -m scripts.translate_cli by-brand atour --dry-run

# Export for review without writing
python -m scripts.translate_cli by-search "测试" --dry-run --export-excel review.xlsx
```

### 6.2 `--no-ai`

```
--no-ai / --no-no-ai    (default: False)
```

Disables the DeepSeek AI enhancement step (step 5 of the orchestrator pipeline).
When set, translations come from the Tencent Cloud MT API with only terminology
replacement and reference library lookups applied.

**Effect on the pipeline:**

| Pipeline Step | `--no-ai` (default) | `--no-ai` set |
|---|---|---|
| Step 1: Cache check | Yes | Yes |
| Step 2: Terminology | Yes | Yes |
| Step 3: Reference lookup | Yes | Yes |
| Step 4: MT API | Yes | Yes |
| Step 5: AI enhancement | Yes | **Skipped** |
| Step 6: Cache result | Yes | Yes |

**Effect on TranslationHistory:**

| Flag | `translation_type` in history |
|---|---|
| (default, AI enabled) | `HYBRID` |
| `--no-ai` | `MACHINE` |

**Use cases:**

- Initial bulk translation passes where speed matters.
- Cost-sensitive operations (avoids DeepSeek API token costs).
- Testing machine translation quality independently.
- Environments where the DeepSeek API key is not configured.

```bash
# Fast, machine-only translation
python -m scripts.translate_cli by-brand atour --no-ai

# Compare: machine-only vs AI-enhanced
python -m scripts.translate_cli by-id <UUID> --no-ai --export-csv mt.csv
python -m scripts.translate_cli by-id <UUID> --export-csv hybrid.csv
diff <(cut -d',' -f6 mt.csv) <(cut -d',' -f6 hybrid.csv)
```

### 6.3 `--concurrency`

```
--concurrency INTEGER    (default: 5)
```

Controls the maximum number of hotels translated concurrently. The underlying
`BatchHotelTranslator` uses `asyncio.Semaphore(concurrency)` to cap concurrent
hotel translations.

**How concurrency works:**

```python
semaphore = asyncio.Semaphore(concurrency)

async def _translate_one(hid):
    async with semaphore:
        result = await self.translate_hotel(hid, db)
        # ... progress callback ...
        return result

tasks = [_translate_one(hid) for hid in hotel_ids]
results = await asyncio.gather(*tasks)
```

Within each hotel, all 13 fields (plus room and extension fields) are translated
in parallel via `asyncio.gather`. These field-level tasks are NOT subject to the
hotel-level semaphore. For a hotel with 3 rooms, that means up to 21 concurrent
API calls per hotel.

**Guidelines:**

| Concurrency | Use Case |
|---|---|
| 1 | Debugging, single-stepping through translations |
| 3 | Conservative, low database/API load |
| 5 | Default, safe for most environments |
| 10 | Moderate throughput, monitor API rate limits |
| 20 | High throughput, ensure adequate DB connection pool |

> [!warning] Concurrency limits
> Setting concurrency too high may:
> - Exceed Tencent Cloud MT API rate limits (causing `ERROR` results)
> - Exhaust database connection pool slots (causing connection errors)
> - Increase memory usage (all hotel results held in memory until preview)
>
> Start with the default of 5 and increase gradually while monitoring error counts
> in the summary line.

```bash
# Single-threaded for debugging
python -m scripts.translate_cli by-id <UUID> --concurrency 1

# Aggressive for large batches
python -m scripts.translate_cli all-untranslated --concurrency 15
```

### 6.4 `--export-csv`

```
--export-csv PATH
```

Exports translation results to a CSV file at the specified path. The file is written
with UTF-8 BOM (`utf-8-sig`) encoding for compatibility with Microsoft Excel.

**CSV format (7 columns):**

| Column | Content | Example |
|---|---|---|
| `Hotel ID` | UUID of the hotel | `550e8400-e29b-41d4-a716-446655440000` |
| `Hotel Name` | `name_cn` value | `上海亚朵酒店` |
| `Level` | `hotel`, `room`, or `room_extension` | `hotel` |
| `Field` | Field key | `name_en` or `<room_id>:name_en` |
| `Original` | Chinese source text | `上海亚朵酒店` |
| `Translated` | English translation result | `Shanghai Atour Hotel` |
| `Source` | Translation source enum | `AI_ENHANCED` |

**Implementation:**

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

**Example output:**

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

Exports translation results to an Excel (`.xlsx`) file at the specified path. Requires
the `openpyxl` package (included in `requirements.txt`).

**Excel format:**

- Same 7 columns as CSV.
- **Sheet name:** `Translations`
- **Header row:** Blue background (`#4472C4`) with white bold text, center-aligned.
- **Column widths:** Auto-calculated based on content, capped at 80 characters.

**Header style code:**

```python
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF")
for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")
```

**Column width code:**

```python
for col in ws.columns:
    max_length = max(len(str(cell.value or "")) for cell in col)
    ws.column_dimensions[col_letter].width = min(max_length + 4, 80)
```

**Error handling:**

If `openpyxl` is not installed:
```
Error: openpyxl is required for Excel export. Install with: pip install openpyxl
```
Exit code: 1.

```bash
python -m scripts.translate_cli by-filter --city 上海 --export-excel shanghai_$(date +%Y%m%d).xlsx
```

### 6.6 Parameter Combinations

All global parameters can be combined freely:

```bash
# Full combination: dry-run, machine-only, high concurrency, both exports
python -m scripts.translate_cli by-brand atour \
    --dry-run --no-ai --concurrency 10 \
    --export-csv results.csv --export-excel results.xlsx

# Minimal: just translate and write
python -m scripts.translate_cli by-id <UUID>

# Export-only: no DB write, just generate files
python -m scripts.translate_cli by-search "测试" --dry-run --export-excel review.xlsx
```

---

## 7. Translation Fields Reference

The tool translates exactly 13 fields across three database models. Each field has a
Chinese source column and an English target column. The field mappings are defined as
module-level constants in `batch_translator.py`.

### 7.1 Hotel-Level Fields (9 fields)

These fields live on the `hotels` table (`Hotel` model in `app/models/hotel.py`).

| # | Target Field | Source Field | Column Type | Nullable | Description |
|---|---|---|---|---|---|
| 1 | `name_en` | `name_cn` | `String(255)` | No | Hotel name |
| 2 | `address_en` | `address_cn` | `String(500)` | No | Street address |
| 3 | `cancellation_policy_en` | `cancellation_policy` | `Text` | Yes | Cancellation policy |
| 4 | `prepayment_policy_en` | `prepayment_policy` | `Text` | Yes | Prepayment policy |
| 5 | `kid_policy_en` | `kid_policy` | `Text` | Yes | Children policy |
| 6 | `pet_policy_en` | `pet_policy` | `Text` | Yes | Pet policy |
| 7 | `services_en` | `services` | `Text` | Yes | Hotel services |
| 8 | `facilities_en` | `facilities` | `Text` | Yes | Hotel facilities |
| 9 | `description_en` | `description` | `Text` | Yes | Hotel description |

**Field mapping in code:**

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

**Translation process for hotel fields:**

```python
hotel_fields, hotel_errors = await self._translate_model_fields(
    orchestrator, hotel, HOTEL_FIELDS, db, level="hotel"
)
all_fields.update(hotel_fields)
```

Each field key in the result is the target column name (e.g., `name_en`), not the
source column name. The `level` is always `"hotel"`.

> [!note] Source field naming inconsistency
> Hotel-level policy fields (`cancellation_policy`, `prepayment_policy`, `kid_policy`,
> `pet_policy`) do NOT have a `_cn` suffix. The `HOTEL_FIELDS` mapping maps each `_en`
> target to the exact database column name. The `get_original_text()` helper in the
> CLI handles this:
> ```python
> cn_field = field_key.replace("_en", "_cn") if field_key.endswith("_en") else field_key
> ```
> For `cancellation_policy_en`, this produces `cancellation_policy_cn` first, then
> falls back to `cancellation_policy` since `_cn` does not exist on the model.

### 7.2 Room-Level Fields (2 fields)

These fields live on the `rooms` table (`Room` model in `app/models/hotel.py`).

| # | Target Field | Source Field | Column Type | Nullable | Description |
|---|---|---|---|---|---|
| 10 | `name_en` | `name_cn` | `String(255)` | No | Room type name |
| 11 | `description_en` | `description_cn` | `Text` | Yes | Room type description |

**Field mapping in code:**

```python
ROOM_FIELDS: Dict[str, str] = {
    "name_en": "name_cn",
    "description_en": "description_cn",
}
```

**Translation process for room fields:**

```python
if hotel.rooms:
    for room in hotel.rooms:
        room_fields, room_errors = await self._translate_model_fields(
            orchestrator, room, ROOM_FIELDS, db, level="room"
        )
        for key, value in room_fields.items():
            all_fields[f"{room.id}:{key}"] = value
```

**Key prefixing:** Room field keys in the result dictionary are prefixed with the
room's UUID to avoid collisions with hotel-level fields. For example:

| Result Key | Meaning |
|---|---|
| `name_en` | Hotel `name_en` (level: hotel) |
| `abc123-def456:name_en` | Room `name_en` for room `abc123-def456` (level: room) |
| `abc123-def456:description_en` | Room `description_en` for room `abc123-def456` (level: room) |

### 7.3 RoomExtension-Level Fields (2 fields)

These fields live on the `room_extensions` table (`RoomExtension` model in
`app/models/room.py`).

| # | Target Field | Source Field | Column Type | Nullable | Description |
|---|---|---|---|---|---|
| 12 | `amenities_en` | `amenities_cn` | `Text` | Yes | Room amenities |
| 13 | `bathroom_amenities_en` | `bathroom_amenities_cn` | `Text` | Yes | Bathroom amenities |

**Field mapping in code:**

```python
ROOM_EXTENSION_FIELDS: Dict[str, str] = {
    "amenities_en": "amenities_cn",
    "bathroom_amenities_en": "bathroom_amenities_cn",
}
```

**Translation process for extension fields:**

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

**Key prefixing:** Like room fields, extension field keys are prefixed with the room UUID:

| Result Key | Meaning |
|---|---|
| `abc123-def456:amenities_en` | RoomExtension `amenities_en` for room `abc123-def456` |
| `abc123-def456:bathroom_amenities_en` | RoomExtension `bathroom_amenities_en` for room `abc123-def456` |

> [!note] RoomExtension loading
> RoomExtensions are NOT eager-loaded with the hotel query. They are loaded separately
> in `translate_hotel()` after room IDs are collected:
> ```python
> ext_stmt = select(RoomExtension).where(RoomExtension.room_id.in_(room_ids))
> ```
> This is because there is no SQLAlchemy relationship from `Room` to `RoomExtension`
> (the `room` relationship on `RoomExtension` is commented out in the model).

### 7.4 Field Result Structure

Each translated field in the result dictionary has this shape:

```python
{
    "translated": str,    # The English translation text
    "source": str,        # "CACHE" | "MACHINE" | "AI_ENHANCED" | "ERROR" | "N/A"
    "level": str,         # "hotel" | "room" | "room_extension"
}
```

The `level` determines the value in the `Level` column of exports and is purely for
categorization. It does not affect the translation process.

### 7.5 Source Enum Values

| Source | Meaning | When it appears |
|---|---|---|
| `CACHE` | Result retrieved from Redis cache | Cache hit in step 1 of orchestrator |
| `MACHINE` | Result from Tencent Cloud MT API | MT success, no AI enhancement or AI produced same text |
| `AI_ENHANCED` | MT result improved by DeepSeek AI | AI enhancement produced different text |
| `ERROR` | Translation failed | API error, network error, or exception |
| `N/A` | No content to translate | Source text was empty or whitespace-only |

### 7.6 Empty / Null Source Handling

When a source field is empty (None or whitespace-only), `_translate_field` returns
without calling any translation API:

```python
if not text or not text.strip():
    return (text or "", "N/A")
```

The `N/A` source means the field had no content. These fields are still included in
the result dictionary (with the original empty text as the "translated" value) and
appear in exports with source `N/A`. They do NOT generate `TranslationHistory` records
during the database write phase:

```python
original_text = get_original_text(hotel, field_key)
if not original_text or not original_text.strip():
    continue  # Skip TranslationHistory creation
```

### 7.7 Complete Field Count Example

For a hotel with 2 rooms, the total number of field translations is:

```
Hotel fields:         9
Room 1 fields:        2
Room 2 fields:        2
Room 1 ext fields:    2
Room 2 ext fields:    2
                    ----
Total:               17 fields
```

Each of these 17 fields produces one row in CSV/Excel exports and (if not empty) one
`TranslationHistory` record.

---

## 8. Export Formats

### 8.1 Rich Table Preview

Every run displays a Rich-formatted table in the terminal before any database write.
This is the primary review mechanism for interactive use.

#### Table Columns

| Column | Style | Width | Description |
|---|---|---|---|
| `#` | `dim`, right-aligned | 4 | Row number per hotel |
| `Hotel` | `cyan`, `no_wrap` | Auto | Hotel `name_cn` |
| `Field` | `green` | Auto | Field key |
| `Original (CN)` | `yellow` | Max 50 chars | Truncated Chinese source text |
| `Translated (EN)` | `magenta` | Max 50 chars | Truncated English translation |
| `Source` | Color-coded | 12 | Translation source |
| `Status` | `bold` | 8 | Checkmark or error indicator |

#### Source Column Coloring

| Source Value | Rich Style String | Visual |
|---|---|---|
| `CACHE` | `[dim]CACHE[/dim]` | Dimmed/gray text |
| `MACHINE` | `[blue]MACHINE[/blue]` | Blue text |
| `AI_ENHANCED` | `[green]AI_ENHANCED[/green]` | Green text |
| `ERROR` | `[red]✗ {error_message}[/red]` | Red text with error |
| (any other) | Plain text | Default color |

The coloring logic in `_translate_workflow`:

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

#### Text Truncation

Both `Original (CN)` and `Translated (EN)` columns are truncated to 50 characters:

```python
def _truncate(text: str, max_len: int = 50) -> str:
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text
```

This keeps the table readable for long policy texts and descriptions. Full text is
available in CSV/Excel exports.

#### Error Row Display

When a field translation fails, an error row is shown:

```
│   1 │ 上海亚朵酒店 │ ERROR        │                  │                  │ ✗ Translation failed for name_en │
```

Error rows span the full width and are displayed in red. The hotel name and row number
are still shown for context.

#### Summary Line

After the table, a summary line shows aggregate statistics:

```
Summary: 3 hotels, 39 fields translated, 2 errors
```

- Green: hotel count and field count.
- Red (if > 0): error count.

#### Example Complete Output

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

### 8.2 CSV Export Format

**File encoding:** UTF-8 with BOM (`utf-8-sig`).

The BOM (Byte Order Mark) ensures Microsoft Excel correctly detects UTF-8 encoding
when opening the file. Without BOM, Excel may misinterpret Chinese characters.

**Header row:**
```
Hotel ID,Hotel Name,Level,Field,Original,Translated,Source
```

**Data rows:** One row per translated field. For a hotel with N rooms:

```
Total rows = 1 (header) + 9 (hotel fields) + (N * 2) (room fields) + (N * 2) (extension fields)
```

**Example CSV content:**
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

**Notes on CSV format:**
- Fields containing commas are properly quoted by Python's `csv.writer`.
- The `Hotel Name` column uses `name_cn` regardless of whether `name_en` exists.
- Empty fields appear as empty CSV cells (two consecutive commas).
- Room and extension field keys include the room UUID for traceability.

### 8.3 Excel Export Format

**File format:** `.xlsx` (Office Open XML Spreadsheet)

**Sheet name:** `Translations`

**Header row styling:**

| Property | Value |
|---|---|
| Background color | `#4472C4` (medium blue) |
| Font color | `#FFFFFF` (white) |
| Font weight | Bold |
| Horizontal alignment | Center |

**Data rows:** No special styling applied.

**Column widths:** Auto-calculated based on the longest content in each column,
capped at 80 characters:

```python
max_length = max(len(str(cell.value or "")) for cell in col)
ws.column_dimensions[col_letter].width = min(max_length + 4, 80)
```

The `+ 4` adds padding so text does not touch column edges. The 80-character cap
prevents extremely wide columns for long policy texts.

**Example Excel structure:**

| Hotel ID (A) | Hotel Name (B) | Level (C) | Field (D) | Original (E) | Translated (F) | Source (G) |
|---|---|---|---|---|---|---|
| *(blue header row with white bold text)* |
| 550e... | 上海亚朵酒店 | hotel | name_en | 上海亚朵酒店 | Shanghai Atour Hotel | AI_ENHANCED |
| 550e... | 上海亚朵酒店 | hotel | address_en | 浦东新区... | Pudong New Area... | CACHE |

**Error handling for Excel export:**

```python
try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
except ImportError:
    console.print("[red]Error: openpyxl is required for Excel export...[/red]")
    raise typer.Exit(1)
```

If `openpyxl` is not installed, the tool prints a clear error message and exits with
code 1. No partial file is created.

---

## 9. Workflow Details

The `_translate_workflow` function in `translate_cli.py` is the shared execution path
for all five subcommands. It runs through five distinct phases.

### Phase 1: Redis Initialization (Optional)

```python
try:
    from app.core.redis import RedisService
    await RedisService.init()
    RedisService.get_client()
except Exception:
    pass
```

Redis is initialized once at the start of the workflow. If Redis is unavailable
(connection refused, wrong URL, not installed), the exception is silently caught
and the workflow continues. Translation still works via direct API calls; caching
is simply disabled for this invocation.

**Why Redis initialization is separate from the orchestrator:**
The orchestrator lazily initializes its `TranslationCacheService`, which in turn
connects to Redis. The explicit initialization in the CLI ensures Redis is ready
before any translation calls, avoiding per-call connection overhead.

### Phase 2: Translation

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

Key details:

- A new database session is created via `get_db_context()`.
- `BatchHotelTranslator` is instantiated fresh (no state carried over from previous
  invocations).
- The Rich `Progress` bar shows `Translating...` with a completion percentage.
- `transient=True` means the progress bar disappears after completion, leaving only
  the result table visible.
- The `progress_callback` is invoked after each hotel completes (success or failure),
  updating the progress bar.
- `translate_batch` returns a list of result dictionaries, one per hotel.

**What happens inside `translate_batch`:**

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

### Phase 3: Rich Table Preview

The tool builds a `rich.table.Table` with the title `"Translation Preview"` and
iterates through results to populate rows.

For each hotel result:
1. Look up the hotel in `hotels_for_display` by `hotel_id`.
2. If errors exist, add error rows (one per error).
3. For each field, add a data row with color-coded source.

The table is printed to the console via `console.print(table)`.

After the table, a summary line is printed:

```python
summary_parts = [f"{len(results)} hotels, {total_fields} fields translated"]
if total_errors:
    summary_parts.append(f"[red]{total_errors} errors[/red]")
console.print(f"\n[bold]Summary:[/bold] {', '.join(summary_parts)}")
```

### Phase 4: Export (If Requested)

```python
if export_csv:
    export_results_to_csv(results, hotels_for_display, export_csv)
if export_excel:
    export_results_to_excel(results, hotels_for_display, export_excel)
```

Both exports are generated from the in-memory `results` list, not from the database.
This means:
- Exports are available in `--dry-run` mode.
- Exports reflect exactly what was shown in the Rich Table preview.
- Failed fields (source `ERROR`) appear in exports with empty translated text.

Success messages are printed in green:
```
✓ CSV exported to /path/to/file.csv
✓ Excel exported to /path/to/file.xlsx
```

### Phase 5: Database Write (Unless Dry-Run)

This is the most complex phase. It runs only when `--dry-run` is NOT set.

#### 5a. Error Warning

```python
if not dry_run:
    if total_errors > 0:
        console.print("[yellow]⚠ There are translation errors. Review carefully before applying.[/yellow]")
```

If any field translations failed (source `ERROR`), a yellow warning is shown. The
user is encouraged to review but can still proceed.

#### 5b. Confirmation Prompt

```python
if not typer.confirm("\nApply translations to database?"):
    console.print("[yellow]Cancelled. No changes were made.[/yellow]")
    return
```

The prompt displays `Apply translations to database? [y/N]:`. The user must type `y`
(or `yes`) and press Enter. Any other input (including just pressing Enter) cancels
the operation. No database changes are made.

> [!warning] Non-interactive environments
> The `typer.confirm()` call reads from stdin. In CI/CD pipelines or cron jobs,
> this will hang waiting for input. Pipe `yes` to handle this:
> ```bash
> yes | python -m scripts.translate_cli by-brand atour --no-ai
> ```

#### 5c. Reload Hotels in Write Session

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

Hotels are re-queried within the write session to ensure the ORM objects are attached
to the current session. The `hotel_map` dictionary provides O(1) lookup by hotel ID.

#### 5d. Load RoomExtensions

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

RoomExtensions are loaded separately and indexed by `room_id` for efficient lookup
during field writes. The `ext_map` is passed to `update_hotel_fields()`.

#### 5e. Determine Translation Type

```python
translation_type = TranslationType.MACHINE if no_ai else TranslationType.HYBRID
```

The translation type stored in `TranslationHistory` depends on the `--no-ai` flag.

#### 5f. Per-Hotel Commit Loop

```python
succeeded_hotels = []
failed_hotels = []

for result in results:
    hotel = hotel_map.get(result["hotel_id"])
    if not hotel:
        failed_hotels.append((result["hotel_id"], "Hotel not reloaded in session"))
        continue

    try:
        # Write field values to ORM objects
        update_hotel_fields(hotel, result["fields"], ext_map)

        # Create TranslationHistory records
        for field_key, field_info in result["fields"].items():
            translated_value = field_info["translated"]
            original_text = get_original_text(hotel, field_key)
            if not original_text or not original_text.strip():
                continue  # Skip empty fields

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

        await db.commit()          # Commit THIS hotel
        succeeded_hotels.append(result["hotel_id"])
    except Exception as e:
        await db.rollback()        # Rollback ONLY this hotel
        failed_hotels.append((result["hotel_id"], str(e)))
```

**Commit guarantee:** Each hotel is committed independently. If hotel 3 of 10 fails
during write, hotels 1 and 2 remain committed. Hotel 3 is rolled back. Hotels 4-10
continue processing normally.

**TranslationHistory fields:**

| Field | Value | Notes |
|---|---|---|
| `source_text` | Chinese original text | From `get_original_text()` |
| `translated_text` | English result | From field info |
| `source_lang` | `"zh"` | Hardcoded |
| `target_lang` | `"en"` | Hardcoded |
| `translation_type` | `HYBRID` or `MACHINE` | Depends on `--no-ai` |
| `reference_used` | `False` | Always false in CLI (not tracked) |
| `glossary_used` | `False` | Always false in CLI (not tracked) |
| `confidence_score` | `None` | MT/AI APIs do not return per-field confidence |
| `review_status` | `PENDING` | All CLI translations start as pending review |
| `booking_reference` | `None` | Not populated by CLI |
| `operator_name` | `"translate_cli"` | Identifies the tool as the operator |

> [!note] Why `reference_used` and `glossary_used` are always `False`
> The orchestrator's terminology and reference lookups happen internally and are not
> exposed in the field-level result. Tracking these would require changes to the
> orchestrator's return type. For now, the CLI always records these as `False`.

#### 5g. Summary Output

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

Example output:
```
Result: ✓ 3 succeeded, ✗ 1 failed
Failed hotels:
  - abc-def-ghi: IntegrityError: duplicate key value violates unique constraint
✓ Translations applied successfully!
```

### Phase 5 (Alternative): Dry-Run Termination

```python
else:
    console.print("\n[blue]Dry run - no changes made to database.[/blue]")
```

When `--dry-run` is set, the workflow ends here. No confirmation prompt, no database
writes.

---

## 10. Error Handling and Recovery

### 10.1 Error Isolation Levels

The tool implements error isolation at three granularities, ensuring that a single
failure never cascades into a complete batch failure.

| Level | Location | Mechanism | Effect of Failure |
|---|---|---|---|
| **Field** | `_translate_field()` in `batch_translator.py` | `try/except` around orchestrator call | One field returns source `ERROR`; other fields in the same hotel continue |
| **Hotel** | `_translate_one()` in `batch_translator.py` | `try/except` around `translate_hotel()` | One hotel returns error dict with zero fields; other hotels in the batch continue |
| **Database Write** | `_translate_workflow()` in `translate_cli.py` | Per-hotel `commit`/`rollback` | Failed hotel rolled back; succeeded hotels remain committed |

### 10.2 Field-Level Error Handling

In `BatchHotelTranslator._translate_field()`:

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

The method is `@staticmethod` and never raises. It always returns a `(text, source)`
tuple. When translation fails:
- The translated text is `None`.
- The source is `"ERROR"`.
- A warning is logged via loguru.
- Other fields in the same hotel continue processing.

In `_translate_model_fields()`, the `None` translation is detected:

```python
if translated is not None:
    fields[key] = {"translated": translated, "source": source, "level": level}
else:
    errors.append(f"Translation failed for {key}")
```

The field is excluded from the `fields` dictionary and added to the `errors` list.
In the Rich Table preview, error fields appear as error rows. In exports, error
fields are omitted (they are not in the `fields` dictionary).

### 10.3 Hotel-Level Error Handling

In `BatchHotelTranslator.translate_batch()`:

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

If `translate_hotel()` raises an exception (not just field errors, but a crash in
the entire hotel translation), the hotel is recorded with:
- Zero translated fields.
- A single error entry with the exception message.
- The progress callback still fires (via `finally` block).

Other hotels in the batch proceed normally. The exception is logged at ERROR level.

### 10.4 Per-Hotel Commit and Rollback

This is the most critical recovery mechanism. During the database write phase,
each hotel is committed independently:

```
Hotel 1: update → commit ✓
Hotel 2: update → commit ✓
Hotel 3: update → EXCEPTION → rollback ✗  (only hotel 3 rolled back)
Hotel 4: update → commit ✓
Hotel 5: update → commit ✓
```

The guarantee: hotels 1, 2, 4, and 5 remain committed. Only hotel 3 is rolled back.
This means a batch of 100 hotels with 1 failure leaves 99 hotels successfully
translated.

**Implementation:**

```python
for result in results:
    hotel = hotel_map.get(result["hotel_id"])
    try:
        update_hotel_fields(hotel, result["fields"], ext_map)
        # ... create TranslationHistory records ...
        await db.commit()          # ← Commit ONLY this hotel
        succeeded_hotels.append(result["hotel_id"])
    except Exception as e:
        await db.rollback()        # ← Rollback ONLY this hotel
        failed_hotels.append((result["hotel_id"], str(e)))
```

### 10.5 Edge Case: Hotel Not Reloaded in Session

If a hotel from the translation results cannot be found in the session reload:

```python
hotel = hotel_map.get(result["hotel_id"])
if not hotel:
    failed_hotels.append((result["hotel_id"], "Hotel not reloaded in session"))
    continue
```

This handles edge cases where the hotel was deleted from the database between the
preview phase and the write phase, or where the hotel ID was somehow corrupted.

### 10.6 Edge Case: Empty Original Text

During `TranslationHistory` creation, fields with empty or whitespace-only original
text are skipped:

```python
original_text = get_original_text(hotel, field_key)
if not original_text or not original_text.strip():
    continue  # Don't create TranslationHistory for empty fields
```

This prevents creating audit records for fields like `pet_policy_en` when the hotel
has no pet policy. These fields still appear in exports with source `N/A`.

### 10.7 Recovery Strategy for Interrupted Batches

If a batch is interrupted (process killed mid-write, `Ctrl+C`, power failure):

1. **Hotels already committed** remain in the database with their English translations.
2. **Hotels not yet committed** are unaffected (no partial writes due to per-hotel
   commit).
3. **TranslationHistory** contains records only for committed fields with
   `operator_name = "translate_cli"`.
4. **Recovery:** Re-run the same command. Already-translated fields will hit the
   Redis cache (source `CACHE`) or be re-translated if the cache is unavailable.
   The `name_en IS NULL` filter in `all-untranslated` will exclude hotels that
   were successfully committed.

### 10.8 Common Error Scenarios

| Error | Cause | Resolution |
|---|---|---|
| `Translation failed for name_en` | Tencent MT API error or network timeout | Check API credentials and network; retry |
| `Hotel not reloaded in session` | Hotel deleted between preview and write | Ignore; hotel no longer exists |
| `IntegrityError` | Database constraint violation | Check for duplicate `expedia_hotel_id` or other unique constraints |
| `ConnectionRefusedError` (Redis) | Redis not running | Silently ignored; translations proceed without cache |
| `ImportError: openpyxl` | `openpyxl` not installed for Excel export | `pip install openpyxl` or use `--export-csv` instead |
| `Hotel not found: <uuid>` | UUID does not exist in database | Verify UUID; use `by-search` to find the correct hotel |
| `No hotels found matching: <keyword>` | No hotels match the search | Broaden the search keyword or use `by-filter` |

---

## 11. Advanced Techniques

### 11.1 Dry-Run Then Execute

The standard safe workflow for any batch:

```bash
# Step 1: Preview
python -m scripts.translate_cli by-search "南京" --dry-run --export-csv preview.csv

# Step 2: Review preview.csv in Excel or a text editor

# Step 3: If satisfied, execute
python -m scripts.translate_cli by-search "南京"
```

### 11.2 Incremental Translation by Status

Process hotels in stages based on their review status:

```bash
# Stage 1: Draft hotels (new, likely untranslated) - fast machine-only
python -m scripts.translate_cli by-filter --status draft --no-ai

# Stage 2: Pending review hotels - machine-only
python -m scripts.translate_cli by-filter --status pending_review --no-ai

# Stage 3: Approved hotels (likely need polish) - with AI
python -m scripts.translate_cli by-filter --status approved

# Stage 4: Published hotels (final quality) - with AI
python -m scripts.translate_cli by-filter --status published
```

### 11.3 Brand-by-Brand Migration

When onboarding a new brand or doing a full re-translation:

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

### 11.4 City-by-City Processing

For large-scale migration broken down by city:

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

### 11.5 Cron Job for Periodic Translation

Run daily to catch any new untranslated hotels:

```bash
# crontab entry: daily at 3 AM
0 3 * * * cd /path/to/backend && \
    . venv/bin/activate && \
    yes | python -m scripts.translate_cli all-untranslated --no-ai \
        --export-csv "/var/log/translations/daily_$(date +\%Y\%m\%d).csv" \
        >> /var/log/translations/cron.log 2>&1
```

> [!warning] Cron and `typer.confirm()`
> The confirmation prompt reads from stdin. In cron, pipe `yes` to auto-confirm:
> ```bash
> yes | python -m scripts.translate_cli all-untranslated --no-ai
> ```
> Without `yes`, the cron job will hang indefinitely.

### 11.6 Combining with grep for Targeted Review

```bash
# Export all results
python -m scripts.translate_cli by-brand atour --dry-run --export-csv all.csv

# Filter AI-enhanced translations for manual review
grep "AI_ENHANCED" all.csv > ai_review.csv

# Filter machine translations that might need improvement
grep "MACHINE" all.csv > mt_review.csv

# Filter errors
grep "ERROR" all.csv > errors.csv

# Count sources
echo "CACHE: $(grep -c 'CACHE' all.csv)"
echo "MACHINE: $(grep -c 'MACHINE' all.csv)"
echo "AI_ENHANCED: $(grep -c 'AI_ENHANCED' all.csv)"
echo "ERROR: $(grep -c 'ERROR' all.csv)"
echo "N/A: $(grep -c 'N/A' all.csv)"
```

### 11.7 Comparing Machine vs AI-Enhanced Translations

```bash
HOTEL_ID="550e8400-e29b-41d4-a716-446655440000"

# Machine-only pass
python -m scripts.translate_cli by-id "$HOTEL_ID" --no-ai --dry-run --export-csv mt.csv

# AI-enhanced pass
python -m scripts.translate_cli by-id "$HOTEL_ID" --dry-run --export-csv ai.csv

# Compare translated text column (column 6)
echo "=== Fields where AI changed the translation ==="
diff <(cut -d',' -f6 mt.csv | tail -n +2) <(cut -d',' -f6 ai.csv | tail -n +2)
```

### 11.8 Bulk Retranslation of Specific Fields

To retranslate only certain fields (e.g., `description_en`) for all hotels:

```bash
# 1. Nullify the field in the database
psql -d expedia_db -c "UPDATE hotels SET description_en = NULL WHERE brand = 'atour';"

# 2. Clear Redis cache for these texts (optional, to force fresh translation)
redis-cli FLUSHDB  # WARNING: clears entire Redis DB

# 3. Run the CLI (it translates all fields, but only description_en is NULL)
python -m scripts.translate_cli by-brand atour
```

> [!note] The CLI always translates all 13 fields
> Even though only `description_en` is NULL, the CLI translates all fields. However,
> already-populated fields will likely hit the Redis cache (source `CACHE`) and not
> incur API costs. The database write only overwrites the `description_en` column.

### 11.9 High-Concurrency Tuning

For large batches (100+ hotels), tune concurrency while monitoring:

```bash
# Terminal 1: Monitor database connections
watch -n 1 'psql -d expedia_db -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '\''expedia_db'\'';"'

# Terminal 2: Run translation
python -m scripts.translate_cli all-untranslated --concurrency 15 --no-ai
```

Watch for:
- **Database connection errors:** Reduce `--concurrency` or increase pool size.
- **Tencent API errors:** Increase `--concurrency` slowly; each hotel generates
  multiple parallel API calls internally.
- **Memory usage:** All results held in memory until preview completes.

### 11.10 Pipeline with jq for JSON Processing

If you export to CSV and need JSON output:

```bash
python -m scripts.translate_cli by-brand atour --dry-run --export-csv results.csv

# Convert CSV to JSON with Python
python -c "
import csv, json, sys
reader = csv.DictReader(open('results.csv', encoding='utf-8-sig'))
data = list(reader)
print(json.dumps(data, indent=2, ensure_ascii=False))
" > results.json
```

### 11.11 Conditional Execution Based on Dry-Run

```bash
#!/bin/bash
# safe_translate.sh: Only execute if dry-run shows no errors

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

### 11.12 Logging and Auditing

The CLI does not produce its own log file (output goes to stdout/stderr). For audit
trails, combine with shell redirection:

```bash
# Log everything to a file
python -m scripts.translate_cli by-brand atour 2>&1 | tee "translate_$(date +%Y%m%d_%H%M%S).log"

# Log only errors
python -m scripts.translate_cli by-brand atour 2> "translate_errors_$(date +%Y%m%d).log"
```

For database-level auditing, query the `TranslationHistory` table:

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

## 12. Testing

### 12.1 Test File Location

Tests live in `backend/tests/test_translate_cli.py` (617 lines).

### 12.2 Test Infrastructure

The test suite uses:

| Component | Library | Purpose |
|---|---|---|
| Test runner | `pytest` | Test discovery and execution |
| CLI invocation | `typer.testing.CliRunner` | Invoke Typer commands in tests |
| Test database | `sqlite+aiosqlite:///:memory:` | In-memory SQLite with async support |
| Mocking | `unittest.mock` (`MagicMock`, `AsyncMock`, `patch`) | Mock `BatchHotelTranslator` and `get_db_context` |

### 12.3 Test Architecture

Each test:
1. Creates an in-memory SQLite database with the full Expedia schema.
2. Seeds test hotels with controlled data.
3. Mocks `BatchHotelTranslator.translate_batch` to return predefined results.
4. Mocks `get_db_context` to provide the test database session.
5. Invokes the CLI via `CliRunner`.
6. Asserts on exit codes, output text, and database state.

### 12.4 Test Cases (14 Total)

| # | Test Name | What It Verifies | Key Assertions |
|---|---|---|---|
| 1 | `test_by_id_help` | `--help` flag prints usage | Exit code 0, output contains "UUID" or "HOTEL" |
| 2 | `test_by_id_not_found` | Invalid UUID exits with code 1 | Exit code 1, "not found" in output |
| 3 | `test_by_id_dry_run` | `--dry-run` does not write to DB | "Dry run" in output, `name_en` remains NULL in DB |
| 4 | `test_by_id_confirm_write` | Confirmed write updates DB | `name_en` set to translated value, `TranslationHistory` records created |
| 5 | `test_by_search_found` | Keyword search finds matches | "Found 2 hotel" in output |
| 6 | `test_by_search_not_found` | No matches exits with code 1 | Exit code 1, "No hotels found" in output |
| 7 | `test_by_brand_valid` | Valid brand returns results | Exit code 0, brand name in output |
| 8 | `test_by_brand_invalid` | Invalid brand rejected by Typer | Exit code != 0 |
| 9 | `test_by_filter_multi` | Combined brand + city filter | "Found 1 hotel" in output |
| 10 | `test_by_filter_no_params` | No filter params exits with code 1 | "At least one filter" in output |
| 11 | `test_all_untranslated` | Finds hotels with NULL `name_en` | "1 hotel" or "missing English" in output |
| 12 | `test_csv_export` | CSV has correct 7-column header | Header matches spec, first row has correct level and source |
| 13 | `test_excel_export` | Excel has correct structure | Sheet name "Translations", 7-column header, styled header row |
| 14 | `test_partial_failure_recovery` | One hotel failure does not block others | Success hotel translation visible, error count in output |

### 12.5 Running Tests

```bash
# Run all CLI tests
cd backend
pytest tests/test_translate_cli.py -v

# Run a specific test
pytest tests/test_translate_cli.py::test_by_id_dry_run -v

# Run with verbose output (see print statements)
pytest tests/test_translate_cli.py -v -s

# Run with coverage
pytest tests/test_translate_cli.py --cov=scripts.translate_cli --cov-report=term-missing

# Run with coverage (HTML report)
pytest tests/test_translate_cli.py --cov=scripts.translate_cli --cov-report=html
open htmlcov/index.html
```

> [!note] Excel test dependency
> `test_excel_export` requires `openpyxl`. If not installed, the test is skipped
> via `pytest.importorskip("openpyxl")`. This is safe: the test is not counted as
> a failure when openpyxl is missing.

### 12.6 Test Helper Functions

The test file defines reusable helpers:

```python
def _make_mock_db_context(session_factory):
    """Return a mock get_db_context replacement."""
    @asynccontextmanager
    async def _mock():
        async with session_factory() as session:
            yield session
    return _mock

def _make_translate_result(hotel_id, fields=None, errors=None):
    """Build a result dict matching BatchHotelTranslator.translate_hotel output."""
    return {
        "hotel_id": hotel_id,
        "fields": fields or {"name_en": {"translated": "Test Hotel EN", "source": "CACHE", "level": "hotel"}},
        "errors": errors or [],
    }

async def _seed_hotel(session, **kwargs):
    """Insert a single hotel and return its id + name_cn."""
    defaults = {"name_cn": "测试酒店", "name_en": None, "brand": HotelBrand.ATour, ...}
    defaults.update(kwargs)
    hotel = Hotel(**defaults)
    session.add(hotel)
    await session.flush()
    await session.refresh(hotel)
    return {"id": str(hotel.id), "name_cn": hotel.name_cn}
```

---

## 13. FAQ

### General Questions

#### Q1: What happens if Redis is down?

The tool continues without caching. Phase 1 of `_translate_workflow` catches all
exceptions from Redis initialization and silently ignores them. Translations still
work via direct API calls. The only downside: repeated translations of the same
text will call the API again instead of hitting the cache.

#### Q2: How do I cancel a running translation?

Press `Ctrl+C`. The process terminates immediately. Hotels that were already
committed to the database remain committed (per-hotel commit guarantee). Hotels
in the middle of translation or not yet started are unaffected. Re-run the command
to process remaining hotels.

#### Q3: Can I translate only specific fields?

Not directly. The `BatchHotelTranslator` always translates all 13 fields for every
hotel. To selectively retranslate:

1. Clear the target columns in the database (set them to NULL).
2. Run the CLI. Already-populated fields will hit the Redis cache.
3. Only the NULL fields will generate new API calls.

To permanently exclude fields, modify `HOTEL_FIELDS`, `ROOM_FIELDS`, or
`ROOM_EXTENSION_FIELDS` in `batch_translator.py`.

#### Q4: What is the difference between MACHINE and HYBRID translation types?

| Aspect | MACHINE (`--no-ai`) | HYBRID (default) |
|---|---|---|
| Pipeline steps | Cache → Terminology → Reference → MT | Cache → Terminology → Reference → MT → AI |
| API calls | Tencent MT only | Tencent MT + DeepSeek |
| Speed | Fast (one API call per text) | Slower (two API calls per text) |
| Cost | Lower (MT only) | Higher (MT + AI tokens) |
| Quality | Good for simple texts | Better for nuanced/policy texts |
| Source in results | `MACHINE` | `AI_ENHANCED` or `MACHINE` |

Use `--no-ai` for initial bulk passes. Use the default (with AI) for final polish.

#### Q5: Why do some fields show source "N/A"?

Fields with empty or whitespace-only Chinese source text are skipped by
`_translate_field()`:

```python
if not text or not text.strip():
    return (text or "", "N/A")
```

No API call is made. This is normal for optional fields like `pet_policy`,
`cancellation_policy`, or `description` that many hotels leave blank.

### Field and Export Questions

#### Q6: How are room and room extension fields identified in exports?

Room fields use the format `<room_id>:<field_name>`:

| Export Key | Meaning |
|---|---|
| `abc123:name_en` | `name_en` of room `abc123` (level: `room`) |
| `abc123:amenities_en` | `amenities_en` of RoomExtension for room `abc123` (level: `room_extension`) |

The `Level` column in exports also distinguishes them. The room UUID prefix ensures
uniqueness since `name_en` exists on both `Hotel` and `Room`.

#### Q7: What happens if the AI enhancement API fails?

The tool falls back to the machine translation result. In the orchestrator's
`translate()` method, step 5 is wrapped in a try/except:

```python
try:
    ai_result = await self.ai_client.enhance_translation(...)
    if enhanced_text and enhanced_text != translated_text:
        translated_text = enhanced_text
        source = TranslationSource.AI_ENHANCED
except Exception as e:
    logger.warning(f"AI enhancement failed, using MT result: {e}")
```

The translation proceeds with the MT output, and the source remains `MACHINE`.
The field is NOT marked as `ERROR`.

#### Q8: How are TranslationHistory records created?

Each translated field generates one `TranslationHistory` row. Key fields:

| Field | Value | Notes |
|---|---|---|
| `source_text` | Chinese original | From `get_original_text()` |
| `translated_text` | English result | From translation result |
| `translation_type` | `HYBRID` or `MACHINE` | Depends on `--no-ai` |
| `operator_name` | `"translate_cli"` | Identifies CLI as the source |
| `review_status` | `PENDING` | All CLI translations start pending |
| `reference_used` | `False` | Not tracked at field level |
| `glossary_used` | `False` | Not tracked at field level |
| `confidence_score` | `None` | MT/AI don't return per-field confidence |

### Operational Questions

#### Q9: Can I use this tool in a CI/CD pipeline?

Yes. Use `--dry-run` for validation and `--no-ai` for speed:

```bash
# Validation step (fails pipeline on errors)
python -m scripts.translate_cli by-filter --status draft --dry-run --no-ai \
    --export-csv ci_preview.csv
if grep -q ",ERROR," ci_preview.csv; then
    echo "Translation errors detected!" >&2
    exit 1
fi

# Execution step (auto-confirm with yes)
yes | python -m scripts.translate_cli by-filter --status draft --no-ai
```

#### Q10: Why does `all-untranslated` only check `name_en`?

The query `Hotel.name_en.is_(None)` is a heuristic: if a hotel has no English name,
it is very likely that none of its other English fields are populated either. This
avoids an expensive multi-column NULL check. Hotels with `name_en` but missing other
fields must be targeted with `by-filter` or `by-search`.

#### Q11: How do I find a hotel's UUID?

```bash
# From database
psql -d expedia_db -c "SELECT id, name_cn, brand, city FROM hotels WHERE name_cn ILIKE '%keyword%';"

# From REST API
curl -s http://localhost:8000/api/v1/hotels?search=keyword | jq '.items[] | {id, name_cn}'

# From a previous CSV export (first column)
head -3 previous_export.csv
```

#### Q12: What is the maximum batch size?

There is no hard limit. The tool processes all matching hotels regardless of count.
Practical limits come from:

- **Database connection pool:** Default typically 10-20 connections. Each hotel uses
  one connection during translation. With `--concurrency 15`, you need at least 15
  connections available.
- **Tencent Cloud MT rate limits:** Check your Tencent Cloud quota.
- **Memory:** All results for all hotels are held in memory until the preview
  completes. For 500 hotels with 3 rooms each, that is `500 * 21 = 10,500` field
  results, each a small dictionary. Memory usage is manageable.
- **Time:** With `--concurrency 5` and `--no-ai`, expect roughly 1-3 seconds per
  hotel. With AI enhancement, 3-8 seconds per hotel.

For batches exceeding 500 hotels, consider splitting by brand or city.

#### Q13: Can I translate from English to Chinese?

The tool is hardcoded for Chinese-to-English:

```python
DEFAULT_SOURCE_LANG = "zh"
DEFAULT_TARGET_LANG = "en"
```

The orchestrator and Tencent client support any language pair, but the
`BatchHotelTranslator` and CLI tool use these constants. To support reverse
translation, these would need to be parameterized and the field mappings would
need to be inverted.

#### Q14: What happens to the progress bar after completion?

The progress bar is created with `transient=True`:

```python
with Progress(transient=True) as progress:
```

This means it disappears from the terminal after completion. Only the final Rich
Table preview and summary remain visible. This keeps the terminal output clean.

#### Q15: How can I verify translations were applied correctly?

```bash
# Check a specific hotel
psql -d expedia_db -c "SELECT name_cn, name_en, address_en FROM hotels WHERE id = '<uuid>';"

# Check all hotels translated today
psql -d expedia_db -c "
    SELECT h.name_cn, h.name_en, th.created_at
    FROM hotels h
    JOIN translation_histories th ON th.source_text = h.name_cn
    WHERE th.operator_name = 'translate_cli'
    AND th.created_at > CURRENT_DATE
    ORDER BY th.created_at DESC;
"

# Count translations by type
psql -d expedia_db -c "
    SELECT translation_type, count(*)
    FROM translation_histories
    WHERE operator_name = 'translate_cli'
    GROUP BY translation_type;
"
```

#### Q16: How do I roll back a batch of translations?

There is no built-in rollback command. Manual rollback options:

```sql
-- Rollback all translations by the CLI from today
UPDATE hotels SET name_en = NULL, address_en = NULL, /* ... all 9 fields ... */
WHERE id IN (
    SELECT DISTINCT h.id FROM hotels h
    JOIN translation_histories th ON th.source_text = h.name_cn
    WHERE th.operator_name = 'translate_cli' AND th.created_at > CURRENT_DATE
);

-- Delete the history records
DELETE FROM translation_histories
WHERE operator_name = 'translate_cli' AND created_at > CURRENT_DATE;
```

> [!warning] Manual rollback is destructive
> Always back up the database before manual rollback operations. Consider using
> database snapshots or transaction dumps.

---

## Appendix A: Complete Option Reference

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

## Appendix B: Source Code Index

| File | Lines | Purpose |
|---|---|---|
| `backend/scripts/translate_cli.py` | 662 | CLI entry point: 5 subcommands, export functions, `_translate_workflow` |
| `backend/app/services/translation/batch_translator.py` | 339 | `BatchHotelTranslator`: field mappings, concurrent hotel translation |
| `backend/app/services/translation/orchestrator.py` | 557 | `TranslationOrchestrator`: 7-step translation pipeline |
| `backend/app/models/hotel.py` | 249 | `Hotel`, `Room`, `HotelBrand`, `HotelStatus` models |
| `backend/app/models/room.py` | 82 | `RoomExtension` model |
| `backend/app/models/translation.py` | 267 | `TranslationHistory`, `TranslationType`, `ReviewStatus` models |
| `backend/app/schemas/translation/__init__.py` | 269 | `TranslationSource`, `TranslationResult`, request/response schemas |
| `backend/tests/test_translate_cli.py` | 617 | 14 integration tests for the CLI tool |

---

## Appendix C: Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | None | PostgreSQL connection string (asyncpg format) |
| `REDIS_URL` | No | None | Redis connection string |
| `TENCENT_SECRET_ID` | Yes | None | Tencent Cloud API Secret ID |
| `TENCENT_SECRET_KEY` | Yes | None | Tencent Cloud API Secret Key |
| `TENCENT_REGION` | No | `ap-guangzhou` | Tencent Cloud region |
| `DEEPSEEK_API_KEY` | No | None | DeepSeek API key (needed without `--no-ai`) |
| `DEEPSEEK_BASE_URL` | No | `https://api.deepseek.com` | DeepSeek API base URL |
| `APP_ENV` | No | `development` | Application environment |
| `LOG_LEVEL` | No | `DEBUG` | Loguru log level |

---

## Appendix D: Exit Codes

| Code | Meaning |
|---|---|
| 0 | Success: all hotels processed, or all hotels already have English names |
| 1 | Error: hotel not found, no hotels match query, at least one filter required, invalid status value, Excel export failed (openpyxl not installed) |
| 2 | Error: Typer argument parsing error (invalid brand, missing required argument) |

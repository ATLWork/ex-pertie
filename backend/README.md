# Expedia 酒店表格生成工具 - 后端服务

## 技术栈

- Python 3.11+
- FastAPI 0.110+
- SQLAlchemy 2.0 (async)
- PostgreSQL (asyncpg)
- Redis
- pydantic-settings
- loguru

## 开发环境设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # 核心模块
│   ├── middleware/          # 中间件
│   ├── schemas/             # Pydantic 模型
│   ├── models/              # SQLAlchemy 模型
│   ├── services/            # 业务逻辑
│   ├── api/                 # API 路由
│   └── utils/               # 工具函数
├── tests/                   # 测试文件
├── alembic/                 # 数据库迁移
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## CLI 翻译工具

内置命令行翻译工具，用于批量将酒店主数据从中文翻译为英文，并可选写回数据库。

### 安装说明

依赖 `typer` 和 `rich`，已包含在 `requirements.txt` 中，安装依赖后即可使用。

### 快速开始

工具提供 5 个子命令，覆盖不同查询场景：

```bash
# 按 UUID 翻译单个酒店
python -m scripts.translate_cli by-id <uuid>

# 按关键词搜索并翻译（模糊匹配 name_cn 或 name_en）
python -m scripts.translate_cli by-search <keyword>

# 按品牌批量翻译（atour / atour_x / zhotel / ahaus）
python -m scripts.translate_cli by-brand atour

# 按多条件筛选翻译（品牌、城市、国家、状态可组合）
python -m scripts.translate_cli by-filter --brand atour --city 上海

# 一键翻译所有缺少英文名的酒店
python -m scripts.translate_cli all-untranslated
```

### 使用建议

- 首次使用建议先加 `--dry-run` 参数预览翻译结果，确认无误后再正式执行
- `by-search` 子命令支持对 name_cn 和 name_en 的模糊匹配
- `by-filter` 子命令的 `--status` 参数支持 draft / pending_review / approved / published / suspended
- `by-id` 子命令需要传入完整的酒店 UUID（可在数据库或 API 响应中获取）
- `all-untranslated` 适合初次批量翻译时一次性补齐缺失字段
- 所有命令都支持 `--export-csv` / `--export-excel` 导出翻译结果为文件

### 全局参数

所有子命令共享以下参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--dry-run` | false | 仅预览不写库 |
| `--no-ai` | false | 禁用 AI 增强 |
| `--concurrency` | 5 | 并发翻译数 |
| `--export-csv` | - | 导出 CSV 文件路径 |
| `--export-excel` | - | 导出 Excel 文件路径 |

### 导出示例

```bash
# 翻译并导出为 Excel
python -m scripts.translate_cli by-brand atour --export-excel atour_translations.xlsx
```

### 翻译字段说明

共 13 个字段参与翻译流程，分属三个模型：

**Hotel（9 个）**
| 字段 | 原文字段 | 说明 |
|------|-----------|------|
| `name_en` | name_cn | 酒店英文名 |
| `address_en` | address_cn | 英文地址 |
| `cancellation_policy_en` | cancellation_policy | 取消政策 |
| `prepayment_policy_en` | prepayment_policy | 预付政策 |
| `kid_policy_en` | kid_policy | 儿童政策 |
| `pet_policy_en` | pet_policy | 宠物政策 |
| `services_en` | services | 酒店服务 |
| `facilities_en` | facilities | 酒店设施 |
| `description_en` | description | 酒店描述 |

**Room（2 个）**
| 字段 | 原文字段 | 说明 |
|------|-----------|------|
| `name_en` | name_cn | 房型英文名 |
| `description_en` | description_cn | 房型描述 |

**RoomExtension（2 个）**
| 字段 | 原文字段 | 说明 |
|------|-----------|------|
| `amenities_en` | amenities_cn | 房间设施 |
| `bathroom_amenities_en` | bathroom_amenities_cn | 卫浴设施 |

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

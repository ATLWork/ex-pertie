# Python 后端技术栈迁移设计文档

## 概述

将 Expedia 酒店表格生成工具的后端从 Next.js/TypeScript 迁移到 Python 技术栈，采用前后端分离架构。

---

## 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│              前端 (Next.js 14.x)                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  前端层: 数据导入 | 翻译工作台 | 数据管理 | 导出中心    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│              后端 (FastAPI)                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  API层: 认证鉴权 | 业务逻辑 | 数据处理                │   │
│  │  (FastAPI + SQLAlchemy + Pydantic)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                              │
│  ┌──────────────────────┐  ┌───────────────────────────┐   │
│  │ MySQL 8.x (生产环境)  │  │ SQLite (开发环境)         │   │
│  └──────────────────────┘  └───────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      外部服务层                              │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ 腾讯云翻译 API    │  │ AI大模型 (OpenAI兼容API)        │  │
│  │ (基础翻译)       │  │ 生产: 阿里百炼 / 开发: StepFun  │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**关键变化**：
- 原单体 Next.js 应用拆分为前后端分离架构
- 前端继续使用 Next.js，通过 HTTP REST 调用后端 API
- 后端独立为 FastAPI 服务，部署在阿里云函数计算

---

## 2. 技术选型

| 类别 | 技术 | 版本 | 用途 |
|-----|------|------|------|
| Web框架 | FastAPI | 0.110+ | RESTful API |
| ORM | SQLAlchemy | 2.0+ | 数据库操作（异步） |
| 数据验证 | Pydantic | 2.x | 请求/响应模型 |
| 数据库驱动 | aiomysql / aiosqlite | 最新 | 异步数据库连接 |
| 认证 | python-jose + passlib | 最新 | JWT + 密码哈希 |
| 文件处理 | openpyxl / pandas | 最新 | Excel 导入导出 |
| HTTP客户端 | httpx | 最新 | 异步外部API调用 |
| 配置管理 | pydantic-settings | 最新 | 环境变量管理 |
| 数据库迁移 | Alembic | 最新 | 数据库版本控制 |

---

## 3. 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── base.py          # 基础模型
│   │   ├── hotel.py         # 酒店模型
│   │   ├── room.py          # 客房模型
│   │   ├── translation.py   # 翻译模型
│   │   └── user.py          # 用户模型
│   ├── schemas/             # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── hotel.py
│   │   ├── room.py
│   │   ├── translation.py
│   │   └── user.py
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py          # 依赖注入
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── hotels.py
│   │       ├── rooms.py
│   │       ├── translate.py
│   │       ├── import_.py
│   │       ├── export.py
│   │       ├── terminology.py
│   │       ├── rules.py
│   │       └── auth.py
│   ├── services/            # 业务逻辑
│   │   ├── __init__.py
│   │   ├── hotel_service.py
│   │   ├── translation_service.py
│   │   ├── import_service.py
│   │   └── export_service.py
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── security.py      # JWT/密码处理
│   │   ├── exceptions.py    # 自定义异常
│   │   └── cache.py         # 缓存服务
│   └── utils/               # 工具函数
│       ├── __init__.py
│       └── validators.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_hotels.py
├── alembic/                 # 数据库迁移
│   ├── versions/
│   └── env.py
├── alembic.ini
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## 4. API 设计

### 4.1 基础约定

- 基础路径: `/api/v1`
- 认证方式: JWT Bearer Token
- 响应格式: JSON
- 编码: UTF-8

### 4.2 统一响应格式

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: T
    timestamp: int

class PagedData(BaseModel, Generic[T]):
    list: List[T]
    total: int
    page: int
    pageSize: int

class PagedResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: PagedData[T]
    timestamp: int
```

### 4.3 核心接口列表

#### 数据导入接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /import/hotels | 导入酒店主数据 |
| POST | /import/rooms | 导入客房主数据 |
| GET | /import/templates | 下载导入模板 |
| GET | /import/history | 导入历史记录 |
| GET | /import/{id}/errors | 获取导入错误详情 |

#### 酒店数据接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /hotels | 获取酒店列表 |
| GET | /hotels/{id} | 获取酒店详情 |
| PUT | /hotels/{id} | 更新酒店信息 |
| DELETE | /hotels/{id} | 删除酒店 |
| GET | /hotels/{id}/rooms | 获取酒店房间列表 |

#### 翻译接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /translate | 执行翻译 |
| POST | /translate/batch | 批量翻译 |
| GET | /translate/history | 翻译历史 |
| PUT | /translate/{id} | 更新翻译结果 |
| POST | /translate/verify | 验证翻译质量 |

#### 导出接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /export | 创建导出任务 |
| GET | /export/{id} | 查询导出状态 |
| GET | /export/{id}/download | 下载导出文件 |
| GET | /export/history | 导出历史记录 |

---

## 5. 数据库模型

### 5.1 酒店模型 (Hotel)

```python
from sqlalchemy import Column, String, Integer, Float, Text, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum

class HotelStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(String(36), primary_key=True)
    hotel_id = Column(String(50), unique=True, nullable=False, index=True)
    name_zh = Column(String(255), nullable=False)
    name_en = Column(String(255))
    address_zh = Column(Text, nullable=False)
    address_en = Column(Text)
    province = Column(String(50), nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    star_rating = Column(Integer)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description_zh = Column(Text)
    description_en = Column(Text)
    status = Column(Enum(HotelStatus), default=HotelStatus.draft)

    # 关联关系
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    translations = relationship("Translation", back_populates="hotel", cascade="all, delete-orphan")
```

### 5.2 客房模型 (Room)

```python
from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base

class BedType(str, enum.Enum):
    KING = "KING"
    TWIN = "TWIN"
    SINGLE = "SINGLE"
    SUPER_KING = "SUPER_KING"
    TATAMI = "TATAMI"

class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True)
    hotel_id = Column(String(36), ForeignKey("hotels.id"), nullable=False, index=True)
    room_type_zh = Column(String(255), nullable=False)
    room_type_en = Column(String(255))
    area = Column(Float)
    bed_type = Column(Enum(BedType), nullable=False)
    bed_count = Column(Integer, nullable=False)
    max_occupancy = Column(Integer, nullable=False)

    # 关联关系
    hotel = relationship("Hotel", back_populates="rooms")
```

---

## 6. 认证与安全

### 6.1 JWT 认证

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### 6.2 依赖注入

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
```

---

## 7. 错误处理

### 7.1 自定义异常

```python
from fastapi import HTTPException, status

class AppException(Exception):
    def __init__(self, code: int, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

# 业务错误
class ImportError(AppException):
    def __init__(self, details: dict = None):
        super().__init__(1001, "数据导入失败", details)

class ValidationError(AppException):
    def __init__(self, details: dict = None):
        super().__init__(1002, "数据校验失败", details)

class TranslationError(AppException):
    def __init__(self, details: dict = None):
        super().__init__(1003, "翻译失败", details)

class ExportError(AppException):
    def __init__(self, details: dict = None):
        super().__init__(1004, "导出失败", details)
```

### 7.2 全局异常处理

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=400,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": exc.details,
            "timestamp": int(datetime.now().timestamp())
        }
    )
```

---

## 8. 部署配置

### 8.1 开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 8.2 阿里云函数计算部署

```yaml
# s.yaml
edition: 1.0.0
name: expertie-backend
access: default

services:
  expertie-api:
    component: fc
    props:
      region: cn-shanghai
      service:
        name: expertie-service
        description: Expedia酒店表格生成工具后端
        logConfig: auto
      function:
        name: api
        runtime: custom.debian10
        codeUri: ./
        handler: index.handler
        memorySize: 512
        timeout: 60
        instanceConcurrency: 10
        environmentVariables:
          DATABASE_URL: ${env.MYSQL_URL}
          SECRET_KEY: ${env.SECRET_KEY}
      triggers:
        - name: http-trigger
          type: http
          config:
            authType: anonymous
            methods:
              - GET
              - POST
              - PUT
              - DELETE
              - OPTIONS
```

---

## 9. 迁移计划

### 9.1 迁移步骤

1. **创建后端项目骨架** - 初始化 FastAPI 项目结构
2. **数据库模型迁移** - 将 Prisma schema 转换为 SQLAlchemy models
3. **API 路由实现** - 实现 RESTful API 端点
4. **业务逻辑迁移** - 迁移 services 层业务代码
5. **认证系统实现** - 实现 JWT 认证
6. **测试覆盖** - 编写单元测试和集成测试
7. **部署配置** - 配置阿里云函数计算

### 9.2 风险与应对

| 风险 | 应对措施 |
|-----|---------|
| 数据库迁移兼容性 | 使用 Alembic 管理迁移，开发环境先验证 |
| API 接口变更 | 保持与原 API 相同的路径和响应格式 |
| 前端适配 | 前端只需修改 API 基础 URL |
| 性能差异 | 异步数据库操作 + 连接池优化 |

---

**文档版本**: v1.0
**创建日期**: 2026-04-08
**作者**: Claude

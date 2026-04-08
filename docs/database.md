# 数据库设计文档

## 概述

- **生产环境**: MySQL 8.x (阿里云RDS)
- **开发环境**: SQLite (本地文件数据库)
- **ORM**: Prisma 5.x

---

## 核心数据表

**说明**: 以下为MySQL语法，开发环境使用Prisma ORM自动适配SQLite。

### 酒店主数据表

```sql
CREATE TABLE hotels (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  hotel_id VARCHAR(50) UNIQUE NOT NULL,     -- 业务ID
  name_zh VARCHAR(200) NOT NULL,            -- 中文名
  name_en VARCHAR(200),                      -- 英文名
  address_zh TEXT,                           -- 中文地址
  address_en TEXT,                           -- 英文地址
  city VARCHAR(100),
  province VARCHAR(100),
  phone VARCHAR(50),
  email VARCHAR(100),
  star_rating INT,
  facilities JSON,                           -- 设施数组
  services JSON,                             -- 服务数组
  description_zh TEXT,
  description_en TEXT,
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  status VARCHAR(20) DEFAULT 'draft',        -- draft/active/archived
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  created_by VARCHAR(36)
);
```

### 客房主数据表

```sql
CREATE TABLE rooms (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  hotel_id VARCHAR(50),                      -- 关联酒店业务ID
  room_type_zh VARCHAR(200) NOT NULL,        -- 房型中文名
  room_type_en VARCHAR(200),                 -- 房型英文名
  area DECIMAL(10, 2),                       -- 面积(平方米)
  bed_type VARCHAR(100),                     -- 床型
  bed_count INT,                             -- 床数量
  max_occupancy INT,                         -- 最大入住人数
  facilities JSON,                           -- 房间设施
  amenities JSON,                            -- 房间用品
  description_zh TEXT,
  description_en TEXT,
  status VARCHAR(20) DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 翻译规则表

```sql
CREATE TABLE translation_rules (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  name VARCHAR(200) NOT NULL,                -- 规则名称
  category VARCHAR(50),                      -- 分类: company/province/city/country
  scope VARCHAR(200),                        -- 适用范围: 省市/国家
  content TEXT NOT NULL,                     -- 规则内容(解析后的文本)
  source_file VARCHAR(500),                  -- 来源文件路径
  priority INT DEFAULT 0,                    -- 优先级(数值越大越优先)
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 翻译参考库表

```sql
CREATE TABLE translation_references (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  source_type VARCHAR(20),                   -- ctrip/booking
  source_id VARCHAR(100),                    -- 源平台ID
  field_type VARCHAR(50),                    -- 字段类型: hotel_name/room_type/facility等
  text_zh TEXT NOT NULL,                     -- 中文原文
  text_en TEXT NOT NULL,                     -- 英文译文
  hotel_id VARCHAR(50),                      -- 关联酒店
  quality_score DECIMAL(3,2),                -- 质量评分
  is_verified BOOLEAN DEFAULT false,         -- 是否已验证
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 翻译历史表

```sql
CREATE TABLE translation_history (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  entity_type VARCHAR(50),                   -- hotel/room
  entity_id VARCHAR(36),                     -- 关联实体ID
  field_name VARCHAR(100),                   -- 字段名
  original_text TEXT,                        -- 原文
  translated_text TEXT,                      -- 译文
  translation_method VARCHAR(50),            -- reference/tencent/ai
  reference_source VARCHAR(100),             -- 参考来源
  ai_prompt TEXT,                            -- AI提示词
  is_edited BOOLEAN DEFAULT false,           -- 是否人工编辑
  edited_by VARCHAR(36),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 术语库表

```sql
CREATE TABLE terminology (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  term_zh VARCHAR(200) NOT NULL,             -- 中文术语
  term_en VARCHAR(200) NOT NULL,             -- 英文术语
  category VARCHAR(50),                      -- 分类: hotel/room/facility/service/location
  context TEXT,                              -- 使用语境
  is_verified BOOLEAN DEFAULT false,
  verified_by VARCHAR(36),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 用户表

```sql
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  username VARCHAR(100) UNIQUE NOT NULL,
  email VARCHAR(200) UNIQUE NOT NULL,
  password_hash VARCHAR(200) NOT NULL,
  role VARCHAR(20) DEFAULT 'operator',       -- admin/operator/translator/viewer
  is_active BOOLEAN DEFAULT true,
  last_login_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 导出记录表

```sql
CREATE TABLE export_records (
  id VARCHAR(36) PRIMARY KEY,               -- UUID字符串
  user_id VARCHAR(36),
  export_type VARCHAR(20),                   -- excel/csv/json
  hotel_count INT,
  room_count INT,
  file_path VARCHAR(500),
  status VARCHAR(20),                        -- processing/completed/failed
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 索引设计

**说明**: MySQL不支持INCLUDE子句和GIN全文索引，以下为简化后的索引设计。翻译参考库查询使用LIKE模糊匹配替代全文搜索。

```sql
-- 查询优化索引
CREATE INDEX idx_hotels_province_city ON hotels(province, city);
CREATE INDEX idx_hotels_status ON hotels(status);
CREATE INDEX idx_hotels_created_at ON hotels(created_at);
CREATE INDEX idx_rooms_hotel_id ON rooms(hotel_id);

-- 复合索引
CREATE INDEX idx_hotels_list ON hotels(status, province, city);

-- 翻译参考索引
CREATE INDEX idx_trans_ref_type ON translation_references(source_type, field_type);
CREATE INDEX idx_trans_ref_hotel ON translation_references(hotel_id);
```

---

## ER 关系图

```
┌─────────────┐     ┌─────────────┐
│   users     │     │   hotels    │
├─────────────┤     ├─────────────┤
│ id          │────▶│ created_by  │
│ username    │     │ id          │────┐
│ email       │     │ hotel_id    │    │
│ role        │     │ name_zh     │    │
└─────────────┘     │ name_en     │    │
                    │ ...         │    │
                    └─────────────┘    │
                           │           │
                           ▼           │
                    ┌─────────────┐    │
                    │    rooms    │    │
                    ├─────────────┤    │
                    │ id          │    │
                    │ hotel_id ◀──┼────┘
                    │ room_type   │
                    │ ...         │
                    └─────────────┘

┌──────────────────┐     ┌─────────────────────┐
│translation_rules │     │translation_references│
├──────────────────┤     ├─────────────────────┤
│ id               │     │ id                  │
│ name             │     │ source_type         │
│ category         │     │ field_type          │
│ priority         │     │ text_zh             │
│ ...              │     │ text_en             │
└──────────────────┘     └─────────────────────┘
```

---

**文档版本**: v1.0
**最后更新**: 2026-04-08

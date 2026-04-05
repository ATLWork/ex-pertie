# Expedia 酒店表格生成工具 - 技术设计文档

## 一、技术架构

### 1.1 系统架构图
```
┌─────────────────────────────────────────────────────────────┐
│              全栈应用 (Next.js)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  前端层: 数据导入 | 翻译工作台 | 数据管理 | 导出中心    │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  API层: 认证鉴权 | 业务逻辑 | 数据处理                │   │
│  │  (Next.js API Routes)                               │   │
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

**架构说明**:
- 采用 Next.js 14 全栈框架，前后端一体化开发
- 支持阿里云云函数部署
- 文件上传后内存处理，解析完成后丢弃，不保留原文件
- 数据库根据环境自动切换：生产环境使用MySQL，开发环境使用SQLite

### 1.2 技术选型

#### 1.2.1 全栈技术栈
| 技术 | 版本 | 用途 |
|-----|------|------|
| Next.js | 14.x | 全栈框架 (App Router) |
| React | 18.x | UI库 |
| TypeScript | 5.x | 类型安全 |
| Ant Design | 5.x | UI 组件库 |
| Zustand | 4.x | 状态管理 |
| TanStack Query | 5.x | 数据请求 |
| Prisma | 5.x | ORM框架 |

#### 1.2.2 数据库
| 环境 | 数据库 | 说明 |
|-----|--------|------|
| 生产环境 | MySQL 8.x | 阿里云RDS |
| 开发环境 | SQLite | 本地文件数据库 |

#### 1.2.3 AI/翻译服务
| 服务 | 环境 | 用途 |
|-----|------|------|
| 阿里百炼 | 生产环境 | AI翻译润色、规则理解 |
| StepFun | 开发环境 | AI翻译润色、规则理解 |
| 腾讯云翻译 API | 全环境 | 基础翻译 |

**说明**:
- AI服务统一使用 OpenAI 兼容 API 接口
- 通过环境变量 `AI_PROVIDER` 切换服务商
- 生产环境使用阿里百炼 (DashScope)，开发环境使用 StepFun

---

## 二、数据库设计

### 2.1 核心数据表

**说明**: 以下为MySQL语法，开发环境使用Prisma ORM自动适配SQLite。

```sql
-- 酒店主数据表
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

-- 客房主数据表
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

-- 翻译规则表
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

-- 翻译参考库表
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

-- 翻译历史表
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

-- 术语库表
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

-- 用户表
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

-- 导出记录表
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

### 2.2 索引设计

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

## 三、API 接口设计

### 3.1 接口规范

#### 3.1.1 基础约定
- 基础路径: `/api/v1`
- 认证方式: JWT Bearer Token
- 响应格式: JSON
- 编码: UTF-8

#### 3.1.2 统一响应格式
```typescript
interface ApiResponse<T> {
  code: number;        // 状态码
  message: string;     // 消息
  data: T;            // 数据
  timestamp: number;   // 时间戳
}

interface PagedResponse<T> {
  code: number;
  message: string;
  data: {
    list: T[];
    total: number;
    page: number;
    pageSize: number;
  };
  timestamp: number;
}
```

### 3.2 核心接口列表

#### 3.2.1 数据导入接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /import/hotels | 导入酒店主数据 |
| POST | /import/rooms | 导入客房主数据 |
| GET | /import/templates | 下载导入模板 |
| GET | /import/history | 导入历史记录 |
| GET | /import/{id}/errors | 获取导入错误详情 |

**导入酒店数据请求示例:**
```typescript
// POST /api/v1/import/hotels
// Content-Type: multipart/form-data

{
  file: File,           // Excel文件
  overwrite: boolean    // 是否覆盖重复数据
}

// 响应
{
  "code": 200,
  "message": "导入成功",
  "data": {
    "total": 100,
    "success": 95,
    "failed": 5,
    "errors": [
      {
        "row": 15,
        "field": "phone",
        "error": "手机号格式不正确"
      }
    ]
  }
}
```

#### 3.2.2 酒店数据接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /hotels | 获取酒店列表 |
| GET | /hotels/{id} | 获取酒店详情 |
| PUT | /hotels/{id} | 更新酒店信息 |
| DELETE | /hotels/{id} | 删除酒店 |
| GET | /hotels/{id}/rooms | 获取酒店房间列表 |

**酒店列表查询参数:**
```typescript
interface HotelQueryParams {
  page?: number;           // 页码，默认1
  pageSize?: number;       // 每页数量，默认20
  keyword?: string;        // 关键词搜索
  province?: string;       // 省份筛选
  city?: string;           // 城市筛选
  status?: 'draft' | 'active' | 'archived';  // 状态筛选
  hasTranslation?: boolean; // 是否有翻译
}
```

#### 3.2.3 翻译接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /translate | 执行翻译 |
| POST | /translate/batch | 批量翻译 |
| GET | /translate/history | 翻译历史 |
| PUT | /translate/{id} | 更新翻译结果 |
| POST | /translate/verify | 验证翻译质量 |

**翻译请求示例:**
```typescript
// POST /api/v1/translate
{
  "entityType": "hotel",      // hotel/room
  "entityId": "uuid",
  "field": "name",            // 字段名
  "text": "亚朵酒店",          // 原文
  "targetLang": "en"          // 目标语言
}

// 响应
{
  "code": 200,
  "message": "翻译成功",
  "data": {
    "originalText": "亚朵酒店",
    "translatedText": "Atour Hotel",
    "method": "reference",     // reference/tencent/ai
    "referenceSource": "booking",
    "confidence": 0.95,
    "alternatives": [
      {
        "text": "Atour Hotel",
        "source": "booking",
        "score": 0.98
      }
    ]
  }
}
```

#### 3.2.4 导出接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| POST | /export | 创建导出任务 |
| GET | /export/{id} | 查询导出状态 |
| GET | /export/{id}/download | 下载导出文件 |
| GET | /export/history | 导出历史记录 |

#### 3.2.5 术语库接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /terminology | 获取术语列表 |
| POST | /terminology | 添加术语 |
| PUT | /terminology/{id} | 更新术语 |
| DELETE | /terminology/{id} | 删除术语 |
| POST | /terminology/import | 批量导入术语 |
| GET | /terminology/export | 导出术语库 |

#### 3.2.6 翻译规则接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /rules | 获取规则列表 |
| POST | /rules | 添加翻译规则 |
| PUT | /rules/{id} | 更新规则 |
| DELETE | /rules/{id} | 删除规则 |
| POST | /rules/upload | 上传规则文件(PDF) |

---

## 四、核心业务流程

### 4.1 数据导入与处理流程

```
用户 → 前端 → API网关 → 导入服务 → 校验服务 → 数据库

流程步骤:
1. 用户上传Excel文件
2. 前端发送POST请求到 /api/import/hotels
3. API网关转发请求到导入服务
4. 导入服务解析文件格式
5. 调用校验服务进行字段检查
6. 校验通过后批量插入数据库
7. 返回导入结果(成功数/失败数/错误详情)
```

### 4.2 翻译处理流程

```
选择待翻译数据 → 查询参考库 → 腾讯云翻译 → AI润色 → 人工审核 → 保存

详细步骤:
1. 用户选择待翻译数据
2. 系统查询翻译参考库(携程/Booking)
   - 命中: 使用参考译文，AI校验润色
   - 未命中: 调用腾讯云翻译API
3. AI大模型根据翻译规则进行润色
4. 展示翻译结果供人工审核
5. 审核通过后保存翻译结果
```

### 4.3 数据导出流程

```
选择导出数据 → 数据校验 → 选择格式 → 生成文件 → 下载

校验清单:
□ 所有必填字段已填充
□ 数据格式符合Expedia要求
□ 英文翻译已完成
□ 数据无重复
□ 关联关系正确
```

---

## 五、翻译规则引擎

### 5.1 规则优先级体系

```
优先级从高到低:
1. 集团规则 (priority: 100)
   └── 亚朵集团翻译规范
   
2. 国家规则 (priority: 80)
   └── 中国酒店行业翻译标准
   
3. 省级规则 (priority: 60)
   └── 各省酒店名称翻译规范
   
4. 市级规则 (priority: 40)
   └── 重点城市地名翻译规范
   
5. 默认规则 (priority: 0)
   └── 通用翻译规则
```

### 5.2 规则结构设计

```typescript
interface TranslationRule {
  id: string
  name: string                    // 规则名称
  category: 'company' | 'country' | 'province' | 'city'
  scope: {                        // 适用范围
    provinces?: string[]          // 省份列表
    cities?: string[]             // 城市列表
    countries?: string[]          // 国家列表
  }
  rules: TranslationRuleItem[]    // 具体规则项
  priority: number                // 优先级
  isActive: boolean               // 是否启用
}

interface TranslationRuleItem {
  pattern: string | RegExp        // 匹配模式
  replacement: string             // 替换内容
  fieldType: string               // 适用字段类型
  examples: {                     // 示例
    original: string
    translated: string
  }[]
}
```

### 5.3 规则匹配算法

```typescript
class TranslationRuleEngine {
  private rules: TranslationRule[] = []
  
  // 加载规则
  async loadRules(hotelInfo: { province: string, city: string }) {
    // 1. 加载集团规则(最高优先级)
    const companyRules = await this.fetchRules({ category: 'company' })
    
    // 2. 加载国家规则
    const countryRules = await this.fetchRules({ category: 'country' })
    
    // 3. 加载省级规则
    const provinceRules = await this.fetchRules({ 
      category: 'province',
      scope: { provinces: [hotelInfo.province] }
    })
    
    // 4. 加载市级规则
    const cityRules = await this.fetchRules({ 
      category: 'city',
      scope: { cities: [hotelInfo.city] }
    })
    
    // 按优先级排序合并
    this.rules = [
      ...companyRules,
      ...countryRules,
      ...provinceRules,
      ...cityRules
    ].sort((a, b) => b.priority - a.priority)
  }
  
  // 应用规则
  applyRules(text: string, fieldType: string): string {
    let result = text
    
    for (const rule of this.rules) {
      for (const item of rule.rules) {
        if (item.fieldType === fieldType || item.fieldType === '*') {
          if (item.pattern instanceof RegExp) {
            result = result.replace(item.pattern, item.replacement)
          } else {
            result = result.replace(new RegExp(item.pattern, 'g'), item.replacement)
          }
        }
      }
    }
    
    return result
  }
}
```

### 5.4 规则示例

#### 5.4.1 集团规则示例
```json
{
  "name": "亚朵集团酒店名称翻译规范",
  "category": "company",
  "priority": 100,
  "rules": [
    {
      "pattern": "亚朵酒店",
      "replacement": "Atour Hotel",
      "fieldType": "hotel_name"
    },
    {
      "pattern": "亚朵S酒店",
      "replacement": "Atour S Hotel",
      "fieldType": "hotel_name"
    },
    {
      "pattern": "亚朵轻居",
      "replacement": "Atour Light",
      "fieldType": "hotel_name"
    }
  ]
}
```

### 5.5 PDF 规则解析

```typescript
interface PDFParsingResult {
  success: boolean
  content: string           // 提取的文本
  rules: ExtractedRule[]    // AI识别的规则
  confidence: number        // 置信度
}

// AI提示词模板
const ruleExtractionPrompt = `
请从以下文档中提取翻译规则，以JSON格式输出：

文档内容:
{documentContent}

输出格式:
{
  "rules": [
    {
      "pattern": "匹配模式",
      "replacement": "替换内容",
      "fieldType": "适用的字段类型",
      "examples": ["示例1", "示例2"]
    }
  ]
}
`
```

---

## 六、安全设计

### 6.1 认证与授权

#### 6.1.1 认证机制
- JWT Token 认证
- Token 有效期: 2小时
- Refresh Token 有效期: 7天
- 支持单点登录(SSO)集成

#### 6.1.2 权限控制
```typescript
// RBAC 权限模型
enum Role {
  ADMIN = 'admin',           // 全部权限
  OPERATOR = 'operator',     // 数据操作
  TRANSLATOR = 'translator', // 翻译相关
  VIEWER = 'viewer'          // 仅查看
}

// 权限配置
const permissions = {
  admin: ['*'],
  operator: [
    'hotel:read', 'hotel:write',
    'room:read', 'room:write',
    'import:execute', 'export:execute'
  ],
  translator: [
    'hotel:read', 'room:read',
    'translate:read', 'translate:write',
    'terminology:read', 'terminology:write'
  ],
  viewer: [
    'hotel:read', 'room:read',
    'translate:read', 'terminology:read'
  ]
}
```

### 6.2 数据安全

#### 6.2.1 敏感数据保护
- 密码加密存储 (bcrypt)
- 敏感字段加密 (AES-256)
- 数据传输加密 (HTTPS)
- 日志脱敏处理

#### 6.2.2 文件上传安全
- 文件类型白名单: `.xlsx`, `.xls`, `.csv`, `.pdf`
- 文件大小限制: 50MB
- 文件内容扫描
- 文件名随机化

### 6.3 接口安全

#### 6.3.1 限流策略
```typescript
const rateLimits = {
  '/api/v1/import': { limit: 10, window: 60000 },    // 10次/分钟
  '/api/v1/translate': { limit: 100, window: 60000 }, // 100次/分钟
  '/api/v1/export': { limit: 20, window: 60000 }      // 20次/分钟
}
```

#### 6.3.2 请求验证
- 参数类型校验
- XSS 过滤
- SQL 注入防护
- CSRF 防护

---

## 七、错误处理

### 7.1 错误分类

#### 7.1.1 业务错误
| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| 1001 | 数据导入失败 | 返回详细错误列表 |
| 1002 | 数据校验失败 | 标注错误字段 |
| 1003 | 翻译失败 | 提供备用方案 |
| 1004 | 导出失败 | 记录日志，支持重试 |
| 1005 | 文件解析失败 | 返回解析错误详情 |

#### 7.1.2 系统错误
| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| 2001 | 数据库连接失败 | 自动重试 + 告警 |
| 2002 | 缓存服务异常 | 降级处理 |
| 2003 | 外部服务超时 | 超时重试 + 降级 |
| 2004 | 文件存储失败 | 自动重试 |
| 2005 | AI服务异常 | 切换备用模型 |

#### 7.1.3 权限错误
| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| 3001 | 未登录 | 跳转登录页 |
| 3002 | 权限不足 | 提示无权限 |
| 3003 | Token过期 | 自动刷新Token |
| 3004 | 账号被禁用 | 提示联系管理员 |

### 7.2 重试机制

```typescript
const retryConfig = {
  translation: {
    maxRetries: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2
  },
  fileUpload: {
    maxRetries: 2,
    initialDelay: 500,
    maxDelay: 5000,
    backoffMultiplier: 2
  },
  database: {
    maxRetries: 3,
    initialDelay: 100,
    maxDelay: 1000,
    backoffMultiplier: 2
  }
}
```

---

## 八、部署架构

### 8.1 开发环境

```bash
# 本地开发启动
npm install
npm run dev

# 数据库初始化 (SQLite)
npx prisma db push
npx prisma generate
```

**开发环境配置** (`.env.development`):
```env
# 数据库 (SQLite)
DATABASE_URL="file:./dev.db"

# AI服务 (StepFun)
AI_PROVIDER=stepfun
AI_API_KEY=your-stepfun-api-key
AI_BASE_URL=https://api.stepfun.com/v1
AI_MODEL=step-1-8k

# 翻译服务
TENCENT_SECRET_ID=xxx
TENCENT_SECRET_KEY=xxx
```

### 8.2 生产环境 - 阿里云云函数

#### 部署架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    阿里云 API 网关                           │
│                  (HTTP Trigger)                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  函数计算 FC (Next.js)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  内存: 512MB-1024MB                                  │   │
│  │  超时: 60s                                           │   │
│  │  并发: 按需自动伸缩                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    阿里云 RDS MySQL                          │
│                  (主实例 + 只读实例)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      外部服务                                │
│  ┌──────────────────┐  ┌────────────────────────────────┐  │
│  │ 腾讯云翻译 API    │  │ 阿里百炼 (AI服务)               │  │
│  └──────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Serverless 配置

```yaml
# s.yaml (阿里云Serverless配置)
edition: 1.0.0
name: expertie
access: default

services:
  expertie:
    component: fc
    props:
      region: cn-shanghai
      service:
        name: expertie-service
        description: Expedia酒店表格生成工具
        logConfig: auto
      function:
        name: expertie-api
        runtime: custom.debian10
        codeUri: ./
        handler: index.handler
        memorySize: 512
        timeout: 60
        instanceConcurrency: 10
        environmentVariables:
          NODE_ENV: production
          DATABASE_URL: ${env.MYSQL_URL}
          AI_PROVIDER: bailian
          AI_API_KEY: ${env.AI_API_KEY}
          AI_BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1
          AI_MODEL: qwen-turbo
          TENCENT_SECRET_ID: ${env.TENCENT_SECRET_ID}
          TENCENT_SECRET_KEY: ${env.TENCENT_SECRET_KEY}
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

#### 生产环境配置

```env
# 数据库 (阿里云RDS MySQL)
DATABASE_URL="mysql://user:password@rm-xxx.mysql.rds.aliyuncs.com:3306/expertie"

# AI服务 (阿里百炼)
AI_PROVIDER=bailian
AI_API_KEY=your-bailian-api-key
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-turbo

# 翻译服务
TENCENT_SECRET_ID=xxx
TENCENT_SECRET_KEY=xxx
```

#### 部署命令

```bash
# 安装 Serverless DevTools
npm install -g @serverless-devs/s

# 部署到阿里云
s deploy

# 查看部署状态
s info

# 查看日志
s logs
```

### 8.3 监控与告警

| 指标类型 | 监控项 | 阈值 |
|---------|--------|------|
| 函数指标 | 内存使用率 | >80% 告警 |
| 函数指标 | 执行超时 | >60s 告警 |
| 函数指标 | 错误率 | >1% 告警 |
| 业务指标 | 翻译成功率 | <95% 告警 |
| 业务指标 | 导出成功率 | <98% 告警 |

---

## 九、性能优化

### 9.1 前端优化

#### 9.1.1 数据加载优化
```typescript
// 虚拟滚动 - 大数据列表
import { useVirtualizer } from '@tanstack/react-virtual'

function HotelList({ hotels }: { hotels: Hotel[] }) {
  const virtualizer = useVirtualizer({
    count: hotels.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 10
  })
  // ...
}
```

#### 9.1.2 缓存策略
```typescript
// React Query 缓存配置
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5分钟内数据视为新鲜
      gcTime: 30 * 60 * 1000,        // 30分钟后清除缓存
      refetchOnWindowFocus: false,
      retry: 2
    }
  }
})
```

### 9.2 后端优化

#### 9.2.1 批量操作优化
```typescript
// Prisma 批量插入优化
async function batchInsertHotels(hotels: Hotel[]) {
  const batchSize = 500
  const results = []

  for (let i = 0; i < hotels.length; i += batchSize) {
    const batch = hotels.slice(i, i + batchSize)
    const inserted = await prisma.hotel.createMany({
      data: batch,
      skipDuplicates: true
    })
    results.push(inserted)
  }

  return results
}
```

#### 9.2.2 内存缓存设计
```typescript
// LRU 内存缓存（替代Redis）
import { LRUCache } from 'lru-cache'

const hotelCache = new LRUCache<string, Hotel>({
  max: 500,           // 最大缓存条目数
  ttl: 1000 * 60 * 5, // 5分钟过期
})

class CacheService {
  async getHotel(hotelId: string): Promise<Hotel | null> {
    const cached = hotelCache.get(hotelId)
    if (cached) return cached

    const hotel = await prisma.hotel.findUnique({
      where: { id: hotelId }
    })
    if (hotel) {
      hotelCache.set(hotelId, hotel)
    }
    return hotel
  }

  invalidateHotel(hotelId: string) {
    hotelCache.delete(hotelId)
  }
}
```

### 9.3 翻译服务优化

#### 9.3.1 并发控制
```typescript
import PQueue from 'p-queue'

const translationQueue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 50
})

async function batchTranslate(items: TranslateItem[]): Promise<TranslateResult[]> {
  const tasks = items.map(item =>
    translationQueue.add(() => translateWithRetry(item))
  )
  return Promise.all(tasks)
}
```

#### 9.3.2 AI服务调用优化
```typescript
// OpenAI兼容客户端封装
import OpenAI from 'openai'

const getAIClient = () => {
  const provider = process.env.AI_PROVIDER || 'stepfun'

  return new OpenAI({
    apiKey: process.env.AI_API_KEY,
    baseURL: process.env.AI_BASE_URL ||
      (provider === 'bailian'
        ? 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        : 'https://api.stepfun.com/v1'),
  })
}

export async function translateWithAI(prompt: string, text: string): Promise<string> {
  const client = getAIClient()

  const response = await client.chat.completions.create({
    model: process.env.AI_MODEL || (process.env.AI_PROVIDER === 'bailian' ? 'qwen-turbo' : 'step-1-8k'),
    messages: [
      { role: 'system', content: prompt },
      { role: 'user', content: text }
    ],
  })

  return response.choices[0]?.message?.content || ''
}
```

---

## 十、测试策略

### 10.1 测试分层

```
┌─────────────────────────────────────────┐
│        E2E 测试 (Agent Browser)          │
│    用户完整流程测试、跨系统集成测试         │
├─────────────────────────────────────────┤
│      集成测试 (Jest + Supertest)          │
│      API接口测试、数据库集成测试            │
├─────────────────────────────────────────┤
│          单元测试 (Vitest)                │
│      函数测试、组件测试、工具类测试          │
└─────────────────────────────────────────┘
```

### 10.2 E2E测试 (Agent Browser)

使用 Agent Browser 进行端到端测试，支持智能交互和自动化操作。

```typescript
// e2e/translation.spec.ts
import { test, expect } from '@agent-cli/test';

test('酒店翻译完整流程', async ({ agent }) => {
  // 访问应用
  await agent.goto('http://localhost:3000');

  // 上传酒店数据
  await agent.uploadFile('input[type="file"]', 'test-data/hotels.xlsx');

  // 验证数据导入成功
  await expect(agent.locator('.success-message')).toBeVisible();

  // 执行翻译
  await agent.click('button:has-text("开始翻译")');

  // 验证翻译结果
  await expect(agent.locator('.translation-result')).toContainText('Atour Hotel');

  // 导出结果
  await agent.click('button:has-text("导出")');
  await expect(agent.locator('.export-complete')).toBeVisible();
});

test('术语库管理', async ({ agent }) => {
  await agent.goto('http://localhost:3000/terminology');

  // 添加术语
  await agent.click('button:has-text("添加术语")');
  await agent.fill('input[name="term_zh"]', '大床房');
  await agent.fill('input[name="term_en"]', 'King Room');
  await agent.click('button:has-text("保存")');

  // 验证添加成功
  await expect(agent.locator('.term-item')).toContainText('King Room');
});
```

**Agent Browser 配置:**
```typescript
// agent.config.ts
export default {
  baseUrl: 'http://localhost:3000',
  headless: process.env.CI === 'true',
  timeout: 30000,
  screenshot: 'only-on-failure',
};
```

### 10.3 测试覆盖率要求

| 模块 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 |
|-----|---------|-----------|-----------|
| 核心业务逻辑 | ≥ 80% | ≥ 70% | ≥ 90% |
| API 接口 | ≥ 70% | ≥ 60% | ≥ 80% |
| 工具函数 | ≥ 90% | ≥ 80% | ≥ 95% |
| UI 组件 | ≥ 60% | ≥ 50% | ≥ 70% |

---

## 十一、开发计划

### 11.1 里程碑规划

| 阶段 | 内容 | 预计周期 |
|-----|------|---------|
| Phase 1 | 基础架构搭建、数据导入功能 | 2周 |
| Phase 2 | 翻译模块、术语库管理 | 2周 |
| Phase 3 | 数据合并、导出功能 | 1.5周 |
| Phase 4 | 系统管理、权限控制 | 1周 |
| Phase 5 | 测试与优化 | 1.5周 |

### 11.2 Phase 1 详细任务

| 任务 | 说明 | 预计工时 |
|-----|------|---------|
| 项目初始化 | 前后端脚手架、数据库配置 | 4h |
| 数据库设计 | 表结构创建、索引优化 | 8h |
| 酒店数据导入 | 文件解析、校验、入库 | 16h |
| 客房数据导入 | 关联逻辑、批量处理 | 12h |
| 数据列表展示 | 分页、筛选、搜索 | 8h |
| 数据编辑功能 | 表单、校验、更新 | 8h |

---

## 十二、附录

### 12.1 术语表

| 术语 | 说明 |
|-----|------|
| OCR | 光学字符识别，用于PDF文档解析 |
| LRU | 最近最少使用，缓存淘汰算法 |
| RBAC | 基于角色的访问控制 |
| JWT | JSON Web Token |

### 12.2 参考文档

- [NestJS 官方文档](https://docs.nestjs.com/)
- [React 官方文档](https://react.dev/)
- [腾讯云翻译 API 文档](https://cloud.tencent.com/document/product/551)
- [Claude API 文档](https://docs.anthropic.com/claude/reference)

### 12.3 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| v1.1 | 2026-04-06 | 技术架构简化：Next.js全栈框架、MySQL/SQLite数据库、阿里云云函数部署、OpenAI兼容API、Agent Browser测试 | 开发团队 |
| v1.0 | 2026-04-06 | 初始版本 | 开发团队 |

---

**文档版本**: v1.1
**最后更新**: 2026-04-06
**维护人员**: 开发团队

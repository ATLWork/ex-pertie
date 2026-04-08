# 用户管理设计文档

## 概述

用户管理模块负责认证、授权和安全控制，采用 JWT 认证和 RBAC 权限模型。

---

## 认证机制

### JWT Token 认证

- Token 有效期: 2小时
- Refresh Token 有效期: 7天
- 支持单点登录(SSO)集成

### Token 结构

```typescript
interface JWTPayload {
  userId: string
  username: string
  role: Role
  iat: number
  exp: number
}
```

### 认证流程

```
1. 用户登录 → 验证凭证
2. 生成 Access Token + Refresh Token
3. 客户端存储 Token
4. 请求携带 Access Token
5. Token 过期 → 使用 Refresh Token 刷新
```

---

## 权限控制

### RBAC 权限模型

```typescript
enum Role {
  ADMIN = 'admin',           // 全部权限
  OPERATOR = 'operator',     // 数据操作
  TRANSLATOR = 'translator', // 翻译相关
  VIEWER = 'viewer'          // 仅查看
}
```

### 权限配置

```typescript
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

### 权限检查中间件

```typescript
import { NextRequest, NextResponse } from 'next/server'

export function withAuth(
  handler: Function,
  requiredPermission?: string
) {
  return async (req: NextRequest) => {
    const token = req.headers.get('authorization')?.replace('Bearer ', '')

    if (!token) {
      return NextResponse.json(
        { code: 3001, message: '未登录' },
        { status: 401 }
      )
    }

    try {
      const payload = verifyToken(token)

      // 检查权限
      if (requiredPermission && !hasPermission(payload.role, requiredPermission)) {
        return NextResponse.json(
          { code: 3002, message: '权限不足' },
          { status: 403 }
        )
      }

      return handler(req, payload)
    } catch (error) {
      return NextResponse.json(
        { code: 3003, message: 'Token过期' },
        { status: 401 }
      )
    }
  }
}
```

---

## 用户数据模型

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

---

## 数据安全

### 敏感数据保护

| 安全措施 | 说明 |
|---------|------|
| 密码加密 | bcrypt 哈希存储 |
| 敏感字段加密 | AES-256 |
| 数据传输加密 | HTTPS |
| 日志脱敏 | 隐藏敏感信息 |

### 密码加密

```typescript
import bcrypt from 'bcrypt'

const SALT_ROUNDS = 10

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, SALT_ROUNDS)
}

export async function verifyPassword(
  password: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(password, hash)
}
```

---

## 文件上传安全

### 安全措施

| 措施 | 配置 |
|-----|------|
| 文件类型白名单 | `.xlsx`, `.xls`, `.csv`, `.pdf` |
| 文件大小限制 | 50MB |
| 内容扫描 | 检测恶意文件 |
| 文件名处理 | 随机化处理 |

### 文件验证

```typescript
const ALLOWED_TYPES = [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'text/csv',
  'application/pdf'
]

const MAX_SIZE = 50 * 1024 * 1024 // 50MB

export function validateFile(file: File): { valid: boolean; error?: string } {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return { valid: false, error: '不支持的文件类型' }
  }

  if (file.size > MAX_SIZE) {
    return { valid: false, error: '文件大小超过限制' }
  }

  return { valid: true }
}
```

---

## 接口安全

### 限流策略

```typescript
const rateLimits = {
  '/api/v1/import': { limit: 10, window: 60000 },    // 10次/分钟
  '/api/v1/translate': { limit: 100, window: 60000 }, // 100次/分钟
  '/api/v1/export': { limit: 20, window: 60000 }      // 20次/分钟
}
```

### 请求验证

| 验证项 | 说明 |
|-------|------|
| 参数类型校验 | 验证请求参数类型 |
| XSS 过滤 | 防止跨站脚本攻击 |
| SQL 注入防护 | 参数化查询 |
| CSRF 防护 | Token 验证 |

---

## 错误码

### 权限错误

| 错误码 | 说明 | 处理方式 |
|-------|------|---------|
| 3001 | 未登录 | 跳转登录页 |
| 3002 | 权限不足 | 提示无权限 |
| 3003 | Token过期 | 自动刷新Token |
| 3004 | 账号被禁用 | 提示联系管理员 |

---

**文档版本**: v1.0
**最后更新**: 2026-04-08

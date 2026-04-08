# AI 服务设计文档

## 概述

AI 服务用于翻译润色和规则理解，统一使用 OpenAI 兼容 API 接口。

| 服务 | 环境 | 用途 |
|-----|------|------|
| 阿里百炼 | 生产环境 | AI翻译润色、规则理解 |
| StepFun | 开发环境 | AI翻译润色、规则理解 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      AI 服务层                               │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  OpenAI 兼容客户端 (统一接口)                          │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ 阿里百炼  │   │ StepFun  │   │  其他    │
        │ (生产)   │   │ (开发)   │   │ (可扩展) │
        └──────────┘   └──────────┘   └──────────┘
```

---

## 环境配置

### 开发环境 (StepFun)

```env
AI_PROVIDER=stepfun
AI_API_KEY=your-stepfun-api-key
AI_BASE_URL=https://api.stepfun.com/v1
AI_MODEL=step-1-8k
```

### 生产环境 (阿里百炼)

```env
AI_PROVIDER=bailian
AI_API_KEY=your-bailian-api-key
AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_MODEL=qwen-turbo
```

---

## 服务调用

### OpenAI 兼容客户端封装

```typescript
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
```

### AI 翻译润色

```typescript
export async function translateWithAI(
  prompt: string,
  text: string
): Promise<string> {
  const client = getAIClient()

  const response = await client.chat.completions.create({
    model: process.env.AI_MODEL ||
      (process.env.AI_PROVIDER === 'bailian' ? 'qwen-turbo' : 'step-1-8k'),
    messages: [
      { role: 'system', content: prompt },
      { role: 'user', content: text }
    ],
  })

  return response.choices[0]?.message?.content || ''
}
```

---

## 提示词模板

### 翻译润色提示词

```typescript
const translationPrompt = `
你是一个专业的酒店行业翻译专家。请根据以下规则润色翻译结果：

## 翻译原则
1. 保持品牌名称一致性（如：亚朵 = Atour）
2. 使用行业标准术语
3. 符合英语表达习惯
4. 保留关键信息，不添加额外内容

## 参考规则
{rules}

## 术语库
{terminology}

## 原文
{originalText}

## 初始翻译
{initialTranslation}

## 输出要求
输出润色后的英文翻译，不需要解释。
`
```

### 规则提取提示词

```typescript
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

## 并发控制

```typescript
import PQueue from 'p-queue'

const aiQueue = new PQueue({
  concurrency: 10,      // 最大并发数
  interval: 1000,       // 时间窗口
  intervalCap: 50       // 窗口内最大请求数
})

async function batchAITranslate(
  items: TranslateItem[]
): Promise<TranslateResult[]> {
  const tasks = items.map(item =>
    aiQueue.add(() => translateWithRetry(item))
  )
  return Promise.all(tasks)
}
```

---

## 错误处理

### 降级策略

```typescript
async function translateWithFallback(text: string): Promise<string> {
  try {
    // 优先使用 AI 翻译
    return await translateWithAI(getPrompt(), text)
  } catch (aiError) {
    console.error('AI 翻译失败:', aiError)

    // 降级到腾讯云翻译
    try {
      return await tencentTranslate(text)
    } catch (tencentError) {
      console.error('腾讯云翻译失败:', tencentError)
      throw new Error('翻译服务不可用')
    }
  }
}
```

### 重试配置

```typescript
const aiRetryConfig = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 10000,
  backoffMultiplier: 2
}
```

---

**文档版本**: v1.0
**最后更新**: 2026-04-08

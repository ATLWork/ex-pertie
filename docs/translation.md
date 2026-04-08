# 翻译服务设计文档

## 概述

翻译服务采用多层翻译策略，优先使用参考库，其次使用机器翻译，最后由 AI 润色。

---

## 翻译流程

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

---

## 翻译规则引擎

### 规则优先级体系

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

### 规则结构设计

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

### 规则匹配算法

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

---

## 规则示例

### 集团规则示例

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

---

## PDF 规则解析

### 解析结果结构

```typescript
interface PDFParsingResult {
  success: boolean
  content: string           // 提取的文本
  rules: ExtractedRule[]    // AI识别的规则
  confidence: number        // 置信度
}
```

### AI 规则提取

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

## 术语库管理

### 术语数据结构

```typescript
interface Terminology {
  id: string
  term_zh: string           // 中文术语
  term_en: string           // 英文术语
  category: string          // 分类: hotel/room/facility/service/location
  context: string           // 使用语境
  is_verified: boolean      // 是否已验证
}
```

### 术语库接口

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | /terminology | 获取术语列表 |
| POST | /terminology | 添加术语 |
| PUT | /terminology/{id} | 更新术语 |
| DELETE | /terminology/{id} | 删除术语 |
| POST | /terminology/import | 批量导入术语 |
| GET | /terminology/export | 导出术语库 |

---

## 翻译参考库

### 数据来源

| 来源 | 说明 | 数据类型 |
|-----|------|---------|
| 携程 (Ctrip) | 酒店名称、房型名称 | 高质量参考 |
| Booking | 酒店描述、设施名称 | 多语言参考 |

### 参考库查询

```typescript
async function findReference(
  text: string,
  fieldType: string
): Promise<TranslationReference | null> {
  const reference = await prisma.translationReferences.findFirst({
    where: {
      text_zh: text,
      field_type: fieldType,
      is_verified: true
    },
    orderBy: {
      quality_score: 'desc'
    }
  })

  return reference
}
```

---

## 并发控制

```typescript
import PQueue from 'p-queue'

const translationQueue = new PQueue({
  concurrency: 10,
  interval: 1000,
  intervalCap: 50
})

async function batchTranslate(
  items: TranslateItem[]
): Promise<TranslateResult[]> {
  const tasks = items.map(item =>
    translationQueue.add(() => translateWithRetry(item))
  )
  return Promise.all(tasks)
}
```

---

**文档版本**: v1.0
**最后更新**: 2026-04-08

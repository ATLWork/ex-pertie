---
name: atour-design-system
description: >
  亚朵集团前端视觉设计系统 skill。基于亚朵品牌视觉手册 v1.0 (2026年3月版本)。
  当用户需要实现亚朵品牌相关的前端页面、组件、UI 设计时必须使用此 skill。
  包含 Radix UI + 亚朵品牌色彩的组件开发规范。
  触发关键词：亚朵、ATOUR、Radix UI、亚朵前端、品牌色彩、字体规范、设计系统。
  务必在生成任何亚朵品牌相关前端代码或设计方案前先阅读本 skill。
---

# 亚朵前端视觉设计系统 v1.0

**来源**：亚朵集团品牌视觉手册 v1.0 (2026年3月版本)
**集成**：Radix UI 组件库 + 亚朵品牌视觉规范

---

## 快速参考索引

| 章节 | 内容 |
|------|------|
| [1. 核心色彩系统](#1-核心色彩系统) | 沃野、白岩、纯白、纯黑及 CSS 变量 |
| [2. 字体规范](#2-字体规范) | 品牌字体、系统字体、CSS 变量 |
| [3. 组件设计原则](#3-组件设计原则) | Radix UI + 亚朵色彩集成规范 |
| [4. 基础组件样式](#4-基础组件样式) | Button, Card, Input, Table 等亚朵化样式 |
| [5. 布局与间距](#5-布局与间距) | 间距系统、页面布局规则 |
| [6. 禁止用法](#6-禁止用法) | 前端实施中严禁的操作 |

---

## 1. 核心色彩系统

### 1.1 四色体系

| 色名 | HEX | CSS 变量 | 用途 |
|------|-----|----------|------|
| **沃野（Wòyě）** | `#3D3028` | `--color-wuye` | 深色背景、Logo 墨稿底色 |
| **白岩（Báiyán）** | `#EAE4DA` | `--color-baiyan` | 浅色背景、辅助图形底色、卡片底色 |
| **纯白** | `#FFFFFF` | `--color-white` | 页面底色、反白 Logo |
| **纯黑** | `#1A1A1A` | `--color-black` | 正文、深色背景上的文字 |

### 1.2 背景与图形色彩联动

| 背景色 | 辅助图形颜色 | 说明 |
|--------|------------|------|
| 沃野（`#3D3028`） | 纯黑（`#1A1A1A`） | 深色中隐约可见 |
| 白岩（`#EAE4DA`） | 白色（`#FFFFFF`） | 米色中退隐 |
| 纯白（`#FFFFFF`） | 白岩色（`#EAE4DA`） | 白底上若隐若现 |

### 1.3 CSS 变量

```css
:root {
  /* === 品牌色彩 === */
  --color-wuye: #3D3028;        /* 沃野：主色深棕 */
  --color-baiyan: #EAE4DA;      /* 白岩：暖米色 */
  --color-white: #FFFFFF;
  --color-black: #1A1A1A;

  /* === 语义化颜色 === */
  --color-primary: var(--color-wuye);
  --color-background: var(--color-white);
  --color-surface: var(--color-baiyan);
  --color-text: var(--color-black);
  --color-text-secondary: #6B6B6B;

  /* === 状态色 === */
  --color-success: #2E7D32;
  --color-warning: #ED6C02;
  --color-error: #D32F2F;
  --color-info: #0288D1;
}
```

---

## 2. 字体规范

### 2.1 字体族

| 类型 | 首选字体 | 备选字体 | 用途 |
|------|---------|---------|------|
| 品牌中文 | 方正FW筑紫明朝 | 思源黑体 | H1/H2 标题 |
| 系统中文 | 思源黑体（Noto Sans CJK SC） | PingFang SC / Microsoft YaHei | 正文、UI |
| 品牌英文 | Canela（商业授权） | DIN Pro | 英文标题 |
| 系统英文 | DIN Pro | Helvetica Neue / Arial | 数字、英文正文 |

### 2.2 字号层级

| 等级 | 字号 | 行高 | 字间距 | 字重 | 字体 |
|------|------|------|--------|------|------|
| **H1** | 40px | 1.2（48px） | -0.02em | 800 | 方正FW筑紫明朝 |
| **H2** | 24px | 1.4（34px） | -0.01em | 700 | 方正FW筑紫明朝 |
| **H3** | 16px | 1.5（24px） | 0 | 600 | 思源黑体 |
| **Body** | 14px | 1.6（22px） | 0 | 400 | 思源黑体 |
| **Caption** | 12px | 1.5（18px） | 0 | 300 | 思源黑体 |

### 2.3 CSS 变量

```css
:root {
  /* === 字体族 === */
  --font-brand-zh: "方正FW筑紫明朝", "FZZhuZiMingChao", serif;
  --font-brand-en: "Canela", Georgia, serif;
  --font-system-zh: "Noto Sans CJK SC", "思源黑体", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-system-en: "DIN Pro", "DIN Next", "Helvetica Neue", Arial, sans-serif;

  /* === 字号 === */
  --text-h1: 40px;
  --text-h2: 24px;
  --text-h3: 16px;
  --text-body: 14px;
  --text-caption: 12px;

  /* === 行高 === */
  --leading-tight: 1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.6;
}
```

### 2.4 Google Fonts 加载

```css
/* 思源黑体 - 系统正文 */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;600&display=swap');
```

---

## 3. 组件设计原则

### 3.1 Radix UI + 亚朵色彩集成

**核心思想**：使用 Radix UI 作为无样式组件层，通过 CSS 变量注入亚朵品牌色彩。

```tsx
// ✅ 正确：使用 Radix 组件 + 亚朵 CSS 变量
import { Button as RadixButton } from '@radix-ui/themes';
import './atour-components.css';

export function AtourButton({ children, variant = 'primary' }) {
  return (
    <RadixButton className={`atour-button atour-button--${variant}`}>
      {children}
    </RadixButton>
  );
}
```

```css
/* atour-components.css */
.atour-button {
  font-family: var(--font-system-zh);
  font-weight: 600;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.atour-button--primary {
  background-color: var(--color-wuye);
  color: var(--color-white);
}

.atour-button--primary:hover {
  background-color: #4A3B32;
}

.atour-button--secondary {
  background-color: var(--color-baiyan);
  color: var(--color-black);
}

.atour-button--secondary:hover {
  background-color: #D9D2C5;
}
```

### 3.2 组件开发模式

**层级架构**：
1. **Radix Primitives** — 无样式基础组件（交互逻辑、无障碍）
2. **Atour Components** — 亚朵品牌层（应用色彩、字体、圆角）
3. **Page Components** — 业务层（组合基础组件）

### 3.3 圆角规范

| 组件类型 | 圆角值 | CSS 变量 |
|---------|--------|----------|
| 按钮、输入框 | 6px | `--radius-sm` |
| 卡片、容器 | 8px | `--radius-md` |
| 模态框、浮层 | 12px | `--radius-lg` |

---

## 4. 基础组件样式

### 4.1 Button

```css
.atour-button {
  /* 尺寸 */
  height: 36px;
  padding: 0 16px;
  font-size: var(--text-body);
  font-family: var(--font-system-zh);
  font-weight: 600;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.atour-button--primary {
  background-color: var(--color-wuye);
  color: var(--color-white);
  border: none;
}

.atour-button--primary:hover {
  background-color: #4A3B32;
}

.atour-button--secondary {
  background-color: transparent;
  color: var(--color-wuye);
  border: 1px solid var(--color-wuye);
}

.atour-button--secondary:hover {
  background-color: var(--color-baiyan);
}

.atour-button--ghost {
  background-color: transparent;
  color: var(--color-text);
}

.atour-button--ghost:hover {
  background-color: var(--color-baiyan);
}

.atour-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

### 4.2 Card

```css
.atour-card {
  background-color: var(--color-baiyan);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.atour-card--elevated {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
```

### 4.3 Input

```css
.atour-input {
  height: 36px;
  padding: 0 12px;
  font-size: var(--text-body);
  font-family: var(--font-system-zh);
  background-color: var(--color-white);
  border: 1px solid #D9D2C5;
  border-radius: var(--radius-sm);
  transition: border-color 0.2s ease;
}

.atour-input:focus {
  outline: none;
  border-color: var(--color-wuye);
  box-shadow: 0 0 0 2px rgba(61, 48, 40, 0.1);
}

.atour-input::placeholder {
  color: var(--color-text-secondary);
}
```

### 4.4 Table

```css
.atour-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-system-zh);
  font-size: var(--text-body);
}

.atour-table th {
  background-color: var(--color-baiyan);
  color: var(--color-black);
  font-weight: 600;
  text-align: left;
  padding: 12px 16px;
  border-bottom: 2px solid var(--color-wuye);
}

.atour-table td {
  padding: 12px 16px;
  border-bottom: 1px solid #E8E2D9;
}

.atour-table tr:hover td {
  background-color: rgba(234, 228, 218, 0.5);
}
```

### 4.5 Tag / Badge

```css
.atour-tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  font-size: var(--text-caption);
  font-weight: 500;
  border-radius: 12px;
  background-color: var(--color-baiyan);
  color: var(--color-text);
}

.atour-tag--success {
  background-color: #E8F5E9;
  color: var(--color-success);
}

.atour-tag--warning {
  background-color: #FFF3E0;
  color: var(--color-warning);
}

.atour-tag--error {
  background-color: #FFEBEE;
  color: var(--color-error);
}
```

---

## 5. 布局与间距

### 5.1 间距系统

基于 4px 网格：

```css
:root {
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
  --space-2xl: 48px;
  --space-3xl: 64px;
}
```

### 5.2 页面布局

```css
.atour-page {
  min-height: 100vh;
  background-color: var(--color-white);
  padding: var(--space-lg);
}

.atour-page-header {
  margin-bottom: var(--space-xl);
}

.atour-page-title {
  font-family: var(--font-brand-zh);
  font-size: var(--text-h1);
  font-weight: 800;
  color: var(--color-black);
  margin-bottom: var(--space-sm);
}
```

---

## 6. 禁止用法

| ❌ 禁止行为 | ✅ 正确做法 |
|-----------|-----------|
| 使用 antd 默认蓝色主题（`#1677ff`） | 使用 `--color-wuye`（`#3D3028`）作为主色 |
| 使用 antd 默认圆角（`borderRadius: 8`） | 使用亚朵规范圆角（6px / 8px / 12px） |
| 使用系统默认字体 | 使用亚朵字体堆栈 |
| 直接使用纯黑 `#000000` | 使用 `--color-black`（`#1A1A1A`） |
| 组件颜色硬编码 | 使用 CSS 变量 |
| 品牌字体用于正文 | 品牌字体仅用于 H1/H2 |

---

## 迁移检查清单

将 antd 组件替换为 Radix UI + 亚朵样式时：

- [ ] 移除 `antd` 和 `@ant-design/icons` 导入
- [ ] 安装 `@radix-ui/themes`
- [ ] 创建 `atour-components.css` 包含所有基础样式
- [ ] 全局引入亚朵 CSS 变量
- [ ] 替换 Button → Radix Button + Atour 样式
- [ ] 替换 Table → Radix Table + Atour 样式
- [ ] 替换 Card → Radix Card + Atour 样式
- [ ] 替换 Input/Textarea → Radix TextField + Atour 样式
- [ ] 替换 Select → Radix Select + Atour 样式
- [ ] 替换 Modal → Radix Dialog + Atour 样式
- [ ] 替换 Tabs → Radix Tabs + Atour 样式
- [ ] 替换 Upload → Radix Upload 或定制
- [ ] 替换 Message → Radix Toast
- [ ] 验证颜色、字体、圆角是否符合规范
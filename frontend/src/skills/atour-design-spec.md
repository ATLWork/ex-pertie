---
name: atour-frontend-design
description: >
  亚朵集团数字端（App / Web / H5）前端视觉设计规范 skill。当需要实现亚朵品牌相关的前端页面、组件、UI 设计时必须使用此 skill。
  包含品牌色彩系统、字体规范、Logo 使用规则、辅助图形规范及禁止用法。
  触发关键词：亚朵、ATOUR、亚朵品牌、前端页面、H5、App 组件、色彩规范、字体规范、Logo 规范、设计规范。
---

# 亚朵集团前端视觉设计规范 v1.0

**核心原则**：延续品牌"自然、静谧、温暖、朴实"的人文调性。

---

## 快速参考

| 章节 | CSS 变量 | 说明 |
|------|---------|------|
| [色彩系统](#色彩系统) | `--color-woye`, `--color-baiyan` | 沃野深棕 + 白岩暖米 |
| [字体规范](#字体规范) | `--font-brand-zh`, `--font-system-zh` | 方正筑紫明朝 / 思源黑体 |
| [Logo 用法](#logo-用法) | `--logo-min-width-*` | 黑/白切图二选一，禁用 CSS 变色 |
| [辅助图形](#辅助图形) | | 山形图案，颜色随背景联动 |
| [禁止用法](#禁止用法) | | CSS 变色、拉伸、模糊背景直接叠加 |

---

## 色彩系统

### 核心品牌色

| 色名 | 用途 | HEX | CSS 变量 |
|------|------|-----|----------|
| **沃野（Wòyě）** | 深色背景·封面·导航栏 dark | `#3D3028` | `--color-woye` |
| **白岩（Báiyán）** | 浅色模块背景·卡片底色 | `#EAE4DA` | `--color-baiyan` |
| **纯白** | 页面底色 | `#FFFFFF` | `--color-white` |
| **纯黑** | 正文·Logo 墨稿 | `#1A1A1A` | `--color-black` |

### Logo 颜色规则（与背景明度强绑定）

| 背景 | Logo 版本 | 资产文件 |
|------|----------|---------|
| 白色 / 白岩（明度 70%+） | **黑色版** | `logo-black.svg` |
| 沃野 / 深色（明度 < 30%） | **白色版** | `logo-white.svg` |
| 中间调（50%-70%） | 加蒙版后再用黑白 | 半透明遮罩 + 对应 Logo |

**核心原则：Logo 只有黑/白两色，不允许 CSS 着色、透明度变化。**

### 辅助图形颜色联动

| 背景色 | 图形颜色 |
|--------|---------|
| 沃野 `#3D3028` | 纯黑 `#1A1A1A` |
| 白岩 `#EAE4DA` | 白色 `#FFFFFF` |
| 纯白 `#FFFFFF` | 白岩色 `#EAE4DA` |

---

## 字体规范

### 字体族

| 用途 | 字体 | CSS 变量 |
|------|------|----------|
| 品牌中文标题 | 方正FW筑紫明朝 | `--font-brand-zh` |
| 品牌英文标题 | Canela（商业授权） | `--font-brand-en` |
| 系统中文正文 | 思源黑体（Noto Sans CJK SC） | `--font-system-zh` |
| 系统英文/数字 | DIN Pro | `--font-system-en` |

### 字号层级

| 等级 | 桌面 | 移动 | 行高 | 字重 | 字体 |
|------|------|------|------|------|------|
| H1 | 40px | 28px | 1.2 | ExtraBold (800) | 方正FW筑紫明朝 |
| H2 | 24px | 20px | 1.4 | Bold (700) | 方正FW筑紫明朝 |
| H3 | 16px | 16px | 1.5 | Regular (400) | 思源黑体 |
| Body | 14px | 14px | 1.6 | Light (300) | 思源黑体 |
| Caption | 12px | 12px | 1.5 | Light (300) | 思源黑体 |

### CSS 变量速查

```css
:root {
  /* 品牌色彩 */
  --color-woye: #3D3028;
  --color-baiyan: #EAE4DA;
  --color-white: #FFFFFF;
  --color-black: #1A1A1A;

  /* 字体族 */
  --font-brand-zh: "方正FW筑紫明朝", "FZZhuZiMingChao", serif;
  --font-brand-en: "Canela", Georgia, serif;
  --font-system-zh: "Noto Sans CJK SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-system-en: "DIN Pro", "DIN Next", "Helvetica Neue", Arial, sans-serif;

  /* 字号 */
  --text-h1: 40px;
  --text-h2: 24px;
  --text-h3: 16px;
  --text-body: 14px;
  --text-caption: 12px;

  /* Logo 最小宽度 */
  --logo-min-width-group: 30px;    /* 集团堆叠版 */
  --logo-min-width-service: 40px; /* 服务品牌横版 */
}
```

---

## Logo 用法

### 三套标识选用

| 场景 | 标识 | 最小宽度 |
|------|------|---------|
| ToC（App/H5 默认） | `亚朵 ATOUR` 服务品牌横版 | 40px |
| ToB（官网/加盟商） | `亚朵集团 ATOUR GROUP` | 30px（堆叠）/ 50px（横版） |
| 线下酒店 | A 标 + `ATOUR HOTEL` | 不用于数字端 |

### 安全距离

- 四周保留 **2X**（X = 英文字标 "A" 的高度，约 14px）
- 移动端 H5 导航栏 Logo 距屏幕边缘 **≥ 16px**

### 正确用法

```html
<!-- ✅ 根据背景切换官方切图 -->
<img src="/brand/logo-black.svg" alt="亚朵 ATOUR">

<!-- ✅ Retina 响应式 -->
<img src="logo@1x.png" srcset="logo@2x.png 2x, logo@3x.png 3x" alt="亚朵 ATOUR">

<!-- ✅ 保持比例 -->
<img src="logo.svg" style="width: 120px; height: auto;" alt="亚朵 ATOUR">
```

---

## 辅助图形

山形图案取材于皇冠山与石月亮山轮廓，体现"自然、静谧"调性。

### 布局规则

```css
.atour-graphic-container {
  position: relative;
  overflow: hidden; /* 必须裁切，营造延伸感 */
}

.atour-graphic {
  max-width: 50%; /* 图形面积不超过版面 1/2 */
  position: absolute;
  /* 建议放在角落或边缘，部分裁切在画面外 */
}
```

**关键限制**：图形面积 ≤ 版面 1/2，必须 `overflow: hidden`，图形应"安静存在于背景中"。

---

## 禁止用法

| ❌ 禁止 | ✅ 正确 |
|---------|---------|
| CSS `filter` 或 `opacity` 改变 Logo 颜色 | 只用官方黑白两色切图 |
| 非等比拉伸/压缩 Logo（`width` + `height`） | 保持 `aspect-ratio`，用 `object-fit: contain` |
| 复杂背景直接叠加 Logo（无蒙版） | 加半透明纯色蒙版，确保对比度 ≥ 4.5:1 |
| 导航栏 Logo 贴近屏幕边缘（< 16px） | 保持 ≥ 16px 安全距离 |
| 仅提供 1x 分辨率素材 | 提供 @2x/@3x，使用 `srcset` |
| 用系统字体键入 Slogan | 使用官方图形切图（PNG/SVG） |
| CSS `filter` 改变辅助图形颜色 | 按背景使用对应颜色的图形资产 |

### 蒙版正确示范

```html
<div style="position:relative; background-image: url(hotel.jpg)">
  <div style="
    position:absolute; inset:0;
    background: linear-gradient(to right, rgba(255,255,255,0.85) 40%, transparent);
  "></div>
  <img src="logo-black.svg" style="position:relative; z-index:1">
</div>
```

---

## 移动端响应式

```css
/* 响应式标题 */
.atour-h1 {
  font-size: clamp(28px, 5vw, 40px);
  font-family: var(--font-brand-zh);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

/* 导航栏安全边距 */
.navbar-logo {
  margin-left: 16px; /* ≥ 2X 安全距离 */
  min-width: 40px;
}
```
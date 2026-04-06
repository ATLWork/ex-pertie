# Stitch 原型页面生成提示词

> 项目地址：https://stitch.withgoogle.com/projects/15250555491043093900
>
> 使用方法：在 Stitch 项目中点击「+」新建屏幕，将对应 prompt 粘贴进去，选择 Desktop 设备类型后生成。
>
> 设计系统已配置：金色主色 #8B6914、奶油底色 #fef9f1、Manrope 标题字体、Inter 正文字体、无边框分隔设计。

---

## 缺失页面清单

根据 PRD 第 3.1 节，以下 6 个页面尚未在原型中创建：

| # | 页面 | PRD 功能描述 | 状态 |
|---|------|------------|------|
| 1 | 登录页 | 用户登录/注册 | ❌ 待生成 |
| 2 | 数据导入页 | 酒店数据、客房数据导入 | ❌ 待生成 |
| 3 | 翻译工作台 | 翻译任务列表、批量处理 | ❌ 待生成 |
| 4 | 翻译编辑页 | 单条翻译审核、润色 | ❌ 待生成 |
| 5 | 导出中心 | 导出任务管理、历史记录 | ❌ 待生成 |
| 6 | 系统设置 | 用户管理、术语库、配置 | ❌ 待生成 |

---

## Page 1 — 登录页

**功能要点（来自 PRD 2.5.1）**：支持邮箱密码登录、企业 SSO 登录、忘记密码流程。

```
Login page (登录页) for "Atour Expedia 渠道数据管理平台" - enterprise SaaS tool for Atour hotel channel operations team. Desktop 1280px wide.

LAYOUT: Split-screen, two columns.
- Left panel (40% width): Deep gold gradient background from #6f5100 to #261a00. Vertically and horizontally centered content: large "亚朵" text in Manrope ExtraBold 48px white, below it "Expedia 渠道数据管理平台" in Inter 16px white 70% opacity, below that a small decorative horizontal rule in white 20% opacity. Bottom-left corner: small "© 2026 亚朵集团" in white 40% opacity.
- Right panel (60% width): Background #fef9f1 (warm cream). Vertically centered login card.

LOGIN CARD: Background #ffffff, border-radius 16px, ambient shadow (blur 32px, color rgba(29,28,23,0.06), offset 0 8px). Width 420px, padding 48px.
- Title "欢迎回来" in Manrope Bold 28px color #1d1c17
- Subtitle "请使用企业邮箱登录" in Inter 14px color #4e4637, margin-bottom 32px
- Email field: label "邮箱" Inter 12px #4e4637, input with background #e7e2da, no border, border-radius 8px, bottom gold accent on focus, placeholder "请输入邮箱地址"
- Password field: label "密码", same style, placeholder "请输入密码", eye icon toggle on right
- Row with "记住我" checkbox left and "忘记密码？" link right in #34568c
- Primary button "登录": full width, height 48px, background linear-gradient(135deg, #8b6914, #6f5100), color white, border-radius 8px, Manrope SemiBold 16px, margin-top 24px
- Divider: centered "或" text with #d1c5b2 lines
- Secondary button "使用企业 SSO 登录": full width, height 48px, background #e7e2da, color #7a502e, border-radius 8px, no border

STYLE RULES: No 1px solid borders anywhere. No pure black. Use warm neutrals. Inputs separated by whitespace and tonal fills only.
```

---

## Page 2 — 数据导入页

**功能要点（来自 PRD 2.1）**：Excel/CSV 文件上传、字段预览与映射、校验结果展示（错误标注、修正建议）、酒店/客房数据 Tab 切换。

```
Data Import page (数据导入页) for Atour Expedia tool. Desktop 1280px. Full page with left sidebar navigation.

SIDEBAR (240px, background #f8f3eb): Logo "亚朵" top-left in Manrope Bold gold. Nav items: 工作台 (home icon), 数据导入 (upload icon, ACTIVE state with gold background #fff0da and gold text), 数据列表 (list icon), 翻译工作台 (language icon), 导出中心 (download icon), 系统设置 (settings icon). All inactive items in #4e4637. No borders between items, use 8px radius on active.

MAIN CONTENT (background #fef9f1):
- Top bar (glassmorphism, background rgba(254,249,241,0.8), backdrop-blur 16px): Page title "数据导入" in Manrope SemiBold 24px, breadcrumb below.
- Tab switcher below title: "酒店主数据" | "客房主数据" — pill style tabs, active tab gold #6f5100 text with #fff0da background, inactive #4e4637.

UPLOAD SECTION (card, background #ffffff, radius 12px, ambient shadow):
- Large dashed upload zone (dashes use #d1c5b2 at 60% opacity, radius 12px, height 200px): Cloud upload icon in gold, main text "拖拽文件至此处，或点击上传" Manrope SemiBold 16px, subtext "支持 .xlsx, .xls, .csv 格式，单次最大 10MB" Inter 14px muted.
- Below zone: "下载模板" tertiary link with download icon in #34568c.

FIELD PREVIEW SECTION (card, background #ffffff, radius 12px, margin-top 16px):
- Section header "字段预览 — 已识别 18 个字段" with "重新映射" secondary button right.
- Table with columns: 源字段名, 映射到 Expedia 字段, 示例数据, 状态. 
- Show 5-6 rows: mix of green "已匹配" chips and orange "需确认" chips. One row has red "格式错误" chip.
- Table background #fef9f1, row hover #f8f3eb, no horizontal dividers (use row spacing).

VALIDATION RESULTS SECTION (below table):
- Green summary chip "✓ 247 行数据通过校验"
- Orange chip "⚠ 3 行需要确认"  
- Red chip "✗ 2 行存在错误"
- Expandable error list showing error details with row numbers.

BOTTOM ACTION BAR (sticky, background rgba(254,249,241,0.9), backdrop-blur):
- Left: "取消" tertiary button
- Right: "上一步" secondary button + "确认导入" primary gold gradient button

STYLE: No 1px borders. Tonal backgrounds for separation. Warm cream gold palette.
```

---

## Page 3 — 翻译工作台

**功能要点（来自 PRD 2.2.5）**：翻译任务列表、状态筛选、批量操作、多源参考来源标注（携程/Booking/AI）、批量翻译触发。

```
Translation Workbench page (翻译工作台) for Atour Expedia tool. Desktop 1280px. Left sidebar navigation (same as other pages, 翻译工作台 nav item active).

TOP STATS ROW (4 metric cards, background #ffffff, radius 12px, ambient shadow, horizontal layout):
- Card 1: "全部任务" value "156" in Manrope Bold 36px gold, label Inter 12px muted
- Card 2: "待翻译" value "43" in #ba1a1a (error color)
- Card 3: "翻译中" value "12" in #34568c (tertiary)
- Card 4: "已完成" value "101" in #6f5100 (primary green-adjacent gold)

FILTER BAR (below stats, background #f8f3eb, radius 8px, padding 12px 16px, no border):
- Dropdown "全部状态" | Dropdown "字段类型" | Dropdown "来源" | Search input "搜索酒店或字段..."
- Right side: "批量翻译" primary gold gradient button with lightning icon, "导出审核报告" secondary button

MAIN TABLE (card, background #ffffff, radius 12px, ambient shadow):
- Table header row background #f8f3eb, Manrope SemiBold 12px uppercase tracking, columns:
  □ (checkbox) | 酒店名称 | 字段类型 | 原文（中文）| 译文预览 | 参考来源 | 状态 | 操作
- Show 8 data rows with varying states:
  - Row 1: 亚朵酒店北京三里屯店 | 酒店描述 | "坐落于繁华的三里屯..." | "Located in the vibrant..." | Tag "携程" (blue pill) | "已完成" green chip | 查看
  - Row 2: 亚朵酒店上海外滩店 | 房型名称 | "豪华大床房" | "Deluxe King Room" | Tag "Booking" (purple pill) | "已完成" green chip | 查看
  - Row 3: 亚朵酒店成都太古里店 | 设施描述 | "免费高速WiFi..." | "(AI 翻译中...)" | Tag "AI" (gold pill) | "翻译中" blue chip | 查看
  - Row 4: 亚朵酒店广州天河店 | 酒店描述 | "位于广州天河核心..." | "—" | "—" | "待翻译" orange chip | 翻译
  - Row 5-8: similar mix
- Row hover: background shifts to #f8f3eb
- No horizontal dividers between rows, use 16px vertical padding per row
- Checkbox column for bulk select

PAGINATION: bottom center, "共 156 条" text left, page numbers center, "每页显示 20 条" right dropdown

STYLE: No 1px borders. Status chips with rounded-full pill shape. Source tags color-coded.
```

---

## Page 4 — 翻译编辑页

**功能要点（来自 PRD 2.2.5）**：原文/译文对照展示、参考来源对比（携程/Booking）、翻译规则提示、接受/修改/拒绝操作、历史记录。

```
Translation Editor page (翻译编辑页) for reviewing and editing a single translation. Desktop 1280px. Left sidebar nav (翻译工作台 active).

TOP BAR: Breadcrumb "翻译工作台 / 亚朵酒店成都太古里店 / 酒店描述". Left arrow back button. Right: progress indicator "第 3 条 / 共 43 条待审核" with prev/next arrows.

MAIN CONTENT (two-column layout below top bar):

LEFT COLUMN (55%, source text):
- Card (background #ffffff, radius 12px, shadow): 
  - Header: label "原文（中文）" in Manrope SemiBold 14px gold + hotel name chip
  - Body: full Chinese source text in Inter 16px line-height 1.8 color #1d1c17, with paragraph spacing
  - Bottom metadata row: 字数 "148 字" | 字段类型 "酒店描述" | 酒店 "成都太古里店"

RIGHT COLUMN (45%, translation + references):
- Top card "当前译文" (background #ffffff, radius 12px, shadow):
  - Editable textarea with current English translation, gold focus border-bottom
  - Word count "127 words" bottom right in muted
  - Small "AI 润色" tertiary button with sparkle icon

- Middle card "参考译文" (background #f8f3eb, radius 12px):
  - Tab row: "携程参考" | "Booking 参考"
  - Content: reference translation text in Inter 15px, muted #4e4637
  - Bottom: "使用此译文" ghost button in gold

- Bottom card "适用翻译规则" (background #fff0da, radius 12px):
  - Rule list: 2-3 applicable rules as bullet points, e.g. "✓ 酒店名称保持英文不翻译", "✓ 地名使用拼音+英文"
  - "查看完整规则" tertiary link

BOTTOM ACTION BAR (sticky, background rgba(254,249,241,0.9), backdrop-blur 16px):
- Left: modification history link "查看修改历史 (2)"
- Center: quality score "AI 评分: 92/100" with gold star icon
- Right actions: "拒绝" tertiary red | "保存草稿" secondary | "接受译文" primary gold gradient button

STYLE: No borders. Tonal card backgrounds. Warm cream palette. Chinese text line-height 1.8.
```

---

## Page 5 — 导出中心

**功能要点（来自 PRD 2.4）**：导出格式选择（Excel/CSV/JSON）、导出前校验清单、进行中任务进度、历史导出记录、导出报告。

```
Export Center page (导出中心) for Atour Expedia tool. Desktop 1280px. Left sidebar nav (导出中心 active).

PAGE HEADER: Title "导出中心" Manrope Bold 24px. Right: "新建导出任务" primary gold gradient button with plus icon.

SECTION 1 — ACTIVE EXPORT TASK (card, background #ffffff, radius 12px, ambient shadow, margin-bottom 24px):
- Header "进行中的任务 (1)" Manrope SemiBold 14px
- Task row: hotel name "亚朵集团 — 批次4 (12家门店)", format tag "Excel", start time "2026-04-06 14:32"
- Progress bar: gold fill #8b6914, 68% complete, label "正在生成... 68%" 
- Right: "取消" tertiary button

SECTION 2 — NEW EXPORT CONFIGURATION (card, background #ffffff, radius 12px, ambient shadow):
- Header "配置导出任务"
- Form fields (no borders, tonal fills):
  - 选择酒店: multi-select tag input showing selected hotels as gold chips, placeholder "搜索并选择酒店..."
  - 导出格式: three radio cards side by side — Excel (selected, gold border-bottom), CSV, JSON. Each shows format icon + name + brief description
  - 数据范围: checkbox group "酒店基本信息 ✓", "客房信息 ✓", "设施信息 ✓", "翻译内容 ✓"
  
- Pre-export checklist section "导出前校验":
  - ✓ "所有必填字段已填充" — green
  - ✓ "数据格式符合 Expedia 要求" — green  
  - ✓ "英文翻译已完成" — green
  - ✓ "数据无重复 (共 247 条)" — green
  - ⚠ "3 条数据缺少经纬度" — orange with "去修复" link
  - ✓ "关联关系正确" — green

SECTION 3 — EXPORT HISTORY (card, background #ffffff, radius 12px):
- Header "历史导出记录"
- Table: columns 导出时间 | 批次名称 | 酒店数量 | 记录数 | 格式 | 状态 | 操作
- 4 rows with "已完成" green chips and download/re-export action links in #34568c
- One row with "失败" red chip

STYLE: No 1px borders. Tonal backgrounds. Gold progress bar. Warm cream palette.
```

---

## Page 6 — 系统设置

**功能要点（来自 PRD 2.5）**：用户权限管理（4 种角色）、术语库管理（增删改查、分类）、翻译规则管理（上传 PDF 解析）、翻译参考库配置。

```
System Settings page (系统设置) for Atour Expedia tool. Desktop 1280px. Left sidebar nav (系统设置 active).

LAYOUT: Two-panel settings layout.
- Left settings menu (200px, background #f8f3eb): Category list with icons:
  - 用户管理 (SELECTED, gold background #fff0da, gold text)
  - 术语库
  - 翻译规则
  - 翻译参考库
  - 基本配置
  No borders between items, 8px radius on selected, 8px padding.

- Right content area (background #fef9f1):

SECTION: 用户管理 (currently shown)
- Header row: "用户管理" title + "邀请成员" primary gold button top right
- Stats row: "共 18 名成员" | "管理员 2" | "运营人员 11" | "翻译人员 4" | "查看人员 1"
- User table (card, background #ffffff, radius 12px, shadow):
  Columns: 姓名 | 邮箱 | 角色 | 最后活跃 | 状态 | 操作
  5-6 rows with:
  - Role chips: "管理员" (gold #fff0da text #6f5100), "运营人员" (blue-ish), "翻译人员" (purple-ish), "查看人员" (grey)
  - Status: "活跃" green chip, "已停用" grey chip
  - Actions: 编辑角色 | 停用 links in muted color
  - No row dividers, alternating hover state

BOTTOM QUICK CARDS (3 cards in a row, each background #ffffff, radius 12px, shadow):
- Card 1 "术语库": icon + "共 342 个术语" large number + "5 个待审核" orange badge + "管理术语库" gold link
- Card 2 "翻译规则": icon + "3 条规则已配置" + "覆盖 24 省市" + "管理规则" gold link  
- Card 3 "翻译参考库": icon + "携程: 1,247 条" + "Booking: 986 条" + "更新参考库" gold link

STYLE: No 1px borders. Tonal layering for panels. Category menu uses background shift not borders. Warm cream gold palette.
```

---

## 设计规范参考

生成时 Stitch 会自动应用项目设计系统，核心规则：

| 规则 | 说明 |
|------|------|
| 禁止 1px 边框 | 用背景色层级区分区域 |
| 主色 | `#6f5100` (gold)，按钮用渐变 `#8b6914 → #6f5100` |
| 底色层级 | `#fef9f1` 基底 → `#f8f3eb` 侧栏 → `#ffffff` 卡片 |
| 标题字体 | Manrope |
| 正文字体 | Inter |
| 圆角 | 8px 按钮/输入框，12-16px 卡片 |
| 阴影 | blur 32px, rgba(29,28,23,0.06), offset 0 8px |

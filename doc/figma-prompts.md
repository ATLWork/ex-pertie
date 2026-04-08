# Figma 原型页面生成提示词

> 项目地址：https://www.figma.com/design/5JmzHb78OaGIh9FKZOGBFB
>
> 使用方法：在 Figma 项目中新建 Frame，选择 Desktop 1280×960，将对应 prompt 粘贴进 AI 生成工具（如 Figma Make）后生成。
>
> 设计系统已配置：金色主色 #8B6914、奶油底色 #fef9f1、Manrope 标题字体、Inter 正文字体、无边框分隔设计。

---

## 缺失页面清单

根据 PRD 第 3.1 节，以下 9 个页面需在原型中创建：

| # | 页面 | PRD 功能描述 | Linear Issue | 状态 |
|---|------|------------|-------------|------|
| 1 | 登录页 | 用户登录/注册 | JAR-27 | ❌ 待生成 |
| 2 | 工作台首页 | 数据概览、快捷入口 | JAR-33 | ❌ 待生成 |
| 3 | 数据导入页 | 酒店数据、客房数据导入 | JAR-28 | ❌ 待生成 |
| 4 | 数据列表页 | 已导入数据查看、筛选、编辑 | JAR-34 | ❌ 待生成 |
| 5 | 数据详情页 | 单条数据详细信息、编辑 | JAR-35 | ❌ 待生成 |
| 6 | 翻译工作台 | 翻译任务列表、批量处理 | JAR-29 | ❌ 待生成 |
| 7 | 翻译编辑页 | 单条翻译审核、润色 | JAR-30 | ❌ 待生成 |
| 8 | 导出中心 | 导出任务管理、历史记录 | JAR-31 | ❌ 待生成 |
| 9 | 系统设置 | 用户管理、术语库、配置 | JAR-32 | ❌ 待生成 |

---

## Page 1 — 登录页

**功能要点（来自 PRD 2.5.1，已更新）**：企业邮箱验证码登录，仅允许 @atour.com / @atahouse.com 后缀，无密码登录。

> **变更记录**：2026-04-08 由邮箱+密码改为验证码登录，见 Linear [JAR-36](https://linear.app/jarvisdesign/issue/JAR-36)。

```
Login page (登录页) for "Atour Expedia 渠道数据管理平台". Desktop 1280px wide. Email OTP login only — no password field.

LAYOUT: Split-screen, two columns.
- Left panel (40% width): Deep gold gradient background from #8b6914 to #261a00. Center content: "亚朵" in Manrope ExtraBold 56px white, "Expedia 渠道数据管理平台" in Inter 16px white 70% opacity, thin white rule below. Security info card (background white 8% opacity, radius 12px): title "仅限亚朵企业邮箱登录" Inter SemiBold 14px white 90%, subtitle "支持后缀：@atour.com · @atahouse.com" Inter 12px white 60%. Bottom-left: "© 2026 亚朵集团" white 40%.
- Right panel (60% width): Background #fef9f1. Vertically centered login card.

LOGIN CARD: Background #ffffff, border-radius 16px, ambient shadow (blur 32px, rgba(29,28,23,0.08), offset 0 8px). Width 420px.
- Title "企业邮箱验证码登录" Manrope Bold 24px #1d1c17
- Subtitle "输入邮箱后发送验证码完成登录" Inter 14px #4e4637

EMAIL ROW (label "企业邮箱"):
- Left input (65% width): background #e7e2da, radius 8px, placeholder "username@atour.com"
- Right button (35% width): "发送验证码" gold gradient (#8b6914→#6f5100), radius 8px, Inter SemiBold 12px white
- Below row: hint chip background #fff0da, text "仅接受 @atour.com 或 @atahouse.com 后缀" Inter 11px #6f5100

CODE ROW (label "验证码"):
- Left input (65% width): background #e7e2da, radius 8px, placeholder "请输入 6 位验证码"
- Right area (35% width): background #e7e2da, radius 8px, text "59 秒后重发" Inter 12px muted (shown after send)
- Error state (shown on invalid domain): chip background #fde8e8, text "非亚朵企业邮箱，无法登录" Inter 11px #ba1a1a

PRIMARY BUTTON: "登录" full width, height 48px, gold gradient, Manrope Bold 16px white, radius 8px.

FOOTER: "登录遇到问题？联系 IT 支持" Inter 12px muted, centered.

STYLE RULES: No 1px borders. No password field. No SSO button. Warm cream palette. Tonal fills only.
```

---

## Page 2 — 工作台首页

**功能要点（来自 PRD 3.1 + JAR-33）**：数据概览指标、快捷入口、最近导入记录、待处理任务提示。

```
Dashboard / Workbench home page (工作台首页) for Atour Expedia tool. Desktop 1280px. Full page with left sidebar navigation.

SIDEBAR (240px, background #f8f3eb): Logo "亚朵" top-left in Manrope Bold gold. Nav items: 工作台 (home icon, ACTIVE state with gold background #fff0da and gold text #6f5100), 数据导入 (upload icon), 数据列表 (list icon), 翻译工作台 (language icon), 导出中心 (download icon), 系统设置 (settings icon). All inactive items in #4e4637. No borders between items, use 8px radius on active.

MAIN CONTENT (background #fef9f1):
- Top bar (glassmorphism, background rgba(254,249,241,0.8), backdrop-blur 16px): Page title "工作台" in Manrope SemiBold 24px. Right side: user avatar chip with name "Chester LU".

STATS ROW (4 metric cards, horizontal layout, margin-top 24px, gap 16px):
- Card 1 (background #ffffff, radius 12px, ambient shadow): icon hotel-building in gold circle, value "42" in Manrope Bold 40px color #1d1c17, label "酒店总数" in Inter 12px #4e4637, sub-label "已上线 38 家" in Inter 11px muted
- Card 2: icon language, value "1,247" in #ba1a1a, label "待翻译字段", sub-label "本周新增 86 条"
- Card 3: icon download, value "8" in #6f5100, label "本月导出", sub-label "最近: 2026-04-06"
- Card 4: icon check-circle, value "89%" in #34568c, label "翻译完成率", sub-label progress bar (gold fill 89%)

QUICK ACTIONS SECTION (margin-top 24px):
- Section header "快捷入口" Manrope SemiBold 14px color #4e4637
- Three action cards side by side (background #ffffff, radius 12px, ambient shadow, height 120px, cursor pointer, hover: background #fff0da transition):
  - Card A: upload icon in large gold 32px, title "导入数据" Manrope SemiBold 16px, subtitle "上传 Excel/CSV 文件" Inter 13px muted
  - Card B: language icon, title "批量翻译", subtitle "启动 AI 翻译任务"
  - Card C: download icon, title "导出表格", subtitle "生成 Expedia 上传文件"

TWO-COLUMN LOWER SECTION (gap 16px):

LEFT (65%): RECENT IMPORTS CARD (background #ffffff, radius 12px, ambient shadow):
- Header "最近导入记录" Manrope SemiBold 14px + "查看全部" link right in #34568c
- Table rows (no horizontal dividers, 16px row padding):
  Row 1: "亚朵集团 批次4" | 酒店主数据 | 12家门店 | 2026-04-06 14:32 | "已完成" green chip
  Row 2: "亚朵集团 批次4" | 客房主数据 | 47个房型 | 2026-04-06 14:35 | "已完成" green chip
  Row 3: "亚朵集团 批次3" | 酒店主数据 | 8家门店 | 2026-03-28 10:12 | "已完成" green chip
  Row 4: "亚朵集团 批次2" | 酒店主数据 | 15家门店 | 2026-03-15 09:44 | "已完成" green chip
  Row 5: "亚朵集团 批次1" | 酒店主数据 | 7家门店 | 2026-03-01 11:20 | "已完成" green chip

RIGHT (35%): PENDING TASKS CARD (background #ffffff, radius 12px, ambient shadow):
- Header "待处理任务" Manrope SemiBold 14px + orange badge "5"
- Task list (vertical, no dividers, 12px gap):
  - Orange alert icon + "1,247 个字段待翻译" bold + "去处理 →" gold link right
  - Orange alert icon + "3 条数据缺少经纬度" + "去修复 →" gold link right
  - Yellow warning icon + "12 个术语待审核" + "去审核 →" gold link right
  - Blue info icon + "批次4 导出报告已就绪" + "查看 →" gold link right
  - Green check icon + "所有必填字段已完整 (批次3)" muted text

STYLE: No 1px borders. Tonal backgrounds. Warm cream gold palette.
```

---

## Page 3 — 数据导入页

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

## Page 4 — 数据列表页

**功能要点（来自 PRD 2.1 + JAR-34）**：酒店/客房 Tab 切换、多维筛选、完整度进度条、分页。

```
Data List page (数据列表页) for Atour Expedia tool. Desktop 1280px. Full page with left sidebar navigation.

SIDEBAR (240px, background #f8f3eb): Logo "亚朵" top-left in Manrope Bold gold. Nav items: 工作台 (home icon), 数据导入 (upload icon), 数据列表 (list icon, ACTIVE state with gold background #fff0da and gold text #6f5100), 翻译工作台 (language icon), 导出中心 (download icon), 系统设置 (settings icon). All inactive items in #4e4637.

MAIN CONTENT (background #fef9f1):
- Top bar (glassmorphism, background rgba(254,249,241,0.8), backdrop-blur 16px): Page title "数据列表" in Manrope SemiBold 24px. Right: "导入数据" primary gold gradient button with upload icon.
- Tab switcher: "酒店主数据 (42)" | "客房主数据 (186)" — pill tabs, active gold.

FILTER BAR (background #f8f3eb, radius 8px, padding 12px 16px, no border, margin-bottom 16px):
- Dropdown "全部省份" | Dropdown "全部状态" | Dropdown "翻译状态" | Search input "搜索酒店名称或 ID..." (flex-grow)
- Right: "重置筛选" tertiary link

MAIN TABLE (card, background #ffffff, radius 12px, ambient shadow):
- Table header row (background #f8f3eb): Manrope SemiBold 12px uppercase tracking
  Columns: □ (checkbox) | 酒店名称 | hotel_id | 省市 | 翻译状态 | 完整度 | 操作
- Show 8 data rows (no horizontal dividers, 16px vertical padding):
  Row 1: □ | 亚朵酒店北京三里屯店 | ATH-001 | 北京市 朝阳区 | "已完成" green chip | progress bar 100% gold fill | 查看 编辑
  Row 2: □ | 亚朵酒店上海外滩店 | ATH-002 | 上海市 黄浦区 | "已完成" green chip | 98% | 查看 编辑
  Row 3: □ | 亚朵酒店成都太古里店 | ATH-003 | 四川省 成都市 | "翻译中" blue chip | 72% | 查看 编辑
  Row 4: □ | 亚朵酒店广州天河店 | ATH-004 | 广东省 广州市 | "待翻译" orange chip | 65% | 查看 编辑
  Row 5: □ | 亚朵酒店杭州西湖店 | ATH-005 | 浙江省 杭州市 | "待翻译" orange chip | 60% | 查看 编辑
  Row 6: □ | 亚朵酒店深圳南山店 | ATH-006 | 广东省 深圳市 | "已完成" green chip | 100% | 查看 编辑
  Row 7: □ | 亚朵酒店武汉光谷店 | ATH-007 | 湖北省 武汉市 | "缺少数据" red chip | 45% | 查看 编辑
  Row 8: □ | 亚朵酒店南京夫子庙店 | ATH-008 | 江苏省 南京市 | "待翻译" orange chip | 58% | 查看 编辑
- Progress bar style: thin 6px bar, gold fill #8b6914, background #e7e2da, border-radius 3px, width 80px
- Row hover: background shifts to #f8f3eb
- Bulk action bar appears when rows checked: "已选 3 项" + "批量翻译" + "批量导出" + "删除" buttons

PAGINATION (bottom): left "共 42 条记录", center page numbers (1 active gold circle, 2 3 4 ... 6), right "每页显示 10 条" dropdown.

STYLE: No 1px borders. Status chips with rounded-full pill shape. Warm cream gold palette.
```

---

## Page 5 — 数据详情页

**功能要点（来自 PRD 4.1 + JAR-35）**：酒店完整字段展示、翻译状态面板、关联客房列表、Expedia 字段映射状态、编辑/导出操作。

```
Hotel Data Detail page (数据详情页) for a single hotel record. Desktop 1280px. Left sidebar navigation (数据列表 active).

TOP BAR: Breadcrumb "数据列表 / 亚朵酒店成都太古里店". Left arrow back button. Right actions: "编辑" secondary button (pencil icon) + "导出此酒店" primary gold gradient button (download icon).

TWO-COLUMN LAYOUT below top bar (gap 16px):

LEFT COLUMN (65%):

BASIC INFO CARD (background #ffffff, radius 12px, ambient shadow, margin-bottom 16px):
- Card header "基本信息" Manrope SemiBold 14px gold + hotel_id chip "ATH-003" in #f8f3eb
- Two-column field grid (label Inter 11px #4e4637 uppercase, value Inter 14px #1d1c17):
  酒店中文名 | 亚朵酒店成都太古里店
  酒店英文名 | Atour Hotel Chengdu Taikoo Li
  中文地址 | 四川省成都市锦江区中纱帽街8号
  英文地址 | No.8 Zhongshama Street, Jinjiang District, Chengdu
  城市 | 成都市 | 省份 | 四川省
  联系电话 | 028-12345678 | 邮箱 | chengdu-taikoo@atour.com
  纬度 | 30.6571 | 经度 | 104.0804
  星级 | ★★★★★ (5星) | 物业类型 | Hotel
  入住时间 | 14:00 | 退房时间 | 12:00

AMENITIES CARD (background #ffffff, radius 12px, ambient shadow, margin-bottom 16px):
- Header "设施与服务"
- Chips layout (wrap): "免费WiFi" "停车场" "早餐" "健身房" "餐厅" "24小时前台" "行李寄存" "会议设施" "商务中心" — each chip background #f8f3eb, color #4e4637, radius 20px, Inter 13px

EXPEDIA MAPPING CARD (background #ffffff, radius 12px, ambient shadow, margin-bottom 16px):
- Header "Expedia 字段映射状态" + "共 24 个字段 · 22 已映射"
- Mini table: 字段名 | Expedia 字段 | 状态
  5-6 rows: show mostly green "已映射" chips, one orange "待确认", one red "缺失"

ROOMS CARD (background #ffffff, radius 12px, ambient shadow):
- Header "关联客房 (6个房型)" Manrope SemiBold 14px
- Mini table columns: 房型名称 | 床型 | 面积 | 最大入住 | 翻译状态
  Row 1: 豪华大床房 | 大床 King | 38㎡ | 2人 | "已完成" green chip
  Row 2: 豪华双床房 | 双床 Twin | 38㎡ | 3人 | "已完成" green chip
  Row 3: 行政套房 | 大床 King | 58㎡ | 2人 | "翻译中" blue chip
  Row 4: 标准大床房 | 大床 King | 32㎡ | 2人 | "待翻译" orange chip
  Row 5: 无障碍大床房 | 大床 King | 35㎡ | 2人 | "已完成" green chip
  Row 6: 亲子家庭房 | 双床 Twin | 52㎡ | 4人 | "待翻译" orange chip
- No horizontal dividers, 12px row padding, row hover #f8f3eb

RIGHT COLUMN (35%):

TRANSLATION STATUS CARD (background #ffffff, radius 12px, ambient shadow, margin-bottom 16px):
- Header "翻译状态" Manrope SemiBold 14px
- Large donut chart centered: 89% completion in gold #8b6914, remaining in #e7e2da. Center text: "89%" Manrope Bold 28px gold, "已完成" Inter 12px muted
- Stats row below chart: "22 已完成" green | "2 进行中" blue | "1 缺失" red

FIELD TRANSLATION LIST (below donut, same card continuing):
- Section label "逐字段翻译状态" Inter 11px uppercase muted
- List of 8 fields (no dividers, 10px gap):
  酒店英文名 | "已完成" green chip
  英文地址 | "已完成" green chip
  酒店描述 | "已完成" green chip
  周边描述 | "翻译中" blue chip
  房型: 豪华大床房 | "已完成" green chip
  房型: 行政套房 | "翻译中" blue chip
  房型: 标准大床房 | "待翻译" orange chip
  房型: 亲子家庭房 | "待翻译" orange chip
- "启动翻译" gold gradient button full width at bottom, height 40px

QUICK ACTIONS CARD (background #ffffff, radius 12px, ambient shadow):
- Header "快捷操作"
- Action list (vertical, 8px gap):
  "查看导出预览" link with external icon in #34568c
  "下载翻译报告" link with download icon in #34568c
  "标记数据异常" link with flag icon in #ba1a1a (muted)

STYLE: No 1px borders. Tonal backgrounds. Donut chart gold fill. Warm cream palette.
```

---

## Page 6 — 翻译工作台

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

## Page 7 — 翻译编辑页

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

## Page 8 — 导出中心

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

## Page 9 — 系统设置

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

生成时自动应用项目设计系统，核心规则：

| 规则 | 说明 |
|------|------|
| 禁止 1px 边框 | 用背景色层级区分区域 |
| 主色 | `#6f5100` (gold)，按钮用渐变 `#8b6914 → #6f5100` |
| 底色层级 | `#fef9f1` 基底 → `#f8f3eb` 侧栏 → `#ffffff` 卡片 |
| 标题字体 | Manrope |
| 正文字体 | Inter |
| 圆角 | 8px 按钮/输入框，12-16px 卡片 |
| 阴影 | blur 32px, rgba(29,28,23,0.06), offset 0 8px |

# 酒店数据管理工具 - 产品需求文档 (PRD)

> **平台优先级**：Booking.com **高优先级** | Expedia 低优先级（后续支持）

## 一、项目概述

### 1.1 项目背景
亚朵渠道运营团队需要将酒店信息上架至 Expedia 和 Booking.com 平台，目前需要手动整理大量数据、翻译内容、填充表格，效率低下且容易出错。本工具旨在自动化这一流程，提升运营效率。

**优先级说明**：Booking.com 平台对接为**高优先级**，Expedia 平台为**低优先级（后续支持）**。

### 1.2 目标用户
- 亚朵渠道运营伙伴
- 酒店数据维护人员
- 翻译审核人员

### 1.3 核心价值
- **效率提升**：自动化数据组合与填充，减少 80% 手动操作
- **翻译质量**：AI 多源参考润色，确保翻译专业准确
- **合规保障**：遵循平台规范，减少上架驳回率

### 1.4 项目范围

**高优先级（当前阶段）**：
- 支持 Booking.com 酒店主数据和客房主数据的导入与管理
- 提供智能翻译功能（以 Booking 翻译为参考基准）
- 自动生成符合 Booking.com XML 规范的数据文件
- 支持翻译审核和术语库管理

**低优先级（后续阶段）**：
- Expedia 平台对接
- Expedia 模板生成与导出

---

## 二、功能模块设计

### 2.1 数据导入模块

> **优先级**：Booking.com 高优先级，Expedia 低优先级

#### 2.1.1 酒店主数据导入

| 功能项 | 说明 |
|-------|------|
| 数据源 | Excel/CSV 文件上传 |
| 字段内容 | 酒店名称、地址、联系方式、设施、服务、描述等 |
| 校验规则 | 必填字段检查、格式校验、重复数据检测 |
| 错误处理 | 标注错误行、提供修正建议、支持批量修正 |

**Booking.com 字段要求**：
- LegalEntityID（法律实体ID）
- HotelName（仅拉丁字符）
- PhysicalLocation 地址（城市、国家、邮编）
- ContactInfo（联系人：姓名、邮箱、电话）
- 经纬度、入住/退房时间、房间数、住宿类型

**数据模型参考**：
- Booking.com: `reference/Booking亚朵集团酒店主数据英文信息--3.25.xlsx`
- 内部格式: `reference/酒店主数据 - 门店信息 2026-03-03 10_26_48.xlsx`

#### 2.1.2 客房主数据导入

| 功能项 | 说明 |
|-------|------|
| 数据源 | Excel/CSV 文件上传 |
| 字段内容 | 房型、面积、床型、设施 |
| 关联关系 | 通过 hotel_id 关联酒店主数据 |
| 校验规则 | 房型完整性、Apartment 必须有厨房 |

**Booking.com 房型特殊要求**：
- Apartment/Aparthotel/Condominium 类型**必须**配备厨房
- 多卧室房型（Suite/Apartment）支持 SubRooms 结构
- 床型使用 AmenityCode（如 203=Twin, 249=Double）

**数据模型参考**：
- Booking.com: `reference/Booking亚朵集团房型英文信息核查-3.25.xlsx`
- 内部格式: `reference/酒店房型静态信息 2026-02-19 13_26_14.xlsx`

---

### 2.2 翻译模块

> **优先级**：Booking.com 翻译为核心（高优先级），Expedia 翻译为辅（低优先级）

#### 2.2.1 翻译规则管理
翻译规则可以由多项规则构成：公司规则、行业规则、国家颁布的规则等。

**规则层级**:
- 用户可以上传多个规则，并为这些规则添加适用的省、市、国家
- 翻译不同省市酒店时优先参考公司规则，其次参考国家、省、市的各项规则

**规则来源**:
- 集团翻译规则: `reference/SOP-酒店房型英文翻译规则1.0.pdf`
- 其他翻译规则以 PDF 格式呈现
- 上传 PDF 后系统自动解析，通过大模型理解含义并生成翻译规则

#### 2.2.2 翻译参考库
翻译时**优先参考 Booking.com 的现有翻译**，符合要求则直接使用，否则使用翻译规则进行翻译。

**参考数据**（按优先级排序）:
1. Booking.com 酒店主数据翻译: `reference/Booking亚朵集团酒店主数据英文信息--3.25.xlsx`
2. Booking.com 房间主数据翻译: `reference/Booking亚朵集团房型英文信息核查-3.25.xlsx`
3. 携程酒店/房间翻译（备用）
4. 翻译规则（大模型校验润色）

#### 2.2.3 翻译工作流（Booking.com 优先）

```
翻译处理流程（Booking.com 优先）:
1. 查询 Booking.com 参考库
   ├── 查到 → 通过公司规范进行大模型校验并润色
   └── 未命中 → 继续下一步

2. 查询携程参考库
   ├── 查到 → 通过公司规范进行大模型校验并润色
   └── 未命中 → 继续下一步

3. 检测源文本语言，调用腾讯云翻译 API
   ├── 翻译成功 → 通过规范进行大模型校验并润色
   └── 翻译不可用 → 继续下一步

4. 直接通过大模型结合规范进行翻译
```

#### 2.2.4 翻译质量评估

> **评估基准**：以 Booking.com 英文翻译为标准

| 评估维度 | 说明 | 指标 |
|---------|------|------|
| 准确性 | 语义是否准确传达 | 人工抽检 |
| 专业性 | 术语使用是否规范 | 术语库匹配率 |
| 本土化 | 表达是否符合目标市场习惯（英语） | AI 评分 |
| 完整性 | 信息是否完整无遗漏 | 字段覆盖率 |
| Booking 匹配度 | 与 Booking 现有翻译的一致性 | 参考库命中率 |

#### 2.2.5 人工审核功能

| 功能项 | 说明 |
|-------|------|
| 翻译对比 | 原文/Booking译文/自译译文对照展示 |
| 批量审核 | 支持批量接受/拒绝/修改 |
| 历史记录 | 翻译修改历史追溯 |
| 术语库更新 | 审核确认后自动更新术语库 |

---

### 2.3 Booking.com 数据配置模块

> **优先级**：高优先级（当前阶段）

#### 2.3.1 数据模型
根据 Booking.com OTA_XML 规范生成数据模型。

**参考文件**:
- Booking.com 酒店主数据: `reference/Booking亚朵集团酒店主数据英文信息--3.25.xlsx`
- Booking.com 房型数据: `reference/Booking亚朵集团房型英文信息核查-3.25.xlsx`
- 内部酒店数据: `reference/酒店主数据 - 门店信息 2026-03-03 10_26_48.xlsx`

#### 2.3.2 数据合并引擎
```
处理流程:
1. 加载酒店主数据（内部格式）
2. 加载客房主数据（内部格式）
3. 通过 hotel_id 建立关联
4. 执行字段映射规则（内部 → Booking.com XML）
5. 生成组合数据集
6. 标记缺失字段（必填/推荐/可选）
```

#### 2.3.3 缺失数据识别与填充
| 缺失类型 | 处理策略 |
|---------|---------|
| 必填字段缺失 | 标红警告，阻止导出 |
| 推荐字段缺失 | 黄色提示，可继续导出 |
| 可选字段缺失 | 灰色标记，可忽略 |

**自动填充规则**:
- CountryCode: 默认 "CN"（中国）
- CurrencyCode: 默认 "CNY"
- CheckInTime: 默认 "14:00"
- CheckOutTime: 默认 "12:00"
- LanguageCode: 默认 "en"（英文）
- 取消政策: 默认全退 (PolicyCode=152)

---

### 2.4 数据导出模块

> **优先级**：Booking.com 高优先级，Expedia 低优先级

#### 2.4.1 导出格式
| 格式 | 说明 | 适用场景 |
|-----|------|---------|
| XML | Booking.com OTA_HotelDescriptiveContentNotif 格式 | API 上传 |
| Excel (.xlsx) | 完整 Booking.com 数据预览 | 人工审核 |
| JSON | 结构化数据 | 系统对接 |

#### 2.4.2 导出校验
```
导出前校验清单:
□ 所有必填字段已填充
□ 数据格式符合 Booking.com XML 要求
□ 英文翻译已完成（酒店名称、地址、描述等）
□ 数据无重复
□ 关联关系正确
□ 房型厨房要求已满足（Apartment 等必须有厨房）
□ 取消政策已设置
```

#### 2.4.3 导出报告
- 导出数据统计
- 缺失字段警告
- 翻译覆盖率
- 错误/警告汇总

---

### 2.5 系统管理模块

#### 2.5.1 用户权限管理
| 角色 | 权限范围 |
|-----|---------|
| 管理员 | 全部功能、用户管理、配置管理 |
| 运营人员 | 数据导入、翻译审核、数据导出 |
| 翻译人员 | 翻译审核、术语库维护 |
| 查看人员 | 仅查看数据 |

#### 2.5.2 术语库管理
- 术语增删改查
- 术语分类（酒店名/房型/设施/服务/地名）
- 术语审核流程
- 导入/导出术语库

#### 2.5.3 日志与审计
- 操作日志记录
- 数据变更追踪
- 导出记录管理

---

## 三、页面设计

### 3.1 页面清单

| 页面 | 功能描述 | 终端 |
|-----|---------|------|
| 登录页 | 用户登录/注册 | 桌面端 |
| 工作台首页 | 数据概览、快捷入口 | 桌面端 |
| 数据导入页 | 酒店数据、客房数据导入 | 桌面端 |
| 数据列表页 | 已导入数据查看、筛选、编辑 | 桌面端 |
| 数据详情页 | 单条数据详细信息、编辑 | 桌面端 |
| 翻译工作台 | 翻译任务列表、批量处理 | 桌面端 |
| 翻译编辑页 | 单条翻译审核、润色 | 桌面端 |
| 导出中心 | 导出任务管理、历史记录 | 桌面端 |
| 系统设置 | 用户管理、术语库、配置 | 桌面端 |

### 3.2 核心页面流程

#### 3.2.1 数据导入流程
```
上传文件 → 格式校验 → 字段识别 → 预览确认 → 导入处理 → 结果反馈
```

#### 3.2.2 翻译处理流程
```
选择待翻译数据 → 批量翻译 → 结果预览 → 人工审核 → 确认保存
```

#### 3.2.3 数据导出流程
```
选择导出数据 → 校验检查 → 选择导出格式 → 生成文件 → 下载
```

---

## 四、Booking.com 字段映射规则

> **优先级**：高优先级（当前阶段）
> **说明**：Expedia 字段映射规则见第八章附录，低优先级后续支持。

### 4.1 酒店字段映射

#### 4.1.1 基本信息
| 内部字段 | Booking.com 字段 | 必填 | 说明 |
|---------|-----------------|------|------|
| hotel_id | HotelCode | 是 | 酒店唯一标识 |
| name_en | HotelName | 是 | 酒店名称（仅拉丁字符） |
| address_en | AddressLine | 是 | 地址（仅拉丁字符） |
| city | CityName | 是 | 城市 |
| country_code | CountryName | 是 | 国家代码（ISO 3166-1 alpha-2） |
| postal_code | PostalCode | 是 | 邮编 |
| province | StateProv | 否 | 省份 |
| phone | Phone/PhoneNumber | 是 | 电话（国际格式） |
| email | Email | 是 | 邮箱 |
| latitude | Position/Latitude | 是 | 纬度 |
| longitude | Position/Longitude | 是 | 经度 |
| star_rating | AffiliationInfo/Awards/Rating | 否 | 星级(0-5) |
| check_in | Policies/PolicyInfo/CheckInTime | 是 | 入住时间 |
| check_out | Policies/PolicyInfo/CheckOutTime | 是 | 退房时间 |
| room_count | GuestRoomInfo/Quantity | 是 | 可售房间数 |
| property_type | HotelCategory/Code | 是 | 住宿类型代码 |
| language_code | LanguageCode | 是 | 语言代码 |

#### 4.1.2 联系人类型 (ContactProfileType)
| 类型 | 说明 | 必填 |
|------|------|------|
| PhysicalLocation | 物理位置地址 | 是 |
| general | 一般联系人 | 是 |
| invoices | 发票联系人 | 是 |
| contract | 合同联系人 | 否 |
| reservations | 预订联系人 | 否 |

#### 4.1.3 设施服务映射
| 内部设施 | Booking.com Amenity Code | 说明 |
|---------|------------------------|------|
| 免费WiFi | 1001 或 Service Code | 无线网络 |
| 停车场 | 1002 | 停车服务 |
| 早餐 | 173 | 早餐服务 |
| 健身房 | 1004 | 健身设施 |
| 游泳池 | 1005 | 泳池 |
| SPA | 1006 | 水疗服务 |
| 餐厅 | 3 (facility_id) | 餐饮设施 |
| 接机服务 | 1037 | 机场接送 |
| 洗衣服务 | 1009 | 洗衣/干洗 |
| 24小时前台 | 1010 | 全天候前台 |

### 4.2 客房字段映射

#### 4.2.1 基本信息
| 内部字段 | Booking.com 字段 | 必填 | 说明 |
|---------|-----------------|------|------|
| room_type_zh | Description/Text | 是 | 房型名称 |
| room_type_en | Description/Text | 是 | 房型英文名 |
| area | Room/SizeMeasurement | 否 | 面积 |
| bed_type | Amenities/Amenity[@AmenityCode] | 是 | 床型代码 |
| bed_count | Amenities/Amenity[@Value] | 是 | 床数量 |
| max_occupancy | Occupancy/MaxOccupancy | 是 | 最大入住人数 |
| max_adults | Occupancy/MaxAdultOccupancy | 是 | 最大成人 |
| max_children | Occupancy/MaxChildOccupancy | 是 | 最大儿童 |
| non_smoking | Room/NonSmoking | 否 | 禁烟 (0/1/2) |

#### 4.2.2 床型映射 (AmenityCode)
| 中文床型 | Booking.com 代码 | 说明 |
|---------|------------------|------|
| 大床 | 249 | Double bed |
| 双床 | 203 | Twin beds |
| 单人床 | 204 | Single bed |
| 特大床 | 200 | King bed |
| 沙发床 | 102 | Sofa bed |
| 双层床 | 211 | Bunk bed |

**Configuration**: 1 = 标准布局, 2 = 备用布局

#### 4.2.3 房间设施映射 (AmenityCode)
| 中文设施 | 代码 | 说明 |
|---------|------|------|
| 空调 | 50 | Air conditioning |
| 电视 | 72 | TV |
| 迷你吧 | 69 | Minibar |
| 保险箱 | 26 | Safe |
| 吹风机 | 5 | Hairdryer |
| 熨斗 | 33 | Iron |
| 拖鞋 | 100 | Slippers |
| 浴袍 | 71 | Bathrobe |
| 免费洗漱用品 | 11 | Free toiletries |
| 冰箱 | 88 | Refrigerator |
| 书桌 | 28 | Desk |
| 厨房ette | 61 | Kitchenette |

#### 4.2.4 房型类型代码 (RoomType)
| 代码 | 房型 | 厨房要求 |
|------|------|---------|
| 1 | Standard Room | - |
| 2 | Superior Room | - |
| 3 | Apartment | **必须** |
| 4 | Suite | - |
| 22 | Lodge | 推荐 |
| 35 | Villa | 推荐 |
| 5000 | Aparthotel | **必须** |
| 5006 | Holiday home | 推荐 |
| 5009 | Holiday park | 推荐 |

---

## 五、数据校验规则

> **优先级**：Booking.com 高优先级，Expedia 低优先级

### 5.1 酒店数据校验

#### 5.1.1 Booking.com 必填字段
- hotel_id（业务ID）
- name_en（英文名称，仅拉丁字符，3-255字符）
- address_en（英文地址）
- city（城市）
- country_code（国家代码）
- phone（联系电话，国际格式）
- email（邮箱）
- latitude（纬度，-90 到 90）
- longitude（经度，-180 到 180）
- check_in（入住时间）
- check_out（退房时间）
- room_count（可售房间数）
- property_type（住宿类型）

#### 5.1.2 格式校验规则
| 字段 | 校验规则 | 错误提示 |
|-----|---------|---------|
| hotel_id | 唯一性校验，不能重复 | 酒店ID已存在 |
| phone | 国际格式 (+86xxxxxxxx) | 电话格式不正确 |
| email | 标准邮箱格式 | 邮箱格式不正确 |
| latitude | 范围: -90 到 90 | 纬度超出范围 |
| longitude | 范围: -180 到 180 | 经度超出范围 |
| star_rating | 范围: 0-5 或空 | 星级必须是0-5 |
| name_en | 仅拉丁字符，无电话 | 名称包含非法字符 |

#### 5.1.3 业务逻辑校验
- 国家与经纬度一致性校验
- 邮箱域名白名单（atour.com, atahouse.com）
- 地址完整性（城市+国家+邮编匹配）

### 5.2 客房数据校验

#### 5.2.1 Booking.com 必填字段
- hotel_id（关联酒店ID）
- room_type_en（房型英文名）
- bed_type（床型代码）
- bed_count（床数量）
- max_occupancy（最大入住人数）
- max_adults（最大成人）
- max_children（最大儿童）

#### 5.2.2 关联校验
| 校验项 | 规则 | 错误提示 |
|-------|------|---------|
| hotel_id 存在性 | 必须在 hotels 表中存在 | 关联的酒店不存在 |
| hotel_id 状态 | 关联酒店状态必须为 active | 关联的酒店未激活 |
| 房型唯一性 | 同一酒店下房型名称不能重复 | 该酒店已存在相同房型 |
| 厨房要求 | Apartment 类型必须有厨房设施 | 房型缺少厨房设备 |

#### 5.2.3 数值范围校验
| 字段 | 范围 | 说明 |
|-----|------|------|
| area | 10-1000 | 面积(平方米) |
| bed_count | 1-20 | 床数量 |
| max_occupancy | 1-30 | 最大入住人数 |
| max_adults | 1-20 | 最大成人 |
| max_children | 0-15 | 最大儿童 |

### 5.3 翻译数据校验

- 译文长度不应小于原文的 30%
- 译文长度不应超过原文的 3 倍
- 英文翻译不应包含中文字符
- 酒店名称必须仅含拉丁字符

---

## 六、Booking.com API 对接详情

> **优先级**：高优先级（当前阶段实现）
> **说明**：本章详细介绍 Booking.com OTA XML API 的请求/响应格式，供开发参考。

### 6.1 Booking.com 平台概述

Booking.com 使用 XML 格式的 OTA (Open Travel Alliance) 接口进行数据交换，主要 API 包括：

| API | 用途 |
|-----|------|
| OTA_HotelDescriptiveContentNotif | 创建/更新酒店主数据 |
| OTA_HotelInvNotif | 创建/更新房型/房间数据 |
| OTA_HotelDescriptiveInfo | 获取酒店信息 |
| Rooms API | 新版模块化客房 API（推荐） |
| Facilities API | 设施服务 API |
| Contacts API | 联系人 API |

**API 基础地址**: `https://supply-xml.booking.com/hotels/ota/`

### 6.2 Booking.com 酒店主数据要求

#### 6.2.1 创建酒店最低要求

| 字段 | 说明 | 必填 |
|-----|------|------|
| LegalEntityID | 法律实体ID（管理公司/酒店集团） | 是 |
| HotelName | 酒店名称（仅拉丁字符，3-255字符） | 是 |
| Address | 地址（仅拉丁字符） | 是 |
| City | 城市名 | 是 |
| CountryCode | 国家代码（ISO 3166-1 alpha-2，如 CN） | 是 |
| PostalCode | 邮编 | 是 |
| ContactPerson | 联系人姓名（GivenName + SurName） | 是 |
| Email | 邮箱地址 | 是 |
| Phone | 电话号码（国际格式 +86xxx） | 是 |
| Latitude/Longitude | 经纬度坐标 | 是 |
| CheckInTime | 入住时间 | 是 |
| CheckOutTime | 退房时间 | 是 |
| RoomCount | 可售房间数 | 是 |
| PropertyCategory | 住宿类型代码 | 是 |
| LanguageCode | 语言代码 | 是 |

#### 6.2.2 酒店主数据结构

```xml
OTA_HotelDescriptiveContentNotifRQ
└── HotelDescriptiveContent
    ├── @HotelName          # 酒店名称
    ├── @LanguageCode       # 语言代码
    ├── @Target             # Test / Production
    ├── ContactInfos        # 联系人信息
    │   └── ContactInfo[@ContactProfileType]
    │       ├── Addresses/Address
    │       ├── Emails/Email
    │       ├── Names/Name
    │       └── Phones/Phone
    ├── HotelInfo           # 酒店信息
    │   ├── CategoryCodes/HotelCategory[@Code]
    │   ├── GuestRoomInfo[@Quantity]
    │   ├── Languages/Language[@LanguageCode]
    │   ├── Position/Latitude,Longitude
    │   └── Services/Service[@Code, @ExistsCode]
    ├── FacilityInfo        # 设施信息
    │   ├── GuestRooms/GuestRoom/Amenities/Amenity
    │   └── Restaurants/Restaurant
    ├── Policies            # 政策
    │   ├── Policy/CheckInTime, CheckOutTime
    │   └── CancelPolicy[@PolicyCode]
    └── TPA_Extensions      # 扩展信息
```

#### 6.2.3 ContactProfileType 联系人类型

| 类型 | 说明 | 必填 |
|------|------|------|
| PhysicalLocation | 物理位置地址 | 是 |
| general | 一般联系人 | 是 |
| invoices | 发票联系人 | 是 |
| contract | 合同联系人 | 否 |
| reservations | 预订联系人 | 否 |
| availability | 可用性联系人 | 否 |

#### 6.2.4 酒店命名规范

- 长度：3-255 字符
- 不含电话号码（或超过5位连续数字）
- 仅含字母（任何语言）、数字、或符号：`! # & ' " - ,`
- 不能全大写
- 某些词汇被限制使用

### 6.3 Booking.com 客房主数据要求

#### 6.3.1 房型数据结构

```xml
OTA_HotelInvNotifRQ
└── SellableProducts[@HotelCode="酒店ID"]
    └── SellableProduct[@InvNotifType, @InvCode]
        └── GuestRoom
            ├── Description/Text          # 房型名称
            ├── Occupancy                 # 入住人数
            │   ├── @MaxOccupancy
            │   ├── @MaxAdultOccupancy
            │   └── @MaxChildOccupancy
            ├── Room                      # 基本信息
            │   ├── @RoomType             # 房型代码
            │   ├── @SizeMeasurement      # 面积
            │   ├── @NonSmoking           # 禁烟 (0/1/2)
            │   └── @Quantity             # 房间数量
            ├── Quantities               # 额外床位
            │   ├── @MaxCribs             # 婴儿床
            │   └── @MaxRollaways         # 加床
            ├── Amenities                # 房间设施
            │   └── Amenity[@AmenityCode, @Value]
            └── TPA_Extensions
                └── SubRooms             # 多卧室房型
                    └── SubRoom[@RoomType, @PrivateBathroom]
                        └── Amenities    # 子房间床位
```

#### 6.3.2 必填字段

| 字段 | 说明 | 必填 |
|-----|------|------|
| HotelCode | 酒店ID | 是 |
| InvCode | Booking.com 房型ID（更新时） | 是 |
| RoomType | 房型代码（创建时） | 是 |
| RoomTypeName | 房型名称 | 是 |
| MaxOccupancy | 最大入住人数 | 是 |
| MaxAdultOccupancy | 最大成人人数 | 是 |

#### 6.3.3 房型类型代码 (RoomType)

| 代码 | 房型 | 厨房要求 |
|------|------|---------|
| 1 | Standard Room | - |
| 2 | Superior Room | - |
| 3 | Apartment | **必须** |
| 4 | Suite | - |
| 22 | Lodge | 推荐 |
| 35 | Villa | 推荐 |
| 5000 | Aparthotel | **必须** |
| 5006 | Holiday home | 推荐 |
| 5009 | Holiday park | 推荐 |

**注意**：Apartment (3)、Aparthotel (5000)、Condominium (8) 必须配备厨房或厨房ette 才能开放预订。

#### 6.3.4 床型代码 (AmenityCode for Beds)

| 代码 | 床型 | 说明 |
|------|------|------|
| 203 | Twin | 双床（两张单人床） |
| 249 | Double | 双人床 |
| 204 | Single | 单人床 |
| 200 | King | 大床 |
| 102 | Sofa bed | 沙发床 |
| 211 | Bunk bed | 双层床 |

**Configuration 属性**：1 = 标准布局, 2 = 备用布局

#### 6.3.5 房间设施代码 (AmenityCode)

| 代码 | 设施 | 说明 |
|------|------|------|
| 61 | Kitchenette | 厨房小吧台 |
| 28 | Desk | 书桌 |
| 69 | Minibar | 迷你吧 |
| 11 | Free toiletries | 免费洗漱用品 |
| 88 | Refrigerator | 冰箱 |
| 50 | Air conditioning | 空调 |
| 72 | TV | 电视 |
| 26 | Safe | 保险箱 |
| 5 | Hairdryer | 吹风机 |
| 100 | Slippers | 拖鞋 |
| 71 | Bathrobe | 浴袍 |

#### 6.3.6 多卧室房型 (SubRooms)

适用于： Apartment、Suite、Chalet、Bungalow、Holiday home、Villa、Mobile home

| SubRoom RoomType | 说明 |
|------------------|------|
| Bedroom | 卧室 |
| Living room | 客厅 |
| Bathroom | 浴室 |

### 6.4 取消政策

- 每个酒店**必须**至少有一个取消政策
- 如不指定，默认使用全退政策 (PolicyCode=152)
- PolicyCode=1 为"不可取消"政策

### 6.5 Expedia vs Booking.com 对比

| 项目 | Expedia | Booking.com |
|------|---------|-------------|
| API 格式 | Excel/CSV 模板 | XML (OTA 接口) |
| 酒店名称 | 中英文 | 仅英文 |
| 联系方式 | 邮箱+电话 | 分类型（General/Invoice/Physical等） |
| 设施服务 | Amenity Code 映射 | Amenity Code |
| 取消政策 | 默认规则 | 必填，默认全退 |
| 房型数据 | Rooms Sheet | OTA_HotelInvNotif / Rooms API |
| 床型配置 | bed_type 字段 | AmenityCode (床型) + Configuration |
| 厨房要求 | 无 | Apartment 等必须厨房 |
| 多卧室 | 不支持 | SubRooms 支持 |
| 禁烟设置 | smoke_free 布尔值 | NonSmoking (0/1/2) |
| 额外床位 | extra_bed 配置 | MaxCribs/MaxRollaways |

---

## 七、非功能性需求

### 7.1 性能要求
| 指标 | 要求 |
|-----|------|
| 页面加载时间 | < 3 秒 |
| 数据导入速度 | > 1000 条/分钟 |
| 翻译处理速度 | > 100 条/分钟 |
| 并发用户数 | 支持 50 人同时在线 |

### 7.2 可用性要求
- 系统可用性: 99.5%
- 数据备份: 每日备份
- 故障恢复时间: < 1 小时

### 7.3 兼容性要求
- 浏览器: Chrome 90+、Edge 90+、Safari 14+
- 分辨率: 最小支持 1280x720

---

## 八、附录

### 8.1 术语表

| 术语 | 说明 |
|-----|------|
| 酒店主数据 | 酒店基本信息、设施、服务等 |
| 客房主数据 | 房型、面积、床型、设施等 |
| 翻译规则 | 集团/行业/行政区域的翻译规范 |
| 翻译参考库 | 携程/Booking等平台的翻译数据 |
| 术语库 | 专业词汇的标准翻译对照 |

### 8.2 参考文档

- [Expedia 合作伙伴帮助中心](https://connect.expedia.com/help)
- [Booking.com Connectivity API 文档](https://developers.booking.com/connectivity/docs/content)
- 亚朵酒店房型翻译规则 v1.0
- 携程/Booking 酒店数据模板

### 8.3 Expedia 字段映射（低优先级，后续支持）

#### A.1 酒店字段映射

| 内部字段 | Expedia 字段 | 必填 | 说明 |
|---------|-------------|------|------|
| hotel_id | Property ID | 是 | 唯一标识 |
| name_zh | Property Name (CN) | 是 | 中文名称 |
| name_en | Property Name (EN) | 是 | 英文名称 |
| address_zh | Address Line 1 (CN) | 是 | 中文地址 |
| address_en | Address Line 1 (EN) | 是 | 英文地址 |
| city | City | 是 | 城市 |
| province | State/Province | 是 | 省份 |
| country | Country | 是 | 默认 "China" |
| phone | Phone | 是 | 联系电话 |
| email | Email | 是 | 酒店邮箱 |
| star_rating | Star Rating | 否 | 星级(1-5) |
| latitude | Latitude | 是 | 纬度 |
| longitude | Longitude | 是 | 经度 |
| description_zh | Property Description (CN) | 是 | 中文描述 |
| description_en | Property Description (EN) | 是 | 英文描述 |

#### A.2 客房字段映射

| 内部字段 | Expedia 字段 | 必填 | 说明 |
|---------|-------------|------|------|
| room_type_zh | Room Type Name (CN) | 是 | 房型中文名 |
| room_type_en | Room Type Name (EN) | 是 | 房型英文名 |
| area | Room Size | 否 | 面积(平方米) |
| bed_type | Bed Type | 是 | 床型 |
| bed_count | Number of Beds | 是 | 床数量 |
| max_occupancy | Max Occupancy | 是 | 最大入住人数 |

#### A.3 床型映射

| 中文床型 | Expedia 代码 | 说明 |
|---------|-------------|------|
| 大床 | KING | 大床(1.8m+) |
| 双床 | TWIN | 双床 |
| 单人床 | SINGLE | 单人床 |
| 特大床 | SUPER_KING | 特大床(2m+) |

#### A.4 房间设施映射

| 设施 | Expedia 代码 | 说明 |
|-----|-------------|------|
| 空调 | 2001 | 空调系统 |
| 电视 | 2002 | 电视机 |
| 迷你吧 | 2003 | 小型冰箱 |
| 保险箱 | 2004 | 客房保险箱 |
| 吹风机 | 2005 | 电吹风 |

### 8.4 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| v1.3 | 2026-05-26 | 新增 Expedia 主数据导入模块设计（第二章），基于模板 sheet "亚朵房型信息"+"门店基础信息" | Claude |
| v1.2 | 2026-05-25 | 调整优先级：Booking.com 高优先级（主数据维护+翻译），Expedia 降为低优先级 | Claude |
| v1.1 | 2026-05-25 | 新增 Booking.com 数据对接章节，对比 Expedia 与 Booking.com 主数据要求 | Claude |

---

## 九、Expedia 主数据导入模块

> **优先级**：低优先级（当前阶段支持数据生成，Expedia 平台对接后续支持）

### 9.1 数据源

**输入文件**: `reference/Expedia 亚朵集团酒店上线表格 - APM Onboarding Sheet example.xlsx`

| Sheet 名 | 内容 | 行数 | 关联键 |
|---------|------|------|--------|
| `门店基础信息` | 酒店基础信息（门店ID、名称、地址、电话、品牌等） | 2067 家 | 门店ID |
| `亚朵房型信息` | 房型主数据（集团房型ID、房型代码、英文名、床型、面积等） | 17025 条 | 集团酒店编号 = 门店ID |

> 注：`门店基础信息.门店ID` = `亚朵房型信息.集团酒店编号`，两表可直接关联。

### 9.2 输出格式

生成文件: `output/酒店主数据导入_YYYY-MM-DD.xlsx`

包含 2 个 Sheet：

#### Sheet1: 酒店主数据

| 输出字段 | 来源 | 说明 |
|---------|------|------|
| Hotel Code | 门店ID | 如 3100054 |
| Hotel Name | 门店名称 | 中文名称 |
| Brand | 品牌 | 如"亚朵S" |
| City | 所属城市 | |
| Country | 固定 "China" | |
| Address | 门店地址 | 中文地址 |
| Phone (Country/Area/Number) | 电话字段拆分 | 86 / 021 / 62211599 |
| Postal Code | 邮编 | |
| Time Zone | 固定 "China Standard Time" | |
| Check-in Time | 固定 "14:00:00" | |
| Check-out Time | 固定 "12:00:00" | |
| Currency | 固定 "CNY" | |
| Business Model | 固定 "Dual" | |
| Rate Acquisition Type | 固定 "SellLAR" | |
| Min Adult Age | 固定 "18" | |
| Rates Inclusive of Taxes | 固定 "Yes" | |
| Cancellation Time | 固定 "12:00:00" | |
| Photos | 固定 "Excel sheet (with media links)" | |

#### Sheet2: 房间主数据

| 输出字段 | 来源 | 说明 |
|---------|------|------|
| Hotel Code | 集团酒店编号（门店ID） | |
| Room Type Code | 集团房型代码 | 如 SK、ET |
| Room Type Name | 房型英文名字 | 如 Superior Queen Room |
| Max Occupancy | 可容纳人数 | |
| Max Adults | 成人人数 | 同可容纳人数 |
| Max Children | 儿童人数 | 默认 0 |
| BeddingOption1 | 床型 → Expedia BedType | 见床型映射规则 |
| Smoking | 固定 "NonSmoking" | |
| RNS Flag | 固定 "Yes" | |
| Rate Plan Code | `{集团房型代码}-HC-A` (Agency) / `{集团房型代码}-EC-A` (Merchant) | |
| Rate Plan Name | `Room Only HC A` (Agency) / `Room Only EC A` (Merchant) | |
| Rate Plan Type | 固定 "Standalone" | |
| Rate Plan Business Model | Agency / Merchant | |
| Value Add 1 | 固定 "Free Wireless Internet" | |
| Cancellation Window Hours | 固定 "18" | |
| Outside/Inside Window Penalty | 固定 "Full Cost of Stay" | |
| Min Advance Booking Days | 0 | |
| Max Advance Booking Days | 180 | |
| Min Length of Stay | 1 | |
| Max Length of Stay | 28 | |
| Waive Taxes Enabled | 固定 "Yes" | |

> **每条房型生成 2 行**：Agency Rate Plan + Merchant Rate Plan

### 9.3 床型映射规则

| 中文床型字符串 | Expedia BeddingOption1 | 示例 |
|--------------|----------------------|------|
| `1.8` / `2` / `2.0` | `1 KingBed` | 大床 |
| `1.5` / `1.5,1.5` | `1 QueenBed` | 中床 |
| `1.2,1.2` | `2 TwinBed` | 双床 |
| `1.2,1.5` / `1.5,1.2` | `1 QueenBed&1 TwinBed` | 混合床 |
| `1.8,1.2` / `2,1.2` | `1 KingBed&1 TwinBed` | 大床+单人床 |
| `1.8,1.0` | `1 KingBed` | 大床（床位数1.0） |
| `1.5(沙发床),1.8` 等含沙发床 | 需特殊处理 | 亲子/套房 |

### 9.4 处理流程

```
1. 读取 亚朵房型信息 + 门店基础信息
2. 通过 集团酒店编号 = 门店ID 合并 hotel-level 信息
3. 床型字符串 → Expedia BedType 转换
4. 生成 Sheet1（酒店主数据，1行/酒店）
5. 生成 Sheet2（房间主数据，每房型2行 = Agency + Merchant）
6. 输出 Excel 到 output/ 目录
```

---

**文档版本**: v1.3
**最后更新**: 2026-05-26
**维护人员**: 产品团队

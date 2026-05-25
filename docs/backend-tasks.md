# 后端开发任务分工

> **优先级说明**：Booking.com 平台对接为**高优先级**，Expedia 平台为**低优先级（后续支持）**

## 任务总览

| Phase | 阶段 | 优先级 | 任务数 | 预计工期 | Agent数量 |
|-------|------|--------|--------|----------|-----------|
| 0 | 项目基础设施 | 高 | 8 | 2天 | 1-2 |
| 1 | 认证与用户管理 | 高 | 9 | 3天 | 1-2 |
| 2 | **翻译核心模块** | ⭐**高优先级** | 18 | 6天 | 2-3 |
| 3 | **数据模型 (Booking)** | ⭐**高优先级** | 12 | 4天 | 2-3 |
| 4 | **酒店与客房管理** | ⭐**高优先级** | 10 | 4天 | 2 |
| 5 | **数据导入模块 (Booking)** | ⭐**高优先级** | 10 | 4天 | 2 |
| 6 | 数据导出模块 (Booking XML) | 中 | 12 | 4天 | 2 |
| 7 | 测试与部署 | 中 | 8 | 3天 | 2-3 |
| **总计** | | | **87** | **约26天** | |

**Phase 2-5 为高优先级（Booking.com 平台），Phase 6-7 为中优先级（后续 Expedia 支持）**

---

## Agent命名体系 🦸

| 代号 | 英雄名 | 专长领域 | 负责模块 |
|------|--------|----------|----------|
| **STARK** | Iron Man (钢铁侠) | 技术架构、核心基础设施 | Phase 0 |
| **ROGERS** | Captain America (美国队长) | 认证授权、安全 | Phase 1 |
| **WANDA** | Scarlet Witch (绯红女巫) | 数据模型、规则引擎 | Phase 3 (Booking数据模型) |
| **STRANGE** | Doctor Strange (奇异博士) | AI翻译、外部服务集成 | Phase 2 (翻译+参考库) |
| **PARKER** | Spider-Man (蜘蛛侠) | 业务CRUD、快速迭代 | Phase 4, Phase 5 |
| **BANNER** | Hulk (绿巨人) | 数据处理、格式转换 | Phase 6 (Booking XML导出) |
| **BUCKY** | Winter Soldier (冬日战士) | 测试、部署、自动化 | Phase 7 |

---

## Phase 0: 项目基础设施 (STARK负责) ⭐高优先级

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T001 | FastAPI项目骨架搭建 | - | 2h | pending |
| T002 | 数据库连接池配置 | T001 | 2h | pending |
| T003 | Redis连接配置 | T001 | 1h | pending |
| T004 | 日志系统配置 | T001 | 1.5h | pending |
| T005 | 全局异常处理中间件 | T001 | 2h | pending |
| T006 | 统一响应格式封装 | T001 | 1.5h | pending |
| T007 | 配置管理(pydantic-settings) | T001 | 1.5h | pending |
| T008 | CORS与安全中间件 | T001 | 1h | pending |

## Phase 1: 认证与用户管理 (ROGERS负责) ⭐高优先级

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T009 | 用户数据模型(User, Role) | T002 | 2h | pending |
| T010 | JWT工具类生成 | T009 | 2h | pending |
| T011 | 密码加密工具 | T009 | 1h | pending |
| T012 | 认证中间件 | T010 | 2h | pending |
| T013 | 用户注册服务 | T009, T011 | 2h | pending |
| T014 | 用户登录服务 | T009, T010 | 2h | pending |
| T015 | 用户权限装饰器 | T012 | 1.5h | pending |
| T016 | 用户API端点 | T013, T014 | 2h | pending |
| T017 | 认证模块单元测试 | T016 | 3h | pending |

## Phase 2: 翻译核心模块 (STRANGE + WANDA协作) ⭐⭐最高优先级

| ID | 任务名称 | 依赖 | 预计工时 | Agent | 状态 |
|----|----------|------|----------|-------|------|
| T018 | 翻译规则数据模型 | T002 | 1.5h | WANDA | pending |
| T019 | **Booking参考库数据模型** | T002 | 1.5h | WANDA | pending |
| T020 | 术语库数据模型 | T002 | 1.5h | WANDA | pending |
| T021 | 翻译历史数据模型 | T002 | 1.5h | WANDA | pending |
| T022 | 翻译规则CRUD服务 | T018 | 2h | WANDA | pending |
| T023 | 翻译规则API端点 | T022 | 2h | WANDA | pending |
| T024 | **Booking参考库CRUD服务** | T019 | 2h | WANDA | pending |
| T025 | **Booking参考库API端点** | T024 | 2h | WANDA | pending |
| T026 | 术语库CRUD服务 | T020 | 2h | WANDA | pending |
| T027 | 术语库API端点 | T026 | 2h | WANDA | pending |
| T028 | 腾讯云翻译API客户端 | T007 | 3h | STRANGE | pending |
| T029 | 腾讯云翻译响应解析 | T028 | 1.5h | STRANGE | pending |
| T030 | AI大模型客户端(DeepSeek) | T007 | 3h | STRANGE | pending |
| T031 | AI翻译润色Prompt模板 | T030 | 2h | STRANGE | pending |
| T032 | **翻译工作流编排器(Booking优先)** | T022, T024, T026, T028, T030 | 4h | STRANGE | pending |
| T033 | 翻译结果缓存服务 | T003, T032 | 2h | STRANGE | pending |
| T034 | 翻译API端点 | T032, T033 | 2h | STRANGE | pending |
| T035 | 翻译模块单元测试 | T034 | 3h | STRANGE | pending |

## Phase 3: 核心数据模型 (WANDA负责) ⭐高优先级

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T036 | **Booking酒店数据模型** | T002 | 2h | pending |
| T037 | **Booking酒店扩展字段** | T036 | 1.5h | pending |
| T038 | **Booking客房数据模型** | T036 | 2h | pending |
| T039 | **Booking客房扩展字段** | T038 | 1.5h | pending |
| T040 | 酒店与客房关联关系 | T037, T039 | 1h | pending |
| T041 | 导入历史数据模型 | T036 | 1.5h | pending |
| T042 | 导出历史数据模型 | T036 | 1.5h | pending |
| T043 | ~~Expedia模板配置模型~~ | T002 | 2h | **低优先级-后续** |
| T044 | ~~字段映射配置模型~~ | T043 | 1.5h | **低优先级-后续** |
| T045 | Alembic迁移脚本生成 | T036-T042 | 2h | pending |
| T046 | 数据库种子数据(Booking) | T045 | 2h | pending |
| T047 | 数据模型单元测试 | T045 | 3h | pending |

> **注意**：T043、T044 为 Expedia 预留，暂不实现

## Phase 4: 酒店与客房管理 (PARKER负责) ⭐高优先级

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T048 | **Booking酒店CRUD服务** | T036 | 2.5h | pending |
| T049 | 酒店批量操作服务 | T048 | 2h | pending |
| T050 | 酒店搜索与筛选服务 | T048 | 2h | pending |
| T051 | **Booking酒店API端点** | T048, T049, T050 | 2h | pending |
| T052 | **Booking客房CRUD服务** | T038 | 2.5h | pending |
| T053 | 客房批量操作服务 | T052 | 2h | pending |
| T054 | **Booking客房API端点** | T052, T053 | 2h | pending |
| T055 | 酒店-客房联动服务 | T048, T052 | 2h | pending |
| T056 | **Booking数据校验器** | T048, T052 | 2h | pending |
| T057 | 酒店/客房模块测试 | T051, T054 | 3h | pending |

## Phase 5: 数据导入模块 (PARKER + BANNER负责) ⭐高优先级

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T058 | Excel文件解析器 | T007 | 3h | pending |
| T059 | CSV文件解析器 | T007 | 2h | pending |
| T060 | **Booking数据校验规则引擎** | T048, T052 | 3h | pending |
| T061 | **Booking酒店数据校验器** | T060 | 2h | pending |
| T062 | **Booking客房数据校验器** | T060 | 2h | pending |
| T063 | **酒店导入服务** | T048, T058, T061 | 3h | pending |
| T064 | **客房导入服务** | T052, T058, T062 | 3h | pending |
| T065 | 导入进度跟踪服务 | T041, T003 | 2h | pending |
| T066 | **导入API端点** | T063, T064, T065 | 2h | pending |
| T067 | 导入模块测试 | T066 | 3h | pending |

## Phase 6: 数据导出模块 (NATASHA负责) ⚠️中优先级

> Booking.com XML 导出为中优先级，Expedia 导出后续支持

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T068 | **Booking字段映射配置** | T036, T037 | 2.5h | pending |
| T069 | ~~Expedia模板配置服务~~ | T043 | 2h | **低优先级-后续** |
| T070 | **Booking XML模板生成器** | T068 | 3h | pending |
| T071 | XML样式配置 | T070 | 2h | pending |
| T072 | **酒店数据XML导出服务** | T048, T068 | 2.5h | pending |
| T073 | **客房数据XML导出服务** | T052, T068 | 2.5h | pending |
| T074 | ~~CSV导出服务~~ | T068 | 2h | **低优先级-后续** |
| T075 | ~~JSON导出服务~~ | T068 | 1.5h | **低优先级-后续** |
| T076 | 导出历史记录服务 | T042 | 2h | pending |
| T077 | 导出任务队列(ARQ) | T003 | 3h | pending |
| T078 | **导出API端点(Booking XML)** | T072-T077 | 2h | pending |
| T079 | 导出模块测试 | T078 | 3h | pending |

> **注意**：T069、T074、T075 为 Expedia 预留，暂不实现

## Phase 7: 测试与部署 (BUCKY负责) ⚠️中优先级

| ID | 任务名称 | 依赖 | 预计工时 | 状态 |
|----|----------|------|----------|------|
| T080 | 集成测试环境配置 | T017, T035, T047, T057, T067, T079 | 2h | pending |
| T081 | API集成测试套件 | T080 | 4h | pending |
| T082 | 端到端测试场景 | T081 | 3h | pending |
| T083 | ~~OpenAPI文档生成~~ | 所有API | 2h | **低优先级-后续** |
| T084 | Docker容器化 | T081 | 3h | pending |
| T085 | podman-compose编排 | T084 | 2h | pending |
| T086 | 部署脚本与CI配置 | T085 | 2h | pending |
| T087 | 性能测试与优化 | T082 | 4h | pending |

---

## Taskwarrior 任务查阅命令

### 基本命令

```bash
# 查看所有后端任务
task list project:backend

# 查看特定Phase的任务
task list project:backend phase:2

# 查看高优先级任务
task list project:backend priority:H

# 查看 Booking 相关任务
task list +booking

# 查看翻译相关任务
task list +translation

# 查看 Expedia 备用任务
task list +expedia
```

### 按优先级查看

```bash
# 高优先级任务 (Booking)
task list project:backend priority:H

# 中优先级任务
task list project:backend priority:M

# 低优先级任务 (Expedia 后续)
task list project:backend priority:L
```

### 任务状态更新

```bash
# 开始任务
task <id> start

# 完成任务
task <id> done

# 标记任务阻塞
task <id> modify status:waiting
```

---

## 开发流程

1. **领取任务**: 从高优先级开始领取 pending 状态的任务
2. **标记开始**: `task <id> start` 将状态改为 in_progress
3. **开发实现**: 按照任务要求完成开发
4. **测试验证**: 编写并运行单元测试
5. **标记完成**: `task <id> done` 完成任务
6. **代码提交**: 提交代码到 git 仓库

---

## Avenger 工作协议

- **每日站会**: 每日同步各 Agent 进度
- **代码审查**: 完成的任务需要其他 Agent 审查
- **依赖协调**: 阻塞任务及时上报，协调资源解决
- **文档更新**: 完成任务后更新相关文档

---

## 更新日志

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.1 | 2026-05-25 | 调整优先级：Phase 2-5 Booking 高优先级，Phase 6-7 中优先级，Expedia 任务标记为后续支持 |
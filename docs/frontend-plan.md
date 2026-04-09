# Ex-pertie 前端开发与测试计划

## Context

后端API开发已完成（55个端点），需要前端工程师基于Figma原型和API文档完成前端开发，同时测试工程师需要编写E2E测试用例。

**Figma原型**: https://www.figma.com/design/1mGr7uxovueykuLHZk8p5M/Ex-pertie-%E2%80%94-Expedia-%E6%B8%A0%E9%81%93%E6%95%B0%E6%8D%AE%E7%AE%A1%E7%90%86%E5%B9%B3%E5%8F%B0-%E5%8E%9F%E5%9E%8B?node-id=0-1&t=qbsn9wstqJyO6MlT-1

**技术栈**: Next.js 14.x + React 18.x + TypeScript + Ant Design 5.x + Zustand + TanStack Query

---

## 前端工程师任务 (FE-1: 前端设计文档与工作拆分)

### 工作内容

1. **对照Figma原型输出前端设计文档**
   - 分析Figma中的每个页面和组件
   - 输出详细的组件映射表（组件 → API调用）
   - 确认API与UI的对应关系
   - 识别复用组件和业务组件

2. **拆分工作项到taskwarrior**

### 前端页面划分

| 页面 | 路由 | API依赖 | 工作项 |
|-----|------|---------|-------|
| 登录/注册 | `/login`, `/register` | auth/* | fe-1.1 |
| 首页仪表盘 | `/` | 无需API (静态) | fe-1.2 |
| 数据导入 | `/import` | imports/* | fe-1.3 |
| 酒店管理 | `/hotels` | hotels/* | fe-1.4 |
| 翻译工作台 | `/translate` | translation/* | fe-1.5 |
| 术语库管理 | `/terminology` | translation/glossary/* | fe-1.6 |
| 翻译规则 | `/rules` | translation/rules/* | fe-1.7 |
| 导出中心 | `/export` | exports/* | fe-1.8 |

### 具体工作项 (taskwarrior) - 使用 fe- 前缀

**前端任务格式**: `fe-1.x 描述` (如: fe-1.1 登录注册页)

```
fe-1.1 登录注册页
  + 创建登录页面组件 LoginPage.tsx
  + 创建注册页面组件 RegisterPage.tsx
  + 实现 auth API hooks (useLogin, useRegister, useMe)
  + 创建路由配置

fe-1.2 首页仪表盘
  + 创建首页布局 PageLayout.tsx
  + 创建侧边栏组件 Sidebar.tsx
  + 创建顶部导航 Header.tsx
  + 创建首页仪表盘组件 Dashboard.tsx

fe-1.3 数据导入页
  + 创建文件上传组件 FileUploader.tsx
  + 创建导入进度组件 ImportProgress.tsx
  + 创建导入错误列表 ImportErrorList.tsx
  + 实现 imports API hooks
  + 创建导入历史列表组件

fe-1.4 酒店管理页
  + 创建酒店列表组件 HotelList.tsx
  + 创建酒店卡片 HotelCard.tsx
  + 创建酒店表单 HotelForm.tsx
  + 创建酒店详情组件 HotelDetail.tsx
  + 实现 hotels API hooks (CRUD + search)

fe-1.5 翻译工作台
  + 创建翻译编辑器 TranslationEditor.tsx
  + 创建翻译预览 TranslationPreview.tsx
  + 创建翻译历史 TranslationHistory.tsx
  + 实现 translation/translate, batch API hooks

fe-1.6 术语库管理
  + 创建术语列表 GlossaryList.tsx
  + 创建术语表单 GlossaryForm.tsx
  + 创建术语分类 GlossaryCategories.tsx
  + 实现 translation/glossary/* API hooks

fe-1.7 翻译规则
  + 创建规则列表 RulesList.tsx
  + 创建规则表单 RuleForm.tsx
  + 实现 translation/rules/* API hooks

fe-1.8 导出中心
  + 创建导出表单 ExportForm.tsx
  + 创建导出进度 ExportProgress.tsx
  + 创建导出历史列表
  + 实现 exports/* API hooks
```

### 交付物

1. **前端设计文档** (`docs/frontend-design.md`)
   - Figma组件与API映射表
   - 组件目录结构
   - 状态管理方案
   - 路由配置

2. **taskwarrior任务列表**

---

## 测试工程师任务 (TE-1: E2E测试用例编写)

### 测试范围

基于API端点编写Playwright E2E测试用例。

### 测试用例拆分 - 使用 te- 前缀

**测试任务格式**: `te-1.x 描述` (如: te-1.1 认证模块测试)

```
te-1.1 认证模块测试
  + 登录成功/失败
  + 注册成功/失败（密码验证）
  + Token刷新
  + 登出

te-1.2 酒店管理测试
  + 酒店列表查询（分页、筛选）
  + 酒店搜索
  + 创建酒店（必填字段验证）
  + 更新酒店
  + 删除酒店

te-1.3 数据导入测试
  + 酒店数据导入（Excel/CSV）
  + 客房数据导入
  + 导入进度查询
  + 导入错误查看
  + 导入历史列表

te-1.4 翻译功能测试
  + 单条翻译
  + 批量翻译
  + 术语库 CRUD
  + 术语库批量导入
  + 翻译规则 CRUD
  + 翻译参考库 CRUD

te-1.5 导出功能测试
  + 酒店数据导出
  + 客房数据导出
  + 导出进度查询
  + 导出文件下载

te-1.6 用户管理测试
  + 用户列表查询
  + 用户激活/停用
  + 角色分配
```

### 技术选型

- **Playwright** - E2E测试框架
- **测试报告** - Allure 或 Playwright HTML Reporter

### 交付物

1. **E2E测试用例文档** (`docs/e2e-test-cases.md`)
   - 测试用例清单
   - 测试数据准备
   - 预期结果

2. **Playwright测试代码** (`e2e/`)
   - page objects
   - test cases
   - fixtures

3. **taskwarrior任务列表**

---

## 验证方式

### 前端验证
1. 启动后端服务 `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
2. 启动前端开发服务器 `npm run dev`
3. 对照Figma原型验证每个页面
4. 验证API调用正确性

### 测试验证
1. 运行Playwright测试 `npx playwright test`
2. 生成测试报告 `npx playwright show-report`

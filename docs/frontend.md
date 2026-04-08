# 前端设计文档

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│              全栈应用 (Next.js)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  前端层: 数据导入 | 翻译工作台 | 数据管理 | 导出中心    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 技术选型

| 技术 | 版本 | 用途 |
|-----|------|------|
| Next.js | 14.x | 全栈框架 (App Router) |
| React | 18.x | UI库 |
| TypeScript | 5.x | 类型安全 |
| Ant Design | 5.x | UI 组件库 |
| Zustand | 4.x | 状态管理 |
| TanStack Query | 5.x | 数据请求 |

---

## 页面结构

### 主要页面

| 路由 | 页面 | 说明 |
|-----|------|------|
| `/` | 首页 | 仪表盘，展示统计数据 |
| `/import` | 数据导入 | 酒店/客房数据导入 |
| `/hotels` | 酒店管理 | 酒店列表与编辑 |
| `/translate` | 翻译工作台 | 翻译任务处理 |
| `/terminology` | 术语库管理 | 术语增删改查 |
| `/rules` | 翻译规则 | 规则配置管理 |
| `/export` | 导出中心 | 数据导出任务 |

---

## 组件设计

### 通用组件

```
src/components/
├── Layout/
│   ├── Header.tsx          # 顶部导航
│   ├── Sidebar.tsx         # 侧边栏菜单
│   └── PageLayout.tsx      # 页面布局容器
├── Table/
│   ├── DataTable.tsx       # 通用数据表格
│   └── TableActions.tsx    # 表格操作按钮
├── Form/
│   ├── SearchForm.tsx      # 搜索表单
│   └── FilterBar.tsx       # 筛选栏
└── Modal/
    ├── ConfirmModal.tsx    # 确认弹窗
    └── FormModal.tsx       # 表单弹窗
```

### 业务组件

```
src/components/business/
├── Import/
│   ├── FileUploader.tsx    # 文件上传组件
│   ├── ImportProgress.tsx  # 导入进度
│   └── ImportErrorList.tsx # 错误列表
├── Hotel/
│   ├── HotelCard.tsx       # 酒店卡片
│   ├── HotelForm.tsx       # 酒店表单
│   └── HotelList.tsx       # 酒店列表
├── Translate/
│   ├── TranslationEditor.tsx    # 翻译编辑器
│   ├── TranslationPreview.tsx   # 翻译预览
│   └── TranslationHistory.tsx   # 翻译历史
└── Export/
    ├── ExportForm.tsx      # 导出表单
    └── ExportProgress.tsx  # 导出进度
```

---

## 状态管理

### Zustand Store 结构

```typescript
// stores/hotelStore.ts
interface HotelState {
  hotels: Hotel[]
  selectedHotel: Hotel | null
  filters: HotelFilters
  pagination: Pagination

  // Actions
  setHotels: (hotels: Hotel[]) => void
  selectHotel: (hotel: Hotel | null) => void
  setFilters: (filters: Partial<HotelFilters>) => void
  fetchHotels: (params: QueryParams) => Promise<void>
}

export const useHotelStore = create<HotelState>((set, get) => ({
  hotels: [],
  selectedHotel: null,
  filters: {},
  pagination: { page: 1, pageSize: 20, total: 0 },

  setHotels: (hotels) => set({ hotels }),
  selectHotel: (hotel) => set({ selectedHotel: hotel }),
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),
  fetchHotels: async (params) => {
    const data = await hotelApi.getList(params)
    set({
      hotels: data.list,
      pagination: data.pagination
    })
  }
}))
```

---

## 数据请求

### TanStack Query 配置

```typescript
// lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5分钟内数据视为新鲜
      gcTime: 30 * 60 * 1000,        // 30分钟后清除缓存
      refetchOnWindowFocus: false,
      retry: 2
    }
  }
})
```

### API Hooks 示例

```typescript
// hooks/useHotels.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { hotelApi } from '@/api/hotel'

export function useHotels(params: HotelQueryParams) {
  return useQuery({
    queryKey: ['hotels', params],
    queryFn: () => hotelApi.getList(params),
  })
}

export function useUpdateHotel() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: hotelApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] })
    }
  })
}
```

---

## 性能优化

### 数据加载优化

#### 虚拟滚动 - 大数据列表
```typescript
import { useVirtualizer } from '@tanstack/react-virtual'

function HotelList({ hotels }: { hotels: Hotel[] }) {
  const virtualizer = useVirtualizer({
    count: hotels.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 10
  })
  // ...
}
```

### 懒加载组件

```typescript
// 使用 dynamic import 懒加载大型组件
import dynamic from 'next/dynamic'

const TranslationEditor = dynamic(
  () => import('@/components/business/Translate/TranslationEditor'),
  { loading: () => <Spin />, ssr: false }
)
```

---

## UI 设计规范

### 主题配置

```typescript
// theme.ts
import type { ThemeConfig } from 'antd'

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 4,
  },
  components: {
    Table: {
      headerBg: '#fafafa',
    },
  },
}
```

### 响应式断点

```typescript
const breakpoints = {
  xs: '480px',
  sm: '576px',
  md: '768px',
  lg: '992px',
  xl: '1200px',
  xxl: '1600px',
}
```

---

**文档版本**: v1.0
**最后更新**: 2026-04-08

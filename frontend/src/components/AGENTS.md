# COMPONENTS LIBRARY KNOWLEDGE BASE

## OVERVIEW
Shared reusable React UI component library used throughout the frontend application. Provides consistent UI elements across all pages and reduces code duplication.

## STRUCTURE
```
src/components/
└── Layout/ # Shared page layout components
    ├── Header.tsx # Page header component
    ├── Sidebar.tsx # Navigation sidebar component
    └── MainLayout.tsx # Main page layout wrapper component
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| UI component development | components/ | All shared reusable UI components |
| Page layout components | components/Layout/ | Shared layout elements used across all pages |
| New shared components | Create new directory/file under components/ | Reusable components used by multiple pages belong here |

## CONVENTIONS
- Components are designed to be reusable across multiple pages and contexts
- Built on top of shadcn/ui component library
- Fully styled with Tailwind CSS for consistency
- All components are strictly typed with TypeScript
- Complex components are self-contained in their own directories with related files
- Components follow accessibility best practices

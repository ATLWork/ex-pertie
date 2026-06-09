# FRONTEND KNOWLEDGE BASE

## OVERVIEW
Next.js 13+ frontend UI built with App Router, TypeScript, React, shadcn/ui components, Tailwind CSS, and Zustand state management. Provides user interface for hotel data import, AI-powered translation, rule configuration, and custom Expedia template export.

## STRUCTURE
```
frontend/
├── src/
│   ├── api/ # Type-safe API client functions
│   ├── app/ # Next.js App Router page structure
│   │   ├── export/ # Expedia template export page
│   │   ├── hotels/ # Hotel data management page
│   │   ├── import/ # Data import page (Excel/CSV)
│   │   ├── login/ # User authentication page
│   │   ├── rules/ # Translation rule configuration page
│   │   ├── terminology/ # Translation terminology management page
│   │   └── translate/ # AI translation interface page
│   ├── components/ # Shared reusable React UI components
│   │   └── Layout/ # Page layout components (header, sidebar, etc.)
│   ├── hooks/ # Custom React hooks
│   ├── lib/ # Shared utility functions and global configurations
│   └── stores/ # Zustand global state management stores
└── public/ # Static assets (images, icons, etc.)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Page development | src/app/ | Next.js App Router pages, each directory represents a route |
| UI component development | src/components/ | Shared reusable React components |
| API integration | src/api/ | Type-safe API client functions with error handling |
| Global state management | src/stores/ | Zustand store definitions |
| Custom React hooks | src/hooks/ | Reusable hooks for common functionality |
| Utility functions | src/lib/ | Shared helper functions and configurations |

## CONVENTIONS
- Uses Next.js 13+ App Router with React Server Components (RSC) pattern
- Strict TypeScript typing required for all components and functions
- shadcn/ui component library with Tailwind CSS for styling
- Zustand for lightweight global state management
- React Query for server state management, data fetching, and caching
- Follows responsive design principles for all page layouts

## ANTI-PATTERNS
- No explicit anti-patterns identified yet

# APP ROUTER KNOWLEDGE BASE

## OVERVIEW
Next.js App Router page structure. Contains all application pages, with each directory representing a separate route in the application. Follows Next.js 13+ App Router conventions.

## STRUCTURE
```
src/app/
├── export/ # Expedia template export page route
├── hotels/ # Hotel data management page route
├── import/ # Data import (Excel/CSV) page route
├── login/ # User authentication page route
├── rules/ # Translation rule configuration page route
├── terminology/ # Translation terminology management page route
└── translate/ # AI translation interface page route
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Page development | app/[route-name]/page.tsx | Each route directory contains a page.tsx as the entry point |
| Export page | app/export/ | Expedia template export functionality |
| Hotels management | app/hotels/ | Hotel data listing and management |
| Data import | app/import/ | Excel/CSV file import and validation |
| Authentication | app/login/ | User login and authentication |
| Translation rules | app/rules/ | Custom translation rule configuration |
| Terminology management | app/terminology/ | Translation terminology dictionary management |
| AI translation | app/translate/ | AI-powered translation interface |

## CONVENTIONS
- Follows Next.js App Router conventions: each directory is a route, page.tsx is the page component
- Uses React Server Components (RSC) pattern by default for improved performance
- Client-side interactivity components are marked with 'use client' directive
- Route-specific components that are not reused across pages are kept within the route directory
- Shared components are moved to src/components/ for reuse across multiple pages
- Page metadata is defined using Next.js metadata API

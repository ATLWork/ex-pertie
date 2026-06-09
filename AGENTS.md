# PROJECT KNOWLEDGE BASE

**Generated:** Sat May 23 15:19:31 CST 2026
**Commit:** 882170a
**Branch:** main

## OVERVIEW
Expedia 酒店表格生成工具 - A tool for Atour channel operations team to automate hotel data upload to Expedia platform. Key features: hotel/room data import/validation, AI-powered translation with multi-source reference, Expedia template configuration and export.

## STRUCTURE
```
./
├── backend/    # FastAPI backend service (Python)
├── frontend/   # Next.js frontend UI (TypeScript/React)
├── e2e/        # Playwright end-to-end test suite
├── docs/       # Project documentation (PRD, technical design, task assignments)
├── reference/  # Data model reference materials
└── CLAUDE.md   # Core project guidance file
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Backend API development | backend/app/api/ | Versioned REST API endpoints |
| Frontend UI development | frontend/src/app/ | Next.js App Router page structure |
| Business logic implementation | backend/app/services/ | Core service layer |
| UI component development | frontend/src/components/ | Reusable React components |
| End-to-end testing | e2e/ | Playwright test suite (frontend + backend) |
| Product documentation | docs/ | PRD, technical design docs, dev task assignments |

## CONVENTIONS
- Project task management uses Taskwarrior (local to current directory)
- Issue tracking uses GitHub Issues
- UI/UX designs follow Figma prototype (link in CLAUDE.md)
- All documentation stored in docs/ directory

## ANTI-PATTERNS (THIS PROJECT)
- No explicit anti-patterns identified yet

## UNIQUE STYLES
- Multi-language support (Chinese/English) for hotel data translation
- Integration with multiple AI translation providers
- Custom Expedia template export with configurable formatting rules

## COMMANDS
```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload  # Start local dev server
cd backend && pytest  # Run backend unit/integration tests

# Frontend
cd frontend && npm run dev  # Start local dev server
cd frontend && npm run build  # Build production bundle

# E2E Tests
cd e2e && npx playwright test  # Run full end-to-end test suite
```

## NOTES
- Always reference Figma prototype when implementing UI requirement changes
- Data model reference materials available in reference/ directory
- Backend development task assignments in docs/backend-tasks.md

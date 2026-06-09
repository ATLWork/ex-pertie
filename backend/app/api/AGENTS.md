# API LAYER KNOWLEDGE BASE

## OVERVIEW
Versioned REST API layer for the FastAPI backend service. Contains all public API endpoints organized by module and API version to ensure backward compatibility as the platform evolves.

## STRUCTURE
```
app/api/
└── v1/ # API Version 1 (current active version)
    └── translation/ # Translation module related API endpoints
        ├── rules/ # Translation rule management endpoints
        ├── terminology/ # Translation terminology management endpoints
        └── translate/ # AI translation execution endpoints
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Version 1 API development | v1/ | All active version 1 API routes |
| Translation module endpoints | v1/translation/ | All AI translation, terminology, and rule related endpoints |
| New API version development | Create new directory e.g. v2/ | For breaking changes, new API versions are created in separate directories |

## CONVENTIONS
- API endpoints are versioned to maintain backward compatibility for existing clients
- Each business module has its own subdirectory of related endpoints
- Endpoints follow standard REST API naming conventions
- All input validation is handled via Pydantic schemas at the API layer
- Authentication and authorization are handled via global and route-specific middleware
- All endpoints return consistent JSON response formats with proper HTTP status codes

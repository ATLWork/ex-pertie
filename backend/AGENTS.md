# BACKEND KNOWLEDGE BASE

## OVERVIEW
FastAPI backend service for the Expedia hotel data management platform. Handles API requests, data validation, AI-powered translation services, database operations, and custom Expedia template generation.

## STRUCTURE
```
backend/
├── alembic/    # Database migration configuration (Alembic)
├── app/        # Main application source code
│   ├── api/    # Versioned API endpoints
│   ├── core/   # Core configurations, security utilities, dependency injection
│   ├── generators/ # Expedia template generation logic
│   ├── middleware/ # Custom HTTP middleware
│   ├── models/ # SQLAlchemy database ORM models
│   ├── parsers/ # Data import file parsers (Excel/CSV)
│   ├── repositories/ # Data access layer (DAL)
│   ├── schemas/ # Pydantic request/response validation schemas
│   ├── services/ # Business logic service layer
│   ├── tasks/ # Background async task definitions
│   ├── utils/ # Shared utility functions
│   └── validators/ # Custom business logic validators
├── docs/ # Backend specific documentation
├── logs/ # Application runtime logs
├── scripts/ # Utility and deployment scripts
├── tests/ # Unit and integration test suite
└── uploads/ # Temporary storage for uploaded user files
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| API endpoint development | app/api/v1/ | Version 1 REST API routes |
| Database schema changes | models/ + alembic/versions/ | SQLAlchemy models + Alembic migrations |
| Business logic implementation | app/services/ | Core service layer |
| API request/response schemas | app/schemas/ | Pydantic validation definitions |
| Database queries | app/repositories/ | Data access layer, reusable queries |
| Backend testing | tests/ | Unit + integration test suite |
| Template generation | app/generators/ | Expedia Excel template export logic |

## CONVENTIONS
- Follows FastAPI + Pydantic best practices for API development
- Uses SQLAlchemy 2.0 as ORM for PostgreSQL database
- Alembic for database schema migrations
- Pytest for test execution
- Type hints required for all Python functions
- Input validation handled at both API and service layers

## ANTI-PATTERNS
- No explicit anti-patterns identified yet

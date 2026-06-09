# SERVICE LAYER KNOWLEDGE BASE

## OVERVIEW
Core business logic layer of the FastAPI backend. Contains all domain and business logic implementations, separated from the API presentation layer and data access layer for better maintainability and testability.

## STRUCTURE
```
app/services/
└── translation/ # Translation module business logic
    ├── rule_service.py # Translation rule management logic
    ├── terminology_service.py # Translation terminology management logic
    └── translation_service.py # AI translation execution business logic
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Business logic implementation | services/ | All core business logic resides in this layer |
| Translation module logic | services/translation/ | All translation, rule, and terminology related business logic |
| New module development | Create new module directory under services/ | Each business module gets its own directory of service classes |

## CONVENTIONS
- Business logic is fully isolated from API presentation concerns and data access concerns
- Services depend on repository classes for all database operations
- Each business module has its own set of service classes
- Input validation and business rule enforcement are performed in this layer
- Services are designed to be testable in isolation from external dependencies
- Cross-module operations are handled via service-to-service calls

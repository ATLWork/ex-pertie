# E2E TEST SUITE KNOWLEDGE BASE

## OVERVIEW
Playwright end-to-end test suite that covers both frontend user interface flows and backend API functionality. Ensures all critical user journeys and business logic work correctly across the entire application stack.

## STRUCTURE
```
e2e/
├── backend/ # Backend API test suite
│   └── tests/ # API endpoint integration test files
├── frontend/ # Frontend UI test suite
│   ├── fixtures/ # Shared test fixtures and test data
│   ├── page-objects/ # Page Object Model (POM) class definitions
│   └── tests/ # UI test files, organized by feature
│       └── fixtures/ # UI test specific fixtures and setup
└── playwright.config.ts # Global Playwright configuration
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Backend API testing | backend/tests/ | API endpoint integration tests |
| Frontend UI flow testing | frontend/tests/ | User journey UI tests, organized by feature |
| Page Object definitions | frontend/page-objects/ | Reusable POM classes for each application page |
| Test data and setup | frontend/fixtures/ | Shared test data and common setup functions |
| Test configuration | playwright.config.ts | Global Playwright test configuration |

## CONVENTIONS
- Uses Playwright framework for cross-browser end-to-end testing
- Follows Page Object Model (POM) pattern for UI tests to reduce duplication
- Tests organized by feature/module
- Both frontend UI and backend API tests are included in the same test suite
- All tests run automatically in CI/CD pipeline on every pull request
- Tests use isolated test data and clean up after execution

## ANTI-PATTERNS
- No explicit anti-patterns identified yet

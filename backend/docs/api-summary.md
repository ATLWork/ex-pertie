# API 模块总结

> 生成时间: 2026-04-09

## 概览

| 模块 | 接口数 | 说明 |
|------|--------|------|
| health | 3 | 健康检查 |
| auth | 10 | 认证授权 |
| users | 7 | 用户管理 |
| translation | 35 | 翻译服务 |
| hotels | 8 | 酒店管理 |
| rooms | 2 | 客房管理 |
| imports | 3 | 数据导入 |
| exports | 3 | 数据导出 |

## /health

- `GET` /api/v1/health - Health Check
- `GET` /api/v1/health/ready - Readiness Check
- `GET` /api/v1/translation/health - Check translation services health

## /auth

- `POST` /api/v1/auth/register - Register
- `POST` /api/v1/auth/login - Login
- `POST` /api/v1/auth/refresh - Refresh Token
- `GET` /api/v1/auth/me - Get Current User Info
- `PUT` /api/v1/auth/me - Update Current User
- `PUT` /api/v1/auth/me/password - Change Password
- `GET` /api/v1/auth/roles - List Roles
- `POST` /api/v1/auth/roles - Create Role
- `GET` /api/v1/auth/roles/{role_id} - Get Role
- `PUT` /api/v1/auth/roles/{role_id} - Update Role

## /users

- `GET` /api/v1/users - List Users
- `GET` /api/v1/users/me - Get My Profile
- `GET` /api/v1/users/{user_id} - Get User
- `POST` /api/v1/users/{user_id}/activate - Activate User
- `POST` /api/v1/users/{user_id}/deactivate - Deactivate User
- `POST` /api/v1/users/{user_id}/roles/{role_id} - Assign Role
- `DELETE` /api/v1/users/{user_id}/roles/{role_id} - Remove Role

## /translation

- `GET` /api/v1/translation/rules - List Translation Rules
- `POST` /api/v1/translation/rules - Create Translation Rule
- `GET` /api/v1/translation/rules/active - Get Active Rules
- `GET` /api/v1/translation/rules/{rule_id} - Get Translation Rule
- `PUT` /api/v1/translation/rules/{rule_id} - Update Translation Rule
- `DELETE` /api/v1/translation/rules/{rule_id} - Delete Translation Rule
- `POST` /api/v1/translation/rules/{rule_id}/activate - Activate Translation Rule
- `POST` /api/v1/translation/rules/{rule_id}/deactivate - Deactivate Translation Rule
- `GET` /api/v1/translation/references - List Translation References
- `POST` /api/v1/translation/references - Create Translation Reference
- `POST` /api/v1/translation/references/bulk - Bulk Create Translation References
- `GET` /api/v1/translation/references/match - Find Matching Reference
- `GET` /api/v1/translation/references/similar - Find Similar References
- `GET` /api/v1/translation/references/statistics - Get Reference Statistics
- `GET` /api/v1/translation/references/{ref_id} - Get Translation Reference
- `PUT` /api/v1/translation/references/{ref_id} - Update Translation Reference
- `DELETE` /api/v1/translation/references/{ref_id} - Delete Translation Reference
- `PATCH` /api/v1/translation/references/{ref_id}/confidence - Update Reference Confidence
- `GET` /api/v1/translation/glossary - List Glossaries
- `POST` /api/v1/translation/glossary - Create Glossary
- `POST` /api/v1/translation/glossary/bulk - Bulk Create Glossaries
- `GET` /api/v1/translation/glossary/active - Get Active Glossaries
- `GET` /api/v1/translation/glossary/categories - Get Glossary Categories
- `GET` /api/v1/translation/glossary/lookup - Lookup Glossary Term
- `GET` /api/v1/translation/glossary/lookup-in-text - Lookup Glossary In Text
- `GET` /api/v1/translation/glossary/{glossary_id} - Get Glossary
- `PUT` /api/v1/translation/glossary/{glossary_id} - Update Glossary
- `DELETE` /api/v1/translation/glossary/{glossary_id} - Delete Glossary
- `POST` /api/v1/translation/glossary/{glossary_id}/activate - Activate Glossary
- `POST` /api/v1/translation/glossary/{glossary_id}/deactivate - Deactivate Glossary
- `POST` /api/v1/translation/translate - Translate single text
- `POST` /api/v1/translation/batch - Batch translate texts
- `GET` /api/v1/translation/history - Get translation history
- `DELETE` /api/v1/translation/cache - Clear translation cache
- `GET` /api/v1/translation/cache/stats - Get translation cache statistics

## /hotels

- `POST` /api/v1/hotels - Create Hotel
- `GET` /api/v1/hotels - List Hotels
- `GET` /api/v1/hotels/search - Search Hotels
- `GET` /api/v1/hotels/{hotel_id} - Get Hotel
- `PUT` /api/v1/hotels/{hotel_id} - Update Hotel
- `DELETE` /api/v1/hotels/{hotel_id} - Delete Hotel
- `POST` /api/v1/imports/hotels - Import hotel data
- `POST` /api/v1/exports/hotels - Export Hotels

## /rooms

- `POST` /api/v1/imports/rooms - Import room data
- `POST` /api/v1/exports/rooms - Export Rooms

## /imports

- `GET` /api/v1/imports - List import history
- `GET` /api/v1/imports/{import_id} - Get import details
- `GET` /api/v1/imports/{import_id}/errors - Get import errors

## /exports

- `GET` /api/v1/exports/{export_id} - Get Export Detail
- `GET` /api/v1/exports - List Exports
- `GET` /api/v1/exports/{export_id}/download - Download Export

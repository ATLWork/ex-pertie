# Ex-pertie 后端接口文档

> 自动生成时间: 2026-04-09  
> API 版本: 0.1.0  
> 接口总数: 55 个

---

## 目录

- [authentication](#authentication)
- [exports](#exports)
- [health](#health)
- [hotels](#hotels)
- [imports](#imports)
- [translation](#translation)
- [users](#users)

---

## authentication

### `POST` /api/v1/auth/login

**Login**

Login with username/email and password.

Returns access token and refresh token.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/LoginRequest"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/auth/me

**Get Current User Info**

Get current authenticated user information.

**响应:**

- `200`: Successful Response

### `PUT` /api/v1/auth/me

**Update Current User**

Update current user information.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/UserUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PUT` /api/v1/auth/me/password

**Change Password**

Change current user password.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/UserPasswordUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/auth/refresh

**Refresh Token**

Refresh access token using a valid refresh token.

Send the refresh token in Authorization header as Bearer token.

**响应:**

- `200`: Successful Response

### `POST` /api/v1/auth/register

**Register**

Register a new user.

- **email**: User email address
- **username**: Unique username
- **password**: Password (min 8 chars, must include uppercase, lowercase, and digit)
- **full_name**: Optional full name

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/UserCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/auth/roles

**List Roles**

Get all roles.

**响应:**

- `200`: Successful Response

### `POST` /api/v1/auth/roles

**Create Role**

Create a new role. Requires superuser privileges.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/RoleCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/auth/roles/{role_id}

**Get Role**

Get role by ID.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| role_id | path | string | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PUT` /api/v1/auth/roles/{role_id}

**Update Role**

Update role. Requires superuser privileges.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| role_id | path | string | 是 |  |

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/RoleUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error


---

## exports

### `GET` /api/v1/exports

**List Exports**

List export history.

- **page**: Page number (default: 1)
- **page_size**: Items per page (default: 20, max: 100)
- **export_type**: Filter by export type (hotel/room)
- **export_format**: Filter by format (excel/csv/json)
- **status**: Filter by status (pending/processing/completed/failed)

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| export_type | query | string | 否 | Filter by export type |
| export_format | query | string | 否 | Filter by format |
| status | query | string | 否 | Filter by status |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/exports/hotels

**Export Hotels**

Export hotel data.

- **export_format**: Export file format (excel/csv/json)
- **hotel_ids**: Optional list of hotel IDs to export (exports all if empty)
- **use_template**: Whether to use Expedia template format

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/HotelExportRequest"
}
```

**响应:**

- `201`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/exports/rooms

**Export Rooms**

Export room data.

- **export_format**: Export file format (excel/csv/json)
- **hotel_ids**: Optional list of hotel IDs to filter rooms
- **room_ids**: Optional list of room IDs to export
- **use_template**: Whether to use Expedia template format

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/RoomExportRequest"
}
```

**响应:**

- `201`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/exports/{export_id}

**Get Export Detail**

Get export task details.

- **export_id**: Export task ID

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| export_id | path | string | 是 | Export task ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/exports/{export_id}/download

**Download Export**

Download export file.

- **export_id**: Export task ID

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| export_id | path | string | 是 | Export task ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error


---

## health

### `GET` /api/v1/health

**Health Check**

Health check endpoint.
Returns the API status and version.

**响应:**

- `200`: Successful Response

### `GET` /api/v1/health/ready

**Readiness Check**

Readiness check endpoint.
Verifies that all required services are available.

**响应:**

- `200`: Successful Response


---

## hotels

### `GET` /api/v1/hotels

**List Hotels**

List hotels with pagination and filtering.

- **page**: Page number (default: 1)
- **page_size**: Items per page (default: 20, max: 100)
- **brand**: Filter by hotel brand
- **status**: Filter by hotel status
- **city**: Filter by city
- **province**: Filter by province
- **name**: Search by hotel name
- **expedia_hotel_id**: Filter by Expedia Hotel ID

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| brand | query | string | 否 | Filter by hotel brand |
| status | query | string | 否 | Filter by hotel status |
| city | query | string | 否 | Filter by city |
| province | query | string | 否 | Filter by province |
| name | query | string | 否 | Search by hotel name |
| expedia_hotel_id | query | string | 否 | Filter by Expedia Hotel ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/hotels

**Create Hotel**

Create a new hotel.

- **name_cn**: Hotel name in Chinese (required)
- **brand**: Hotel brand (default: atour)
- **status**: Hotel status (default: draft)
- **province**: Province/State (required)
- **city**: City (required)
- **address_cn**: Address in Chinese (required)
- **expedia_hotel_id**: Expedia Hotel ID (optional, unique)

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/HotelCreate"
}
```

**响应:**

- `201`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/hotels/search

**Search Hotels**

Comprehensive hotel search with multiple conditions.

- **keyword**: Keyword to search in hotel names (fuzzy match)
- **brand**: Filter by hotel brand
- **status**: Filter by hotel status
- **city**: Filter by city
- **province**: Filter by province
- **is_active**: Filter by active status
- **page**: Page number (default: 1)
- **page_size**: Items per page (default: 20, max: 100)
- **order_by**: Field to order by (default: updated_at)
- **order_desc**: Whether to order in descending order (default: True)

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| keyword | query | string | 否 | Keyword to search in hotel names |
| brand | query | string | 否 | Filter by hotel brand |
| status | query | string | 否 | Filter by hotel status |
| city | query | string | 否 | Filter by city |
| province | query | string | 否 | Filter by province |
| is_active | query | string | 否 | Filter by active status |
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| order_by | query | string | 否 | Field to order by |
| order_desc | query | boolean | 否 | Whether to order in descending order |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `DELETE` /api/v1/hotels/{hotel_id}

**Delete Hotel**

Delete a hotel by ID.

- **hotel_id**: Hotel ID (required)

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| hotel_id | path | string | 是 | Hotel ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/hotels/{hotel_id}

**Get Hotel**

Get a hotel by ID.

- **hotel_id**: Hotel ID (required)

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| hotel_id | path | string | 是 | Hotel ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PUT` /api/v1/hotels/{hotel_id}

**Update Hotel**

Update an existing hotel.

- **hotel_id**: Hotel ID (required)
- All fields are optional for partial update

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| hotel_id | path | string | 是 | Hotel ID |

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/HotelUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error


---

## imports

### `GET` /api/v1/imports

**List import history**

Get list of all import history records with pagination.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| import_type | query | string | 否 | Filter by import type |
| status | query | string | 否 | Filter by status |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/imports/hotels

**Import hotel data**

Import hotel data from uploaded Excel or CSV file.

**请求体 (multipart/form-data):**

```json
{
  "$ref": "#/components/schemas/Body_import_hotels_api_v1_imports_hotels_post"
}
```

**响应:**

- `201`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/imports/rooms

**Import room data**

Import room data from uploaded Excel or CSV file.

**请求体 (multipart/form-data):**

```json
{
  "$ref": "#/components/schemas/Body_import_rooms_api_v1_imports_rooms_post"
}
```

**响应:**

- `201`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/imports/{import_id}

**Get import details**

Get detailed information about a specific import.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| import_id | path | string | 是 | Import history ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/imports/{import_id}/errors

**Get import errors**

Get detailed error information for a specific import.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| import_id | path | string | 是 | Import history ID |

**响应:**

- `200`: Successful Response
- `422`: Validation Error


---

## translation

### `POST` /api/v1/translation/batch

**Batch translate texts**

Translate multiple texts in a single request with optimized batch processing.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/BatchTranslateRequest"
}
```

**响应:**

- `200`: Batch translation successful
- `400`: Invalid request
- `500`: Translation service error
- `422`: Validation Error

### `DELETE` /api/v1/translation/cache

**Clear translation cache**

Clear all cached translations.

**响应:**

- `200`: Cache cleared successfully
- `500`: Failed to clear cache

### `GET` /api/v1/translation/cache/stats

**Get translation cache statistics**

Get statistics about the translation cache.

**响应:**

- `200`: Successful Response

### `GET` /api/v1/translation/glossary

**List Glossaries**

List glossary entries with pagination and filtering.

- **page**: Page number (starts from 1)
- **page_size**: Number of items per page (max 100)
- **source_lang**: Filter by source language code
- **target_lang**: Filter by target language code
- **category**: Filter by term category
- **is_active**: Filter by active status
- **search**: Search in term or translation

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |
| category | query | string | 否 | Filter by category |
| is_active | query | string | 否 | Filter by active status |
| search | query | string | 否 | Search term in term or translation |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/glossary

**Create Glossary**

Create a new glossary entry.

- **term**: Term in source language
- **translation**: Standard translation
- **source_lang**: Source language code (e.g., zh-CN)
- **target_lang**: Target language code (e.g., en-US)
- **category**: Term category (hotel, room, amenity, general)
- **notes**: Additional notes
- **is_active**: Whether the term is active

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/GlossaryCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/glossary/active

**Get Active Glossaries**

Get all active glossary entries for a language pair.

This endpoint returns active terms that can be used during
translation for terminology consistency.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| source_lang | query | string | 是 | Source language code |
| target_lang | query | string | 是 | Target language code |
| category | query | string | 否 | Filter by category |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/glossary/bulk

**Bulk Create Glossaries**

Bulk create glossary entries.

Creates multiple glossary entries in a single request.
Useful for importing terminology from external sources.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/GlossaryBulkCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/glossary/categories

**Get Glossary Categories**

Get count of glossary entries by category.

Returns a breakdown of terms by their category.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/glossary/lookup

**Lookup Glossary Term**

Look up a term in the glossary.

Returns the exact match if found, useful for checking if
a specific term exists in the glossary.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| text | query | string | 是 | Text to look up |
| source_lang | query | string | 是 | Source language code |
| target_lang | query | string | 是 | Target language code |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/glossary/lookup-in-text

**Lookup Glossary In Text**

Find all glossary terms that appear in the given text.

This endpoint is useful for identifying which glossary terms
need to be applied during translation.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| text | query | string | 是 | Text to search in |
| source_lang | query | string | 是 | Source language code |
| target_lang | query | string | 是 | Target language code |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `DELETE` /api/v1/translation/glossary/{glossary_id}

**Delete Glossary**

Delete a glossary entry.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| glossary_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/glossary/{glossary_id}

**Get Glossary**

Get a specific glossary entry by ID.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| glossary_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PUT` /api/v1/translation/glossary/{glossary_id}

**Update Glossary**

Update a glossary entry.

Only provided fields will be updated.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| glossary_id | path | integer | 是 |  |

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/GlossaryUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/glossary/{glossary_id}/activate

**Activate Glossary**

Activate a glossary entry.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| glossary_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/glossary/{glossary_id}/deactivate

**Deactivate Glossary**

Deactivate a glossary entry.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| glossary_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/health

**Check translation services health**

Check the health status of all translation-related services.

**响应:**

- `200`: Successful Response

### `GET` /api/v1/translation/history

**Get translation history**

Retrieve paginated translation history records.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/references

**List Translation References**

List translation references with pagination and filtering.

- **page**: Page number (starts from 1)
- **page_size**: Number of items per page (max 100)
- **source_lang**: Filter by source language code
- **target_lang**: Filter by target language code
- **source**: Filter by reference source
- **min_confidence**: Minimum confidence score filter

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |
| source | query | string | 否 | Filter by source |
| min_confidence | query | string | 否 | Minimum confidence |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/references

**Create Translation Reference**

Create a new translation reference.

- **source_text**: Original text
- **translated_text**: Translated text
- **source_lang**: Source language code (e.g., zh-CN)
- **target_lang**: Target language code (e.g., en-US)
- **context**: Optional context information
- **confidence**: Confidence score (0-1, default 1.0)
- **source**: Reference source (manual, imported, ai)

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/TranslationReferenceCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/references/bulk

**Bulk Create Translation References**

Bulk create translation references.

Creates multiple translation reference entries in a single request.
Useful for importing reference data from external sources.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/TranslationReferenceBulkCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/references/match

**Find Matching Reference**

Find the best matching reference for a source text.

This endpoint is used during translation to find existing
high-quality translations from the reference library.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| source_text | query | string | 是 | Source text to match |
| source_lang | query | string | 是 | Source language code |
| target_lang | query | string | 是 | Target language code |
| min_confidence | query | number | 否 | Minimum confidence threshold |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/references/similar

**Find Similar References**

Find similar references (contains search).

Returns references that contain the search text, useful for
finding partial matches or related translations.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| source_text | query | string | 是 | Source text to search |
| source_lang | query | string | 是 | Source language code |
| target_lang | query | string | 是 | Target language code |
| limit | query | integer | 否 | Maximum results |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/references/statistics

**Get Reference Statistics**

Get statistics for translation references.

Returns counts by source, average confidence, and total count.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `DELETE` /api/v1/translation/references/{ref_id}

**Delete Translation Reference**

Delete a translation reference.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| ref_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/references/{ref_id}

**Get Translation Reference**

Get a specific translation reference by ID.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| ref_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PUT` /api/v1/translation/references/{ref_id}

**Update Translation Reference**

Update a translation reference.

Only provided fields will be updated.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| ref_id | path | integer | 是 |  |

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/TranslationReferenceUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PATCH` /api/v1/translation/references/{ref_id}/confidence

**Update Reference Confidence**

Update confidence score for a reference.

This endpoint is useful for adjusting confidence based on
user feedback or quality assessment.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| ref_id | path | integer | 是 |  |
| confidence | query | number | 是 | New confidence score |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/rules

**List Translation Rules**

List translation rules with pagination and filtering.

- **page**: Page number (starts from 1)
- **page_size**: Number of items per page (max 100)
- **source_lang**: Filter by source language code
- **target_lang**: Filter by target language code
- **field_name**: Filter by field name
- **rule_type**: Filter by rule type
- **is_active**: Filter by active status

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |
| field_name | query | string | 否 | Filter by field name |
| rule_type | query | string | 否 | Filter by rule type |
| is_active | query | string | 否 | Filter by active status |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/rules

**Create Translation Rule**

Create a new translation rule.

- **name**: Rule name (unique identifier)
- **source_lang**: Source language code (e.g., zh-CN)
- **target_lang**: Target language code (e.g., en-US)
- **field_name**: Field name to apply the rule
- **rule_type**: Type of rule (direct, glossary, ai)
- **rule_value**: Rule configuration (JSON string)
- **is_active**: Whether the rule is active

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/TranslationRuleCreate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/rules/active

**Get Active Rules**

Get all active translation rules.

This endpoint returns rules that are currently active and can be used
for translation operations.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| source_lang | query | string | 否 | Filter by source language |
| target_lang | query | string | 否 | Filter by target language |
| field_name | query | string | 否 | Filter by field name |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `DELETE` /api/v1/translation/rules/{rule_id}

**Delete Translation Rule**

Delete a translation rule.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| rule_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/translation/rules/{rule_id}

**Get Translation Rule**

Get a specific translation rule by ID.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| rule_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `PUT` /api/v1/translation/rules/{rule_id}

**Update Translation Rule**

Update a translation rule.

Only provided fields will be updated.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| rule_id | path | integer | 是 |  |

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/TranslationRuleUpdate"
}
```

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/rules/{rule_id}/activate

**Activate Translation Rule**

Activate a translation rule.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| rule_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/rules/{rule_id}/deactivate

**Deactivate Translation Rule**

Deactivate a translation rule.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| rule_id | path | integer | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/translation/translate

**Translate single text**

Translate a single text from source language to target language with optional AI enhancement.

**请求体 (application/json):**

```json
{
  "$ref": "#/components/schemas/TranslateRequest"
}
```

**响应:**

- `200`: Translation successful
- `400`: Invalid request
- `500`: Translation service error
- `422`: Validation Error


---

## users

### `GET` /api/v1/users

**List Users**

List all users with pagination. Requires authentication.

- **page**: Page number (default: 1)
- **page_size**: Items per page (default: 20, max: 100)
- **status**: Filter by user status
- **search**: Search by username or email

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| page | query | integer | 否 | Page number |
| page_size | query | integer | 否 | Items per page |
| status | query | string | 否 | Filter by status |
| search | query | string | 否 | Search by username or email |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `GET` /api/v1/users/me

**Get My Profile**

Get current authenticated user profile.

**响应:**

- `200`: Successful Response

### `GET` /api/v1/users/{user_id}

**Get User**

Get user by ID.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| user_id | path | string | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/users/{user_id}/activate

**Activate User**

Activate a user account. Requires superuser privileges.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| user_id | path | string | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/users/{user_id}/deactivate

**Deactivate User**

Deactivate a user account. Requires superuser privileges.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| user_id | path | string | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `DELETE` /api/v1/users/{user_id}/roles/{role_id}

**Remove Role**

Remove a role from a user. Requires superuser privileges.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| user_id | path | string | 是 |  |
| role_id | path | string | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error

### `POST` /api/v1/users/{user_id}/roles/{role_id}

**Assign Role**

Assign a role to a user. Requires superuser privileges.

**参数:**

| 名称 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| user_id | path | string | 是 |  |
| role_id | path | string | 是 |  |

**响应:**

- `200`: Successful Response
- `422`: Validation Error


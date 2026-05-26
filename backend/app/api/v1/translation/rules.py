"""
Translation Rule API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Path, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.translation import RuleType
from app.schemas.response import ApiResponse, PagedResponse, paged_response
from app.schemas.translation import (
    TranslationRuleCreate,
    TranslationRuleResponse,
    TranslationRuleUpdate,
    TranslationRuleQuery,
)
from app.services.translation_rule import translation_rule
from app.services.translation_rule_parser import get_rule_parser
from app.middleware.exception import NotFoundError, BadRequestError

router = APIRouter()


# ============== Routes WITHOUT path parameters (must come first) ==============


@router.get("", response_model=PagedResponse[TranslationRuleResponse])
async def list_translation_rules(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    field_name: Optional[str] = Query(None, description="Filter by field name"),
    rule_type: Optional[RuleType] = Query(None, description="Filter by rule type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List translation rules with pagination and filtering.

    - **page**: Page number (starts from 1)
    - **page_size**: Number of items per page (max 100)
    - **source_lang**: Filter by source language code
    - **target_lang**: Filter by target language code
    - **field_name**: Filter by field name
    - **rule_type**: Filter by rule type
    - **is_active**: Filter by active status
    """
    query_params = TranslationRuleQuery(
        source_lang=source_lang,
        target_lang=target_lang,
        field_name=field_name,
        rule_type=rule_type,
        is_active=is_active,
    )

    skip = (page - 1) * page_size
    items = await translation_rule.search(
        db, query_params=query_params, skip=skip, limit=page_size
    )
    total = await translation_rule.count_with_query(db, query_params=query_params)

    return paged_response(
        items=[TranslationRuleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ApiResponse[TranslationRuleResponse])
async def create_translation_rule(
    rule_in: TranslationRuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new translation rule.

    - **name**: Rule name (unique identifier)
    - **source_lang**: Source language code (e.g., zh-CN)
    - **target_lang**: Target language code (e.g., en-US)
    - **field_name**: Field name to apply the rule
    - **rule_type**: Type of rule (direct, glossary, ai)
    - **rule_value**: Rule configuration (JSON string)
    - **is_active**: Whether the rule is active
    """
    # Check if rule with same name exists
    existing = await translation_rule.get_by_name(db, name=rule_in.name)
    if existing:
        raise BadRequestError(
            message="Translation rule with this name already exists",
            details={"name": rule_in.name},
        )

    rule = await translation_rule.create(db, obj_in=rule_in)
    return ApiResponse(
        code=201,
        message="Translation rule created successfully",
        data=TranslationRuleResponse.model_validate(rule),
    )


@router.get("/active", response_model=ApiResponse[list[TranslationRuleResponse]])
async def get_active_rules(
    source_lang: Optional[str] = Query(None, description="Filter by source language"),
    target_lang: Optional[str] = Query(None, description="Filter by target language"),
    field_name: Optional[str] = Query(None, description="Filter by field name"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all active translation rules.

    This endpoint returns rules that are currently active and can be used
    for translation operations.
    """
    rules = await translation_rule.get_active_rules(
        db,
        source_lang=source_lang,
        target_lang=target_lang,
        field_name=field_name,
    )
    return ApiResponse(
        code=200,
        message="success",
        data=[TranslationRuleResponse.model_validate(rule) for rule in rules],
    )


# ============== PDF Import Endpoints ==============


@router.post(
    "/parse-pdf",
    response_model=ApiResponse[dict],
    summary="Parse PDF and generate translation rules",
    description="Upload a PDF document containing translation rules, parse it using AI, and generate structured rules.",
)
async def parse_pdf_rules(
    file: UploadFile = File(..., description="PDF file containing translation rules"),
    use_ai: bool = Query(True, description="Whether to use AI for parsing (disable for faster fallback parsing)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Parse a PDF document and generate structured translation rules.

    - **file**: PDF file containing translation rules (e.g., SOP document)
    - **use_ai**: Whether to use AI for intelligent parsing (default: True)

    The PDF content will be analyzed and translated into structured rules
    that can be stored and used during translation operations.
    """
    if not file.filename:
        raise BadRequestError(message="No file provided")

    # Validate file extension
    file_ext = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    if file_ext != "pdf":
        raise BadRequestError(
            message="Invalid file format",
            details={"supported_formats": [".pdf"]},
        )

    # Read file content
    content = await file.read()
    if not content:
        raise BadRequestError(message="Empty file provided")

    # Parse PDF
    parser = get_rule_parser()
    try:
        result = await parser.parse_pdf(
            pdf_content=content,
            source_filename=file.filename,
            use_ai=use_ai,
        )

        if not result.get("success"):
            raise BadRequestError(
                message="Failed to parse PDF",
                details={"error": result.get("error", "Unknown error")},
            )

        return ApiResponse(
            code=200,
            message=f"Successfully parsed {result.get('rules_count', 0)} rules from PDF",
            data={
                "rules_count": result.get("rules_count", 0),
                "rules": result.get("rules", []),
                "summary": result.get("summary", ""),
                "document_type": result.get("document_type", ""),
                "warning": result.get("warning"),
            },
        )

    except ImportError as e:
        raise BadRequestError(
            message="PDF parsing library not available",
            details={"error": str(e)},
        )
    except Exception as e:
        raise BadRequestError(
            message="Failed to parse PDF",
            details={"error": str(e)},
        )


@router.post(
    "/import-pdf",
    response_model=ApiResponse[dict],
    summary="Import translation rules from PDF",
    description="Upload a PDF document, parse it, and save the generated rules to database.",
)
async def import_pdf_rules(
    file: UploadFile = File(..., description="PDF file containing translation rules"),
    use_ai: bool = Query(True, description="Whether to use AI for parsing"),
    overwrite: bool = Query(False, description="Whether to overwrite existing rules with same name prefix"),
    db: AsyncSession = Depends(get_db),
):
    """
    Import translation rules from a PDF document.

    - **file**: PDF file containing translation rules
    - **use_ai**: Whether to use AI for intelligent parsing (default: True)
    - **overwrite**: Whether to overwrite existing rules with the same source prefix

    This endpoint parses the PDF and saves the generated rules directly
    to the database.
    """
    if not file.filename:
        raise BadRequestError(message="No file provided")

    file_ext = file.filename.lower().split(".")[-1] if "." in file.filename else ""
    if file_ext != "pdf":
        raise BadRequestError(
            message="Invalid file format",
            details={"supported_formats": [".pdf"]},
        )

    content = await file.read()
    if not content:
        raise BadRequestError(message="Empty file provided")

    parser = get_rule_parser()
    try:
        result = await parser.parse_pdf(
            pdf_content=content,
            source_filename=file.filename,
            use_ai=use_ai,
        )

        if not result.get("success"):
            raise BadRequestError(
                message="Failed to parse PDF",
                details={"error": result.get("error", "Unknown error")},
            )

        rules = result.get("rules", [])
        imported_count = 0
        skipped_count = 0
        errors = []

        for rule_data in rules:
            try:
                # Check if rule with similar name exists
                rule_name = rule_data.get("name", "")
                existing = await translation_rule.get_by_name(db, name=rule_name)

                if existing:
                    if overwrite:
                        # Update existing rule
                        rule_update = TranslationRuleUpdate(
                            rule_value=rule_data.get("rule_value", "{}"),
                            is_active=rule_data.get("is_active", True),
                        )
                        await translation_rule.update(db, db_obj=existing, obj_in=rule_update)
                        imported_count += 1
                    else:
                        skipped_count += 1
                        continue

                # Create new rule
                rule_create = TranslationRuleCreate(
                    name=rule_data.get("name", ""),
                    source_lang=rule_data.get("source_lang", "zh"),
                    target_lang=rule_data.get("target_lang", "en"),
                    field_name=rule_data.get("field_name", "general"),
                    rule_type=rule_data.get("rule_type", "direct"),
                    rule_value=rule_data.get("rule_value", "{}"),
                    is_active=rule_data.get("is_active", True),
                )
                await translation_rule.create(db, obj_in=rule_create)
                imported_count += 1

            except Exception as e:
                errors.append({"rule": rule_data.get("name", ""), "error": str(e)})

        await db.commit()

        return ApiResponse(
            code=200 if not errors else 207,
            message=f"Imported {imported_count} rules, skipped {skipped_count}, {len(errors)} errors",
            data={
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "error_count": len(errors),
                "errors": errors,
                "summary": result.get("summary", ""),
            },
        )

    except ImportError as e:
        raise BadRequestError(
            message="PDF parsing library not available",
            details={"error": str(e)},
        )
    except Exception as e:
        raise BadRequestError(
            message="Failed to import rules from PDF",
            details={"error": str(e)},
        )


# ============== Routes WITH path parameters (must come last) ==============


@router.get("/{rule_id}", response_model=ApiResponse[TranslationRuleResponse])
async def get_translation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific translation rule by ID.
    """
    rule = await translation_rule.get(db, id=rule_id)
    if not rule:
        raise NotFoundError(
            message="Translation rule not found",
            details={"id": rule_id},
        )

    return ApiResponse(
        code=200,
        message="success",
        data=TranslationRuleResponse.model_validate(rule),
    )


@router.put("/{rule_id}", response_model=ApiResponse[TranslationRuleResponse])
async def update_translation_rule(
    rule_id: int,
    rule_in: TranslationRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a translation rule.

    Only provided fields will be updated.
    """
    rule = await translation_rule.get(db, id=rule_id)
    if not rule:
        raise NotFoundError(
            message="Translation rule not found",
            details={"id": rule_id},
        )

    # Check name uniqueness if name is being updated
    if rule_in.name and rule_in.name != rule.name:
        existing = await translation_rule.get_by_name(db, name=rule_in.name)
        if existing:
            raise BadRequestError(
                message="Translation rule with this name already exists",
                details={"name": rule_in.name},
            )

    updated_rule = await translation_rule.update(db, db_obj=rule, obj_in=rule_in)
    return ApiResponse(
        code=200,
        message="Translation rule updated successfully",
        data=TranslationRuleResponse.model_validate(updated_rule),
    )


@router.delete("/{rule_id}", response_model=ApiResponse[dict])
async def delete_translation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a translation rule.
    """
    deleted = await translation_rule.delete(db, id=rule_id)
    if not deleted:
        raise NotFoundError(
            message="Translation rule not found",
            details={"id": rule_id},
        )

    return ApiResponse(
        code=200,
        message="Translation rule deleted successfully",
        data={"id": rule_id},
    )


@router.post("/{rule_id}/activate", response_model=ApiResponse[TranslationRuleResponse])
async def activate_translation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Activate a translation rule.
    """
    rule = await translation_rule.activate(db, id=rule_id)
    if not rule:
        raise NotFoundError(
            message="Translation rule not found",
            details={"id": rule_id},
        )

    return ApiResponse(
        code=200,
        message="Translation rule activated successfully",
        data=TranslationRuleResponse.model_validate(rule),
    )


@router.post("/{rule_id}/deactivate", response_model=ApiResponse[TranslationRuleResponse])
async def deactivate_translation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate a translation rule.
    """
    rule = await translation_rule.deactivate(db, id=rule_id)
    if not rule:
        raise NotFoundError(
            message="Translation rule not found",
            details={"id": rule_id},
        )

    return ApiResponse(
        code=200,
        message="Translation rule deactivated successfully",
        data=TranslationRuleResponse.model_validate(rule),
    )

"""
Batch Hotel Translator.

Translates all 13 Chinese fields of a hotel (Hotel, Room, RoomExtension)
to English using the TranslationOrchestrator.

13 translatable fields:
  Hotel (9):      name_en, address_en, cancellation_policy_en, prepayment_policy_en,
                  kid_policy_en, pet_policy_en, services_en, facilities_en, description_en
  Room (2):       name_en, description_en
  RoomExtension (2): amenities_en, bathroom_amenities_en

Provides:
- Lazy-load of TranslationOrchestrator (no API keys needed at import time)
- Field-level error isolation (one field failure does not abort the hotel)
- Hotel-level error isolation (one hotel failure does not abort the batch)
- Configurable concurrency via asyncio.Semaphore
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.hotel import Hotel, Room
from app.models.room import RoomExtension

# ---------------------------------------------------------------------------
# Field mappings: output key -> Chinese source attribute on the model
# ---------------------------------------------------------------------------

HOTEL_FIELDS: Dict[str, str] = {
    "name_en": "name_cn",
    "address_en": "address_cn",
    "cancellation_policy_en": "cancellation_policy",
    "prepayment_policy_en": "prepayment_policy",
    "kid_policy_en": "kid_policy",
    "pet_policy_en": "pet_policy",
    "services_en": "services",
    "facilities_en": "facilities",
    "description_en": "description",
}

ROOM_FIELDS: Dict[str, str] = {
    "name_en": "name_cn",
    "description_en": "description_cn",
}

ROOM_EXTENSION_FIELDS: Dict[str, str] = {
    "amenities_en": "amenities_cn",
    "bathroom_amenities_en": "bathroom_amenities_cn",
}

# Default language settings
DEFAULT_SOURCE_LANG = "zh"
DEFAULT_TARGET_LANG = "en"


class BatchHotelTranslator:
    """
    Batch translator for hotel-related content.

    Translates hotel, room, and room-extension fields from Chinese to English
    using the TranslationOrchestrator.  The orchestrator is lazily initialised
    so that API keys are not required at import time.

    Usage::

        translator = BatchHotelTranslator()
        result = await translator.translate_hotel("hotel-uuid", db)
        results = await translator.translate_batch(["uuid1", "uuid2"], db)
    """

    def __init__(self) -> None:
        """Initialise the batch translator (no external dependencies needed)."""
        self._orchestrator: Optional["TranslationOrchestrator"] = None  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Lazy-load helpers
    # ------------------------------------------------------------------

    def _get_orchestrator(self) -> "TranslationOrchestrator":  # type: ignore[name-defined]
        """
        Return the TranslationOrchestrator singleton, creating it on first access.

        This avoids importing and instantiating the orchestrator (which reads
        API keys / environment) at module load time.
        """
        if self._orchestrator is None:
            from app.services.translation.orchestrator import get_orchestrator

            self._orchestrator = get_orchestrator()
        return self._orchestrator

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _translate_field(
        orchestrator: "TranslationOrchestrator",  # type: ignore[name-defined]
        text: str,
        db: AsyncSession,
    ) -> tuple[Optional[str], str]:
        """
        Translate a single text snippet.

        Returns ``(translated_text_or_None, source_string)``.  Never raises.
        Source is ``"CACHE"``, ``"MACHINE"``, ``"AI_ENHANCED"``, ``"ERROR"`` or ``"N/A"``.
        """
        if not text or not text.strip():
            return (text or "", "N/A")

        try:
            result = await orchestrator.translate(
                text=text.strip(),
                source_lang=DEFAULT_SOURCE_LANG,
                target_lang=DEFAULT_TARGET_LANG,
                use_cache=True,
                use_ai_enhance=True,
                db=db,
            )
            return (result.translated_text, result.source.name)
        except Exception as exc:
            logger.warning(f"Translation failed: {exc}")
            return (None, "ERROR")

    async def _translate_model_fields(
        self,
        orchestrator: "TranslationOrchestrator",  # type: ignore[name-defined]
        model: Any,
        field_map: Dict[str, str],
        db: AsyncSession,
        level: str = "hotel",
    ) -> tuple[Dict[str, dict], List[str]]:
        """
        Translate every mapped field on *model* in parallel.

        Returns ``(fields, errors)`` where *fields* maps output key to a dict
        ``{"translated": str, "source": str, "level": str}`` and *errors*
        lists failure descriptions.
        """
        tasks = []
        keys = []
        for field_key, source_attr in field_map.items():
            source_text = getattr(model, source_attr, None) or ""
            keys.append(field_key)
            tasks.append(self._translate_field(orchestrator, source_text, db))

        raw_results = await asyncio.gather(*tasks)

        fields: Dict[str, dict] = {}
        errors: List[str] = []
        for key, (translated, source) in zip(keys, raw_results):
            if translated is not None:
                fields[key] = {"translated": translated, "source": source, "level": level}
            else:
                errors.append(f"Translation failed for {key}")

        return fields, errors

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def translate_hotel(
        self,
        hotel_id: str,
        db: AsyncSession,
    ) -> dict:
        """
        Translate all 13 fields for a single hotel and its rooms.

        Queries the hotel with eager-loaded rooms and their extensions,
        then translates every mapped field from Chinese to English.

        Args:
            hotel_id: Primary key of the hotel.
            db: Async database session.

        Returns:
            .. code-block:: python

                {
                    "hotel_id": str,
                    "fields": {
                        "name_en": {"translated": "...", "source": "AI_ENHANCED", "level": "hotel"},
                        "address_en": {"translated": "...", "source": "CACHE", "level": "hotel"},
                        # ... hotel-level fields ...
                        "<room_id>:name_en": {"translated": "...", "source": "MACHINE", "level": "room"},
                        "<room_id>:description_en": {"translated": "...", "source": "MACHINE", "level": "room"},
                        "<room_id>:amenities_en": {"translated": "...", "source": "CACHE", "level": "room_extension"},
                        "<room_id>:bathroom_amenities_en": {"translated": "...", "source": "AI_ENHANCED", "level": "room_extension"},
                    },
                    "errors": [
                        "Translation failed for name_en",
                        ...
                    ],
                }

            Room and extension fields are prefixed with ``<room_id>:`` to avoid
            key collisions (``name_en`` exists on both Hotel and Room).
        """
        # --- Load hotel with rooms ---
        stmt = (
            select(Hotel)
            .options(selectinload(Hotel.rooms))
            .where(Hotel.id == hotel_id)
        )
        result = await db.execute(stmt)
        hotel = result.scalars().first()

        if hotel is None:
            return {
                "hotel_id": hotel_id,
                "fields": {},
                "errors": [f"Hotel not found: {hotel_id}"],
            }

        orchestrator = self._get_orchestrator()
        all_fields: Dict[str, dict] = {}
        all_errors: List[str] = []

        # ---- Hotel-level fields (9) ----
        hotel_fields, hotel_errors = await self._translate_model_fields(
            orchestrator, hotel, HOTEL_FIELDS, db, level="hotel"
        )
        all_fields.update(hotel_fields)
        all_errors.extend(hotel_errors)

        # ---- Room-level fields (2 per room) ----
        room_ids: List[str] = []
        if hotel.rooms:
            for room in hotel.rooms:
                room_ids.append(room.id)
                room_fields, room_errors = await self._translate_model_fields(
                    orchestrator, room, ROOM_FIELDS, db, level="room"
                )
                for key, value in room_fields.items():
                    all_fields[f"{room.id}:{key}"] = value
                all_errors.extend(room_errors)

        # ---- Room-extension fields (2 per extension) ----
        if room_ids:
            ext_stmt = select(RoomExtension).where(
                RoomExtension.room_id.in_(room_ids)
            )
            ext_result = await db.execute(ext_stmt)
            extensions = ext_result.scalars().all()

            for ext in extensions:
                ext_fields, ext_errors = await self._translate_model_fields(
                    orchestrator, ext, ROOM_EXTENSION_FIELDS, db, level="room_extension"
                )
                for key, value in ext_fields.items():
                    all_fields[f"{ext.room_id}:{key}"] = value
                all_errors.extend(ext_errors)

        logger.info(
            "Hotel translation completed",
            extra={
                "hotel_id": hotel_id,
                "fields_count": len(all_fields),
                "errors_count": len(all_errors),
            },
        )

        return {
            "hotel_id": hotel_id,
            "fields": all_fields,
            "errors": all_errors,
        }

    async def translate_batch(
        self,
        hotel_ids: List[str],
        db: AsyncSession,
        concurrency: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[dict]:
        """
        Translate multiple hotels concurrently.

        Uses ``asyncio.Semaphore`` to cap the number of concurrent hotel
        translations.  Each hotel is independent — a failure in one hotel
        does not affect others.

        Args:
            hotel_ids: List of hotel primary keys.
            db: Async database session.
            concurrency: Maximum number of concurrent hotel translations.
            progress_callback: Optional callback ``fn(done, total)`` invoked
                after each hotel translation completes.

        Returns:
            List of result dicts (same format as :meth:`translate_hotel`),
            one entry per requested ``hotel_id``.
        """
        semaphore = asyncio.Semaphore(concurrency)
        completed = 0
        total = len(hotel_ids)

        async def _translate_one(hid: str) -> dict:
            nonlocal completed
            async with semaphore:
                try:
                    result = await self.translate_hotel(hid, db)
                    return result
                except Exception as exc:
                    logger.error(
                        f"Hotel translation raised exception",
                        extra={"hotel_id": hid, "error": str(exc)},
                    )
                    return {
                        "hotel_id": hid,
                        "fields": {},
                        "errors": [f"Unexpected error: {exc}"],
                    }
                finally:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total)

        tasks = [_translate_one(hid) for hid in hotel_ids]
        results = await asyncio.gather(*tasks)

        total_errors = sum(len(r.get("errors", [])) for r in results)
        logger.info(
            "Batch hotel translation completed",
            extra={
                "hotels_count": len(results),
                "total_errors": total_errors,
            },
        )

        return list(results)

"""
SQLAlchemy database models.
"""

from app.models.base import BaseModel
from app.models.role import Permission, Role
from app.models.user import User, UserStatus
from app.models.user_role import user_roles
from app.models.translation import (
    TranslationRule,
    TranslationReference,
    Glossary,
    TranslationHistory,
    RuleType,
    ReferenceSource,
    GlossaryCategory,
    TranslationType,
)
from app.models.hotel import (
    Hotel,
    HotelBrand,
    HotelStatus,
    Room,
)
from app.models.room import RoomExtension
from app.models.import_history import ImportHistory, ImportType, ImportStatus
from app.models.export_history import ExportHistory, ExportType, ExportFormat, ExportStatus
from app.models.booking import (
    BookingHotel,
    BookingHotelExtension,
    BookingRoom,
    BookingRoomExtension,
    BookingSource,
)
from app.models.expedia_template import (
    ExpediaTemplate,
    FieldMapping,
    TemplateType,
    TemplateStatus,
    FieldMappingType,
)
from app.models.terminology import (
    Terminology,
    TerminologyCategory,
)
from app.models.booking_reference import BookingReference

__all__ = [
    "BaseModel",
    "User",
    "UserStatus",
    "Role",
    "Permission",
    "user_roles",
    "TranslationRule",
    "TranslationReference",
    "Glossary",
    "TranslationHistory",
    "RuleType",
    "ReferenceSource",
    "GlossaryCategory",
    "TranslationType",
    "Hotel",
    "HotelBrand",
    "HotelStatus",
    "Room",
    "RoomExtension",
    "ImportHistory",
    "ImportType",
    "ImportStatus",
    "ExportHistory",
    "ExportType",
    "ExportFormat",
    "ExportStatus",
    "BookingHotel",
    "BookingHotelExtension",
    "BookingRoom",
    "BookingRoomExtension",
    "BookingSource",
    "ExpediaTemplate",
    "FieldMapping",
    "TemplateType",
    "TemplateStatus",
    "FieldMappingType",
    "Terminology",
    "TerminologyCategory",
    "BookingReference",
]

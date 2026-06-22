from enum import Enum


class StudyStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    COLLECTING = "collecting"
    CONSOLIDATING = "consolidating"
    SCORING = "scoring"
    GENERATING = "generating"
    RENDERING = "rendering"
    QA_FAILED = "qa_failed"
    READY = "ready"
    PUBLISHED = "published"


class VerdictEnum(str, Enum):
    GO = "GO"
    GO_CONDITIONAL = "GO_CONDITIONAL"
    NO_GO = "NO_GO"


class PriorityEnum(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class ConfidenceGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class GeoLevel(str, Enum):
    POSTAL_CODE = "postal_code"
    MUNICIPALITY = "municipality"
    METRO_AREA = "metro_area"
    PROVINCE = "province"
    REGION = "region"
    COUNTRY = "country"


class SourceType(str, Enum):
    OFFICIAL_NATIONAL = "official_national"
    OFFICIAL_REGIONAL = "official_regional"
    OFFICIAL_LOCAL = "official_local"
    SEMI_OFFICIAL = "semi_official"
    COMMERCIAL = "commercial"
    PRESS = "press"
    CORPORATE = "corporate"


class FreshnessLevel(str, Enum):
    REALTIME = "realtime"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    HISTORICAL = "historical"


class RenderType(str, Enum):
    HTML = "html"
    PPTX = "pptx"
    PDF = "pdf"
    JSON = "json"


class QASeverity(str, Enum):
    BLOCKING = "blocking"
    WARNING = "warning"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FitLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

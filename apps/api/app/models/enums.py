from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    USER = "user"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPORTED = "exported"
    FAILED = "failed"


class DocumentType(StrEnum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    REQUEST = "request"
    REPORT = "report"
    UNKNOWN = "unknown"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

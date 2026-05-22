import json
import logging
import sys
from datetime import UTC, datetime

from app.core.request_context import get_request_id

EXTRA_LOG_FIELDS = (
    "event",
    "action",
    "request_id",
    "document_id",
    "user_id",
    "status",
    "processing_status",
    "duration_ms",
    "ai_provider",
    "failure_reason",
    "path",
    "method",
)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "request_id", None):
            record.request_id = get_request_id()
        return True


class StructuredJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field in EXTRA_LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(StructuredJSONFormatter())
    stream_handler.addFilter(RequestContextFilter())

    logging.basicConfig(
        level=logging.INFO,
        handlers=[stream_handler],
        force=True,
    )

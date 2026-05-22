from uuid import UUID

from sqlalchemy.orm import Session

from app.core.request_context import get_request_id
from app.models.audit import AuditLog


def log_event(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: str | UUID | None = None,
    metadata: dict | None = None,
    commit: bool = True,
) -> AuditLog:
    actor_uuid = None
    if actor_id is not None:
        actor_uuid = UUID(str(actor_id))

    safe_metadata = dict(metadata or {})
    request_id = get_request_id()
    if request_id and "request_id" not in safe_metadata:
        safe_metadata["request_id"] = request_id

    event = AuditLog(
        actor_id=actor_uuid,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=safe_metadata,
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event

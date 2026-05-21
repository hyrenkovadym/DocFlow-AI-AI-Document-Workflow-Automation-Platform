from uuid import UUID

from sqlalchemy.orm import Session

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

    event = AuditLog(
        actor_id=actor_uuid,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event

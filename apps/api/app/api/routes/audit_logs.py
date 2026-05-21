from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.schemas.audit import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles(UserRole.ADMIN)),
) -> list[AuditLogResponse]:
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(500)
    return list(db.scalars(query))

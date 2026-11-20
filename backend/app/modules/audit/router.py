"""Audit log query endpoints per Section 13.3."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.request_context import RequestContext, get_current_request_context
from app.modules.audit.models import AuditEvent
from app.modules.audit.schemas import AuditEventOut, AuditLogPage
from app.modules.auth.models import User

router = APIRouter(prefix="", tags=["Audit & Operational Visibility"])


@router.get("/audit/events", response_model=AuditLogPage)
def list_audit_events(
    action: Optional[str] = Query(None, description="Optional action filter"),
    entity_type: Optional[str] = Query(None, description="Optional entity type filter"),
    entity_id: Optional[str] = Query(None, description="Optional entity ID filter"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Retrieves immutable audit trail records scoped strictly to the caller's school."""
    query = (
        db.query(AuditEvent, User)
        .outerjoin(User, AuditEvent.actor_id == User.id)
        .filter(AuditEvent.school_id == ctx.school_id)
    )

    if action:
        query = query.filter(AuditEvent.action == action)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)

    total_count = query.count()
    rows = (
        query.order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    events_out = [
        AuditEventOut(
            id=ev.AuditEvent.id,
            school_id=ev.AuditEvent.school_id,
            actor_id=ev.AuditEvent.actor_id,
            actor_name=ev.User.full_name if ev.User else "System",
            action=ev.AuditEvent.action,
            entity_type=ev.AuditEvent.entity_type,
            entity_id=ev.AuditEvent.entity_id,
            request_id=ev.AuditEvent.request_id,
            metadata_json=ev.AuditEvent.metadata_json,
            created_at=ev.AuditEvent.created_at,
        )
        for ev in rows
    ]

    return AuditLogPage(
        total_count=total_count,
        limit=limit,
        offset=offset,
        events=events_out,
    )

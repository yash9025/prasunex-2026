"""Audit event schemas per Section 13.3."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    """Immutable audit trail record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    actor_id: str
    actor_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    request_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime


class AuditLogPage(BaseModel):
    """Paginated collection of audit events."""

    total_count: int
    limit: int
    offset: int
    events: List[AuditEventOut]

"""Audit event logging model per Section 6.2 & 13.3.

Provides append-only traceability of teacher decisions, imports, approvals, and assignments.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from datetime import datetime, timezone

from app.core.database import Base, generate_uuid


class AuditEvent(Base):
    """Append-only audit trail for operational visibility and compliance."""

    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., IMPORT_UPLOADED, EVIDENCE_CONFIRMED, PLAN_APPROVED
    entity_type = Column(String(50), nullable=False)  # assessment, gap_evidence, plan_version, assignment
    entity_id = Column(String(36), nullable=False, index=True)
    request_id = Column(String(36), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

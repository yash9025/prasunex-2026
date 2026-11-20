"""Background job tracking, transactional outbox, and idempotency models.

Supports safe at-least-once job delivery and idempotent replay per Section 5.3 & 7.3.
"""

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)

from app.core.database import Base, TimestampMixin, generate_uuid


class Job(Base, TimestampMixin):
    """Durable job execution record stored in PostgreSQL."""

    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(50), nullable=False)  # csv_import, plan_draft
    status = Column(String(50), nullable=False, default="queued")  # queued, running, succeeded, failed, retry_pending
    request_hash = Column(String(64), nullable=False, index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    heartbeat = Column(DateTime, nullable=True)
    failure_code = Column(String(100), nullable=True)
    failure_message = Column(Text, nullable=True)
    result_summary = Column(JSON, nullable=True)


class OutboxEvent(Base, TimestampMixin):
    """Transactional outbox event published to Redis broker."""

    __tablename__ = "outbox_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # job_queued, job_completed
    payload = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, dispatched, failed
    retry_count = Column(Integer, nullable=False, default=0)
    next_attempt = Column(DateTime, nullable=True)


class IdempotencyRecord(Base, TimestampMixin):
    """Guarantees idempotent client operations scoped to school, actor, and operation."""

    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    operation = Column(String(50), nullable=False)  # import_csv, draft_plan
    idempotency_key = Column(String(100), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "actor_id", "operation", "idempotency_key", name="uq_idempotency_scoped_key"),
    )

"""Database connectivity, session lifecycle, and RLS context management.

Supports both PostgreSQL (production and Docker) and SQLite (fast local testing).
Enforces tenant isolation by applying session-local school identifiers.
"""

from datetime import datetime, timezone
from typing import Generator
import uuid

from sqlalchemy import Column, DateTime, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Engine configuration with dialect-specific options
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DATABASE_ECHO,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class TimestampMixin:
    """Standard audit timestamps for all persistent entities."""

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def generate_uuid() -> str:
    """Generates standard UUIDv4 strings for entity keys."""
    return str(uuid.uuid4())


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a clean database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_tenant_context(session: Session, school_id: str) -> None:
    """Sets the transaction-local PostgreSQL session variable for Row-Level Security (RLS).

    On SQLite, safely no-ops so development and unit tests run seamlessly without
    requiring an active Postgres service.
    """
    dialect = session.bind.dialect.name if session.bind else ""
    if dialect == "postgresql":
        # Parameterized local session setting
        session.execute(
            text("SET LOCAL app.current_school_id = :school_id"),
            {"school_id": school_id},
        )

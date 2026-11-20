"""Pytest configuration and test fixtures.

Configures test database session, provisions test tokens, and sets up TestClient.
"""

import sys
from pathlib import Path
from typing import Generator

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import create_access_token
from app.main import app
from seeds.run_seed import (
    CLASS_6A_ID,
    CLASS_6B_ID,
    OAKRIDGE_SCHOOL_ID,
    PINEGROVE_SCHOOL_ID,
    TEACHER_DAVID_ID,
    TEACHER_PRIYA_ID,
    seed_database,
)


@pytest.fixture(scope="session", autouse=True)
def ensure_database_seeded():
    """Ensures database is initialized and seeded before test suite execution."""
    seed_database()
    # Clean any dynamic transaction tables from previous runs
    session = SessionLocal()
    try:
        from app.modules.jobs.models import IdempotencyRecord, Job, OutboxEvent
        from app.modules.evidence.models import Assessment, Question, Attempt, GapEvidence, EvidenceAttempt
        from app.modules.audit.models import AuditEvent

        session.query(EvidenceAttempt).delete()
        session.query(GapEvidence).delete()
        session.query(Attempt).delete()
        session.query(Question).delete()
        session.query(Assessment).delete()
        session.query(OutboxEvent).delete()
        session.query(IdempotencyRecord).delete()
        session.query(Job).delete()
        session.query(AuditEvent).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provides a transactional database session for tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with active session dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def priya_token() -> str:
    """Signed JWT token for Teacher Priya Sharma (Oakridge International Academy)."""
    return create_access_token(
        subject=TEACHER_PRIYA_ID,
        claims={"school_id": OAKRIDGE_SCHOOL_ID, "role": "teacher"},
    )


@pytest.fixture
def david_token() -> str:
    """Signed JWT token for Teacher David Chen (Pinegrove Public School)."""
    return create_access_token(
        subject=TEACHER_DAVID_ID,
        claims={"school_id": PINEGROVE_SCHOOL_ID, "role": "teacher"},
    )

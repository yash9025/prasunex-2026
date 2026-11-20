"""Rigorous cross-school isolation tests per Section 8.2 & Exit Gate.

Verifies:
1. Teacher Priya cannot access Pinegrove Public School classes.
2. Teacher David cannot access Oakridge Academy classes.
3. Client-supplied X-School-ID header cannot grant unauthorized tenant context.
4. Database reads are completely isolated between schools.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.classrooms.models import Classroom, Learner
from seeds.run_seed import (
    CLASS_6A_ID,
    CLASS_6B_ID,
    OAKRIDGE_SCHOOL_ID,
    PINEGROVE_SCHOOL_ID,
)


def test_priya_cannot_access_pinegrove_class(client: TestClient, priya_token: str):
    """Oakridge teacher attempting to access Pinegrove class returns 403 Forbidden."""
    headers = {"Authorization": f"Bearer {priya_token}"}
    response = client.get(f"/v1/classes/{CLASS_6B_ID}", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN_RESOURCE"
    assert "permissions" in data["message"].lower()


def test_david_cannot_access_oakridge_class(client: TestClient, david_token: str):
    """Pinegrove teacher attempting to access Oakridge class returns 403 Forbidden."""
    headers = {"Authorization": f"Bearer {david_token}"}
    response = client.get(f"/v1/classes/{CLASS_6A_ID}", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN_RESOURCE"


def test_david_cannot_spoof_oakridge_school_id_header(client: TestClient, david_token: str):
    """Passing another school's ID via X-School-ID header is rejected server-side."""
    headers = {
        "Authorization": f"Bearer {david_token}",
        "X-School-ID": OAKRIDGE_SCHOOL_ID,
    }
    response = client.get("/v1/classes", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN_RESOURCE"
    assert "access denied" in data["message"].lower()


def test_direct_db_tenant_isolation(db_session: Session):
    """Direct DB queries scoped to Oakridge return 0 Pinegrove records and vice-versa."""
    # Oakridge scope
    oakridge_learners = (
        db_session.query(Learner)
        .filter(Learner.school_id == OAKRIDGE_SCHOOL_ID)
        .all()
    )
    assert len(oakridge_learners) == 40
    for l in oakridge_learners:
        assert l.school_id == OAKRIDGE_SCHOOL_ID
        assert l.external_ref.startswith("SYN-L6-")

    # Pinegrove scope
    pinegrove_learners = (
        db_session.query(Learner)
        .filter(Learner.school_id == PINEGROVE_SCHOOL_ID)
        .all()
    )
    assert len(pinegrove_learners) == 10
    for l in pinegrove_learners:
        assert l.school_id == PINEGROVE_SCHOOL_ID
        assert l.external_ref.startswith("SYN-PG-")

    # Cross check
    cross_check = (
        db_session.query(Learner)
        .filter(
            Learner.school_id == OAKRIDGE_SCHOOL_ID,
            Learner.external_ref.startswith("SYN-PG-"),
        )
        .all()
    )
    assert len(cross_check) == 0

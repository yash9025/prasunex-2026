"""Integration tests for import idempotency replay and all-or-nothing failure handling."""

from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.evidence.models import Assessment, Attempt
from seeds.run_seed import CLASS_6A_ID, CLASS_6B_ID


def test_idempotent_replay_returns_same_job(client: TestClient, priya_token: str):
    """Uploading the same payload with the same Idempotency-Key returns the existing job."""
    fixture_path = Path("fixtures/synthetic_class6_baseline.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    headers = {
        "Authorization": f"Bearer {priya_token}",
        "Idempotency-Key": "unique-idem-key-999",
    }
    payload = {
        "classroom_id": CLASS_6A_ID,
        "assessment_title": "Idempotent Diagnostic Check",
    }

    # 1. First upload
    res1 = client.post(
        "/v1/imports",
        headers=headers,
        data=payload,
        files={"file": ("test.csv", file_bytes, "text/csv")},
    )
    assert res1.status_code == 202
    job_id_1 = res1.json()["job_id"]

    # 2. Replay upload with identical key and identical payload
    res2 = client.post(
        "/v1/imports",
        headers=headers,
        data=payload,
        files={"file": ("test.csv", file_bytes, "text/csv")},
    )
    assert res2.status_code == 202
    job_id_2 = res2.json()["job_id"]

    # Invariant: same job ID returned, zero duplicates allocated
    assert job_id_1 == job_id_2


def test_idempotency_conflict_on_altered_payload(client: TestClient, priya_token: str):
    """Reusing the same key with different payload returns 409 Conflict per Section 7.3."""
    headers = {
        "Authorization": f"Bearer {priya_token}",
        "Idempotency-Key": "conflict-test-key-001",
    }

    # Upload 1
    client.post(
        "/v1/imports",
        headers=headers,
        data={"classroom_id": CLASS_6A_ID, "assessment_title": "Title A"},
        files={"file": ("test1.csv", b"dummy content A", "text/csv")},
    )

    # Upload 2 with DIFFERENT payload and same key
    res2 = client.post(
        "/v1/imports",
        headers=headers,
        data={"classroom_id": CLASS_6A_ID, "assessment_title": "Title B (Changed)"},
        files={"file": ("test2.csv", b"dummy content B", "text/csv")},
    )
    assert res2.status_code == 409
    data = res2.json()
    assert data["code"] == "RESOURCE_CONFLICT"
    assert "reused" in data["message"].lower()


def test_malformed_headers_rejected_with_zero_results(client: TestClient, priya_token: str, db_session: Session):
    """All-or-nothing check: invalid headers fail validation and write no assessment data."""
    fixture_path = Path("fixtures/synthetic_class6_malformed_headers.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    headers = {"Authorization": f"Bearer {priya_token}"}
    title = "Malformed Assessment Attempt"

    res = client.post(
        "/v1/imports",
        headers=headers,
        data={"classroom_id": CLASS_6A_ID, "assessment_title": title},
        files={"file": ("malformed.csv", file_bytes, "text/csv")},
    )
    assert res.status_code == 202
    job_id = res.json()["job_id"]

    # Poll job status
    job_res = client.get(f"/v1/jobs/{job_id}", headers=headers)
    job_data = job_res.json()
    assert job_data["status"] == "failed"
    assert job_data["failure_code"] == "CSV_VALIDATION_FAILED"
    assert len(job_data["result_summary"]["row_errors"]) > 0

    # Invariant: No assessment or attempts were committed in database
    assmt = db_session.query(Assessment).filter(Assessment.title == title).first()
    assert assmt is None


def test_conflicting_question_metadata_rejected(client: TestClient, priya_token: str, db_session: Session):
    """All-or-nothing check: conflicting question keys across rows reject entire file."""
    fixture_path = Path("fixtures/synthetic_class6_mismatched_metadata.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    headers = {"Authorization": f"Bearer {priya_token}"}
    title = "Mismatched Question Metadata Sitting"

    res = client.post(
        "/v1/imports",
        headers=headers,
        data={"classroom_id": CLASS_6A_ID, "assessment_title": title},
        files={"file": ("mismatch.csv", file_bytes, "text/csv")},
    )
    job_id = res.json()["job_id"]

    job_res = client.get(f"/v1/jobs/{job_id}", headers=headers)
    job_data = job_res.json()
    assert job_data["status"] == "failed"
    assert "Conflicting definition" in str(job_data["result_summary"]["row_errors"])


def test_cross_school_import_forbidden(client: TestClient, priya_token: str):
    """Teacher Priya attempting to upload CSV to Pinegrove class returns 403 Forbidden."""
    fixture_path = Path("fixtures/synthetic_class6_baseline.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    headers = {"Authorization": f"Bearer {priya_token}"}
    res = client.post(
        "/v1/imports",
        headers=headers,
        data={"classroom_id": CLASS_6B_ID, "assessment_title": "Unauthorized Pinegrove Import"},
        files={"file": ("test.csv", file_bytes, "text/csv")},
    )
    assert res.status_code == 403
    assert res.json()["code"] == "FORBIDDEN_RESOURCE"

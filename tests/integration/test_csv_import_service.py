"""Integration tests for CSV assessment import, scoring pipeline, and evidence generation."""

from pathlib import Path
from fastapi.testclient import TestClient
from seeds.run_seed import CLASS_6A_ID


def test_download_csv_template(client: TestClient):
    response = client.get("/v1/imports/template")
    assert response.status_code == 200
    assert "learner_ref,question_ref,topic_ref" in response.text
    assert "text/csv" in response.headers["Content-Type"]


def test_import_baseline_csv_and_verify_evidence(client: TestClient, priya_token: str):
    """Uploads the 400-response synthetic baseline CSV and inspects diagnostic evidence."""
    fixture_path = Path("fixtures/synthetic_class6_baseline.csv")
    assert fixture_path.exists(), "fixtures/synthetic_class6_baseline.csv must exist"

    headers = {
        "Authorization": f"Bearer {priya_token}",
        "Idempotency-Key": "test-key-baseline-001",
    }

    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/v1/imports",
        headers=headers,
        data={
            "classroom_id": CLASS_6A_ID,
            "assessment_title": "Class 6 Term 1 Diagnostic Baseline",
        },
        files={"file": ("synthetic_class6_baseline.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "succeeded"

    job_id = data["job_id"]

    # Poll Job Status Endpoint
    job_res = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "succeeded"
    summary = job_data["result_summary"]
    assert summary["rows_processed"] == 400
    assert summary["learners_count"] == 40
    assert summary["questions_count"] == 10
    assessment_id = summary["assessment_id"]

    # Inspect Diagnostic Evidence
    ev_res = client.get(f"/v1/assessments/{assessment_id}/evidence", headers=headers)
    assert ev_res.status_code == 200
    ev_data = ev_res.json()

    # 40 learners x 3 topics = 120 evidence snapshots
    assert ev_data["total_records"] == 120

    evidence_map = {
        (e["learner_ref"], e["topic_code"]): e
        for e in ev_data["evidence"]
    }

    # 1. Verify Primary Demo Learner: Aarav Patel (SYN-L6-014)
    # 7/10 overall mark: 1/3 Frac, 3/3 Dec, 3/4 Pct
    aarav_frac = evidence_map[("SYN-L6-014", "MATH-G6-FRAC")]
    assert float(aarav_frac["awarded_marks"]) == 1.0
    assert float(aarav_frac["possible_marks"]) == 3.0
    assert float(aarav_frac["percentage"]) == 33.33
    assert aarav_frac["status"] == "pending_review"  # Below 60% review flag!

    # Check supporting attempts for Aarav's fractions
    supporting = {att["question_ref"]: att for att in aarav_frac["supporting_attempts"]}
    assert supporting["Q1"]["raw_response"] == "2/5"
    assert supporting["Q1"]["outcome"] == "incorrect"
    assert supporting["Q2"]["raw_response"] == "1/3"
    assert supporting["Q2"]["outcome"] == "incorrect"
    assert supporting["Q3"]["raw_response"] == "2/5"
    assert supporting["Q3"]["outcome"] == "correct"

    # Decimals: 3/3
    aarav_dec = evidence_map[("SYN-L6-014", "MATH-G6-DEC")]
    assert float(aarav_dec["awarded_marks"]) == 3.0
    assert float(aarav_dec["percentage"]) == 100.0
    assert aarav_dec["status"] == "secure"

    # Percentages: 3/4
    aarav_pct = evidence_map[("SYN-L6-014", "MATH-G6-PCT")]
    assert float(aarav_pct["awarded_marks"]) == 3.0
    assert float(aarav_pct["percentage"]) == 75.0
    assert aarav_pct["status"] == "secure"

    # 2. Verify Boundary Learner: Rhea Varma (SYN-L6-020)
    rhea_frac = evidence_map[("SYN-L6-020", "MATH-G6-FRAC")]
    assert float(rhea_frac["awarded_marks"]) == 2.0
    assert float(rhea_frac["percentage"]) == 66.67
    assert rhea_frac["status"] == "secure"  # >= 60% does not flag!

    # 3. Verify Completion Concern: Ishaan Joshi (SYN-L6-021)
    ishaan_frac = evidence_map[("SYN-L6-021", "MATH-G6-FRAC")]
    assert ishaan_frac["assessed_items_count"] == 0
    assert ishaan_frac["unattempted_count"] == 3
    assert ishaan_frac["percentage"] is None
    assert ishaan_frac["status"] == "insufficient_evidence"

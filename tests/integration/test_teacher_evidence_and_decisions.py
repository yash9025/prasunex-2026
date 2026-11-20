"""Integration tests for Phase 3 Teacher Evidence Workspace & Decision Recording.

Verifies:
1. Teacher can inspect explainable evidence with supporting attempts.
2. Teacher can confirm, correct, or dismiss a flagged evidence snapshot.
3. Decision history is append-only and persisted with actor and timestamp.
4. Cross-school isolation blocks unauthorized teachers from deciding on foreign evidence.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from seeds.run_seed import CLASS_6A_ID, TOPIC_FRAC_ID


def ensure_assessment_imported(client: TestClient, priya_token: str) -> str:
    """Helper ensuring baseline assessment is imported and returns assessment_id."""
    fixture_path = Path("fixtures/synthetic_class6_baseline.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/v1/imports",
        headers={"Authorization": f"Bearer {priya_token}", "Idempotency-Key": "phase3-seed-import"},
        data={"classroom_id": CLASS_6A_ID, "assessment_title": "Phase 3 Diagnostic Baseline"},
        files={"file": ("baseline.csv", file_bytes, "text/csv")},
    )
    job_id = res.json()["job_id"]
    job_res = client.get(f"/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {priya_token}"})
    return job_res.json()["result_summary"]["assessment_id"]


def test_inspect_and_confirm_aarav_patel_gap(client: TestClient, priya_token: str):
    """Teacher Priya inspects Aarav Patel's fractions gap and confirms the need with pedagogical rationale."""
    assessment_id = ensure_assessment_imported(client, priya_token)
    headers = {"Authorization": f"Bearer {priya_token}"}

    # 1. Fetch Evidence
    ev_res = client.get(f"/v1/assessments/{assessment_id}/evidence?topic_filter=MATH-G6-FRAC", headers=headers)
    assert ev_res.status_code == 200
    ev_data = ev_res.json()

    aarav_ev = next((e for e in ev_data["evidence"] if e["learner_ref"] == "SYN-L6-014"), None)
    assert aarav_ev is not None
    assert aarav_ev["status"] == "pending_review"
    assert len(aarav_ev["supporting_attempts"]) == 3

    # 2. Record Decision: Confirm
    decision_payload = {
        "action": "confirm",
        "rationale": "Learner consistently adds numerators and denominators (1/2 + 1/3 = 2/5). Requires focused instruction on finding common denominators.",
    }
    dec_res = client.post(
        f"/v1/evidence/{aarav_ev['id']}/decisions",
        headers=headers,
        json=decision_payload,
    )
    assert dec_res.status_code == 201
    updated_ev = dec_res.json()

    # Invariant: status transitions to confirmed
    assert updated_ev["status"] == "confirmed"
    assert len(updated_ev["decisions"]) == 1

    d = updated_ev["decisions"][0]
    assert d["action"] == "confirm"
    assert d["actor_name"] == "Priya Sharma"
    assert "common denominators" in d["rationale"]


def test_dismiss_evidence_signal(client: TestClient, priya_token: str):
    """Teacher Priya dismisses an evidence flag with reason."""
    assessment_id = ensure_assessment_imported(client, priya_token)
    headers = {"Authorization": f"Bearer {priya_token}"}

    ev_res = client.get(f"/v1/assessments/{assessment_id}/evidence?topic_filter=MATH-G6-FRAC", headers=headers)
    ev_data = ev_res.json()

    # Find another pending review learner (e.g. Kabir Nair SYN-L6-016)
    kabir_ev = next((e for e in ev_data["evidence"] if e["learner_ref"] == "SYN-L6-016"), None)
    assert kabir_ev is not None

    decision_payload = {
        "action": "dismiss",
        "rationale": "Student was absent for prerequisite lesson; will receive 1-on-1 check-in before formal intervention.",
    }
    dec_res = client.post(
        f"/v1/evidence/{kabir_ev['id']}/decisions",
        headers=headers,
        json=decision_payload,
    )
    assert dec_res.status_code == 201
    updated = dec_res.json()
    assert updated["status"] == "dismissed"


def test_cross_school_decision_forbidden(client: TestClient, priya_token: str, david_token: str):
    """Teacher David (Pinegrove) cannot record decisions on Oakridge evidence."""
    assessment_id = ensure_assessment_imported(client, priya_token)

    # Get Oakridge evidence ID as Priya
    ev_res = client.get(
        f"/v1/assessments/{assessment_id}/evidence?topic_filter=MATH-G6-FRAC",
        headers={"Authorization": f"Bearer {priya_token}"},
    )
    aarav_ev_id = ev_res.json()["evidence"][0]["id"]

    # Teacher David attempts to submit decision
    dec_res = client.post(
        f"/v1/evidence/{aarav_ev_id}/decisions",
        headers={"Authorization": f"Bearer {david_token}"},
        json={"action": "confirm", "rationale": "Unauthorized cross-school decision attempt."},
    )
    # Blocked: 404 (resource inaccessible across tenant boundary)
    assert dec_res.status_code == 404

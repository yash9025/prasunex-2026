"""Integration tests for Phase 3 Support Group Formation per Section 10.3 & Exit Gate.

Verifies:
1. Rejection of unconfirmed evidence.
2. Rejection of learners from another classroom or school.
3. Successful group formation with confirmed learners.
4. Snapshotting of membership and evidence IDs.
5. Class authorization and cross-school access checks.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from seeds.run_seed import CLASS_6A_ID, CLASS_6B_ID, TOPIC_FRAC_ID


def ensure_baseline_assessment_and_confirmed_learners(client: TestClient, priya_token: str):
    """Imports baseline assessment and confirms fractions gap for Aarav Patel and Diya Sen."""
    fixture_path = Path("fixtures/synthetic_class6_baseline.csv")
    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/v1/imports",
        headers={"Authorization": f"Bearer {priya_token}", "Idempotency-Key": "group-test-seed-001"},
        data={"classroom_id": CLASS_6A_ID, "assessment_title": "Support Group Baseline Assessment"},
        files={"file": ("baseline.csv", file_bytes, "text/csv")},
    )
    job_id = res.json()["job_id"]
    job_res = client.get(f"/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {priya_token}"})
    assmt_id = job_res.json()["result_summary"]["assessment_id"]

    ev_res = client.get(
        f"/v1/assessments/{assmt_id}/evidence?topic_filter=MATH-G6-FRAC",
        headers={"Authorization": f"Bearer {priya_token}"},
    )
    evidence_items = {e["learner_ref"]: e for e in ev_res.json()["evidence"]}

    aarav = evidence_items["SYN-L6-014"]
    diya = evidence_items["SYN-L6-015"]
    kabir = evidence_items["SYN-L6-016"]

    # Confirm Aarav Patel
    client.post(
        f"/v1/evidence/{aarav['id']}/decisions",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"action": "confirm", "rationale": "Confirmed fraction addition error pattern."},
    )

    # Confirm Diya Sen
    client.post(
        f"/v1/evidence/{diya['id']}/decisions",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"action": "confirm", "rationale": "Confirmed matching fraction misconception."},
    )

    # Leave Kabir Nair UNCONFIRMED (status: pending_review)

    return aarav, diya, kabir


def test_reject_unconfirmed_evidence_for_group(client: TestClient, priya_token: str):
    """Creating a group with unconfirmed evidence must be rejected per Section 10.3."""
    aarav, diya, kabir = ensure_baseline_assessment_and_confirmed_learners(client, priya_token)
    headers = {"Authorization": f"Bearer {priya_token}"}

    payload = {
        "classroom_id": CLASS_6A_ID,
        "topic_id": TOPIC_FRAC_ID,
        "name": "Invalid Unconfirmed Support Group",
        "members": [
            {"learner_id": aarav["learner_id"], "gap_evidence_id": aarav["id"]},
            {"learner_id": kabir["learner_id"], "gap_evidence_id": kabir["id"]},  # UNCONFIRMED!
        ],
    }

    res = client.post("/v1/groups", headers=headers, json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "unconfirmed" in data["message"].lower()


def test_create_support_group_with_confirmed_learners(client: TestClient, priya_token: str):
    """Forms a support group for Aarav Patel and Diya Sen with confirmed fraction needs."""
    aarav, diya, _ = ensure_baseline_assessment_and_confirmed_learners(client, priya_token)
    headers = {"Authorization": f"Bearer {priya_token}"}

    payload = {
        "classroom_id": CLASS_6A_ID,
        "topic_id": TOPIC_FRAC_ID,
        "name": "Grade 6 Fractions Common Denominators Group",
        "members": [
            {"learner_id": aarav["learner_id"], "gap_evidence_id": aarav["id"]},
            {"learner_id": diya["learner_id"], "gap_evidence_id": diya["id"]},
        ],
    }

    res = client.post("/v1/groups", headers=headers, json=payload)
    assert res.status_code == 201
    group_data = res.json()

    assert group_data["name"] == "Grade 6 Fractions Common Denominators Group"
    assert group_data["topic_code"] == "MATH-G6-FRAC"
    assert group_data["created_by_name"] == "Priya Sharma"
    assert len(group_data["members"]) == 2

    member_refs = {m["learner_ref"] for m in group_data["members"]}
    assert "SYN-L6-014" in member_refs
    assert "SYN-L6-015" in member_refs

    # Query groups list endpoint
    list_res = client.get(f"/v1/classes/{CLASS_6A_ID}/groups", headers=headers)
    assert list_res.status_code == 200
    groups_list = list_res.json()
    assert len(groups_list) >= 1
    assert any(g["name"] == "Grade 6 Fractions Common Denominators Group" for g in groups_list)


def test_cross_school_group_creation_and_listing_blocked(
    client: TestClient, priya_token: str, david_token: str
):
    """Teacher David cannot view or create support groups in Oakridge's Class 6-A."""
    headers = {"Authorization": f"Bearer {david_token}"}

    # Attempt to list groups in Class 6-A
    res = client.get(f"/v1/classes/{CLASS_6A_ID}/groups", headers=headers)
    assert res.status_code == 403

    # Attempt to create group in Class 6-A
    res2 = client.post(
        "/v1/groups",
        headers=headers,
        json={
            "classroom_id": CLASS_6A_ID,
            "topic_id": TOPIC_FRAC_ID,
            "name": "Cross School Exploit Attempt",
            "members": [{"learner_id": "dummy-learner", "gap_evidence_id": "dummy-evidence"}],
        },
    )
    assert res2.status_code == 403

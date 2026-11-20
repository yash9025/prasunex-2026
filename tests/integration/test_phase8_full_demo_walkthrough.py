"""End-to-End Five-Minute Demonstration Narrative Walkthrough per Section 15.2.

Automates the complete teacher intervention lifecycle:
1. 0:00 - Resettable starting conditions (Section 15.1).
2. 0:40 - Ingest question-level CSV & inspect learning map (Section 9 & 10.1).
3. 1:30 - Inspect wrong answers, misconception pattern, and confirm evidence (Section 10.2).
4. 2:15 - Form support group with Aarav Patel and Diya Sen (Section 10.3).
5. 3:15 - Grounded support drafting, rational math verification, and SHA-256 approval (Section 11 & 12.1).
6. 4:15 - Assign, fresh quiz sitting without key leakage, 100% mastery submission, and closure (Section 12.2-12.4).
7. 5:00 - Tamper-evident audit trail and operational health diagnostics (Section 13.3).
"""

from pathlib import Path
import time
from fastapi.testclient import TestClient

from seeds.run_seed import (
    CLASS_6A_ID,
    OAKRIDGE_SCHOOL_ID,
    TEACHER_PRIYA_ID,
)


def test_full_five_minute_demonstration_narrative(client: TestClient, priya_token: str):
    """Executes the complete competition presentation narrative seamlessly."""
    headers = {
        "Authorization": f"Bearer {priya_token}",
        "X-School-ID": OAKRIDGE_SCHOOL_ID,
    }

    # =========================================================================
    # Segment 1 (0:00–0:40): Resettable Starting State (Section 15.1)
    # =========================================================================
    reset_res = client.post("/v1/demo/reset", headers=headers, json={"preload_baseline": False})
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "success"
    assert reset_data["preloaded_baseline"] is False

    # Verify classroom has zero lingering assessments
    assessments_empty = client.get(f"/v1/classes/{CLASS_6A_ID}/assessments", headers=headers)
    assert assessments_empty.status_code == 200
    assert len(assessments_empty.json()) == 0

    # =========================================================================
    # Segment 2 (0:40–1:30): CSV Ingestion & Class Learning Map (Section 9 & 10)
    # =========================================================================
    csv_path = Path("fixtures/synthetic_class6_baseline.csv").resolve()
    assert csv_path.exists()
    csv_bytes = csv_path.read_bytes()

    import_res = client.post(
        "/v1/imports",
        headers={
            "Authorization": f"Bearer {priya_token}",
            "Idempotency-Key": f"demo-e2e-{int(time.time())}",
        },
        data={
            "classroom_id": CLASS_6A_ID,
            "assessment_title": "Grade 6 Term 1 Diagnostic Baseline",
        },
        files={"file": ("synthetic_class6_baseline.csv", csv_bytes, "text/csv")},
    )
    assert import_res.status_code == 202
    import_data = import_res.json()
    assert import_data["status"] == "succeeded"
    job_id = import_data["job_id"]

    # Retrieve completed job details
    job_res = client.get(f"/v1/jobs/{job_id}", headers=headers)
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["status"] == "succeeded"
    assessment_id = job_data["result_summary"]["assessment_id"]
    assert assessment_id is not None

    # Inspect class learning map evidence
    ev_res = client.get(f"/v1/assessments/{assessment_id}/evidence", headers=headers)
    assert ev_res.status_code == 200
    all_evidence = ev_res.json()["evidence"]
    assert len(all_evidence) > 0

    # =========================================================================
    # Segment 3 (1:30–2:15): Explainable Evidence & Misconception Confirmation
    # =========================================================================
    # Find Aarav Patel's fractions evidence
    aarav_ev = next(
        e for e in all_evidence
        if e["learner_ref"] == "SYN-L6-014" and e["topic_code"] == "MATH-G6-FRAC"
    )
    assert float(aarav_ev["awarded_marks"]) == 1.0
    assert float(aarav_ev["possible_marks"]) == 3.0
    assert aarav_ev["status"] == "pending_review"
    assert len(aarav_ev["supporting_attempts"]) == 3
    assert any(a["raw_response"] == "2/5" for a in aarav_ev["supporting_attempts"])

    # Priya records pedagogical confirmation
    confirm_res = client.post(
        f"/v1/evidence/{aarav_ev['id']}/decisions",
        headers=headers,
        json={
            "action": "confirm",
            "rationale": "Confirmed misconception adding across numerators and denominators.",
        },
    )
    assert confirm_res.status_code == 201
    assert confirm_res.json()["status"] == "confirmed"

    # Also confirm Diya Sen's fractions evidence
    diya_ev = next(
        e for e in all_evidence
        if e["learner_ref"] == "SYN-L6-015" and e["topic_code"] == "MATH-G6-FRAC"
    )
    diya_confirm_res = client.post(
        f"/v1/evidence/{diya_ev['id']}/decisions",
        headers=headers,
        json={
            "action": "confirm",
            "rationale": "Confirmed fraction addition denominator error pattern.",
        },
    )
    assert diya_confirm_res.status_code == 201

    # =========================================================================
    # Segment 4 (2:15–3:15): Support Group Formation
    # =========================================================================
    group_res = client.post(
        "/v1/groups",
        headers=headers,
        json={
            "classroom_id": CLASS_6A_ID,
            "topic_id": aarav_ev["topic_id"],
            "name": "Grade 6 Fractions Common Denominators Support",
            "members": [
                {"learner_id": aarav_ev["learner_id"], "gap_evidence_id": aarav_ev["id"]},
                {"learner_id": diya_ev["learner_id"], "gap_evidence_id": diya_ev["id"]},
            ],
        },
    )
    assert group_res.status_code == 201
    group = group_res.json()
    group_id = group["id"]
    assert len(group["members"]) == 2

    # =========================================================================
    # Segment 5 (3:15–4:15): Grounded Support Drafting & SHA-256 Approval
    # =========================================================================
    # Generate draft using NCTM fractions snippet
    draft_res = client.post(
        "/v1/plans/drafts",
        headers=headers,
        json={
            "support_group_id": group_id,
            "source_snippet_ids": ["snip-frac-001"],
            "generation_mode": "template",
        },
    )
    assert draft_res.status_code == 201
    plan = draft_res.json()
    plan_id = plan["id"]
    active_version = plan["current_version"]
    assert active_version["version_num"] == 1
    assert len(active_version["practice_items"]) == 3

    # Teacher Priya edits rationale and verifies math
    patch_res = client.patch(
        f"/v1/plans/{plan_id}/draft",
        headers=headers,
        json={
            "revision": plan["revision"],
            "explanation": "Focused visual area model review for fractions with unlike denominators.",
            "practice_items": active_version["practice_items"],
        },
    )
    assert patch_res.status_code == 200
    patched_plan = patch_res.json()
    patched_version = patched_plan["current_version"]
    assert patched_version["version_num"] == 2

    # Teacher Priya approves and signs off plan version 2
    approve_res = client.post(
        f"/v1/plans/{plan_id}/approve",
        headers=headers,
        json={
            "revision": patched_plan["revision"],
            "sign_off_responsibility": True,
        },
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["approval_hash"] is not None
    assert len(approved_data["approval_hash"]) == 64

    # =========================================================================
    # Segment 6 (4:15–5:00): Assignment, Fresh Reassessment Quiz & Plan Closure
    # =========================================================================
    # Distribute assignment
    assign_res = client.post(
        f"/v1/plans/{plan_id}/assign",
        headers=headers,
        json={"plan_version_id": patched_version["id"]},
    )
    assert assign_res.status_code == 201
    assignment = assign_res.json()
    assert assignment["status"] == "active"
    assert len(assignment["recipients"]) == 2

    # Find Aarav Patel's recipient ID
    aarav_recipient = next(
        r for r in assignment["recipients"] if r["learner_ref"] == "SYN-L6-014"
    )

    # Deliver quiz: verify answers keys are withheld
    quiz_res = client.get(
        f"/v1/reassessments/quiz/{aarav_recipient['id']}",
        headers=headers,
    )
    assert quiz_res.status_code == 200
    quiz = quiz_res.json()
    assert len(quiz["questions"]) == 3
    # Server-side key protection check
    for q in quiz["questions"]:
        assert "expected_answer" not in q
        assert "rationale" not in q

    # Aarav submits correct rational answers: Q-RE-FRAC-01 (1/4+1/3=7/12), Q-RE-FRAC-02 (2/3+1/6=5/6), Q-RE-FRAC-03 (3/8+1/4=5/8)
    submit_res = client.post(
        f"/v1/reassessments/quiz/{aarav_recipient['id']}/submit",
        headers=headers,
        json={
            "submission_key": f"aarav-sub-{int(time.time())}",
            "answers": [
                {"question_ref": "Q-RE-FRAC-01", "raw_response": "7/12"},
                {"question_ref": "Q-RE-FRAC-02", "raw_response": "5/6"},
                {"question_ref": "Q-RE-FRAC-03", "raw_response": "5/8"},
            ],
        },
    )
    assert submit_res.status_code == 200
    result = submit_res.json()
    assert float(result["awarded_marks"]) == 3.0
    assert float(result["possible_marks"]) == 3.0
    assert result["mastery_achieved"] is True

    # Priya reviews comparative progress report
    progress_res = client.get(f"/v1/plans/{plan_id}/progress", headers=headers)
    assert progress_res.status_code == 200
    report = progress_res.json()
    aarav_prog = next(l for l in report["learners"] if l["learner_ref"] == "SYN-L6-014")
    assert float(aarav_prog["baseline_awarded"]) == 1.0
    assert float(aarav_prog["reassessment_awarded"]) == 3.0
    assert float(aarav_prog["reassessment_percentage"]) == 100.0

    # Priya records closing rationale
    close_res = client.post(
        f"/v1/plans/{plan_id}/close",
        headers=headers,
        json={
            "action": "close",
            "rationale": "Learner demonstrated 100% mastery on fresh unlike denominator fraction items. Misconception resolved.",
        },
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"

    # =========================================================================
    # Segment 7: Audit Traceability & Operational Health Visibility
    # =========================================================================
    audit_res = client.get("/v1/audit/events", headers=headers)
    assert audit_res.status_code == 200
    audit_events = audit_res.json()["events"]
    assert len(audit_events) >= 5
    actions = [e["action"] for e in audit_events]
    assert "demo_environment_reset" in actions
    assert "EVIDENCE_DECISION_RECORDED" in actions
    assert "DRAFT_CREATED" in actions
    assert "PLAN_APPROVED" in actions
    assert "ASSIGNMENT_CREATED" in actions
    assert "REASSESSMENT_SUBMITTED" in actions
    assert "PLAN_CLOSE" in actions

    # System Health check
    health_res = client.get("/health/system")
    assert health_res.status_code == 200
    health = health_res.json()
    assert health["status"] == "healthy"
    assert health["database"]["status"] == "connected"
    assert health["database"]["ping_latency_ms"] < 50.0

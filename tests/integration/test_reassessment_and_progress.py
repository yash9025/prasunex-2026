"""Integration tests for Phase 5 Assignment, Reassessment, and Progress Review.

Verifies the complete closed-loop classroom intervention journey:
1. Rejection of unapproved plan assignment (Exit Gate requirement).
2. Assignment creation with recipient records and initial reassessment states.
3. Server-side key protection: Quiz endpoint omits all answer keys.
4. Submission scoring via ExactAnswerChecker and idempotency replay protection.
5. Double-submission prevention (409 Conflict).
6. Cohort progress reporting comparing baseline topic evidence with fresh reassessment.
7. Explicit teacher closure with observation rationale.
8. Strict cross-school tenant isolation across all Phase 5 endpoints.
"""

from fastapi.testclient import TestClient

from seeds.run_seed import CLASS_6A_ID, TOPIC_FRAC_ID
from tests.integration.test_support_groups import ensure_baseline_assessment_and_confirmed_learners


def _create_approved_plan(client: TestClient, priya_token: str) -> dict:
    """Helper creating a support group, grounded draft, and teacher-approved version."""
    aarav, diya, _ = ensure_baseline_assessment_and_confirmed_learners(client, priya_token)

    # 1. Create support group
    grp_res = client.post(
        "/v1/groups",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "classroom_id": CLASS_6A_ID,
            "topic_id": TOPIC_FRAC_ID,
            "name": "Phase 5 Fractions Reassessment Cohort",
            "members": [
                {"learner_id": aarav["learner_id"], "gap_evidence_id": aarav["id"]},
                {"learner_id": diya["learner_id"], "gap_evidence_id": diya["id"]},
            ],
        },
    )
    assert grp_res.status_code == 201
    group = grp_res.json()

    # 2. Generate draft
    draft_res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "support_group_id": group["id"],
            "source_snippet_ids": ["snip-frac-001", "snip-frac-002"],
            "generation_mode": "auto",
        },
    )
    assert draft_res.status_code == 201
    plan = draft_res.json()

    # 3. Approve draft
    appr_res = client.post(
        f"/v1/plans/{plan['id']}/approve",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "revision": plan["revision"],
            "sign_off_responsibility": True,
        },
    )
    assert appr_res.status_code == 200

    # Reload plan
    reloaded = client.get(f"/v1/plans/{plan['id']}", headers={"Authorization": f"Bearer {priya_token}"})
    return reloaded.json()


def test_assign_unapproved_plan_rejected(client: TestClient, priya_token: str):
    aarav, diya, _ = ensure_baseline_assessment_and_confirmed_learners(client, priya_token)
    grp_res = client.post(
        "/v1/groups",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "classroom_id": CLASS_6A_ID,
            "topic_id": TOPIC_FRAC_ID,
            "name": "Unapproved Assignment Test Group",
            "members": [
                {"learner_id": aarav["learner_id"], "gap_evidence_id": aarav["id"]},
            ],
        },
    )
    group = grp_res.json()

    draft_res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"support_group_id": group["id"], "source_snippet_ids": ["snip-frac-001"]},
    )
    unapproved_plan = draft_res.json()
    version_id = unapproved_plan["current_version"]["id"]

    # Attempt assignment without approving
    assign_res = client.post(
        f"/v1/plans/{unapproved_plan['id']}/assign",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"plan_version_id": version_id},
    )
    assert assign_res.status_code == 422
    assert "must be approved by teacher first" in assign_res.json()["message"]


def test_complete_phase5_intervention_cycle(client: TestClient, priya_token: str, david_token: str):
    # 1. Setup approved plan
    plan = _create_approved_plan(client, priya_token)
    plan_id = plan["id"]
    version_id = plan["current_version"]["id"]
    assert plan["status"] == "reviewed"

    # 2. Assign intervention to learners
    assign_res = client.post(
        f"/v1/plans/{plan_id}/assign",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"plan_version_id": version_id},
    )
    assert assign_res.status_code == 201
    assignment = assign_res.json()
    assert assignment["status"] == "active"
    assert len(assignment["recipients"]) == 2

    aarav_recipient = next(r for r in assignment["recipients"] if "Aarav" in r["learner_name"])
    diya_recipient = next(r for r in assignment["recipients"] if "Diya" in r["learner_name"])

    # 3. Retrieve fresh reassessment quiz (Server-side key protection check)
    quiz_res = client.get(
        f"/v1/reassessments/quiz/{aarav_recipient['id']}",
        headers={"Authorization": f"Bearer {priya_token}"},
    )
    assert quiz_res.status_code == 200
    quiz_data = quiz_res.json()
    assert len(quiz_data["questions"]) == 3

    # CRITICAL: Verify NO answers or keys are exposed to the quiz client
    for q in quiz_data["questions"]:
        assert "expected_answer" not in q
        assert "rationale" not in q
        assert "7/12" not in q["question_text"]  # Key not leaked in prompt

    # 4. Aarav Patel submits quiz with mastered answers
    aarav_sub_res = client.post(
        f"/v1/reassessments/quiz/{aarav_recipient['id']}/submit",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "submission_key": "sub-aarav-test-001",
            "answers": [
                {"question_ref": "Q-RE-FRAC-01", "raw_response": "7/12"},  # 1/4 + 1/3 = 7/12
                {"question_ref": "Q-RE-FRAC-02", "raw_response": "5/6"},   # 2/3 + 1/6 = 5/6
                {"question_ref": "Q-RE-FRAC-03", "raw_response": "5/8"},   # 3/8 + 1/4 = 5/8
            ],
        },
    )
    assert aarav_sub_res.status_code == 200
    aarav_result = aarav_sub_res.json()
    assert aarav_result["awarded_marks"] == 3.0
    assert aarav_result["possible_marks"] == 3.0
    assert aarav_result["percentage"] == 100.0
    assert aarav_result["mastery_achieved"] is True

    # 5. Idempotent replay with same submission key
    replay_res = client.post(
        f"/v1/reassessments/quiz/{aarav_recipient['id']}/submit",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "submission_key": "sub-aarav-test-001",
            "answers": [
                {"question_ref": "Q-RE-FRAC-01", "raw_response": "7/12"},
            ],
        },
    )
    assert replay_res.status_code == 200
    assert replay_res.json()["awarded_marks"] == 3.0

    # 6. Double submission with new key without authorization is blocked (409)
    double_sub = client.post(
        f"/v1/reassessments/quiz/{aarav_recipient['id']}/submit",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "submission_key": "sub-aarav-test-002",
            "answers": [{"question_ref": "Q-RE-FRAC-01", "raw_response": "7/12"}],
        },
    )
    assert double_sub.status_code == 409
    assert "already been completed" in double_sub.json()["message"]

    # 7. Diya Sen submits quiz
    diya_sub_res = client.post(
        f"/v1/reassessments/quiz/{diya_recipient['id']}/submit",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "submission_key": "sub-diya-test-001",
            "answers": [
                {"question_ref": "Q-RE-FRAC-01", "raw_response": "7/12"},
                {"question_ref": "Q-RE-FRAC-02", "raw_response": "5/6"},
                {"question_ref": "Q-RE-FRAC-03", "raw_response": "5/8"},
            ],
        },
    )
    assert diya_sub_res.status_code == 200
    assert diya_sub_res.json()["mastery_achieved"] is True

    # 8. Check Progress Review endpoint (Pre vs Post comparison)
    prog_res = client.get(
        f"/v1/plans/{plan_id}/progress",
        headers={"Authorization": f"Bearer {priya_token}"},
    )
    assert prog_res.status_code == 200
    progress = prog_res.json()
    assert progress["all_completed"] is True
    assert progress["completed_count"] == 2
    assert progress["total_learners"] == 2

    aarav_prog = next(p for p in progress["learners"] if "Aarav" in p["learner_name"])
    # Aarav started at 1/3 (33.33%) and improved to 3/3 (100%)
    assert aarav_prog["baseline_awarded"] == 1.0
    assert aarav_prog["baseline_possible"] == 3.0
    assert aarav_prog["reassessment_awarded"] == 3.0
    assert aarav_prog["reassessment_possible"] == 3.0
    assert aarav_prog["reassessment_percentage"] == 100.0

    # 9. Teacher reviews progress and closes the intervention
    close_res = client.post(
        f"/v1/plans/{plan_id}/close",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={
            "action": "close",
            "rationale": "Learners Aarav Patel and Diya Sen demonstrated 100% mastery on fresh fraction addition items. Misconception resolved.",
        },
    )
    assert close_res.status_code == 200
    close_data = close_res.json()
    assert close_data["status"] == "closed"
    assert close_data["action_taken"] == "close"

    # Verify plan status in database
    final_plan = client.get(f"/v1/plans/{plan_id}", headers={"Authorization": f"Bearer {priya_token}"}).json()
    assert final_plan["status"] == "closed"

    # 10. Cross-school isolation check: David Chen cannot access Oakridge progress or quiz
    david_prog = client.get(f"/v1/plans/{plan_id}/progress", headers={"Authorization": f"Bearer {david_token}"})
    assert david_prog.status_code in [403, 404]

    david_quiz = client.get(f"/v1/reassessments/quiz/{aarav_recipient['id']}", headers={"Authorization": f"Bearer {david_token}"})
    assert david_quiz.status_code in [403, 404]

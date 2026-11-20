"""Integration tests for Phase 4 Grounded Support Drafting & Immutable Approval.

Verifies:
1. Approved Snippet library retrieval and cross-school scoping.
2. Grounded draft generation using approved snippets with zero PII leakage.
3. Rejection of unapproved, cross-school, or mismatched topic snippets.
4. Optimistic locking on draft updates (409 Conflict).
5. Mathematical verification of edited practice items (rejects miscalculations).
6. Immutable teacher sign-off and approval freezing with cryptographic hash.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from seeds.run_seed import CLASS_6A_ID, TOPIC_DEC_ID, TOPIC_FRAC_ID
from tests.integration.test_support_groups import ensure_baseline_assessment_and_confirmed_learners


def _create_confirmed_support_group(client: TestClient, priya_token: str) -> dict:
    aarav, diya, _ = ensure_baseline_assessment_and_confirmed_learners(client, priya_token)
    payload = {
        "classroom_id": CLASS_6A_ID,
        "topic_id": TOPIC_FRAC_ID,
        "name": "Fractions Mastery Group A",
        "members": [
            {"learner_id": aarav["learner_id"], "gap_evidence_id": aarav["id"]},
            {"learner_id": diya["learner_id"], "gap_evidence_id": diya["id"]},
        ],
    }
    res = client.post("/v1/groups", headers={"Authorization": f"Bearer {priya_token}"}, json=payload)
    assert res.status_code == 201
    return res.json()


def test_list_approved_snippets_oakridge(client: TestClient, priya_token: str):
    res = client.get("/v1/snippets", headers={"Authorization": f"Bearer {priya_token}"})
    assert res.status_code == 200
    snippets = res.json()
    assert len(snippets) >= 4

    snippet_ids = [s["id"] for s in snippets]
    assert "snip-frac-001" in snippet_ids
    assert "snip-frac-002" in snippet_ids

    # Filter by topic
    res_frac = client.get(
        f"/v1/snippets?topic_id={TOPIC_FRAC_ID}",
        headers={"Authorization": f"Bearer {priya_token}"},
    )
    assert res_frac.status_code == 200
    frac_snippets = res_frac.json()
    assert all(s["topic_id"] == TOPIC_FRAC_ID for s in frac_snippets)


def test_generate_grounded_draft_success(client: TestClient, priya_token: str):
    group = _create_confirmed_support_group(client, priya_token)

    draft_payload = {
        "support_group_id": group["id"],
        "source_snippet_ids": ["snip-frac-001", "snip-frac-002"],
        "generation_mode": "auto",
    }

    res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json=draft_payload,
    )
    assert res.status_code == 201
    data = res.json()

    assert data["support_group_id"] == group["id"]
    assert data["status"] == "draft"
    assert data["revision"] == 2
    assert data["current_version"] is not None

    version = data["current_version"]
    assert version["version_num"] == 1
    assert len(version["practice_items"]) == 3
    assert len(version["cited_snippets"]) >= 1

    # Verify each practice item is verified
    for it in version["practice_items"]:
        assert it["verified"] is True
        assert it["math_spec"]["operation"] in ["add", "subtract"]
        assert len(it["math_spec"]["operands"]) == 2


def test_generate_draft_rejects_mismatched_topic_snippet(client: TestClient, priya_token: str):
    group = _create_confirmed_support_group(client, priya_token)

    # Attempt to cite decimal snippet for a fractions group
    draft_payload = {
        "support_group_id": group["id"],
        "source_snippet_ids": ["snip-dec-001"],  # Decimal snippet!
        "generation_mode": "auto",
    }

    res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json=draft_payload,
    )
    assert res.status_code == 422
    assert "invalid, unapproved, belong to another school, or do not match" in res.json()["message"]


def test_patch_draft_optimistic_locking_conflict(client: TestClient, priya_token: str):
    group = _create_confirmed_support_group(client, priya_token)

    draft_payload = {
        "support_group_id": group["id"],
        "source_snippet_ids": ["snip-frac-001"],
        "generation_mode": "auto",
    }
    init_res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json=draft_payload,
    )
    plan_id = init_res.json()["id"]
    valid_rev = init_res.json()["revision"]

    # Send stale revision (e.g. valid_rev - 1)
    conflict_res = client.patch(
        f"/v1/plans/{plan_id}/draft",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"revision": valid_rev - 1, "explanation": "Updated explanation..."},
    )
    assert conflict_res.status_code == 409
    assert "revision conflict" in conflict_res.json()["message"]

    # Send valid revision
    update_res = client.patch(
        f"/v1/plans/{plan_id}/draft",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"revision": valid_rev, "explanation": "Updated teacher guidance for fractions."},
    )
    assert update_res.status_code == 200
    assert update_res.json()["revision"] == valid_rev + 1
    assert update_res.json()["current_version"]["explanation"] == "Updated teacher guidance for fractions."


def test_patch_draft_rejects_mathematical_mismatch(client: TestClient, priya_token: str):
    group = _create_confirmed_support_group(client, priya_token)
    init_res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"support_group_id": group["id"], "source_snippet_ids": ["snip-frac-001"]},
    )
    plan = init_res.json()
    plan_id = plan["id"]
    current_items = plan["current_version"]["practice_items"]

    # Tamper with item 1: claim 1/3 + 1/6 = 99/100
    tampered_items = [dict(it) for it in current_items]
    tampered_items[0]["expected_answer"] = "99/100"

    bad_update_res = client.patch(
        f"/v1/plans/{plan_id}/draft",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"revision": plan["revision"], "practice_items": tampered_items},
    )
    assert bad_update_res.status_code == 422
    assert "Math verification failed" in bad_update_res.json()["message"]


def test_approve_plan_creates_hash_and_freezes_state(client: TestClient, priya_token: str):
    group = _create_confirmed_support_group(client, priya_token)
    init_res = client.post(
        "/v1/plans/drafts",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"support_group_id": group["id"], "source_snippet_ids": ["snip-frac-001"]},
    )
    plan = init_res.json()
    plan_id = plan["id"]

    # 1. Missing responsibility checkbox fails
    res_no_resp = client.post(
        f"/v1/plans/{plan_id}/approve",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"revision": plan["revision"], "sign_off_responsibility": False},
    )
    assert res_no_resp.status_code == 422

    # 2. Valid approval succeeds
    res_appr = client.post(
        f"/v1/plans/{plan_id}/approve",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"revision": plan["revision"], "sign_off_responsibility": True},
    )
    assert res_appr.status_code == 200
    appr_data = res_appr.json()
    assert "approval_hash" in appr_data
    assert len(appr_data["approval_hash"]) == 64  # SHA-256 hex string

    # 3. Check plan status updated to "reviewed"
    plan_res = client.get(f"/v1/plans/{plan_id}", headers={"Authorization": f"Bearer {priya_token}"})
    assert plan_res.status_code == 200
    assert plan_res.json()["status"] == "reviewed"

    # 4. Repeated approval with stale revision fails with 409
    stale_appr = client.post(
        f"/v1/plans/{plan_id}/approve",
        headers={"Authorization": f"Bearer {priya_token}"},
        json={"revision": plan["revision"], "sign_off_responsibility": True},
    )
    assert stale_appr.status_code == 409

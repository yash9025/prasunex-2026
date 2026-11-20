"""Integration tests for Classroom and Learner endpoints."""

from fastapi.testclient import TestClient
from seeds.run_seed import CLASS_6A_ID


def test_list_classes_scoped_to_teacher(client: TestClient, priya_token: str):
    headers = {"Authorization": f"Bearer {priya_token}"}
    response = client.get("/v1/classes", headers=headers)
    assert response.status_code == 200
    classes = response.json()

    assert len(classes) == 1
    c = classes[0]
    assert c["id"] == CLASS_6A_ID
    assert c["name"] == "Grade 6 Mathematics"
    assert c["section"] == "A"
    assert c["learner_count"] == 40


def test_get_classroom_detail_with_40_learners(client: TestClient, priya_token: str):
    headers = {"Authorization": f"Bearer {priya_token}"}
    response = client.get(f"/v1/classes/{CLASS_6A_ID}", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == CLASS_6A_ID
    assert len(data["learners"]) == 40

    # Verify primary synthetic demo learner (Aarav Patel - SYN-L6-014) is present
    learner_map = {l["external_ref"]: l for l in data["learners"]}
    assert "SYN-L6-014" in learner_map
    aarav = learner_map["SYN-L6-014"]
    assert aarav["first_name"] == "Aarav"
    assert aarav["last_name"] == "Patel"
    assert aarav["is_synthetic"] is True


def test_class_overview_endpoint(client: TestClient, priya_token: str):
    headers = {"Authorization": f"Bearer {priya_token}"}
    response = client.get(f"/v1/classes/{CLASS_6A_ID}/overview", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_learners"] == 40
    assert data["synthetic_count"] == 40

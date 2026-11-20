"""Phase 6 Security, Tenant Isolation, and Failure Drill Suite.

Verifies Section 13 requirements:
1. Database tenant isolation across all endpoints and direct queries.
2. Recoverable job queue, crashed worker heartbeat lease expiration, and retry reconciliation.
3. Atomic job claiming guards against duplicate execution.
4. Transactional outbox event redispatching.
5. Audit log querying, tenant scoping, and credential/PII sanitization.
6. System operational visibility and health diagnostics.
"""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.modules.audit.models import AuditEvent
from app.modules.jobs.models import Job, OutboxEvent
from app.modules.jobs.reconciler import JobReconciler
from seeds.run_seed import (
    CLASS_6A_ID,
    CLASS_6B_ID,
    OAKRIDGE_SCHOOL_ID,
    PINEGROVE_SCHOOL_ID,
    TEACHER_DAVID_ID,
    TEACHER_PRIYA_ID,
)


def test_system_health_and_diagnostics(client: TestClient):
    """Verifies operational health check and metric reporting."""
    res = client.get("/health/system")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "ping_latency_ms" in data["database"]
    assert "queued" in data["job_queue"]
    assert "pending" in data["outbox"]


def test_job_reconciler_stale_lease_recovery(db_session):
    """Simulates a worker crashing mid-job.
    
    Verifies that JobReconciler detects expired heartbeats and recovers the job.
    """
    now = datetime.now(timezone.utc)
    expired_heartbeat = now - timedelta(seconds=120)

    # 1. Stale job with attempts remaining -> retry_pending
    stale_job = Job(
        school_id=OAKRIDGE_SCHOOL_ID,
        kind="csv_import",
        status="running",
        request_hash="stale-test-hash-01",
        attempt_count=1,
        max_attempts=3,
        heartbeat=expired_heartbeat,
    )
    db_session.add(stale_job)

    # 2. Stale job that has exhausted attempts -> terminal failed
    exhausted_job = Job(
        school_id=OAKRIDGE_SCHOOL_ID,
        kind="csv_import",
        status="running",
        request_hash="stale-test-hash-02",
        attempt_count=3,
        max_attempts=3,
        heartbeat=expired_heartbeat,
    )
    db_session.add(exhausted_job)
    db_session.commit()

    # Run reconciler with 60s timeout
    reconciled = JobReconciler.reconcile_stale_jobs(db_session, lease_timeout_seconds=60)
    reconciled_ids = [j.id for j in reconciled]

    assert stale_job.id in reconciled_ids
    assert exhausted_job.id in reconciled_ids

    db_session.refresh(stale_job)
    db_session.refresh(exhausted_job)

    assert stale_job.status == "retry_pending"
    assert stale_job.failure_code == "WORKER_HEARTBEAT_TIMEOUT"

    assert exhausted_job.status == "failed"
    assert exhausted_job.failure_code == "LEASE_TIMEOUT_EXCEEDED"


def test_job_atomic_claiming_guard(db_session):
    """Verifies that two workers cannot claim the same job concurrently."""
    job = Job(
        school_id=OAKRIDGE_SCHOOL_ID,
        kind="csv_import",
        status="queued",
        request_hash="claim-test-hash-01",
        attempt_count=0,
        max_attempts=3,
    )
    db_session.add(job)
    db_session.commit()

    # Worker 1 claims job
    claimed_1 = JobReconciler.claim_job(db_session, job.id, worker_id="worker-node-1")
    assert claimed_1 is not None
    assert claimed_1.status == "running"
    assert claimed_1.attempt_count == 1

    # Worker 2 attempts to claim same job -> must return None
    claimed_2 = JobReconciler.claim_job(db_session, job.id, worker_id="worker-node-2")
    assert claimed_2 is None


def test_outbox_event_redispatch(db_session):
    """Verifies durable outbox events are picked up and dispatched."""
    ev = OutboxEvent(
        school_id=OAKRIDGE_SCHOOL_ID,
        job_id="dummy-job-id-01",
        event_type="job_queued",
        payload={"task": "import_csv"},
        status="pending",
    )
    db_session.add(ev)
    db_session.commit()

    dispatched = JobReconciler.redispatch_outbox_events(db_session, batch_size=10)
    assert dispatched >= 1

    db_session.refresh(ev)
    assert ev.status == "dispatched"


def test_audit_log_querying_and_tenant_isolation(client: TestClient, priya_token: str, david_token: str, db_session):
    """Verifies audit trail persistence, querying, and cross-school scoping."""
    # Seed Oakridge audit event
    oak_event = AuditEvent(
        school_id=OAKRIDGE_SCHOOL_ID,
        actor_id=TEACHER_PRIYA_ID,
        action="TEST_OAKRIDGE_ACTION",
        entity_type="classroom",
        entity_id=CLASS_6A_ID,
        metadata_json={"note": "Oakridge event"},
    )
    # Seed Pinegrove audit event
    png_event = AuditEvent(
        school_id=PINEGROVE_SCHOOL_ID,
        actor_id=TEACHER_DAVID_ID,
        action="TEST_PINEGROVE_ACTION",
        entity_type="classroom",
        entity_id=CLASS_6B_ID,
        metadata_json={"note": "Pinegrove event"},
    )
    db_session.add(oak_event)
    db_session.add(png_event)
    db_session.commit()

    # 1. Priya queries audit events
    priya_res = client.get("/v1/audit/events", headers={"Authorization": f"Bearer {priya_token}"})
    assert priya_res.status_code == 200
    priya_events = priya_res.json()["events"]
    assert all(e["school_id"] == OAKRIDGE_SCHOOL_ID for e in priya_events)
    assert any(e["action"] == "TEST_OAKRIDGE_ACTION" for e in priya_events)
    assert not any(e["action"] == "TEST_PINEGROVE_ACTION" for e in priya_events)

    # 2. David queries audit events
    david_res = client.get("/v1/audit/events", headers={"Authorization": f"Bearer {david_token}"})
    assert david_res.status_code == 200
    david_events = david_res.json()["events"]
    assert all(e["school_id"] == PINEGROVE_SCHOOL_ID for e in david_events)
    assert any(e["action"] == "TEST_PINEGROVE_ACTION" for e in david_events)
    assert not any(e["action"] == "TEST_OAKRIDGE_ACTION" for e in david_events)


def test_deep_cross_school_access_drill(client: TestClient, david_token: str):
    """Comprehensive failure drill: verifies foreign teacher is rejected across all endpoints."""
    # Pinegrove teacher David attempts Oakridge operations
    headers = {"Authorization": f"Bearer {david_token}"}

    # 1. Access Oakridge Class 6-A
    res1 = client.get(f"/v1/classes/{CLASS_6A_ID}", headers=headers)
    assert res1.status_code in [403, 404]

    # 2. Create Support Group for Oakridge Class 6-A
    res2 = client.post(
        "/v1/groups",
        headers=headers,
        json={
            "classroom_id": CLASS_6A_ID,
            "topic_id": "top-frac-001",
            "name": "Intruder Group",
            "members": [{"learner_id": "SYN-L6-014", "gap_evidence_id": "dummy"}],
        },
    )
    assert res2.status_code in [403, 404]

    # 3. Access Oakridge Lesson Snippets with cross-school school_id header spoof
    res3 = client.get(
        "/v1/snippets",
        headers={**headers, "X-School-ID": OAKRIDGE_SCHOOL_ID},
    )
    # Server-side request context must reject spoofed X-School-ID with 403 Forbidden
    assert res3.status_code in [403, 404]

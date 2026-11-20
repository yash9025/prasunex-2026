"""Recoverable job management and transactional outbox dispatcher per Section 13.2.

Provides:
1. Atomic job claiming with status guards.
2. Heartbeat tracking to detect crashed or stalled workers.
3. Automated stale job reconciliation (marks for retry or terminal failure).
4. Durable transactional outbox redispatching.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.modules.jobs.models import Job, OutboxEvent

logger = logging.getLogger(__name__)


class JobReconciler:
    """Manages worker job lifecycle, leases, and failure recovery."""

    @classmethod
    def claim_job(
        cls,
        db: Session,
        job_id: str,
        worker_id: str,
    ) -> Optional[Job]:
        """Atomically claims a queued or retry_pending job for execution.
        
        Guarantees that two concurrent workers cannot claim the same job.
        """
        job = (
            db.query(Job)
            .filter(
                Job.id == job_id,
                Job.status.in_(["queued", "retry_pending"]),
            )
            .with_for_update()
            .first()
        )
        if not job:
            return None

        now = datetime.now(timezone.utc)
        job.status = "running"
        job.attempt_count += 1
        job.heartbeat = now
        job.updated_at = now
        db.commit()
        db.refresh(job)
        return job

    @classmethod
    def update_heartbeat(cls, db: Session, job_id: str) -> bool:
        """Updates the running heartbeat for an active worker execution."""
        job = db.query(Job).filter(Job.id == job_id, Job.status == "running").first()
        if not job:
            return False
        job.heartbeat = datetime.now(timezone.utc)
        db.commit()
        return True

    @classmethod
    def reconcile_stale_jobs(
        cls,
        db: Session,
        lease_timeout_seconds: int = 60,
    ) -> List[Job]:
        """Detects crashed or stalled jobs whose heartbeats have expired.
        
        Transitions jobs to 'retry_pending' if attempts remain, or 'failed'
        if max_attempts has been reached.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=lease_timeout_seconds)

        stale_jobs = (
            db.query(Job)
            .filter(
                Job.status == "running",
                (Job.heartbeat < cutoff) | (Job.heartbeat.is_(None)),
            )
            .all()
        )

        reconciled = []
        for job in stale_jobs:
            if job.attempt_count < job.max_attempts:
                job.status = "retry_pending"
                job.failure_code = "WORKER_HEARTBEAT_TIMEOUT"
                job.failure_message = f"Worker heartbeat timed out after {lease_timeout_seconds}s. Scheduled for retry."
                logger.warning(f"Reconciled crashed job {job.id}: marked retry_pending (attempt {job.attempt_count}/{job.max_attempts})")
            else:
                job.status = "failed"
                job.failure_code = "LEASE_TIMEOUT_EXCEEDED"
                job.failure_message = f"Job failed: exceeded max attempts ({job.max_attempts}) and worker heartbeat timed out."
                logger.error(f"Reconciled dead job {job.id}: marked terminal failed.")

            job.updated_at = now
            reconciled.append(job)

        db.commit()
        return reconciled

    @classmethod
    def redispatch_outbox_events(cls, db: Session, batch_size: int = 50) -> int:
        """Pulls pending outbox events and marks them dispatched."""
        pending_events = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "pending")
            .limit(batch_size)
            .all()
        )

        dispatched_count = 0
        now = datetime.now(timezone.utc)
        for ev in pending_events:
            ev.status = "dispatched"
            ev.updated_at = now
            dispatched_count += 1

        db.commit()
        return dispatched_count

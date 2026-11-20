# LearningBridge — Operational Rollback Procedures

> **Specification Standard:** Section 14.3 (Rollback Steps & Disaster Recovery)  
> **Target Release:** v0.1.0-prod  
> **Objective:** Zero data loss, bounded recovery time (< 5 minutes), strict tenant safety.

---

## 1. Quick Emergency Rollback (Container Image Revert)

If an issue is detected immediately post-deployment:

```bash
# 1. Stop current containers
docker compose -f infra/docker-compose.yml down

# 2. Revert to the previous known-good Git commit / release tag
git checkout tags/v0.1.0-pre-release

# 3. Start containers using previous verified build
docker compose -f infra/docker-compose.yml up --build -d
```

---

## 2. Database Migration Rollback

If the incident involves an unverified schema migration:

### Step 1: Check Current Revision
```bash
docker compose -f infra/docker-compose.yml exec backend alembic current
```

### Step 2: Rollback Exactly One Revision
```bash
docker compose -f infra/docker-compose.yml exec backend alembic downgrade -1
```

### Step 3: Verify Integrity
```bash
docker compose -f infra/docker-compose.yml exec backend python -c "
from app.core.database import SessionLocal
from sqlalchemy import text
with SessionLocal() as db:
    res = db.execute(text('SELECT count(*) FROM schools;')).scalar()
    print('Schools verified:', res)
"
```

---

## 3. Disaster Snapshot Recovery (Point-in-Time Restore)

If data corruption occurred or a critical failure corrupts tenant records:

### Step 1: Identify Latest Verified Backup
List available verified snapshots in the backup registry:
```bash
ls -lt backups/
```

### Step 2: Verify Backup Checksum
```bash
# Verify SHA-256 checksum matches the generation record
sha256sum backups/learningbridge_backup_<TIMESTAMP>.db
```

### Step 3: Execute Verified Restore
Run the automated verification and restore engine:
```bash
python backend/scripts/backup_restore.py
```

For SQLite local instance:
```bash
cp backups/learningbridge_backup_<TIMESTAMP>.db learningbridge.db
```

For PostgreSQL production instance:
```bash
docker compose -f infra/docker-compose.yml exec -T postgres psql -U postgres -d learningbridge < backups/learningbridge_backup_<TIMESTAMP>.sql
```

---

## 4. In-Flight Job Reconciliation on Rollback

When containers are restarted or rolled back, running background workers terminate immediately, leaving jobs in `running` status with stale leases.

The built-in `JobReconciler` automatically handles this:
```python
from app.modules.jobs.reconciler import JobReconciler
from app.core.database import SessionLocal

with SessionLocal() as db:
    # Recovers jobs whose heartbeat lease has expired (> 30s)
    # Transitions to retry_pending or terminal failed
    recovered = JobReconciler.reconcile_stale_jobs(db, lease_timeout_seconds=30)
    print(f"Reconciled {recovered} stale jobs during rollback.")

    # Redispatches unacknowledged transactional outbox events
    redispatched = JobReconciler.redispatch_outbox_events(db, lease_timeout_seconds=30)
    print(f"Redispatched {redispatched} pending outbox messages.")
```

---

## 5. Post-Rollback Verification Checklist

1. [ ] **Readiness Probe:** `GET /health/ready` returns HTTP 200 `{"status": "ready", "database": "connected"}`.
2. [ ] **System Diagnostics:** `GET /health/system` shows `failed` and `queued` job counts within acceptable operational bounds.
3. [ ] **Tenant Isolation Drill:** Pinegrove teacher David Chen cannot access Oakridge Class 6-A records (HTTP 403 verified).
4. [ ] **Audit Trail Integrity:** Query `GET /v1/audit/events` to ensure no historical audit logs were destroyed during the rollback.
5. [ ] **Frontend Cache Reset:** Verify that static Nginx caches are invalidated or serve the correct reverted assets.

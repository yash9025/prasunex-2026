# LearningBridge — Setup & Execution Guide

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Node.js v20+ & npm
- Docker (optional for local SQLite development, required for containerized deployment)

---

### Step 1: Install Backend Dependencies & Seed Database

```bash
# 1. Install Python dependencies
pip install -r backend/requirements.txt

# 2. Run database migrations to head
cd backend
python -m alembic upgrade head
cd ..

# 3. Seed persistent database with two schools & synthetic classrooms
python backend/seeds/run_seed.py
```

Expected output:
```
🌱 Seeding LearningBridge database...
✅ Database seeding completed successfully!
   • School 1: Oakridge (sch-oakridge-001) - 40 Synthetic Learners in Class 6-A
   • Teacher 1: Priya Sharma (priya.sharma@demo.learningbridge.internal)
   • School 2: Pinegrove (sch-pinegrove-002) - 10 Synthetic Learners in Class 6-B
   • Teacher 2: David Chen (david.chen@demo.learningbridge.internal)
```

---

### Step 2: Run Full Automated Test Suite

To verify configuration, security, identity, database persistence, cross-school tenant isolation, exact answer scoring, rule-based diagnostic engine, CSV ingestion with idempotency, explainable teacher evidence, decision audit logging, intervention support groups, grounded support drafting, math verification, immutable assignment, fresh reassessment, and progress review:

```bash
python -m pytest tests -v
```

All 66 tests pass cleanly in under 10 seconds.

---

### Step 3: Run the Backend API Service

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger OpenAPI Documentation: `http://127.0.0.1:8000/docs`
- Liveness Probe: `http://127.0.0.1:8000/health/live`
- Readiness Probe: `http://127.0.0.1:8000/health/ready`

---

### Step 4: Run the Frontend Development Server

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` in your browser.
Click **"1-Click Demo Login (Oakridge Teacher Priya)"** to enter the teacher workspace.

---

## Containerized Deployment (Docker Compose)

To start the complete multi-service stack (PostgreSQL 16, Redis 7, Backend API, Celery Worker, Frontend Nginx):

```bash
cd infra
docker compose up --build -d
```

- Web UI: `http://localhost:3000`
- API / Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432` (`learningbridge`)
- Redis: `localhost:6379`

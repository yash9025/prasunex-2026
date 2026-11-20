# LearningBridge — Production Deployment & Operations Guide

> **Specification Standard:** Section 14.3 (Repeatable Deployment & Production Environment)  
> **Target Release:** v0.1.0-prod (PRASUNEX INNOVATHON 2026 Prototype)  
> **Platform:** Linux / Windows Container Infrastructure (Docker 24+, Compose v2+)

---

## 1. Architecture Overview

LearningBridge is architected as an isolated, multi-tenant web application adhering to zero-trust container principles:

```
[ Internet / Browser ]
           │
           ▼ (HTTPS / Port 80)
   ┌───────────────┐
   │ Nginx Alpine  │ (Static SPA + Reverse Proxy + Security Headers)
   └───────┬───────┘
           │
           ├────────────────────────────┐
           ▼ (/v1, /health)             ▼ (/*)
   ┌───────────────────────┐    ┌─────────────────────┐
   │ FastAPI Backend (8000)│    │ Vite React 18 SPA   │
   │ (Non-root 'appuser')  │    │ (Precompiled Dist)  │
   └──────────┬────────────┘    └─────────────────────┘
              │ (Private Bridge Network)
       ┌──────┴──────┐
       ▼             ▼
┌──────────────┐ ┌───────────────┐
│ PostgreSQL 16│ │ Redis 7       │
│ (RLS Active) │ │ (Jobs/Events) │
└──────────────┘ └───────────────┘
```

---

## 2. Pinned Production Images

Every service image is strictly pinned to prevent drift:

| Component | Pinned Base Image | Security Posture |
| :--- | :--- | :--- |
| **Reverse Proxy** | `nginx:alpine` | Static caching, gzip, security headers |
| **Frontend SPA** | `node:22-alpine` $\rightarrow$ `nginx:alpine` | Multi-stage build, zero node runtime in production |
| **Backend API** | `python:3.13-slim` | Multi-stage build, unprivileged user `appuser` (UID 1000) |
| **Database** | `postgres:16-alpine` | Private network only, non-default credentials |
| **Job Queue Broker** | `redis:7-alpine` | Private network only |

---

## 3. Environment Configuration

1. Copy the template to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure environment variables in `.env`:
   * `APP_ENV`: `production`
   * `DEBUG`: `false`
   * `DATABASE_URL`: `postgresql://postgres:<STRONG_PASSWORD>@postgres:5432/learningbridge`
   * `SECRET_KEY`: Set to a strong 32+ character cryptographically random key.
   * `GEMINI_API_KEY`: *(Optional)* Google Gemini API key. If omitted, the deterministic template drafting provider operates seamlessly.

> [!IMPORTANT]
> Frontend assets never contain backend secrets or API keys. All credentials remain strictly within server-side containers.

---

## 4. Single-Command Deployment

Execute the multi-service build and launch:

```bash
docker compose -f infra/docker-compose.yml up --build -d
```

### Automated Lifecycle:
1. **PostgreSQL** initializes and executes [`infra/init-db.sql`](file:///c:/Users/YASH/Desktop/prasunex%202026/infra/init-db.sql) to provision database roles and schemas.
2. **Backend container** starts, executes Alembic migrations, runs database health check, and binds to internal port 8000.
3. **Frontend container** compiles TypeScript assets via Vite, packages the static output into Nginx, and binds to host port 3000 (or port 80 in production).

---

## 5. Operational Probes & Health Checks

LearningBridge separates process liveness from operational readiness per Section 8.1 and 14.3:

### 1. Liveness Probe
* **Endpoint:** `GET http://localhost:8000/health/live`
* **Response:** `{"status": "alive", "service": "learningbridge-backend"}`
* **Purpose:** Validates the Python ASGI event loop is active.

### 2. Readiness Probe
* **Endpoint:** `GET http://localhost:8000/health/ready`
* **Response:** `{"status": "ready", "database": "connected"}`
* **Purpose:** Validates live database connectivity before routing user traffic.

### 3. System Diagnostics Probe (Section 13.3)
* **Endpoint:** `GET http://localhost:8000/health/system`
* **Response:**
  ```json
  {
    "status": "healthy",
    "environment": "production",
    "database": {
      "status": "connected",
      "ping_latency_ms": 3.8
    },
    "job_queue": {
      "queued": 0,
      "running": 0,
      "succeeded": 12,
      "failed": 0,
      "retry_pending": 0
    },
    "outbox": {
      "pending": 0,
      "dispatched": 12
    }
  }
  ```

---

## 6. Pre-Flight Verification Checklist

- [x] Backend passes all 77 automated test suites (`pytest tests`).
- [x] Frontend compiles with zero TypeScript errors (`tsc && vite build`).
- [x] Database snapshot and restore verified via [`backend/scripts/backup_restore.py`](file:///c:/Users/YASH/Desktop/prasunex%202026/backend/scripts/backup_restore.py).
- [x] Multi-tenant cross-school access attempts rejected with HTTP 403 Forbidden.
- [x] Keyboard focus visible across all interactive components (`*:focus-visible`).
- [x] Modal dialogs close on `Escape` key and trap keyboard `Tab` navigation.

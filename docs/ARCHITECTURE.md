# LearningBridge — System Architecture & Low-Level Design (Phase 1)

## 1. Architectural Philosophy

LearningBridge is engineered as a **modular monolith** adhering to Google Senior Developer engineering standards. It bridges diagnostic question-level assessment evidence with traceable, teacher-directed pedagogical interventions.

```
                    ┌───────────────────────────────────────────────┐
                    │               Client Layer                    │
                    │   React 18 + TypeScript + Bridge at Night     │
                    └───────────────────────┬───────────────────────┘
                                            │ HTTP / JSON
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │            API Gateway / Reverse Proxy        │
                    │               Nginx / TLS Boundary            │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │             FastAPI Application               │
                    │  - Request Tracing (X-Request-ID)             │
                    │  - Server-side Identity & RequestContext      │
                    │  - Strict Pydantic v2 Schema Envelopes        │
                    │  - Tenant Scoping & RLS Session Initialization│
                    └───────┬───────────────────────────────┬───────┘
                            │                               │
            Domain Services │               Outbox / Broker │
                            ▼                               ▼
    ┌───────────────────────────────┐             ┌───────────────────┐
    │     Modular Domain Layer      │             │   Redis Broker    │
    │  - auth (JWT / RBAC)          │             └─────────┬─────────┘
    │  - classrooms & learners      │                       │
    │  - evidence & assessment      │                       ▼
    │  - plans, versions, snippets  │             ┌───────────────────┐
    │  - reassessments              │             │  Celery Worker    │
    │  - jobs & audit trails        │             │  Background Tasks │
    └───────────────┬───────────────┘             └─────────┬─────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        │ SQLAlchemy 2.0
                                        ▼
                    ┌───────────────────────────────────────────────┐
                    │         PostgreSQL 16 Durable Storage         │
                    │    - Row-Level Security (RLS) Policies        │
                    │    - Composite Tenant Foreign Keys            │
                    │    - Immutable Version Snapshots              │
                    └───────────────────────────────────────────────┘
```

## 2. Security & Tenant Isolation Model

1. **Server-Side Authorization Resolution**:
   Client requests supply a signed HMAC-SHA256 JWT in the `Authorization: Bearer <token>` header. The server verifies the token signature, issuer (`learningbridge-auth`), audience (`learningbridge-api`), and expiration.
   Tenant membership is resolved strictly server-side against the `school_memberships` table. Client requests cannot override or forge tenant roles or school IDs.

2. **Session-Level Row-Level Security (RLS)**:
   For PostgreSQL deployments, the session sets a transaction-local setting:
   ```sql
   SET LOCAL app.current_school_id = '<school_id>';
   ```
   All tenant-scoped tables carry `school_id` with composite indexes and constraints.

3. **Cross-School Boundary Enforcement**:
   Endpoints explicitly verify that the authenticated actor's active membership permits access to the requested classroom, learner, or assessment. Cross-tenant reads return `403 Forbidden`.

## 3. Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── core/           # Config, logging, security, database, exceptions, request_context
│   │   ├── modules/
│   │   │   ├── auth/       # User, SchoolMembership, ClassMembership, JWT issuance, GET /v1/me
│   │   │   ├── classrooms/ # School, Classroom, Learner, roster queries
│   │   │   ├── imports/    # CSV ingestion and validation foundation
│   │   │   ├── scoring/    # Rational arithmetic and answer checking
│   │   │   ├── evidence/   # Topic, Assessment, Question, Attempt, GapEvidence
│   │   │   ├── plans/      # SupportGroup, SupportPlan, PlanVersion, Snippets
│   │   │   ├── reassessments/ # Reassessment, ReassessmentResponse
│   │   │   ├── jobs/       # Durable background job tracking & transactional outbox
│   │   │   └── audit/      # Append-only audit events
│   │   ├── api.py          # Central v1 route aggregator
│   │   └── main.py         # FastAPI application lifecycle and middleware
│   ├── alembic/            # Database schema migrations
│   └── seeds/              # Deterministic database seeder (Oakridge & Pinegrove)
├── frontend/               # React 18, TypeScript, Vite SPA
├── infra/                  # Docker Compose, Dockerfiles, Nginx, PostgreSQL init
├── fixtures/               # Synthetic CSV datasets & expected results manifest
├── tests/                  # Unit, integration, isolation, and fixture test suites
└── docs/                   # Engineering documentation
```

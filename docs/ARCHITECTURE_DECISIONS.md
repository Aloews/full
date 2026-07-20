# Architecture Decisions

Version: 1.0

Status: Active

This document is the index of architecture-level decisions for AlphaPulse.

Product and business decisions are tracked in [DECISIONS.md](DECISIONS.md).

Detailed records live in [adr/](adr/).

---

# AD-001

Decision:

Monolith-first architecture (Next.js + FastAPI + PostgreSQL + Redis).

No microservices for MVP.

Reason:

Simplicity, speed, controlled infrastructure cost (€100–300/month).

Reference:

docs/03_SYSTEM_ARCHITECTURE.md

Status:

Accepted

---

# AD-002

Decision:

PostgreSQL is the single source of truth.

Metrics are stored as append-only snapshots and never overwritten.

Reference:

docs/04_DATABASE_DESIGN.md

Status:

Accepted

---

# AD-003

Decision:

Rule-based scoring for MVP. No machine learning at launch.

Formula:

GitHub Growth 50% / Reddit Momentum 30% / HN Momentum 20%

Reference:

docs/06_AI_MODELS.md

Status:

Accepted

---

# AD-004 (Amendment A)

Decision:

Unified engineering standards:

- UTC timestamps (`TIMESTAMPTZ`)
- UUIDv7 primary keys
- snake_case naming
- audit fields (`created_at`, `updated_at`)
- soft delete only for `users` and `projects`
- unified API response envelope and enums

Reference:

Amendment A in docs/03_SYSTEM_ARCHITECTURE.md and docs/04_DATABASE_DESIGN.md

Status:

Accepted

---

# AD-005 (Amendment B)

Decision:

Data Reliability Layer:

- Data Coverage Score (GitHub 50 / Reddit 30 / HN 20)
- HIGH confidence requires Opportunity Score ≥ 80 AND Coverage ≥ 80
- Source reliability weights, batch collection, Redis cache, retry with backoff
- If GitHub is unavailable, signal generation pauses

Reference:

Amendment B in docs/03_SYSTEM_ARCHITECTURE.md and docs/06_AI_MODELS.md

Status:

Accepted

---

# AD-006 (Amendment C)

Decision:

Signal Traceability:

- `signal_sources` table stores the evidence behind every signal
- Every signal includes an Evidence section

Reference:

Amendment C in docs/04_DATABASE_DESIGN.md and docs/06_AI_MODELS.md

Status:

Mandatory

---

# ADR Index

| ADR | Title | Status |
|------|--------|---------|
| [ADR-001](adr/ADR-001-Technology-Stack.md) | Technology Stack Selection | Accepted |

---

# Review Frequency

Quarterly.

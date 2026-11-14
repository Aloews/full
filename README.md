# AUREL

[Project map](./docs/MAP.md) — architecture, release gates and AI agent toolchain. — Private Property Platform

A premium platform for verified exceptional property, buyer mandates, private inventory and property ownership services.

## Technology
All backend business services and domain logic are implemented in **Rust** (Axum/Tokio). Next.js/TypeScript is the presentation layer only. PostgreSQL is the system of record with tenant row-level security and versioned SQL migrations.

## Product domains
1. Elite Estate — verified property discovery.
2. Private Buyer — buyer mandates and advisory workflow.
3. Estate Studio — property media and campaigns.
4. Estate Intelligence — sourced market observations and scenarios.
5. Off-Market Club — confidential inventory and access grants.
6. Estate Transaction — diligence and secure deal workflow.
7. Estate Management — property operations and vendor workflow.
8. Global Residency — relocation coordination through licensed partners.
9. Developer Intelligence — developer inventory, leads and sales analytics.
10. Elite Lifestyle — vetted concierge provider network.

Elite Estate is the first delivery target. The remaining domains are registered boundaries, not completed products.

## Elite Estate API
- `GET /health` — liveness.
- `GET /ready` — database readiness.
- `GET /api/v1/modules` — domain catalogue.
- `POST /api/v1/properties` — create a private listing (JWT owner/broker/admin).
- `GET /api/v1/properties` — tenant-scoped inventory.
- `GET /api/v1/review-queue` — reviewer/admin queue for listings awaiting independent review.
- `GET /api/v1/properties/{id}/evidence` — inspect tenant-scoped evidence.
- `POST /api/v1/properties/{id}/evidence` — append source and verification evidence.
- `POST /api/v1/properties/{id}/submit` — submit for independent review.
- `POST /api/v1/properties/{id}/review` — reviewer/admin approves or rejects; self-review is blocked.
- `GET /public/properties` — public verified inventory only.
- `GET /public/properties/{id}` — public verified property details.
- `POST /public/properties/{id}/enquiries` — consent-gated enquiry for a public verified listing.

Protected endpoints require an HS256 JWT signed by the AUREL identity issuer. Required claims: `sub` (actor UUID), `org_id` (organization UUID), `role`, `iss=aurel`, `aud=aurel-api`, and `exp`. Allowed write roles: `owner`, `broker`, `admin`; review roles: `reviewer`, `admin`. The API does not issue user tokens; connect a real identity provider before onboarding users.

## Runtime configuration
- `DATABASE_URL`: dedicated AUREL PostgreSQL database; the application role must not be superuser or have `BYPASSRLS`.
- `AUREL_JWT_SECRET`: at least 32 bytes, stored only in the deployment secret manager.
- `AUREL_WEB_ORIGIN`: exact HTTPS origin of the deployed web client; CORS does not allow wildcard origins.
- `AUREL_API_URL`: server-side API base URL for the property collection and detail pages.
- `NEXT_PUBLIC_AUREL_API_URL`: public API base URL used by the browser enquiry form.
- `PORT`: optional, defaults to 8080.

The service applies embedded migrations at startup. Never point it at Sherlock Scholes, Novel Forge or another production database. The Docker image includes the migration directory at compile time.

## Local checks
```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo build --release --workspace
```

## Release status
This is an implementation increment, not a live brokerage release. No real listings or partner credentials are fabricated. Dedicated database/identity configuration, enquiry abuse controls, jurisdiction and licensing review, staging deployment, browser E2E tests and rollback rehearsal remain required. See [the project map](docs/MAP.md) and [delivery plan](docs/DELIVERY_PLAN.md).

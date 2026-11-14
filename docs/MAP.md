# AUREL / Elite Estate — Project Map

Last verified against branch `foundation/luxury-estate-platform`.

## Product order
Elite Estate is the first release target. The other nine AUREL domains remain registered as future bounded contexts and must not be represented as completed products.

## Current implementation
- Rust workspace and Axum/Tokio API.
- PostgreSQL migration for organizations, properties, evidence, append-only audit events and buyer enquiries.
- Tenant-scoped PostgreSQL row-level security for internal records.
- HS256 JWT authentication contract for protected API routes. Claims: `sub` (actor UUID), `org_id` (organization UUID), `role`, `iss=aurel`, `aud=aurel-api`, `exp`.
- Property creation, tenant-scoped listing, evidence append, submission for review, independent reviewer approval/rejection, public verified listing search and consent-gated enquiry capture.
- Database-level publication guard: a listing cannot become verified/public without evidence and a reviewer distinct from its creator.
- Evidence and audit records are append-only.
- Next.js is presentation-only.

## API contract
- `GET /health`
- `GET /api/v1/modules`
- `POST /api/v1/properties` — owner/broker/admin JWT.
- `GET /api/v1/properties` — tenant-scoped list.
- `POST /api/v1/properties/{id}/evidence` — append source/ownership/mandate/price/media evidence.
- `POST /api/v1/properties/{id}/submit` — submit a record with evidence for review.
- `POST /api/v1/properties/{id}/review` — reviewer/admin only; reviewer cannot approve their own record.
- `GET /public/properties` — verified public inventory only.
- `GET /public/properties/{id}` — verified public property detail.
- `POST /public/properties/{id}/enquiries` — consent required; public verified inventory only.

## Required runtime configuration
- `DATABASE_URL`: dedicated AUREL PostgreSQL connection. The database role must not be a superuser or have `BYPASSRLS`.
- `AUREL_JWT_SECRET`: at least 32 bytes, held only in the deployment secret store.
- `AUREL_WEB_ORIGIN`: exact allowed browser origin for CORS.
- `AUREL_API_URL`: server-side API base URL for property pages.
- `NEXT_PUBLIC_AUREL_API_URL`: browser API base URL for enquiries.
- `PORT`: optional; defaults to 8080.

The API applies embedded SQL migrations at startup. Do not point it at Sherlock Scholes, Novel Forge or any other production database. No AUREL database credentials have been verified in this repository.

## Release blockers / not yet verified
- No dedicated AUREL PostgreSQL instance or deployment credentials are connected/verified.
- JWT issuer and token-issuance integration with a real identity provider is not connected. The API accepts only correctly signed AUREL JWTs; it does not issue user tokens.
- Public enquiry endpoint still needs edge/API rate limiting, abuse controls, email verification and retention policy before internet exposure.
- Browser property collection/detail/enquiry screens are wired to the API URL configuration but remain empty until a dedicated API and verified inventory are deployed.
- No real licensed property supply, partner agreements, evidence or listing data have been provided; no sample properties are fabricated.
- No launch jurisdiction, legal entity or brokerage/partner model has been approved.
- No staging deployment, production deployment, rollback rehearsal or end-to-end browser journey has been verified.
- Frontend still contains concept copy and is not yet wired to the live API.

## Latest checks
- Earlier foundation SHA `492ab94372d1d1d965d7a425f2d3ed41b8915a5a`: Rust fmt, Clippy, workspace tests and release build passed; frontend npm install and Next.js production build passed.
- Subsequent Elite Estate persistence/API/UI commits are newer than that checked SHA. The latest CI must pass on the exact branch HEAD before this increment is considered validated.
- Do not merge or deploy until all required checks pass on the exact candidate SHA, the security review approves RLS/auth/public enquiry boundaries, and staging smoke tests pass.

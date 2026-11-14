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

## Owner-approved launch decisions (2026-11-14)

- Launch scope: international market. This is a product direction, not a determination that the service may legally operate in every country. Before enabling listings or transactions in a country, complete a country-by-country legal, licensing, privacy, consumer-protection, sanctions and tax review.
- Property supply: both (1) licensed/contracted agencies and property owners, and (2) lawful open/public sources. Every listing must retain source attribution, retrieval time, permitted-use basis, and verification state. Publicly accessible data is not automatically licensed for republication; do not scrape or republish where terms or law prohibit it.
- Infrastructure budget: prefer free tiers and existing connected services. Do not create paid resources, exceed free quotas, enable paid plans, or incur recurring charges without explicit owner approval. Report exact free-tier constraints when they block production.
- These decisions do not waive the existing release gates for dedicated database, real identity/JWT issuance, abuse controls, legal review, licensed supply, staging, end-to-end verification and rollback.

## API contract
- `GET /health` — liveness.
- `GET /ready` — database readiness.
- `GET /api/v1/modules`
- `POST /api/v1/properties` — owner/broker/admin JWT.
- `GET /api/v1/properties` — tenant-scoped list.
- `GET /api/v1/review-queue` — reviewer/admin list of records awaiting review.
- `GET /api/v1/properties/{id}/evidence` — inspect tenant-scoped evidence.
- `POST /api/v1/properties/{id}/evidence` — append source/ownership/mandate/price/media evidence.
- `POST /api/v1/properties/{id}/submit` — submit a record with evidence for review.
- `POST /api/v1/properties/{id}/review` — reviewer/admin only; reviewer cannot approve their own record.
- `GET /public/properties` — verified public inventory only.
- `GET /public/properties/{id}` — verified public property detail.
- `POST /public/properties/{id}/enquiries` — consent required; public verified inventory only.

## Required runtime configuration
- `DATABASE_URL`: dedicated AUREL PostgreSQL connection. The database role must not be a superuser or have `BYPASSRLS`.
- `AUREL_JWT_SECRET`: at least 32 bytes, held only in the deployment secret store.
- `AUREL_WEB_ORIGIN`: exact allowed browser origin for CORS; wildcard origins are not enabled.
- `AUREL_API_URL`: server-side API base URL for property pages.
- `NEXT_PUBLIC_AUREL_API_URL`: browser API base URL for enquiries.
- `PORT`: optional; defaults to 8080.

The API applies embedded SQL migrations at startup. Do not point it at Sherlock Scholes, Novel Forge or any other production database. No AUREL database credentials have been verified in this repository.

## Release blockers / not yet verified
- Dedicated Neon project `aurel-production` is provisioned in `aws-eu-central-1` (project `quiet-band-32908169`), with default branch `main` (`br-dry-lake-b91cdjc5`) and database `aurel`. Managed Better Auth is active with mandatory email OTP verification and the organization plugin. AUREL `aurel_app` is a login role with neither SUPERUSER nor BYPASSRLS; verified RLS is enabled and forced on `organizations`, `properties`, `property_evidence`, `property_audit_events` and `property_enquiries`. A pooled TLS-required connection URI for `aurel_app` and a separately generated 48-byte staging cookie secret have been stored in the Vercel project `aurel-private-property` as sensitive `DATABASE_URL` and `NEON_AUTH_COOKIE_SECRET` variables for Preview/Development only. No secret values are committed.

- Vercel project `aurel-private-property` is confirmed to exist and has successful Preview deployments. Its staging API/auth variables are scoped to Preview/Development; production auth and database variables have not been enabled. SSO protection remains enabled.
- The Neon `aurel_app` role has SELECT/INSERT on organizations and the append-only evidence/audit/enquiry tables, SELECT/INSERT/UPDATE on properties, and no DELETE privileges on the application tables. This is a privilege snapshot, not a substitute for endpoint-level authorization tests.

- JWT issuer and token-issuance integration with a real identity provider is not connected. The API accepts only correctly signed AUREL JWTs; it does not issue user tokens.
- Public enquiry endpoint still needs edge/API rate limiting, abuse controls, email verification and retention policy before internet exposure.
- Browser property collection/detail/enquiry screens are wired to `AUREL_API_URL` and `NEXT_PUBLIC_AUREL_API_URL`; they remain empty until a dedicated API and verified inventory are deployed.
- No real licensed property supply, partner agreements, evidence or listing data have been provided; no sample properties are fabricated.
- No launch jurisdiction, legal entity or brokerage/partner model has been approved.
- No staging deployment, production deployment, rollback rehearsal or end-to-end browser journey has been verified.
- Frontend still contains concept copy and is not yet wired to the live API.

## Latest checks
- Candidate code SHA `b001f29bc1588ae102988087ab11a4310cac9a8c` passed GitHub Actions:
  - Rust CI run `43579101241`: `cargo fmt --check`, Clippy with warnings denied, unit + PostgreSQL 16 RLS integration tests, release build and production Docker image build all passed.
  - Frontend CI run `43579101266`: `npm ci`, `npm audit --audit-level=low` and Next.js production build all passed.
- The PostgreSQL integration test proves cross-tenant isolation, rejects creator self-review and rejects publication without evidence, and allows independently reviewed evidence-backed publication.
- Vercel status for this candidate is failed with `build-rate-limit` (free-plan daily deployment cap). No workaround or plan upgrade was attempted.
- This is a tested technical vertical slice, not a production release. Do not merge or deploy until the dedicated database, identity provider, enquiry abuse controls, licensed supply, jurisdiction review and staging/rollback gates are completed.

## AI delivery runtime — 2026-11-14

- AUREL is the first Product Factory target; its code repository does not host the coding-agent process.
- The control plane `Aloews/russian-dev-projects` runs Claude Code/Fable 5.2 with the pinned Caveman 4.1.0 plugin and a local Qwen2.5-Coder 3B fallback on isolated GitHub Actions runners.
- Qwen is installed per run through Ollama, its exact model is checked before inference, and the generated patch is restricted to application/source/tests/docs before the existing database, Rust, frontend and browser verification pipeline.
- No model or agent receives production database credentials, identity-provider secrets, live property inventory or deployment access.
- The current AUREL branch remains a technical vertical slice, not a production release. The Product Factory agent setup does not waive dedicated database, real JWT issuance, abuse controls, licensed supply, jurisdiction review, staging E2E or rollback gates.

### Other requested agent integrations

- `codebase-memory-mcp`: documented but not installed/indexed. The current Product Factory runner is ephemeral; a durable MCP graph needs an explicit persistent host or a separately validated cache strategy and agent MCP configuration.
- Spotify Portal / shunt: documented but not connected. Portal CLI authentication and AiKA readiness have not been established; do not treat the GitHub Actions Qwen fallback as Spotify delegation.

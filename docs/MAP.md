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
- No dedicated AUREL PostgreSQL instance or deployment credentials are connected/verified.
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


## AI engineering toolchain — required project standard

A repository entry is not proof that an integration is installed or active.

### Caveman — concise agent output
- Upstream: https://github.com/JuliusBrussee/caveman
- Claude Code: `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`
- Codex CLI: `npx -y github:JuliusBrussee/caveman -- --only codex` (or `npx skills add JuliusBrussee/caveman -a codex -g`).
- Restart/reload the actual host and verify skill discovery. Never compress code, identifiers, errors, assertions, contracts, negations or acceptance criteria.

### codebase-memory-mcp — persistent code graph
- Upstream: https://github.com/DeusData/codebase-memory-mcp
- Host install (macOS/Linux): `curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash`
- Restart the coding agent, verify the MCP server is visible, then index this repository.
- Keep its graph on a persistent host. Ephemeral CI/cron runners are not persistent memory hosts. Pin and verify release/checksum before production use.

### Spotify Portal AI Plugins — AiKA delegation
- Upstream: https://github.com/spotify/portal-ai-plugins
- Claude Code: `claude plugin marketplace add spotify/portal-ai-plugins`, `claude plugin install portal@portal`, `claude plugin install shunt@portal`.
- Codex: `codex plugin marketplace add spotify/portal-ai-plugins`, then install Spotify Portal from `/plugins`. Cursor uses its team marketplace.
- In a new supported session run `/portal:setup`, authenticate Portal CLI and run readiness diagnostics. Shunt is Claude Code-only; verify AiKA modes `bulk-reader` and `code-writer`.
- Never commit Portal credentials or local MCP config.

### Runtime compatibility and evidence
- These are coding-agent integrations, not generic application dependencies. An HTTP-only Starimg worker cannot load Claude/Codex plugins or use a local MCP server without the corresponding runtime and MCP client.
- Do not use ephemeral CI or cron containers as persistent MCP/Portal hosts.
- Record each tool independently as `not installed`, `installed`, `connected`, `indexed`, `verified`; advance only after observing its runtime check.
- Last Fable/Starimg request returned HTTP 402 before model execution. Do not retry billable generation until an authenticated test request succeeds.

### GitHub Actions fallback
- Use Actions only when a repository-owned agent workflow, trigger, permissions, model invocation and draft-PR output are verified.
- This repository's current PR/CI workflow is a test gate, not an autonomous coding agent. Do not label it an agent fallback without adding and verifying an agent runner.
- No automatic merge, production deployment, paid resource creation, or production data migration.

### Installation status — 2026-11-14
| Integration | Documentation | Active runtime |
|---|---|---|
| Caveman | Project skills at `.agents/skills/caveman/` and `.claude/skills/caveman/` | Included in this PR; host discovery/activation not yet verified |
| codebase-memory-mcp | Pinned project config `.mcp.json` (`0.12.1`) | MCP startup and indexing not yet verified on a persistent host |
| Spotify Portal / shunt | `.claude/settings.json` registers marketplace, enables `portal@portal`, disables `shunt@portal` | Portal auth/session setup pending; shunt blocked pending upstream hook fix and AiKA verification |

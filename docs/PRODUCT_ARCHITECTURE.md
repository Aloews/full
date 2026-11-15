# AUREL — Product Architecture

## Technology and service boundaries
All backend services, business rules, scheduled jobs and integration adapters are Rust. The initial deployment is a modular Rust API (Axum/Tokio) with domain modules and explicit interfaces. Do not split into ten network microservices until independent scaling, ownership or fault isolation justifies the operational cost. The Next.js application is presentation-only; it must not own business rules or privileged data access.

## Ten bounded contexts

| Rust domain | Core records | Initial acceptance criteria |
|---|---|---|
| Elite Estate | Property, media, location, provenance | Publish only reviewed inventory; each material claim has evidence and verification state |
| Private Buyer | Mandate, criteria, shortlist, viewing | Consent-based mandate lifecycle and advisor assignment |
| Estate Studio | Campaign, asset, approval | Versioned assets, rights metadata and client approval |
| Estate Intelligence | Comparable, observation, scenario | Every metric carries source, timestamp, methodology and confidence |
| Off-Market Club | Opportunity, access grant, NDA | No public indexing; explicit access grants and audit trail |
| Estate Transaction | Deal room, checklist, document | Least-privilege document access and immutable audit events |
| Estate Management | Asset, task, vendor, expense | Owner approvals, vendor controls and expense evidence |
| Global Residency | Case, jurisdiction, referral | No legal/tax advice; licensed partner credentials and scope disclosed |
| Developer Intelligence | Project, unit, lead, funnel | Tenant isolation, inventory sync and funnel provenance |
| Elite Lifestyle | Request, provider, fulfilment | Consent, provider vetting and transparent terms |

## Rust workspace layout
- `services/platform-api`: Axum HTTP API, Tokio runtime, request limits, structured tracing and graceful shutdown.
- `services/platform-api/src/modules.rs`: domain registry (not the completed product implementations).
- Future domain modules live under `services/platform-api/src/domains/<domain>/`, each with model, repository, service, handler and tests.
- Shared Rust crates may be extracted for auth, audit, persistence and provider integrations when dependency boundaries are stable.

## Shared platform services
- Identity and access roles for clients, brokers, owners, developers, advisors, operators and administrators.
- Organization and tenancy isolation for agencies and developers.
- Normalized property master with address, geospatial point, building, unit, media and source records.
- Provenance: source reference, observed timestamp, verification state, reviewer and evidence.
- Multilingual search; confidential inventory excluded without explicit access grant.
- Workflows for mandates, enquiries, viewings, offers, diligence and service requests.
- Append-only audit events for sensitive reads, exports and permission changes.
- Private object storage, short-lived signed links, malware scanning and retention controls.
- Rust provider adapters with timeouts, retries, idempotency, rate limits and consent boundaries.

## Verification states
`unverified → in_review → verified`; rejected and stale records require review. A listing cannot be labelled verified without evidence, reviewer and verification timestamp. Estimates must never be presented as confirmed sale prices.

## Data and security
Use a dedicated AUREL PostgreSQL project. Do not reuse Sherlock Scholes or Novel Forge databases. Apply migrations through version control. Enforce tenant isolation in database policies as well as API authorization; use least-privilege database credentials, verified JWT claims, audit trails and private object storage. Never commit secrets. Do not ingest or expose confidential inventory without documented rights and access grants.

## Delivery sequence
R0 Rust foundation and API contract; R1 Elite Estate + Private Buyer + broker CRM; R2 Off-Market access controls; R3 Estate Transaction + sourced Intelligence; R4 Studio, Management, Residency, Developer and Lifestyle workflows.

## Jurisdictional constraints
Brokerage licensing, AML/KYC, sanctions, privacy, advertising, cross-border data transfers and referral fees vary by jurisdiction. Local counsel and licensed providers must approve operating workflows. The platform must not imply it is a law firm, bank, immigration adviser or licensed broker where it is not.

## Explicit non-goals
No fabricated listings, prices, clients or testimonials; no automated legal conclusions, valuation guarantees or investment-return promises; no public exposure of confidential inventory; no handling of client funds or identity documents before security and compliance approval.

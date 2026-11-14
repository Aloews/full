# AUREL — Delivery Plan

## Implementation standard
Backend domain logic is Rust-only. The web client is presentation-only. Begin with a modular Rust API and extract separately deployable Rust services only where operational evidence supports it.

## Workstreams
1. Operating model: select first jurisdiction, legal entity, brokerage model and customer segment.
2. Rust platform: Axum API, domain boundaries, configuration, structured logs, error contracts and health checks.
3. Data platform: dedicated PostgreSQL/Supabase project, migrations, auth integration and tenant isolation.
4. Inventory: partner data agreements, provenance, deduplication, moderation and freshness SLAs.
5. Commercial workflows: buyer mandates, enquiry qualification, CRM and viewing coordination.
6. Trust: privacy impact assessment, AML/KYC responsibilities, sanctions controls, retention and local counsel.
7. Go-to-market: secure supply before demand generation; onboard a small vetted partner group.

## Milestones
- M0: Rust workspace, API foundation, web shell and CI.
- M1: dedicated database, schema migrations, Auth/JWT validation and row-level security.
- M2: property ingestion and verification queue with audit history.
- M3: search and listing publication workflow.
- M4: buyer mandates, enquiry pipeline and broker workspace.
- M5: Off-Market access grants and secure deal-room MVP.
- M6: security review, test suite, monitoring and launch rehearsal.
- M7: implement remaining domain workflows in Rust and integrate them through stable API contracts.

## Release gates
Acceptance criteria documented and tested; migrations apply to a clean environment; cross-tenant and unauthorized access denied; Rust formatting, Clippy, tests and release build pass; secrets/configuration verified without exposing values; deployed health and critical journeys tested; limitations and risks recorded.

## Open decisions
First launch jurisdiction and legal entity; licensed broker vs partner-led marketplace; buyer segment and minimum transaction size; verified inventory sources and licensing; dedicated database project provisioning and billing; payment provider and fee model.

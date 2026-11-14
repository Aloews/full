# AUREL — Delivery Plan

## Workstreams
1. Operating model: select first jurisdiction, legal entity, brokerage model and customer segment.
2. Platform engineering: dedicated database, authentication, tenancy, migrations, API and observability.
3. Inventory: partner data agreements, provenance, deduplication, moderation and freshness SLAs.
4. Commercial workflows: buyer mandates, enquiry qualification, CRM and viewing coordination.
5. Trust: privacy impact assessment, AML/KYC responsibilities, sanctions controls, retention and local counsel.
6. Go-to-market: secure supply before demand generation; onboard a small vetted partner group.

## Milestones
- M0: responsive shell and product architecture.
- M1: dedicated Supabase project, schema migrations, Auth and row-level security.
- M2: property ingestion and verification queue with audit history.
- M3: search and listing publication workflow.
- M4: buyer mandates, enquiry pipeline and broker workspace.
- M5: Off-Market access grants and secure deal-room MVP.
- M6: security review, test suite, monitoring and launch rehearsal.

## Release gates
Acceptance criteria documented and tested; migrations apply to a clean environment; cross-tenant and unauthorized access denied; automated tests pass with inspected output; secrets/configuration verified without exposing values; deployed health and critical journeys tested; limitations and risks recorded.

## Open decisions
First launch jurisdiction and legal entity; licensed broker vs partner-led marketplace; buyer segment and minimum transaction size; verified inventory sources and licensing; database project billing/organization approval; payment provider and fee model.

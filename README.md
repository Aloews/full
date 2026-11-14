# AUREL — Private Property Platform

Premium modular real-estate platform for high-value residential property, private buyer mandates and ownership services.

## Ten services
1. Elite Estate — curated property discovery.
2. Private Buyer — buyer mandates and search advisory.
3. Estate Studio — property presentation and marketing.
4. Estate Intelligence — sourced comparables and market analytics.
5. Off-Market Club — confidential opportunities and access controls.
6. Estate Transaction — secure diligence and deal workflow.
7. Estate Management — property and household operations.
8. Global Residency — relocation coordination through licensed partners.
9. Developer Intelligence — developer sales and demand analytics.
10. Elite Lifestyle — vetted concierge partner network.

## Current state
This branch contains a responsive application shell, service catalogue, market overview and client-side service filtering. It intentionally contains no fabricated property inventory, market prices, clients, testimonials or transaction data.

## Intended stack
- Next.js + TypeScript application on Vercel.
- Dedicated Supabase project for database, Auth and private storage (not yet provisioned).
- Railway for independent backend workloads when required.
- GitHub for source control and CI.

## Production gates
Dedicated database and migrations; Auth and role-based access; tenant isolation and RLS; property provenance and moderation; buyer mandates and CRM; secure document rooms; jurisdiction-specific legal review; automated tests; monitoring; backup/restore drills; deployed end-to-end verification.

Status: foundation interface prototype. Not a live brokerage, verified listing marketplace or transaction platform.

# AUREL — Private Property Platform

A premium platform for exceptional residential property, buyer mandates, private inventory and property ownership services.

## Technology decision
All backend business services and domain logic are implemented in **Rust**. The initial architecture is a modular Rust application, not ten independently deployed microservices: this keeps deployment and operations manageable while preserving strict domain boundaries. The web presentation layer remains Next.js/TypeScript; it is a client interface, not a business-service runtime.

- Rust workspace: `services/platform-api` (Axum, Tokio).
- Web client: Next.js + TypeScript, deployed independently.
- Target data platform: a dedicated PostgreSQL/Supabase project for AUREL. Existing unrelated projects are not reused.
- Target API hosting: a dedicated Railway project.
- Source control and CI: GitHub.

## Ten product domains
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

## Current implementation state
- Rust workspace and API service scaffold.
- Health endpoint: `GET /health`.
- Domain catalogue endpoint: `GET /api/v1/modules`.
- Rust formatting, Clippy, test and release-build CI workflow.
- Responsive web shell and product catalogue.

The ten domains are registered in the API, but their business workflows are not yet implemented. No property listings, client records, prices, valuations, partners or completed transactions are fabricated.

## Local development
```bash
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo run -p aurel-platform-api
``

API listens on `PORT` (default 8080). This is a foundation build, not yet a live brokerage or production transaction system.

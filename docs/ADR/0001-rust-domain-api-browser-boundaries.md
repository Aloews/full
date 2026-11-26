# ADR 0001 — Rust gameplay domain with transport and browser adapters

- Status: Accepted for the first playable slice
- Date: 2026-11-26

## Context

The project must follow the modular engineering organization used by Sherlock while remaining a standalone game. Gameplay code should be testable without running the UI or HTTP server. The first release also needs a small playable browser interface.

## Decision

Use a Cargo workspace with `slotbound-core` for deterministic gameplay rules and `slotbound-api` for Axum HTTP and persistence. Keep the browser client in `web/` as static JavaScript/CSS served by the API. All authoritative costs, recruitment, absorption, promotion, Core, item, and battle outcomes remain in the Rust domain.

## Consequences

- Domain logic can be unit tested without a server or browser.
- API and browser can evolve without duplicating core rules.
- The initial JSON file store enables local saves with no service credentials.
- The JSON file store is single-process only; production multi-instance deployment requires a shared transactional adapter.
- The browser is intentionally not a WASM client in this milestone; a Rust/WASM renderer can be evaluated later without moving rules into UI code.

# Architecture

## Runtime topology

Slotbound is a Rust-first game domain with an Axum API and a browser client. The dependency direction is one-way:

```text
Browser UI (web/)
   │ command requests / server state
   ▼
Axum API (crates/api)
   │ validates transport, loads/locks run, executes typed command
   ▼
Pure Rust domain (crates/game-core)
   ├── deterministic RNG and run state
   ├── sigil board and paylines
   ├── units, absorption and promotions
   ├── economy, items and Cores
   ├── wave/encounter definitions
   └── deterministic battle timeline (target; current battle is simplified)
   │
   ▼
Run repository adapter
   ├── PostgreSQL transaction + row lock (multi-instance)
   └── JSON snapshot + atomic rename (local single-process only)
```

The Vercel Container build serves the Axum API and static browser assets from one service. It is not a substitute for persistent storage. Multi-instance hosting must use PostgreSQL.

## Domain boundary

`slotbound-core` owns every gameplay rule: resource costs, valid phases, board outcomes, summon count, roster capacity, lock/absorb rules, promotions, Core/item effects, enemy scaling, battle events and rewards. It is a pure domain crate and must not depend on Axum, Tokio, browser APIs, filesystem or external services.

The API:
- validates request shape and caller/run identity;
- fetches the latest run state;
- executes one domain command;
- persists the resulting state in an atomic transaction;
- maps typed domain errors to stable HTTP errors;
- returns authoritative state and action results.

The browser:
- displays state received from the API;
- sends player commands;
- handles loading, errors, focus, accessible labels and responsive layout;
- animates the result of state transitions;
- never calculates summon odds, game economy, combat, rewards or progression.

## State model

A run includes:
- stable run ID, seed and ruleset version;
- phase, wave, gold, hearts and remaining action budgets;
- current board and last spin outcome;
- units with stable IDs, class, stats, lock, growth, imprint and promotion data;
- items, Core inventory and pending reward choices;
- current encounter and last battle report;
- command history/event sequence (planned acceptance scope for deterministic replay).

Save schemas must be versioned. Loading a save treats the payload as untrusted input and validates structural and domain invariants before accepting it.

## Command lifecycle

1. Parse transport input and reject malformed fields.
2. Resolve caller and run ownership (authentication/ownership is a production requirement).
3. Load the latest run and obtain exclusive mutation rights. PostgreSQL uses a transaction and row-level lock.
4. Clone or otherwise retain a rollback-safe prior state.
5. Apply one typed domain command. Validation occurs before irreversible mutation.
6. Persist the new state and event/report in the same transaction.
7. Commit; only then return success to the browser.
8. On any failure, roll back and keep the previously committed state.

A rejected command must not spend resources, advance RNG, append events or alter the saved state. Concurrent requests must not both mutate the same run from the same stale revision.

## Determinism and replay

A reproducible run is identified by its seed, ruleset version and ordered commands. RNG state belongs to the domain. Do not use current time, browser randomness or non-seeded server randomness for gameplay decisions after run creation.

The planned command/event system should persist:
- command sequence number;
- command type and validated payload;
- ruleset version;
- pre/post state hash;
- generated domain events.

Replay must reconstruct canonical state and combat events from the same initial seed and command sequence. Invalid commands are not recorded as successful events.

## Combat engine

Current behaviour is a deterministic army-power comparison. It is explicitly a prototype simplification.

Target behaviour is a pure Rust tick/timeline simulation with:
- battle participants, positions and lanes;
- stable initiative and target selection;
- attack clocks and ability cooldowns;
- armour, guard, shields, healing, statuses and deaths;
- boss telegraphs and encounter modifiers;
- typed events for every causal change;
- a deterministic terminal condition and bounded maximum tick count.

The browser receives an event log and renders it. It cannot change the event order or recompute battle outcomes.

## Persistence

- PostgreSQL is the multi-instance source of truth. Mutations use transactions and row-level locks.
- Database migrations are applied by a separate privileged migration role; the runtime application role receives only the table permissions it needs.
- The local JSON fallback uses atomic snapshots and is single-process only. It is not safe for multiple server processes or shared network volumes.
- Vercel runtime filesystems must not be used as player save storage.
- Backups, restore rehearsals, idempotency keys, ownership/authentication and retention policies are release requirements.
- The Neon development branch previously provisioned for related work has no compute endpoint; do not claim remote schema/migrations are active until a live database check proves it.

## Agent and CI boundaries

See `docs/AI_AGENT_OPERATING_MODEL.md`. Agents propose scoped patches; the repository and exact-head CI provide evidence. Workflow, permission, secret, production DB and deployment changes require human review. A green build is a necessary condition, not proof of game completeness.

## Current limitations

The current candidate still needs unit-by-unit combat, enemy abilities, stage/route map, a versioned ruleset, calibrated symbol weights, richer imprints/promotions, real-browser E2E, auth/ownership and production operations. The browser art is still a prototype and the current emoji symbols must be replaced with original pixel sprites.

# Architecture

## Dependency direction

`slotbound-core` owns game state and rules. It does not depend on Axum, Tokio, browser APIs, filesystems, or external services. `slotbound-api` is an adapter that validates transport input, calls domain commands, maps typed errors to HTTP responses, and persists state. `web` is a browser projection of server state and sends commands; it does not calculate authoritative odds, costs, or battle results.

```text
Browser (web/*)
    │ JSON commands / state
    ▼
Axum API (crates/api)
    ├── Run store adapter (atomic JSON snapshots, single process)
    └── Gameplay boundary
          ▼
    Pure Rust domain (crates/game-core)
      ├── deterministic RNG
      ├── slot board and paylines
      ├── units, absorption and promotions
      ├── cores and items
      └── wave/boss resolution
```

## Run-state lifecycle

- A new run receives a unique run ID and a gameplay seed.
- The gameplay core owns its RNG state; all generated symbols and unit rolls derive from it.
- A command validates phase, IDs, affordability, capacity and action limits before making a state transition.
- The API clones the prior state, applies the domain transition, writes the new JSON snapshot to a temporary file, and atomically renames it. If persistence fails, in-memory state rolls back to the prior clone.
- At startup, the API loads valid JSON run snapshots from `SLOTBOUND_DATA_DIR` (default `.slotbound-data/runs`). Invalid snapshots are skipped with a diagnostic; a production recovery path is still required.

## Current limitations

The file adapter uses a process-local write lock and filesystem rename. It is not safe for multiple server processes or shared network volumes. Run ownership/authentication and cross-process idempotency are not implemented. Before multi-instance deployment, replace this adapter with a transactional database repository and add concurrency, migration, ownership and backup/restore tests.

The combat resolver is deliberately simple in the first vertical slice. A future combat timeline remains in the domain crate and must be deterministic and replayable. The browser may show only server-provided results.

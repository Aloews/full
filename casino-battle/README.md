# Casino Battle

Casino Battle is a standalone 2D roguelite auto-battler prototype. Its visual language is warm, hand-crafted, readable and character-first. Combat is fully automated; the player's skill is expressed through drafting, formation, combinations, equipment and run decisions.

The project lives in this directory on the `casino-battle/foundation` branch. It does not replace Slotbound files or change the default branch.

## Non-negotiable product constraints

- **2D only.** No 3D scenes, meshes, perspective cameras or pseudo-3D presentation.
- **Auto-battle only.** The player prepares the party and formation; the simulation resolves combat.
- **Warm, charming, collectible visual identity.** Hand-drawn contours, soft paper-like surfaces, gentle colors and distinct silhouettes.
- Casino mechanics are a probability-and-combination system, not a casino setting. No slot-machine cabinet, roulette wheel, poker table, chips or casino room.
- No real-money wagering, cash-out, paid chance mechanics or purchasable random outcomes.
- The combat/domain rules live in Rust, never in UI event handlers.

## Current implementation

- `crates/game-core`: deterministic run state, a 4×4 connected-cluster Fate Board, rank-based recruitment, party synergies, duplicate evolution, lane-aware Auto-battle, bosses and relic rewards.
- `crates/game-server`: Axum API, PostgreSQL JSONB persistence, transactional row-locked state transitions, non-secret public snapshots, configurable CORS and health check.
- `client/`: reads run state from the API and replays the server-authoritative Auto-battle event log.
- `client/`: strict 2D Godot prototype with original hand-drawn-style vector character studies, a 4×4 Fate Board preview, server-driven party HUD, preparation-only lane changes by clicking a unit and tick-by-tick Auto-battle replay. All six allied sigil families now have distinct 2D prototype silhouettes (Mossguard, Cinderkit, Puddlekin, Pebbleback, Moonmote and Breezeling). These are code-drawn prototypes; authored sprite sheets, hand-painted animation and finished UI art remain release work.

## Run

Requirements: Rust stable (1.85+) and Godot 4.3+ for the client.

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo run -p casino-battle-core --bin balance -- 5000
cargo run -p casino-battle-server
```

Run `docker compose up --build` from this directory to start the API and PostgreSQL locally. Open `http://localhost:3000/healthz` for the server health check. Without `DATABASE_URL`, the server uses an explicitly development-only single-process in-memory store. Set `DATABASE_URL` to a PostgreSQL connection string to enable durable run storage and transactional row-locked transitions. Configure `CORS_ALLOWED_ORIGINS` with comma-separated trusted frontend origins.

Start the API with `docker compose up --build`, then open `client/project.godot` in Godot 4 to run the 2D client. Set `CASINO_BATTLE_API` to the server origin when it is not `http://127.0.0.1:3000`.

The first verified balance sample (1,000 seeded runs) is in `docs/BALANCE_BASELINE.md`; it records a 93.10% first-wave win rate after five draws. This is a wave-one baseline, not a claim that full-run balance is complete.

## API

- `GET /healthz`
- `POST /api/v1/runs` with an empty JSON object; the server generates the run seed
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/draw`
- `POST /api/v1/runs/{run_id}/formation` with `{"unit_id": 1, "lane": 2}` (lanes are `0`, `1`, `2`; preparation phase only)
- `POST /api/v1/runs/{run_id}/merge` with `{"keeper_id": 1, "donor_id": 2}`
- `POST /api/v1/runs/{run_id}/relic` with `{"relic": "honey_bell"}` after a boss victory while a relic choice is pending
- `POST /api/v1/runs/{run_id}/battle`

The initial API is a local development foundation, not a production-hardened public service. Authentication, per-player ownership, migrations-as-a-release-step, rate limits, observability and deployment secrets are release gates.

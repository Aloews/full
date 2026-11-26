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

- `crates/game-core`: deterministic run state, rune draws, line combinations and automatic battle simulation.
- `crates/game-server`: Axum API, optional PostgreSQL persistence, health check and run endpoints.
- `client/`: strict 2D Godot presentation prototype. The current geometric actors are layout placeholders, not final production art.

## Run

Requirements: Rust stable (1.85+) and Godot 4.3+ for the client.

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo run -p casino-battle-server
```

Open `http://localhost:3000/healthz` for the server health check. Without `DATABASE_URL`, the server uses an explicitly development-only in-memory store. Set `DATABASE_URL` to a PostgreSQL connection string to enable durable run storage and migrations.

Open `client/project.godot` in Godot 4 to run the 2D visual sandbox.

## API

- `GET /healthz`
- `POST /api/v1/runs` with optional `{"seed": 123}`
- `GET /api/v1/runs/{run_id}`
- `POST /api/v1/runs/{run_id}/draw`
- `POST /api/v1/runs/{run_id}/battle`

The initial API is a local development foundation, not a production-hardened public service. Authentication, per-player ownership, migrations-as-a-release-step, rate limits, observability and deployment secrets are release gates.

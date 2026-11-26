# Slotbound

Slotbound is an original 2D cozy-fantasy roguelite auto-battler. A 3×3 Fate Board aligns magical sigils to recruit creatures; the player shapes a roster through absorption, promotion, items and permanent Cores; the squad fights automatically against escalating waves.

**Visual direction:** Cozy 16-bit Fantasy Pixel Art. All game art, characters, environments, animations, audio and UI must be original or properly licensed. This project uses broad retro-game principles only and does not include commercial-game code, assets, audio, data tables or binaries.

## Canonical game specification

Read [the complete game design](docs/GAME_DESIGN.md), [the visual style guide](docs/VISUAL_STYLE_GUIDE.md), [current combat rules](docs/BATTLE_SIMULATION_RULES.md), [architecture](docs/ARCHITECTURE.md), [AI agent execution plan](docs/AI_AGENT_EXECUTION_PLAN.md) and [project MAP](docs/MAP.md). The canonical Fate Board is 3×3 with eight straight lines. The current game also includes deterministic three-choice per-wave route forks; a connected multi-stage biome map is still future work.

## Run locally

Requirements: Rust 1.85+ (stable), Cargo, and a supported desktop browser.

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo build --release --workspace
cargo run -p slotbound-api
```

Open `http://localhost:3000`.

Runs use PostgreSQL when `SLOTBOUND_DATABASE_URL` (or fallback `DATABASE_URL`) is set. `GET /healthz` checks the database connection and required `public.slotbound_runs` table before reporting PostgreSQL readiness. The local JSON snapshot fallback is single-process only and must not be used for multi-instance deployment. Database migrations are under `crates/api/migrations` and are applied by a separate privileged migration step; the runtime application role does not receive DDL permissions.

## Current playable loop

- Review gold, hearts, roster, next draw cost and encounter.
- Draw a 3×3 sigil board with eight horizontal, vertical and diagonal lines.
- Three matching class symbols on a line summon a creature.
- Use one column shift per wave.
- Select a keeper, lock important units and absorb donors to grow the keeper.
- Choose promotions at growth thresholds.
- Start an automatic battle, collect the result and continue.
- Resolve a journey event after battle, then choose a route: normal battle, recovery, merchant, elite encounter or boss gate.
- The Boss Gate grants +15% allied attack damage in the next boss battle (minimum +1 damage per hit).
- Every fifth wave is a boss; a boss victory offers one of three Cores.
- Use the between-wave cache for permanent attack, mitigation or healing items.

The current combat resolver uses a deterministic tick timeline with class-specific effects, persistent survivor health, casualties and a typed combat log. Journey-event and route choices are saved in the run and the browser replays the authoritative battle event stream on a pixel battlefield. The route and battle model is still an early foundation: authored enemy waves, full lane formation, richer abilities, cooldowns and balance validation remain. The web client has first-pass coded pixel sprites and a procedural forest scene, not a finished production asset library; complete sprite sheets, animation strips, biome tilemaps, bitmap typography and full visual E2E checks are still required. The BossGate +15% damage rule is the latest gameplay patch and awaits its exact-head CI result. See `docs/MAP.md` for scope and release gates.

## Engineering contract

`AGENTS.md` is mandatory for contributors and coding agents. Gameplay rules belong in `slotbound-core`, not UI handlers. Material transitions must be deterministic for a fixed seed and ruleset, validated before mutation, persisted atomically and covered by tests. CI on the exact candidate commit is a release gate. Never state that a build, agent cycle, runtime, database or deployment is verified without direct evidence.

Read:
- `docs/PRODUCT_CONCEPT.md` — product and mechanics.
- `docs/VISUAL_STYLE_GUIDE.md` — approved pixel-art direction and asset rules.
- `docs/ARCHITECTURE.md` — domain/API/browser/storage boundaries.
- `docs/AI_AGENT_OPERATING_MODEL.md` — specialist roles and delivery workflow.
- `docs/MAP.md` — current state and executable roadmap.

## Vercel

A separate Vercel project named `slotbound` exists in the `aloews-projects` team. The first preview deployment request was rejected by the Vercel API with a daily deployments quota error (HTTP 402). No deployment URL has been verified. The Vercel Container build uses `Dockerfile.vercel`; player saves must use PostgreSQL, never the container filesystem. Configure a pooled `SLOTBOUND_DATABASE_URL` only after a dedicated database and migration path are provisioned and verified.

## Agent task pipeline

The backlog records a responsible implementing role per task. The Qwen/Ollama workflow uses a separate task branch and a dedicated release-candidate integration branch. It applies bounded patch rules, role-separated Simulation QA and Product Integrator reviews, exact-head CI gates, and a maximum of two repair attempts. Treat automation as active only after a real successful agent PR lifecycle is observed. See `docs/AI_AGENT_OPERATING_MODEL.md` and `.github/agent-backlog.json`.


## Release-candidate branch

Current integration branch: `feat/slotbound-release-candidate`. Autonomous task PRs use `agents/slotbound-release-candidate` and target the integration branch, never `main`. The current runner uses one Ollama-hosted Qwen 2.5 Coder 3B model with separate role contracts; this is a bounded role pipeline, not a fleet of independent models. See `docs/AI_AGENT_EXECUTION_PLAN.md`.

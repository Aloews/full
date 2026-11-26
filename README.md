# Slotbound

Slotbound is an original 2D cozy-fantasy roguelite auto-battler. A 3×3 rune board recruits creatures; the player shapes a roster through absorption, promotion, items and permanent Cores; the squad fights automatically against escalating waves.

**Visual direction:** Cozy 16-bit Fantasy Pixel Art. All game art, characters, environments, animations, audio and UI must be original or properly licensed. This project uses broad retro-game principles only and does not include commercial-game code, assets, audio, data tables or binaries.

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

- Review gold, hearts, roster, next spin cost and encounter.
- Roll a 3×3 board with eight horizontal, vertical and diagonal paylines.
- Three matching class symbols on a line summon a creature.
- Use one column nudge per wave.
- Select a keeper, lock important units and absorb donors to grow the keeper.
- Choose promotions at growth thresholds.
- Start an automatic battle, collect the result and continue.
- Every fifth wave is a boss; a boss victory offers one of three Cores.
- Use the between-wave cache for permanent attack, mitigation or healing items.

The current combat resolver uses a deterministic tick timeline with class-specific effects, persistent survivor health, casualties and a typed combat log. This is an early combat foundation and still needs authored enemy waves, richer abilities and balance validation. The web visual layer is also a prototype: its symbols still need original pixel sprites, animation strips, bitmap typography and a full asset pipeline. See `docs/MAP.md` for implemented scope, limitations and release gates.

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

# Casino Battle development map

**Current gate: Foundation branch — Rust domain, server API and 2D visual sandbox.**

The map is the source of truth for autonomous coding agents. Update status only when a file, test, CI run or deployment proves the state.

## Product locks

- [x] Strict 2D presentation contract documented.
- [x] Auto-battle is the only battle mode.
- [x] Art direction locked to warm, hand-crafted, character-led fantasy.
- [x] Casino logic represented as sigils / probability / combinations, not a casino setting.
- [ ] Final camera/layout decision: flat top-down vs side-on battlefield.
- [ ] Original character bible and visual asset library.
- [ ] Final UI style guide, typography and icon set.

## Foundation

- [x] Standalone project subtree under `casino-battle/`.
- [x] Rust workspace.
- [x] Deterministic core crate.
- [x] 3×3 sigil-draw prototype and eight matching lines.
- [x] Initial party roster and recruit cap.
- [x] Automatic battle simulator.
- [x] Axum API endpoints for start, state, draw and battle.
- [x] Optional PostgreSQL JSONB persistence and migration.
- [x] Health endpoint that distinguishes Postgres from memory-only mode.
- [x] Godot 2D visual sandbox.
- [x] Rust CI workflow.
- [ ] CI result inspected and all failures fixed.
- [ ] Godot headless import / parse verification.

## Gameplay systems

- [ ] Formation grid with front / middle / back rows and lane targeting.
- [ ] Unit roles, affinities, factions and tier data as content definitions.
- [ ] Duplicate merging, rank-up and branching evolution.
- [ ] Imprints / traits that alter combat behavior.
- [ ] Relics and build-defining cores.
- [ ] Player-controlled preparation tools: lock, nudge, reroll and pity.
- [ ] Event, shop and route nodes.
- [ ] Elite encounters and boss behavior.
- [ ] Meta progression and unlocks.
- [ ] Run summary, battle log and damage breakdown.
- [ ] Balance simulation harness with seed batches and distribution reports.

## Client and art

- [ ] Final 2D camera and scale grid.
- [ ] Original hero and enemy sprite sheets.
- [ ] Idle / anticipation / attack / hit / defeat / victory animation sets.
- [ ] Background biome kits with multiple layers.
- [ ] Hand-painted VFX library.
- [ ] UI components with readable text at 1280×720 and Steam Deck scale.
- [ ] Reduced motion and color-accessibility checks.
- [ ] Asset license provenance and source files tracked.

## Backend and production

- [ ] Player identity and run ownership.
- [ ] Durable state transitions with concurrency control.
- [ ] Session security and request validation.
- [ ] PostgreSQL schema versioning and migration release job.
- [ ] Rate limits and abuse protection.
- [ ] Structured logs, metrics and tracing.
- [ ] Backups and recovery validation.
- [ ] Production environment variables provisioned outside Git.
- [ ] Deployment with a successful health check.
- [ ] Load / soak tests and multi-instance tests.

## Release gates

No Steam demo candidate until:
1. Gameplay loop is complete for at least one full run.
2. Auto-battle is deterministic, explainable and balance-tested.
3. Art is original, consistent and complete for the demo content.
4. Save/load, crashes, input, window scaling and Steam Deck UI are tested.
5. CI is green on the exact candidate commit.
6. No blocking QA / red-team findings remain.


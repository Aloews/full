# Casino Battle development map

**Current gate: Foundation branch — Rust domain, server API and strict 2D pixel-art sandbox.**

The map is the source of truth for autonomous coding agents. Update status only when a file, test, CI run or deployment proves the state.

## Product locks

- [x] Strict 2D presentation contract documented.
- [x] Auto-battle is the only battle mode.
- [x] Art direction locked to cozy retro 16-bit pixel art: Slotbound battle readability + Zelda world charm + Mario-like character clarity.
- [x] Casino logic represented as sigils / probability / combinations, not a casino setting.
- [x] Flat side-on 2D battlefield layout selected for the first prototype.
- [x] 640×360 internal canvas with 2× nearest-neighbour viewport scaling specified and implemented.
- [x] Integer stretch mode, fixed aspect and a 640×360 minimum window guard configured.
- [x] Pixel snapping and non-antialiased pixel-cluster contours specified and implemented.
- [ ] Original character bible and visual asset library.
- [ ] Final UI style guide, typography and icon set.

## Foundation

- [x] Standalone project subtree under `casino-battle/`.
- [x] Rust workspace.
- [x] Deterministic core crate.
- [x] 4×4 Fate Board using orthogonally connected clusters (no paylines).
- [x] Initial party roster and recruit cap.
- [x] Automatic battle simulator.
- [x] Axum API endpoints for start, state, draw and battle.
- [x] Optional PostgreSQL JSONB persistence and migration.
- [x] Health endpoint that distinguishes Postgres from memory-only mode.
- [x] Godot 2D pixel-art sandbox with original 16×16 code-drawn sprite maps.
- [x] Godot client is connected to the API for run state, Fate draws and Auto-battle.
- [x] Client replays server-authoritative battle events, damage, healing and defeat states.
- [x] Prototype pixel idle blink/bob, attack lunge, hit flash and healing frame feedback.
- [x] Pixel idle blink/bob, attack lunge, hit flash and healing frame feedback.
- [x] Rust CI workflow.
- [x] Current full CI passed on visual candidate commit `aa512c9ffaefd8dfcb210bcdefd5d0ee49214263` in GitHub Actions run [45892465386](https://github.com/Aloews/full/actions/runs/45892465386): strict 2D/pixel-art audit, Godot 4.3 import and launch, Rust format, Clippy, tests, seeded balance sample, HTTP API smoke, PostgreSQL migration and restart-persistence checks.
- [ ] Re-run full CI after subsequent code changes; the verified commit above is the current tested visual candidate.

## Gameplay systems

- [x] Three-lane targeting with nearest-lane target selection.
- [x] Preparation-only unit lane placement through the client and validated server endpoint.
- [x] Initial unit roles and sigil synergies (two tiers); data-driven content definitions remain open.
- [x] Duplicate merging and rank-up to three ranks (basic prototype).
- [ ] Branching evolution, imprints and traits that alter combat behavior.
- [x] Five first-pass relics with deterministic three-choice rewards after every third boss victory.
- [ ] Larger build-defining core pool.
- [ ] Player-controlled preparation tools: lock, nudge, reroll and pity.
- [ ] Event, shop and route nodes.
- [x] Boss encounters every third wave with a dedicated Mosswood Guardian boss prototype.
- [ ] Elite encounter variety and advanced boss phases.
- [ ] Meta progression and unlocks.
- [x] Server battle event log with tick, source, target, damage, healing and defeat events.
- [ ] Player-facing run summary and detailed damage breakdown.
- [x] Deterministic balance simulation harness with seed batches and distribution reports.
- [x] First 1,000-seed wave-one baseline recorded in `docs/BALANCE_BASELINE.md`.

## Client and art

- [x] Nine distinct 16×16 pixel sprite maps: six allies, two common enemies and one boss; CI checks dimensions, palette keys, silhouette coverage and uniqueness.
- [ ] Final sprite grid audit and tile-size consistency check across production art assets.
- [ ] Production-quality original hero and enemy sprite sheets (current sprite maps are in-client prototypes, not final external art assets).
- [~] Code-level animation prototype: staggered idle bob/blink, attack lunge, hit flash and heal glow; full authored anticipation/contact/recovery/defeat/victory frame strips remain pending.
- [ ] Background biome kits with multiple layers.
- [ ] Pixel-art VFX library with attack, hit, healing, defeat and reward frame strips.
- [ ] UI components with readable text at 1280×720 and Steam Deck scale.
- [ ] Reduced motion and color-accessibility checks.
- [ ] Asset license provenance and source files tracked.

## Backend and production

- [ ] Player identity and run ownership.
- [x] Cross-instance mutation serialization through PostgreSQL row locks; in-memory mode explicitly remains single-process.
- [ ] Player authentication, session ownership and authorization checks.
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


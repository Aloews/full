# Project MAP — Slotbound

## North-star outcome

Deliver a replayable 2D cozy-fantasy roguelite auto-battler. A 3×3 rune board recruits creatures; the player develops a compact army and prepares it for deterministic automatic battles across authored stages, escalating enemy waves and boss encounters. Production quality means a complete, understandable, persistent and balanced player journey—not only a web page that compiles.

## Repository and branch

- Repository: `Aloews/full`.
- Active Slotbound source branch: `feat/slotbound-rust-rebuild`.
- This branch contains an isolated Slotbound project tree at repository root; the default `main` branch is not modified by this work.
- A separate GitHub repository could not be created through the available GitHub actions in this session. Keep the game isolated on this branch until repository creation/transfer is available.
- Vercel project `slotbound` was created in team `aloews-projects`. A preview deployment request was rejected by Vercel's daily deployment API quota (402); no deployment URL is available yet. Do not describe the project as deployed.
- Existing Vercel project `aurel-private-property` is linked to `Aloews/full`; it was not reconfigured or used for Slotbound.

## Current source layout

- `crates/game-core` — pure deterministic gameplay state, rules, commands, progression and battle result.
- `crates/api` — Axum HTTP boundary; serves browser assets and run API; supports PostgreSQL and local JSON storage.
- `crates/api/migrations` — database migrations applied separately by the privileged deployment/migration role.
- `Dockerfile.vercel` / `vercel.json` — Vercel Container runtime definition.
- `web` — responsive browser client; no authoritative game-rule calculations.
- `.github/agents` — specialist role contracts.
- `.github/agent-backlog.json` and `.github/agent-state.json` — scoped tasks and controller state.
- `.github/scripts` — bounded agent controller and policy tests.
- `.github/workflows` — exact-head CI, agent cycle and exact-SHA merge gate.
- `docs` — game concept, style guide, mechanics research, architecture, agent operating model and delivery map.

## Verified implementation in source

- Deterministic run seed/RNG state; repeated seed and initial command reproduce the same starting board.
- 3×3 recruitment board with eight straight three-cell paylines.
- Six unit classes: Guardian, Archer, Mage, Cleric, Rogue and Beast.
- Three matching class symbols on a line summon one unit per winning line; all-nine-equal can complete all eight lines.
- Six spins per wave; first spin 100 gold, each later paid spin costs 50 gold more.
- One vertical column nudge per wave; nudge awards only newly completed matches.
- Roster capacity pressure, unit lock/unlock, keeper selection, donor absorption, stat growth, one current imprint field and promotion choices at absorption thresholds 5 and 12.
- Deterministic tick-based automatic combat (maximum 40 ticks), stable initiative, Guardian-priority targeting, class-specific combat bonuses, Mage splash, Cleric healing, Guardian mitigation, enemy attacks and boss telegraph events.
- Typed combat event history for attacks, healing, unit/enemy defeats and battle completion; surviving unit health persists across waves with a small camp recovery, while defeated units leave the roster.
- Wave-derived enemy groups, boss unit on every fifth wave, hearts and rewards.
- Boss marker every fifth wave; boss victory grants three Core choices.
- Between-wave supply cache with attack, mitigation and healing items.
- Axum endpoints for create/read run, spin, nudge, absorb, promotion, lock, battle, next wave, Core selection and item purchase.
- Browser client with current run-ID recovery, recruitment board, roster, shop, Core selection, battle result and status panels.
- PostgreSQL adapter uses transactions and row-level locking for run updates; local JSON snapshot fallback is single-process only.

## Exact-head verification evidence

The baseline source candidate commit `680ec889595b4defaa590f1721f000630d3c7ab4` passed Slotbound CI in GitHub Actions:
- push run [45849594472](https://github.com/Aloews/full/actions/runs/45849594472);
- pull-request run [45849612291](https://github.com/Aloews/full/actions/runs/45849612291).

The CI workflow includes Rust formatting, Clippy, Rust tests, release build, Vercel container image build, JavaScript syntax, API/browser contract checks and agent patch-policy tests. This evidence applies to that exact source commit only. The later GDD, pixel renderer and combat timeline changes require a new green run on the latest candidate SHA before they can be called verified.

## Product and art direction

- [x] Product direction defined: 2D roguelite auto-battler with symbolic recruitment, army development and wave defence.
- [x] Cozy 16-bit Fantasy Pixel Art direction documented in `docs/VISUAL_STYLE_GUIDE.md`.
- [x] Originality, rendering grid, palette, silhouette, animation, biome, interface and asset QA rules documented.
- [ ] Replace emoji glyphs and prototype interface styling with original production sprite sheets and pixel UI assets.
- [ ] Add bitmap font and asset provenance/atlas manifest.
- [x] Add a first procedural woodland-frontier Canvas scene with a rune shrine, stepped mountains, tree silhouettes and path tiles (composition prototype; not a production tilemap).
- [ ] Create first full biome tile set and parallax/ambient layers.
- [ ] Author animation strips for all common units, enemies and bosses.

## Gameplay roadmap

### S0 — First playable loop
- [x] Rust domain, Axum API and browser client separation.
- [x] 3×3 board, eight paylines and six recruit classes.
- [x] Spin economy, one column nudge and basic roster/absorption.
- [x] Basic promotions, boss/Core reward and item cache.
- [x] Run persistence adapter and exact-head CI on commit above.
- [ ] Real-browser Playwright first-wave journey and reload/restore verification.
- [ ] Verify the new woodland scene and six class sprites at desktop/mobile sizes; add visual regression coverage.

### S1 — Make battles real and readable
- [x] Deterministic tick-based combat timeline with stable initiative and target selection.
- [x] Basic Guardian mitigation, Archer/Rogue/Beast/Mage attack modifiers, Cleric healing and unit deaths/health persistence.
- [x] Boss telegraph events and causal combat event log rendered by the browser.
- [ ] Full lane/position model, armour/shields/status system, cooldown-based abilities and richer boss patterns.
- [ ] Authored enemy definitions and wave compositions (current groups are generated from wave number).
- [ ] Battle outcome properties: empty army, simultaneous defeat, stalemate/turn cap, tie-break order and terminal state.

### S2 — Make runs strategic
- [ ] Versioned Ruleset containing symbol weights, costs, unit data, enemy scaling, rewards and stage rules.
- [ ] Deterministic command history and replay with canonical state hashes.
- [ ] Monte Carlo simulator with seed ranges, sample sizes and uncertainty intervals.
- [ ] Typed imprint slots, donor inheritance and promotion tree.
- [ ] More reel tools (including Blast) with explicit charges, targets, costs and phase rules.
- [ ] Formation positions, role synergies, stage map and route choices.
- [ ] Distinct biomes, enemy families, bosses and environmental effects.

### S3 — Production-quality player experience
- [ ] Original pixel sprite/tile production pipeline, complete character strips, effects and bitmap typography.
- [ ] Responsive and accessible UI; keyboard navigation, focus states, reduced motion and readable combat log.
- [ ] Playwright end-to-end real-browser journeys against the real API.
- [ ] Versioned saves, migration rehearsal, backup/restore, idempotency and ownership/authentication.
- [ ] Rate limits, structured logs, metrics, tracing, crash visibility and security review.
- [ ] Hosted PostgreSQL provisioned and live-checked for the intended environment.
- [ ] Preview deployment, deployed API/player journey smoke and rollback plan.
- [ ] Desktop packaging, build artifacts, release checklist and controlled playtest report.

## AI agent delivery system

- [x] Specialist role contracts exist for architect, game designer, Rust engineer, persistence engineer, frontend integrator, simulation QA and product integrator.
- [x] Scoped backlog, agent task state and patch-policy tests exist.
- [x] Local Qwen/Ollama agent runner and GitHub Actions workflow are defined in source.
- [ ] Verify a real successful agent cycle run before claiming autonomous delivery is active.
- [ ] Adapt workflow branch/base conditions and merge policy to this isolated feature branch before enabling the agent cycle. Current agent workflow targets `main` and the `agents/slotbound-autonomy` branch; do not allow it to open or merge Slotbound work against the unrelated default branch.
- [ ] Human review of workflow permissions and exact merge target.

## Infrastructure and release blockers

- [x] Separate Vercel project `slotbound` created.
- [ ] Preview deployment pending: Vercel returned `402 payment_required` due to `api-deployments-free-per-day` quota (>100 deployments/day); retry only after the provider's 24-hour reset or plan/quota resolution.
- [ ] Production/preview PostgreSQL connection not configured or verified for Slotbound.
- [ ] No production deployment, public playable build or release has been verified.

## Acceptance and stop criteria

A milestone is accepted only when:
1. domain invariants and regression tests pass;
2. fixed-seed tests prove deterministic state and combat output;
3. API tests exercise the real router and actual persistence adapter;
4. browser tests exercise the complete real user journey;
5. the exact candidate SHA has all required CI checks green;
6. an independent QA reviewer records no unresolved critical/high defects;
7. MAP, release notes and deployment claims match observed evidence.

Stop autonomous work and request human triage on unsafe migrations, unexpected branch drift, missing required secrets/permissions, repeated test failures after the repair limit, unexplained balance regressions, or a proposed change to production data/hosting configuration.

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
- Six sigil draws per wave; first paid draw 100 gold, each later paid draw costs 50 gold more.
- One vertical column shift per wave; it awards only newly completed matches.
- Roster capacity pressure, unit lock/unlock, keeper selection, donor absorption, stat growth, one current imprint field and promotion choices at absorption thresholds 5 and 12.
- Deterministic tick-based automatic combat (maximum 40 ticks), stable initiative, Guardian-priority targeting, class-specific combat bonuses, Mage splash, Cleric healing, Guardian mitigation, enemy attacks and boss telegraph events.
- Typed combat event history for attacks, healing, unit/enemy defeats and battle completion; surviving unit health persists across waves with a small camp recovery, while defeated units leave the roster.
- Wave-derived enemy groups, boss unit on every fifth wave, hearts and rewards.
- Five deterministic journey event families with two choices each, resource/unit effects, persisted event history and replay-safe choice handling.
- A three-branch route decision after events with Battle, Rest, Merchant, Elite and BossGate routes; Rest restores hearts and unit HP, Merchant grants gold, Elite adds and strengthens an enemy.
- BossGate is now coded to add 15% ally damage (rounded up with a minimum +1) during the next boss battle; exact-head CI for this change is pending.
- Battle reports persist starting party/enemy snapshots and selected route; the browser renders a deterministic event replay by stable unit ID.
- Boss marker every fifth wave; boss victory grants three Core choices.
- Between-wave supply cache with attack, mitigation and healing items.
- Axum endpoints for create/read run, sigil draw, column shift, absorb, promotion, lock, battle, journey-event choice, route choice, next wave, Core selection and item purchase.
- Browser client with run-ID recovery, Fate Board, roster, shop, Core selection, journey-event choices, route forks, pixel battlefield snapshots and deterministic battle replay.
- PostgreSQL adapter uses transactions and row-level locking for run updates; local JSON snapshot fallback is single-process only.

## Exact-head verification evidence

The baseline source candidate commit `680ec889595b4defaa590f1721f000630d3c7ab4` passed Slotbound CI in GitHub Actions:
- push run [45849594472](https://github.com/Aloews/full/actions/runs/45849594472);
- pull-request run [45849612291](https://github.com/Aloews/full/actions/runs/45849612291).

The latest completed full CI run is [45995006734](https://github.com/Aloews/full/actions/runs/45995006734). It covered the Rust domain/API/browser candidate including branching routes, BossGate damage, stable-ID telegraph targets, route-history trail and legacy-save migration. All required steps passed: format, Clippy, Rust unit/integration tests, release API, Vercel Docker image, JavaScript syntax, API/browser contract and agent patch-policy checks. The workflow format step generated branch head `75bf25a27e29f35ea8491d4904574ae3757019ba` before the remaining checks ran.

**Current gameplay slice:** the API applies and persists ruleset migration on the first read or mutation; unchanged GETs no longer rewrite local JSON or PostgreSQL rows. The battle replay identifies the actual boss telegraph target by stable unit ID and shows the predicted post-mitigation damage before the following hit. The route fork includes the last four selected path nodes as a connected trail. These changes are covered by run 45995006734. Vercel Preview/production deployment remains separate and is not claimed.

## Product and art direction

- [x] Product direction defined: 2D roguelite auto-battler with symbolic recruitment, army development and wave defence.
- [x] Cozy 16-bit Fantasy Pixel Art direction documented in `docs/VISUAL_STYLE_GUIDE.md`.
- [x] Six original 16×16 canvas class-sprite prototypes and the first procedural woodland-frontier scene are rendered by the browser.
- [x] Originality, rendering grid, palette, silhouette, animation, biome, interface and asset QA rules documented.
- [x] Replace the six class emoji placeholders with original coded 16×16 pixel-sprite prototypes and pixel-style UI treatment.
- [ ] Replace the prototype drawing code with a validated, versioned external pixel-asset and sprite-sheet pipeline.
- [ ] Add bitmap font and asset provenance/atlas manifest.
- [x] Add a procedural woodland-frontier Canvas scene with a rune shrine, stepped mountains, tree silhouettes and path tiles (composition prototype; not a production tilemap).
- [ ] Create first full biome tile set and parallax/ambient layers.
- [ ] Author animation strips for all common units, enemies and bosses.

## Gameplay roadmap

### S0 — First playable loop
- [x] Rust domain, Axum API and browser client separation.
- [x] 3×3 board, eight paylines and six recruit classes.
- [x] Spin economy, one column nudge and basic roster/absorption.
- [x] Basic promotions, boss/Core reward and item cache.
- [x] Run persistence adapter and exact-head CI on commit `cea19ed2c8de5731790fbc87999562b0c0b6e739` (run 116).
- [ ] Real-browser Playwright first-wave journey and reload/restore verification.
- [ ] Verify the woodland scene and six class sprites at desktop/mobile sizes; add visual regression coverage.

### S1 — Make battles real and readable
- [x] Deterministic tick-based combat timeline with stable initiative and target selection.
- [x] Basic Guardian mitigation, Archer/Rogue/Beast/Mage attack modifiers, Cleric healing and unit deaths/health persistence.
- [x] Boss telegraph events and causal combat event log rendered by the browser.
- [ ] Full lane/position model, armour/shields/status system, cooldown-based abilities and richer boss patterns.
- [ ] Authored enemy definitions and wave compositions (current groups are generated from wave number).
- [x] Remove player-facing casino/reel terminology: the recruitment device is labelled Fate Board and sigil draws in the UI.
- [ ] Battle outcome properties: empty army, simultaneous defeat, stalemate/turn cap, tie-break order and terminal state.


### S1.5 — Journey events and visible battles (required core loop)

- [x] Army recruitment through the 3×3 sigil board, roster management, keeper/donor absorption, growth and promotions exist in the Rust domain.
- [x] Deterministic automatic battle simulation emits typed combat events and a combat report.
- [x] Add a seeded, weighted event director with deterministic selection across five journey event families (cache, shrine, merchant, ranger, ambush).
- [x] Implement first event families: travelling merchant, treasure/cache, shrine/blessing, wounded ranger/recruit and bandit ambush; elite, hazard, bargain/curse and multi-node story chains remain future content.
- [x] Give each implemented event explicit choices, costs, state effects, rewards and consequences; biome/once-per-run eligibility rules remain future expansion.
- [x] Persist pending event, event history and resolved choice/outcome in GameState; event selection is seeded and reproducible.
- [x] Gate next-wave progression on event resolution; reject invalid, duplicate and out-of-phase event choices.
- [x] Add a deterministic three-branch route fork after each resolved journey event, with standard battle, rest, merchant and elite paths; boss waves offer a dedicated boss gate plus recovery/supply detours.
- [x] Persist selected route and route history; rest heals hearts/units, merchant routes grant gold, elite routes add an enemy and increase enemy stats/rewards, and boss gates lead to the mandatory fifth-wave boss.
- [x] Include a route decision in every between-wave journey, with persisted outcome and a deterministic three-node branch.
- [ ] Expand route choices into a multi-step biome map with connected nodes, dead-end prevention, stage transitions and route-specific narrative events.
- [x] Replace result-only presentation with a pixel battlefield snapshot inferred from the authoritative combat event stream, allied/enemy silhouettes and health bars; lane positions, projectile assets and authored boss phases remain future polish.
- [x] Animate the Rust-authoritative BattleEvent stream as a replay on the pixel battlefield; replay timing does not affect combat outcomes and reduced-motion mode renders the final state immediately.
- [x] Telegraph boss attacks against the actual selected defender using a stable target ID and pre-hit damage preview; the browser renders a warning beam and target frame before the hit.
- [x] Add Guardian Shieldwall: every fourth tick grants up to 2 temporary shield to each living ally (cap 4 per unit); the Rust resolver consumes shield before HP and the browser replay renders shield bars and block events.
- [x] Show the recent expedition route history as a connected path trail alongside the next route fork.
- [x] Migrate legacy intermission saves on first API read/mutation, persist the migrated event/route state, and avoid writes when a GET leaves state unchanged.
- [ ] Add Playwright browser E2E tests for event choice effects, save/restore mid-run, event determinism, battle playback ordering and replay protection (Rust domain and API persistence tests added).


**Journey and battle implementation status:** the Rust domain now generates one seeded encounter after a surviving battle, persists it in the run state, validates two consequential choices and records the selected outcome. Five event families are implemented with seeded selection weights of 25%, 20%, 20%, 15% and 20% respectively: cache, moonwell, merchant, wounded ranger and bandit ambush. The API exposes `POST /api/runs/{run_id}/event`; next-wave progression is blocked until the pending event is resolved. The browser renders the encounter choices and replays the authoritative combat event stream on a pixel battlefield canvas with ally/enemy health bars, target-specific boss warnings and a route-history trail. Legacy saves are migrated and persisted on first access. This is a functional first pass; a multi-step biome map, richer event catalogue, authored combat sprites/lanes and real-browser E2E remain open acceptance work. Battle reports now include server-authored initial ally/enemy formation snapshots with three-lane front/back positions and stack offsets, so the browser renders the actual formation as well as exact starting HP and event deltas. Guardian Shieldwall is resolved in Rust and shown as shield gain/absorption events.

**Acceptance:** a fresh run must demonstrate recruitment → army composition/development → a meaningful non-battle event with at least two consequential choices → an animated battle that visibly corresponds to the authoritative event stream → rewards and a route choice. A screenshot of the battle report alone does not satisfy visible-battle acceptance.

### S2 — Make runs strategic
- [ ] Versioned Ruleset containing symbol weights, costs, unit data, enemy scaling, rewards and stage rules.
- [ ] Deterministic command history and replay with canonical state hashes.
- [ ] Monte Carlo simulator with seed ranges, sample sizes and uncertainty intervals.
- [ ] Typed imprint slots, donor inheritance and promotion tree.
- [ ] More reel tools (including Blast) with explicit charges, targets, costs and phase rules.
- [x] Deterministic three-lane front/back formation positions; server-authored battle snapshots drive lane-local frontline screening, flanking, nearest-lane target selection and pixel battlefield placement.
- [x] Player-controlled formation editing: every unit can move between front/back rows and directly select any of the three lanes; positions persist and are used by Rust combat resolution.
- [x] Automatic recruitment assigns new units to the least-occupied lane in their class-default row, respecting prior player rearrangements; ties select the lower lane.
- [ ] Formation synergies, stage map and advanced route choices.
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

- [x] Specialist role contracts exist for architect, game designer, Rust engineer, persistence engineer, frontend integrator, simulation QA, product integrator and Pixel Art Director.
- [x] Scoped backlog, agent task state and patch-policy tests exist.
- [x] Local Qwen/Ollama agent runner and GitHub Actions workflow are defined in source.
- [ ] Verify a real successful agent cycle run before claiming autonomous delivery is active.
- [x] Add task-specific implementing-agent metadata to the task backlog and a pixel-art specialist role contract.
- [x] Validate role-to-contract resolution for pixel-art and unknown role cases in controller unit tests.
- [ ] Adapt workflow branch/base conditions and merge policy to this isolated feature branch before enabling the agent cycle. The controller currently opens agent PRs against `main` and uses an `agents/slotbound-autonomy` branch. Do not enable it until the exact base and PR target are corrected and reviewed.
- [ ] Human review of workflow permissions and exact merge target.

## Infrastructure and release blockers

- [x] Separate Vercel project `slotbound` created.
- [ ] Preview deployment pending: Vercel returned `402 payment_required` due to `api-deployments-free-per-day` quota (>100 deployments/day); retry only after the provider's 24-hour reset or plan/quota resolution.
- [ ] Production/preview PostgreSQL connection not configured or verified for Slotbound.
- [ ] The working branch is isolated inside `Aloews/full`, not yet transferred to a dedicated GitHub repository. The available GitHub connection does not expose repository creation.
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

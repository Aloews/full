# Project MAP — Slotbound

## North-star outcome

Deliver a replayable, persistent roguelite defence game where the 3×3 recruitment machine, unit development, items, Cores, and auto-battler combat form one coherent decision system. Build an original implementation with independently authored assets and clear provenance for all balance data.

## Current repository shape

- `crates/game-core` — pure deterministic gameplay state, rules, commands, progression and combat summary.
- `crates/api` — Axum HTTP boundary; owns no gameplay rules. Serves browser assets and run API, with file and PostgreSQL storage adapters.
- `crates/api/migrations` — versioned database migrations applied by the privileged deployment/migration step; the runtime role does not have DDL rights.
- `Dockerfile.vercel` / `vercel.json` — Vercel Container runtime for the Axum server.
- `web` — responsive browser client; no game-rule calculations beyond presentation previews.
- `.github/agents` — role contracts for architecture, game design, Rust, persistence, frontend, QA and product integration.
- `.github/workflows` — exact-SHA CI and bounded AI-agent cycle.
- `docs` — concept, mechanic research, architecture decisions, testing and execution map.

## Verified implementation scope in this candidate

The source candidate contains:
- Deterministic RNG state stored in a run; fixed seeds reproduce the same first spin board.
- Eight 3-cell paylines over a 3×3 board.
- Six class symbols and one unit summoned per matching line; all-nine-equal jackpot resolves eight winning lines.
- Six spins per wave, first spin 100 gold and subsequent paid spins +50 gold.
- One vertical column nudge per wave, awarding only newly completed class/line matches.
- Roster capacity check before a new spin; a completed spin may temporarily push the roster over capacity, after which absorption is needed.
- Lock/unlock, donor absorption, stat growth, one imprint, promotion choices at absorb levels 5 and 12.
- Deterministic wave/boss power resolution, hearts, gold rewards, three Core choices after a boss win, and a between-wave item cache.
- Axum endpoints for create/read run, spin, nudge, absorb, promotion, lock, battle, next wave, Core selection and item purchase.
- Transactional PostgreSQL save/load via `SLOTBOUND_DATABASE_URL` or fallback `DATABASE_URL`, including row-level locking for each game command. Production schema migrations are applied separately by a privileged deployment role; the application role has only table CRUD permissions. Local JSON snapshots remain the development fallback.
- Browser client with local run-ID recovery, responsive panels, machine, roster, shop, cores, battle results, and action feedback.

These are code-level statements. Runtime/CI status must be added only after GitHub Actions completes on the exact commit.

## Known limitations — do not describe as release-ready

- The battle is a deterministic power comparison, not a unit-by-unit combat simulation.
- Reels currently use uniform class selection; no published probability table has been calibrated.
- Nudge is a simplified vertical column rotation; Blast and other reel tools are not implemented.
- Imprints are represented by one string; inheritance and multiple skill slots are incomplete.
- Factions, traits, rarity tiers, awakening, stage selection, campaign map, enemy abilities, equipment slots, and endless mode are not implemented.
- Local JSON fallback is single-process only. Vercel deployment must use `SLOTBOUND_DATABASE_URL` (or fallback `DATABASE_URL`); PostgreSQL transactions and row-level locks are required for shared serverless instances.
- Authentication, online multiplayer, analytics, crash telemetry and production backup/restore are not implemented.
- Browser UI has static contract checks; automated real-browser end-to-end coverage remains a release gate.

## Execution order

### S0 — First playable slice (current candidate)
- [x] Domain/API/client split.
- [x] Basic slot → recruit → absorb → battle → next wave loop.
- [x] Deterministic seed and state machine.
- [x] First save/load implementation.
- [x] Exact-head CI green on the deployed candidate; independent QA review remains a separate release gate.
- [ ] Real-browser smoke/E2E test; deployed HTTP/API smoke and database persistence have been verified separately.

### S1 — Combat and progression correctness
- [ ] Unit-by-unit combat ticks, targeting, blocking, abilities, cooldowns and statuses.
- [ ] Enemy roster, wave composition, boss patterns and casualties.
- [ ] Multiple imprint slots, donor inheritance rules and promotion tree.
- [ ] Formation/positioning and role synergies.
- [ ] Blast and other machine tools with explicit cost/cooldown semantics.

### S2 — Balance and replayability
- [ ] Versioned `Ruleset` config; no hard-coded balance constants in handlers.
- [ ] Weighted symbol distributions, Monte Carlo run simulator and economy reports.
- [ ] Deterministic command log/replay and property-based invariants.
- [ ] Stage progression, faction rules, traits, rarity and endless mode.

### S3 — Persistence and product hardening
- [ ] Versioned save migrations, backup/restore, checksums and corrupted-save recovery.
- [x] PostgreSQL adapter with transactions and row-level locking for multi-instance safety.
- [ ] Idempotency keys and schema migration rehearsals on a disposable branch.
- [ ] Auth, player ownership, rate limits and abuse protection.
- [ ] Playwright end-to-end journeys and accessibility audit.
- [ ] Build artifacts, signed desktop packaging, crash reporting and release checklist.

## S0.5 — Retro pixel UI pass (branch-only, unverified)
- [x] Restore original 16-bit pixel-art design direction to product concept.
- [x] Add an override stylesheet for square pixel panels, chunky borders, palette, and short stepped win flash.
- [x] Wire `web/pixel.css` before the existing base stylesheet so original layout rules stay intact and pixel overrides win.
- [ ] Run CSS/HTML validation and real browser screenshot inspection.
- [ ] Replace glyph/emoji placeholders with original sprite-sheet assets.
- [ ] Add battle scene/event feed visuals after combat simulation emits structured events.

## Next implementation milestones

1. **S1-A Combat event model (Rust core):** expose deterministic event records (battle start, enemy spawn, target selection, hit, block, status, unit defeated, wave result) in the battle report. Keep simulation seed and event ordering deterministic; add exact-seed replay tests.
2. **S1-B Tactical auto-battle:** replace power-only resolution with tick-based unit simulation, class-specific attack range/target rules, cooldown/status timers, Guardian interception, Cleric healing, enemy wave compositions and boss patterns. No client-side rules.
3. **S1-C Living-world events:** add event deck/weighting driven by wave, party traits, class composition, recent outcomes, and deterministic RNG; each event must have choices, costs/effects, and logged consequences. Validate action availability and reject invalid choices without mutating state.
4. **S1-D Army and formation:** define slot/position data, roster reserve, battlefield placement, party synergies, casualty/injury states and formation UI. Explicitly test limits and overflow.
5. **S1-E Playable journey:** automate start → spin/recruit → select keeper/absorb → event choice → battle → reward/cache → next wave → boss/core with browser and API assertions.

## Acceptance gates

A milestone is accepted only when its domain invariants pass, fixed-seed replays match, API tests exercise the real router, save/load round-trips preserve state, browser journeys use the real API, CI is green on the exact candidate SHA, and an independent QA role records no unresolved critical/high defects. A successful compile alone is not acceptance.

## Branch isolation

This branch is based on current `main` SHA `d9cb82d10104e3b6a019274193f74d57cb385325`. Pixel UI edits are intentionally isolated; production deploy and merge are not authorized by this branch-only continuation. The last deployed version is not assumed to include this branch.

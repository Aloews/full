# Slotbound — AI Agent Execution Plan

## Purpose
Run a bounded software-delivery pipeline in which specialist role prompts implement and verify small Slotbound tasks. Agents are contributors, not release authorities. The repository, deterministic tests, exact-head CI and runtime observations are the source of truth.

## Current topology
The current automation uses **one Qwen 2.5 Coder 3B model served by Ollama on a GitHub Actions runner**. The orchestrator invokes it with different role contracts. These are role-separated stages, not separate independent foundation models. Do not advertise a live multi-model fleet.

| Stage | Role | Output |
|---|---|---|
| 1 | Systems Architect | minimal implementation plan, domain boundaries, invariants and risks |
| 2 | Game Systems Designer | design/economy/probability review; labels assumptions |
| 3 | Specialist Implementer | one bounded diff in its owned files |
| 4 | Simulation QA / Red Team | adversarial review, regression and edge-case evidence |
| 5 | Product Integrator | full-slice and MAP accuracy review |
| 6 | GitHub CI | exact candidate validation |
| 7 | Merge gate | exact-head merge into isolated Slotbound integration branch |

The same Qwen model is prompted separately for architecture, implementation, QA and product review. This is useful role separation, but not equivalent to independent human review or different models. High-risk security, workflow, migration and release decisions still require human approval.

## Roles and ownership

| Role | Main write area | Expected artefacts |
|---|---|---|
| Systems Architect | `docs/ADR/**`, architecture docs | typed contracts, state machine, deterministic RNG/replay, save compatibility |
| Game Systems Designer | `docs/**`, ruleset proposals | classes, event logic, resource curves, probabilities, balance hypotheses |
| Rust Gameplay Engineer | `crates/game-core/**` | authoritative transitions, combat and deterministic tests |
| Persistence Engineer | `crates/api/**`, migrations | atomic transactions, locking, migrations, idempotency, recovery |
| Frontend Integrator | `web/**` | presentation of authoritative state/events, responsive UI, accessibility/E2E |
| Pixel Art Director | art manifests and assets | palette, spritesheets, tile sets, frame metadata and asset QA |
| Simulation QA / Red Team | tests/test-only tools | property tests, edge cases, seed sweeps, API/persistence abuse tests |
| Product Integrator | `docs/MAP.md`, release docs | acceptance, evidence, scope and release decision |

Every task names one implementing role and a different review role. No agent may treat its own implementation review as final release approval.

## Branch model

- Current code baseline: `feat/slotbound-rust-rebuild`.
- Integration/base branch for this iteration: `feat/slotbound-release-candidate`.
- Autonomous task branch: `agents/slotbound-release-candidate`.
- Default `main` is never an agent PR target in this workflow.

An agent PR targets only the integration branch. Exact-head green CI may merge that PR into the integration branch. After merge, the workflow dispatches CI on the integration branch; after its success the next backlog task can start.

Before merge verify: PR open and not draft; PR head equals successful workflow SHA; base is the integration branch; required CI check is successful on that exact SHA; no failing/cancelled/timed-out/action-required checks; no stale head or unexpected base drift. Never force-push main, merge directly into main or weaken checks. Final integration into main requires human review.

## Task lifecycle

1. Preflight triggering SHA, branch, open PRs, backlog and active-task state. Refuse overlapping work.
2. Select the first unmerged task in `.github/agent-backlog.json`; every task has objective, implementing role and executable acceptance criteria.
3. Architect prompt reads `AGENTS.md`, product concept, MAP and target files; returns minimal plan and risks.
4. Designer prompt checks meaningful choices, economy and class identity; labels assumptions.
5. Specialist receives one scoped task and produces a text diff.
6. Policy rejects patches over 16 KB, over eight files, binary content, deletes, renames, symlinks, lockfiles, secret paths, workflows and paths outside allowlist.
7. Run formatting, Clippy, Rust tests, release build, browser JS syntax, API/browser contract and agent-policy tests.
8. QA role reviews the diff/test output; Product Integrator checks the whole slice and MAP. Either may reject.
9. Commit one task and open one PR against the integration branch.
10. Run CI on PR head. Any later commit invalidates previous green status.
11. Merge only the exact green PR. A failed candidate has at most two bounded repair attempts, then pauses for human triage.
12. Dispatch CI on updated integration branch; successful completion triggers the next bounded task.

## Agent write allowlist

- `crates/game-core/**`
- `crates/api/**`
- `web/**`
- `docs/**`
- `tests/**`
- `tools/**`
- root files `Cargo.toml`, `README.md`, `AGENTS.md`

Agents may not edit `.github/workflows/**`, `.github/agent-state.json`, their own policy tests, lockfiles, environment files, secrets, credentials, private keys, production endpoints, Vercel settings, domains, database resources or production data. Workflow, permission, secrets, migration and deployment changes require explicit human review.

## Backlog order

1. GAME-001 — deterministic command history and replay.
2. GAME-002 — tactical combat: positions, armour, shields, cooldown abilities, statuses and boss patterns.
3. GAME-003 — versioned Ruleset and seeded Monte Carlo balance simulator.
4. GAME-004 — second sigil manipulation tool and modifier loadout.
5. GAME-005 — typed imprint slots and promotion branches.
6. GAME-006 — authored stages, enemy roster and boss abilities.
7. GAME-007 — Playwright real-browser journeys, reload and restore.
8. GAME-008 — original pixel-art pipeline, spritesheets and Mosslight Meadow tiles.
9. GAME-009 — complete battle playback from authoritative events.
10. GAME-010 — save schema, idempotency, ownership and recovery.
11. GAME-011 — extend the implemented per-wave three-choice route fork into a persistent multi-stage route graph with biome transitions.
12. GAME-012 — implement event expansion, biome eligibility, delayed consequences and frequency telemetry; designer provides separate reviewed content proposal.

Dependencies: tactical combat and Ruleset precede large-scale balance; route map precedes a full campaign; manifest/style guide precede bulk asset generation.

## Required checks

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo build --release --workspace
node --check web/app.js
python3 tools/check_contract.py
python3 -m unittest discover -s .github/scripts -p 'test_slotbound_agent_cycle.py' -v
```

API/persistence changes need real integration tests. Browser changes need Playwright against the real API. Balance changes need reproducible seed ranges and uncertainty intervals. Art changes need manifest validation and inspection at native/integer-scaled sizes.

## Stop and escalation

Require human triage on production data/infrastructure changes; unsafe migrations; branch drift or unrelated commits; missing runner/provider access; repeated QA rejection after the repair limit; unexplained determinism/balance regression; workflow permissions, secrets or protected branch changes; or a failure that cannot be isolated.

## Truth and activation

Workflow files, role prompts and the Qwen script are configuration, not evidence that an agent ran. Agent automation is active only after Actions shows an actual successful `Slotbound AI Agent Cycle` on the intended integration branch and the run creates a validated task PR. A task is complete only after merge and exact-head CI.

The runner uses one Qwen 2.5 Coder 3B model with role prompts. No separate Claude/GPT models or external agent APIs are configured here. A green local orchestrator test does not prove model availability, task completion or production readiness.


## Current source baseline

The current source already contains five seeded journey-event families, two-choice event outcomes, persisted route selection, three-choice per-wave route forks (Battle/Rest/Merchant/Elite/BossGate depending on encounter), route consequence logic, and browser route-fork presentation. GAME-011 must extend this into a connected multi-stage route graph and biome progression; it must not rebuild the per-wave fork. The current battle resolver is a deterministic 40-tick system with typed replay snapshots and BossGate bonus; lane grids, cooldown abilities, shields and statuses remain future work. Consult `docs/BATTLE_SIMULATION_RULES.md` for current formulas.

## Agent context inputs

Every task planner and implementer must read `docs/GAME_DESIGN.md`, `docs/VISUAL_STYLE_GUIDE.md`, `docs/BATTLE_SIMULATION_RULES.md`, `docs/PRODUCT_CONCEPT.md` and `docs/MAP.md`. These files distinguish current implementation from planned product behaviour. Never implement a “future” feature twice or mark it complete from the existence of a UI mock.

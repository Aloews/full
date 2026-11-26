# AI Agent Operating Model — Slotbound

## Objective

Use a bounded, reviewable software-delivery pipeline in which specialist agents can implement small tasks without changing game rules in multiple layers, weakening persistence, editing secrets or declaring work complete without evidence.

Agents are contributors, not authorities over release quality. The source of truth is the committed repository, deterministic tests, exact-head CI and runtime observations.

## Roles and file ownership

| Role | Responsibility | Primary write area |
|---|---|---|
| Systems Architect | Domain boundaries, state machine, deterministic RNG, command/event contracts, ADRs | `docs/ADR/**`, `docs/ARCHITECTURE.md` |
| Game Systems Designer | Economy, class identities, symbol weights, progression, waves, items, cores and balance hypotheses | `docs/**`, ruleset proposals; no direct gameplay implementation |
| Rust Gameplay Engineer | Typed domain commands, invariants, combat resolution, deterministic replay | `crates/game-core/**` |
| Persistence Engineer | Run repository, migrations, atomic writes, row locks, recovery and idempotency | `crates/api/**`, migrations |
| Frontend Integrator | Browser projection, accessible controls, responsive UI, complete player journey | `web/**` |
| Simulation QA / Red Team | Independent test design, exploit hunting, deterministic seed sweeps, save/API adversarial tests | test files and test-only tools |
| Product Integrator | End-to-end acceptance, MAP accuracy, release evidence and scope control | `docs/MAP.md`, release docs |

A task has one implementing role and a different reviewer. Do not let the author self-approve a high-risk game-rule or persistence change.

## Delivery flow

1. **Triage:** select one uncompleted backlog item. Confirm the current branch head, existing PRs and active task state. Refuse overlapping work.
2. **Architect plan:** the Systems Architect reads the product concept, MAP and target files, returns a minimal ordered plan, identifies invariants and names the relevant tests.
3. **Design check:** the Game Systems Designer verifies that proposed changes preserve meaningful choices, economy constraints and class identity. Balance assumptions are labelled as assumptions until supported by seeded simulations or controlled playtests.
4. **Implementation:** one specialist implements only the scoped change. Game logic stays in Rust domain code; HTTP handlers validate transport only; the browser renders authoritative server state.
5. **Local verification:** formatting, Clippy, unit/integration tests, release build, JavaScript syntax, API/browser contract and agent patch-policy tests run before a PR is opened.
6. **Independent QA:** Simulation QA reviews the diff and evidence as a non-author. It attempts to reject invalid transitions, nondeterminism, arithmetic overflow, replay drift, persistence rollback defects, client/server duplication and uncovered edge cases.
7. **Product integration:** Product Integrator checks the complete user journey, MAP accuracy, task acceptance and remaining release risks.
8. **Pull request:** one task per PR, with acceptance criteria, candidate base SHA, changed paths and check evidence.
9. **Exact-head gate:** CI must pass on the PR's current head SHA. Any new commit invalidates previous evidence. A failed candidate is repaired only within a bounded retry count; after the limit the task pauses for human triage.
10. **Release decision:** never treat a green build as proof of a complete game. Human release review checks playable journeys, saved progress, balance results, accessibility, runtime behaviour and deployment readiness.

## Existing automation in this repository

The repository includes:
- role contracts in `.github/agents/`;
- a JSON backlog and task state file;
- a Python agent-cycle controller with a strict path allowlist, patch-size/file-count limits, delete/rename/symlink rejection and bounded repair attempts;
- a GitHub Actions workflow that installs a pinned Ollama runtime and pulls `qwen2.5-coder:3b`;
- exact-head CI with Rust, PostgreSQL, container, browser syntax and policy checks;
- an auto-merge workflow that checks the exact successful candidate before merging an eligible automation PR.

The configured model is a local Qwen 2.5 Coder 3B runner, not proof of a multi-model team or external Claude/GPT agents. Each backlog task now names an implementing role, with role-to-contract routing validated by unit tests. Pixel-art work has a dedicated Pixel Art Director contract. The orchestrator still does not start on this branch until its trigger/base/PR-target wiring is corrected; role metadata and green policy tests do not count as an executed agent cycle. The workflow source is present, but automation is only considered active when a real run appears in Actions and passes. Do not infer agent activity from the existence of YAML, an agent manifest or a role prompt.

## Current branch and activation constraint

The working Slotbound source is isolated on `feat/slotbound-rust-rebuild`; the repository default branch is `main`. The current agent-cycle workflow is wired around successful CI on `main` and repair events for `agents/slotbound-autonomy`. The Python controller also creates its automation PR against `main`.

Therefore the configured cycle must **not** be activated from this feature branch as-is: its branch/base assumptions could target the unrelated default-branch tree. A workflow maintainer must explicitly adapt and review the workflow conditions, PR base branch and auto-merge policy for the selected Slotbound integration branch before enabling autonomous delivery. Workflow and permission changes require human review; the model-generated patch allowlist intentionally excludes them.

No secrets or production database credentials belong in the repository or agent prompts. Model provider configuration must be explicit, scoped and auditable.

## Task contract

Each backlog task must define:
- a stable ID and one-sentence outcome;
- allowed files and forbidden files;
- prerequisites and dependencies;
- domain invariants that must remain true;
- deterministic examples and failure cases;
- acceptance tests that exercise real boundaries where relevant;
- metrics/simulation criteria where balance is affected;
- rollback or migration considerations;
- the exact evidence needed for acceptance.

## Global invariants

- A fixed seed, ruleset version and ordered command sequence produce the same canonical game state and combat event log.
- Invalid commands do not change state, spend resources, advance RNG or append events.
- Economy, symbol distribution, progression and combat rules have one authoritative implementation in `slotbound-core`.
- API state transitions are atomic. Persistence failure leaves the prior state intact.
- Multi-instance hosting requires PostgreSQL transactions and row-level locking; local JSON persistence is single-process only.
- Browser code never decides summon probability, attack outcomes, rewards, costs or progression.
- Every fix has a regression test. Balance changes have reproducible seeded simulation evidence.
- Save format changes are versioned and backward-compatible or have an explicit migration.
- No workflow, secret, credential, or production setting is modified by an unreviewed agent patch.

## Required checks

Run on the exact candidate:
```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo build --release --workspace
node --check web/app.js
python3 tools/check_contract.py
python3 -m unittest discover -s .github/scripts -p 'test_slotbound_agent_cycle.py' -v
```

A PR is acceptable only when all required checks are green on its current head and the independent reviewer records no unresolved critical or high-severity issue.


## Isolated Slotbound delivery branch

The current agent-delivery branch pair is documented in `docs/AI_AGENT_EXECUTION_PLAN.md`: integration branch `feat/slotbound-gdd-agent-routing` and task branch `agents/slotbound-gdd`. Workflow conditions, PR base and exact-head merge checks are configured for this pair only. The default `main` branch is not the agent PR base. The runner still uses a single Qwen 2.5 Coder 3B model with distinct role prompts; execution status must be read from GitHub Actions, not inferred from these files.

See `docs/GAME_DESIGN.md` for the canonical 3×3 Fate Board and complete game specification. The 4×4 board prototype from the separate Casino Battle branch is not part of Slotbound.

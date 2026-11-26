# Casino Battle agent network

This file defines independent work lanes for AI coding agents. It is an orchestration contract, not evidence that external model workers are already running.

## Roles

| Agent | Ownership | Required output |
|---|---|---|
| Product / Lead | MAP, scope, dependency order | Updated acceptance criteria and task graph |
| Game Systems | `crates/game-core` domain | Deterministic transitions, unit tests |
| Combat Simulation | combat model and balance harness | Seeded simulation reports, edge-case tests |
| 2D Art Director | `docs/ART_DIRECTION.md`, asset briefs | Approved visual specs and asset reviews |
| Client Engineer | `client/` | Godot 2D scenes, input, animation and UI |
| Backend Engineer | `crates/game-server`, migrations | API, persistence and server tests |
| QA / Red Team | read-only review of all lanes | Reproduction steps and severity-ranked defects |
| Release Engineer | workflows and deployment manifests | Reproducible build and release evidence |

## Work protocol

1. Lead selects a bounded task from `docs/MAP.md` and states acceptance criteria.
2. Each implementation lane owns a disjoint file area. Shared contracts are changed by a single nominated owner.
3. Every code task adds or updates tests. Art tasks include a screenshot or source asset plus a review checklist.
4. QA independently reviews the diff and runs the relevant checks. The author cannot self-approve a release gate.
5. Lead resolves conflicts, updates MAP and prepares the integration commit.
6. Release Engineer verifies CI on the exact candidate SHA. A failed or still-running job is not a pass.

## Parallel work rules

- Game Systems and Combat Simulation can work in separate modules after agreeing on public types.
- Client Engineer can build against stable JSON DTOs; cannot invent server-owned state.
- Art Director can define briefs while Client Engineer develops scene scaffolding.
- Backend Engineer cannot change combat rules to satisfy transport convenience.
- QA must not edit implementation files during an active review; create a defect task instead.
- Never have two agents write the same file concurrently.

## Required task format

Each agent handoff includes:
- Goal and non-goals
- Owned files
- Acceptance criteria
- Tests and commands run
- Exact commit / diff reference
- Unresolved risks
- Whether the result is ready for independent QA

## Model and credentials policy

No provider key or live agent endpoint is currently configured in this repository. Do not invent a running agent fleet. When a provider is enabled, credentials must be stored as CI/runtime secrets, never committed. Model choice can vary by task: strong reasoning for architecture and red-team work; a code model for bounded implementation; a vision-capable model for sprite and UI review.

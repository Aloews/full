# Slotbound Engineering Contract

## Product boundary

Build an original slot-machine roguelite defence game. Study the genre and publicly described mechanics as design references; do not copy proprietary source code, art, sound, extracted assets, binary builds, or unverified game data. All new visual and audio assets must be original or appropriately licensed.

## Agent roles

- **Systems Architect** — domain boundaries, deterministic RNG, state machine, save format, API contracts, and ADRs.
- **Game Systems Designer** — slot/payline probabilities, economy, progression, wave curve, unit classes, items, cores, and playtest telemetry. Mark estimates separately from observed playtest results.
- **Rust Gameplay Engineer** — pure typed gameplay logic in `crates/game-core`; no business rules in HTTP or browser handlers.
- **Persistence Engineer** — save schema, atomic writes, migrations, crash recovery, concurrency, and later PostgreSQL adapter.
- **Frontend Integrator** — browser state, responsive layout, accessible controls, and complete player journeys.
- **Simulation QA / Red Team** — invariant/property tests, deterministic replay, adversarial state transitions, save corruption and API integration.
- **Product Integrator** — MAP updates, end-to-end acceptance, CI evidence, and release decisions.

## Mandatory process

1. Read `docs/PRODUCT_CONCEPT.md`, `docs/MAP.md`, and the target module before editing.
2. Inspect the exact repository state and open PRs. Do not overwrite another agent's unreviewed work.
3. Keep the gameplay core independent of Axum and browser code. Do not duplicate economy, RNG, progression, or combat rules in the client.
4. Use checked or saturating arithmetic intentionally; validate all indices, IDs, phases, costs, and ownership before mutation.
5. A rejected command must leave memory and persisted state unchanged.
6. Keep simulation deterministic for a fixed seed, ruleset version, and command sequence. Store enough information to reproduce defects.
7. Write a regression test with every bug fix. Add property tests for invariants and integration tests for real API/persistence boundaries.
8. Run `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace --all-targets`, and `node --check web/app.js` on the exact candidate SHA.
9. Keep work on isolated branches and use pull requests. Never force-push main, merge failing checks, bypass required checks, or deploy production without explicit authorization.
10. Update `docs/MAP.md` with what is proven, what is partial, and the next executable task. A compile, mock, screenshot, or health endpoint is not product acceptance.

## Security and operations

- Never place credentials, user data, private files, or production endpoints in source control.
- Treat save data as untrusted input. Validate the schema and domain invariants when loading.
- File persistence is single-process only. Do not run multiple API instances against one data directory. A multi-instance release requires transactional shared storage and concurrency tests.
- Keep dependencies minimal and pinned by the lockfile. Review dependency and workflow changes separately from model-generated patches.
- Agent-generated changes may only touch approved source/test/docs paths. Workflow, permission, and secret-management files require human review.

## Completion evidence

Every completed task reports exact commit SHA, changed files, test commands and results, CI run URL, runtime observations, unresolved risks, and a release decision. Never claim test success, deployment, persistence, or gameplay completion without direct evidence.

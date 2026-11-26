# Testing and release evidence

## Required local checks

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo build --release --workspace
node --check web/app.js
python tools/check_contract.py
python -m unittest discover -s .github/scripts -p 'test_slotbound_agent_cycle.py' -v
```

## Domain test coverage

The current domain tests cover the eight paylines, fixed-seed spin determinism, spin economy, all-cell jackpot line resolution, capacity lockout, nudge limits, donor consumption, absorb lock validation, promotion thresholds, between-wave absorption, boss rewards and Core selection, shop healing, mandatory Core choice, run loss, and wave-state transitions. Journey-event tests cover seeded selection, all five event effect branches, insufficient gold, full-roster recruitment, invalid/duplicate choices, event gating and resolution history. Route tests cover seeded three-option forks, rest and merchant effects, elite encounter scaling/rewards, boss-gate constraints, invalid/replayed selections and next-wave gating. Battle reports are tested for authoritative starting formations; legacy-save deserialization verifies new event, route and snapshot fields default safely.

## API test coverage

The API tests cover health, run creation/read, a real spin action, persisted snapshot reload in a fresh router instance, invalid phase rejection, and journey-event resolution persistence/replay rejection through the event endpoint, and branching route selection persistence/replay rejection through the route endpoint. The browser currently has JavaScript syntax and static API/DOM contract checks, including the journey-event and route endpoints, both choice flows, pixel battlefield starting snapshots and replay integration. The battlefield replay supports skip and reduced-motion rendering. Real-browser E2E, visual regression and a full tactical lane/sprite presentation are outstanding release gates.

## Evidence policy

CI checks must be read from the exact candidate commit. A local command that could not execute is not a pass. A green build does not prove deployment, multi-user isolation, multi-process persistence, balancing, or full feature parity.


## Current verification boundary

The event-system, API and browser changes are authored on `feat/slotbound-rust-rebuild`. They have not yet been confirmed by an exact-head GitHub Actions run. The previously documented passing CI run applies only to its earlier commit and must not be used as evidence for the current candidate. Vercel has reported a daily build-rate-limit failure; no deployment is claimed.


The Rust game-core test target now declares `serde_json` as a dev-dependency for backwards-compatibility fixtures; `Cargo.lock` already includes the workspace package.

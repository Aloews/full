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

The current domain tests cover the eight paylines, fixed-seed spin determinism, spin economy, all-cell jackpot line resolution, capacity lockout, nudge limits, donor consumption, absorb lock validation, promotion thresholds, between-wave absorption, boss rewards and Core selection, shop healing, mandatory Core choice, run loss, and wave-state transitions.

## API test coverage

The API tests cover health, run creation/read, a real spin action, persisted snapshot reload in a fresh router instance, and invalid phase rejection. The browser currently has JavaScript syntax and static API/DOM contract checks. Real-browser E2E and visual regression are outstanding release gates.

## Evidence policy

CI checks must be read from the exact candidate commit. A local command that could not execute is not a pass. A green build does not prove deployment, multi-user isolation, multi-process persistence, balancing, or full feature parity.


## Current validation candidate

The isolated Slotbound validation branch `feat/slotbound-validation` is used to execute the exact-head CI workflow without merging the product branch into `main`.

# Slotbound

A Rust-first, original slot-machine roguelite defence prototype. The project is structured as a deterministic gameplay domain, an Axum API, and a browser client. It is an independent implementation; it does not contain code, assets, audio, data tables, or binaries from the commercial game.

## Run locally

Requirements: Rust 1.85+ (stable), Cargo, and a supported desktop browser.

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
cargo run -p slotbound-api
```

Open `http://localhost:3000`. Runs are saved as atomic JSON snapshots in `.slotbound-data/runs` by default. Set `SLOTBOUND_DATA_DIR` to a writable persistent directory when deploying the API. The current storage adapter is single-process file storage; it is not a substitute for shared PostgreSQL storage in a multi-instance deployment.

## Current playable loop

- Roll a 3×3 board. Three matching symbols on any of eight straight paylines summon a unit.
- Six spins are available per wave. Paid spin cost rises by 50 gold each time, starting at 100.
- Use one column nudge per wave to alter the last board and capture newly completed lines.
- Manage the roster, lock units, absorb donors into a keeper, gain imprints, and choose promotions at growth thresholds.
- Resolve an automatic battle, earn gold, take damage when the formation loses, and progress to the next wave.
- Every fifth wave is a boss encounter. A victory offers one of three Cores; the between-wave cache sells permanent items and healing.

The current build is a first playable slice, not a feature-complete recreation. See `docs/MAP.md` for implemented scope, limitations, and the next release gates.

## Engineering contract

`AGENTS.md` is mandatory for contributors and coding agents. Gameplay rules belong in `slotbound-core`, not UI handlers. Material state transitions must be deterministic for a fixed seed and input sequence, validated before mutation, persisted atomically, and covered by tests. CI on the exact candidate commit is a release gate. Never state that a build or runtime is verified without evidence from the relevant job or test.

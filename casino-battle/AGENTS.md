# Casino Battle engineering contract

## Product contract

1. The game is a **2D roguelite auto-battler**. Do not introduce player-controlled action combat.
2. Keep the screen, characters, enemies, effects, backgrounds and UI in 2D. Do not add 3D, pseudo-3D, isometric 3D assets or 3D cameras.
3. Art direction is mandatory. Read `docs/ART_DIRECTION.md` before changing visual code or adding assets.
4. Casino logic is an abstract fate/sigil draw and probability system. The game must not look like a real-world casino.
5. The player makes meaningful decisions between and around automated battles: party composition, placement, draw manipulation, upgrades, relics and risk management.
6. Do not copy Slotbound source code, assets, audio, sprites, data tables or exact UI. Use it only as a high-level reference for readable hand-crafted 2D presentation and the preparation-to-auto-battle loop.

## Engineering contract

- Rust domain code is deterministic for a fixed seed and input sequence.
- Validate a command before mutating run state.
- Keep gameplay rules in `crates/game-core`; server handlers only validate transport input, load state, call the domain and persist the result.
- Persist a completed transition atomically when PostgreSQL is enabled.
- Add tests for every material state transition, edge case and RNG rule.
- Keep errors explicit; never silently repair invalid player actions.
- Do not use client-provided combat outcomes or reward values as authority.
- Do not add real-money wagering, real-money cash-out or paid random rewards.
- Do not store credentials in the repository. Never log connection strings or secrets.
- Keep the client in Godot's 2D node family (`Node2D`, `Control`, `Sprite2D`, `CanvasItem`). Reject `Node3D`, `SubViewport` 3D scenes, meshes and perspective cameras.
- The in-memory server store is development-only and must never be treated as safe for multiple replicas.

## Verification

Run from this directory:

```sh
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-targets
```

Do not claim a test, CI run, deployment or database connection succeeded without its actual result. A green local test is not a production release approval.

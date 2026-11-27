# Product Concept — Slotbound

## Product definition

A tactical roguelite defence game in which a 3×3 symbol machine recruits a small army. The player manages a scarce spin budget, decides which recruits to keep or absorb, develops unit roles, selects machine/army modifiers, and prepares for escalating enemy waves and boss encounters.

The machine is not an isolated gambling minigame: every result changes army composition, unit-cap pressure, available growth material, and the player's future combat options. Player agency comes from formation choices, absorption targets, nudge tools, item purchases, and core selection—not from passive random outcomes alone.

## Core player loop

1. **Prepare** — review gold, health, roster, unit cap, core effects, and the next wave.
2. **Recruit** — spend a limited number of spins to generate a 3×3 grid. A matching class across a valid line summons a unit.
3. **Shape the result** — use a limited reel adjustment, choose a keeper, lock valuable units, and absorb donors into the unit being developed.
4. **Specialize** — at growth thresholds choose a branch; retain compatible imprints and manage unit roles.
5. **Defend** — resolve an automatic battle against a wave whose strength scales with progression.
6. **Recover and invest** — earn or lose resources, select a Core after boss milestones, buy items/healing, and prepare the next wave.

## Design principles

- **Deterministic rules, variable outcomes:** a stored seed plus command sequence reproduces the same run.
- **Meaningful scarcity:** spins, gold, hearts, unit capacity, item slots, and core slots create competing priorities.
- **Growth through sacrifice:** absorbing a donor is a permanent roster trade-off, not free experience.
- **Readable probability:** symbol weights, payline rules, and modifiers must be inspectable and testable.
- **Build diversity:** classes, imprints, promotions, items, and cores should change decisions rather than only inflate numbers.
- **Causal combat reports:** show the formation power, enemy power, boss modifier, rewards, and damage.
- **No false provenance:** third-party community guides are treated as secondary references; balance values in this implementation are our own until verified through controlled playtests.

## Differentiation and originality

The project may use broad genre-level ideas (reel-based recruitment, auto-battler defence, absorbing units, roguelite modifiers) as design references. It must use independently authored source code, original UI, original text, original sound and commissioned/original art. Do not import assets or decompile/copy code from commercial distributions or unofficial recovered builds.

## Initial balance model

The first playable slice uses six classes, an eight-line 3×3 board, six spins per wave, an initial spin cost of 100 gold increasing by 50 each paid spin, a five-unit starting capacity, absorption thresholds at levels 5 and 12, and a boss milestone every five waves. These are explicit prototype parameters, not claims about the commercial game's exact internal balance. Each parameter must be moved into a versioned ruleset/configuration module before balance expansion.

## Visual direction — original 16-bit pixel-art fantasy

Use an authored pixel-art language inspired by the clear silhouettes and charm of classic console adventures. These are broad genre references only: every sprite, map, icon, effect, sound, text, and layout must be original.

- Logical tile grid, integer pixel scale, nearest-neighbour rendering. Never smooth pixel sprites.
- Palette: forest green, teal shadow, parchment, brass/gold reward accents, restrained danger reds.
- Readable class silhouettes at 16×16 or 24×24 source size; shape before color.
- Chunky outlines, limited highlight tones, purposeful empty space; avoid glass panels, gradients, soft shadows and rounded SaaS cards.
- Treat the slot machine as a fantasy relic/arcade altar. Reels stop, paylines flash, units pop in, fighters recoil, bosses enter, and rewards reveal in stepped animations; honor reduced-motion settings.
- Separate world, character, machine, HUD and feedback layers. Critical information never relies on color alone.
- Browser rendering is presentation only; Rust remains authoritative for simulation, state transitions and combat. Pixel assets are data-driven and versioned; current glyphs are placeholders until sprite art lands.

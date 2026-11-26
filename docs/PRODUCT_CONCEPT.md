# Product Concept — Slotbound

## Product definition

Slotbound is a 2D cozy-fantasy roguelite auto-battler. The player runs a small woodland defence company whose recruitment board converts matching magical sigils into creatures. The player shapes the roster through controlled randomness, keeper selection, locking, absorption, promotion, items and permanent Cores. The squad then fights automatically against escalating waves and bosses.

The recruitment board is a game mechanic, not a real-money gambling product. There are no cash stakes, payouts or casino venue fantasy. No roulette tables, chips, cabinets or poker-room props belong in the art direction. The 3×3 board is an enchanted rune device that summons allies.

**Core promise:** turn imperfect random recruits into a specialised team, then watch the choices you made in preparation determine the outcome of an automatic battle.

## Player and experience

- Audience: players who enjoy approachable roguelites, party-building, auto-battlers, collection and short strategic sessions.
- Mood: warm, curious, optimistic and lightly adventurous. Losses should be understandable and encourage a new build, not feel punitive or opaque.
- Session: a run is a sequence of quick preparation decisions, visible recruitment outcomes, automatic combat resolution and between-wave investment.
- Player agency: the player does not control every attack. Agency comes from resource allocation, board manipulation, roster composition, sacrifice, formation, specialisation and build synergies.
- Platform target: browser-first prototype, designed so the game domain can later support a desktop build without moving rules into the browser.

## Visual identity

The approved direction is **Cozy 16-bit Fantasy Pixel Art**. Classic 8/16-bit adventures are broad references for tile-based spaces, expressive silhouettes, limited palettes and readable action. Slotbound uses original characters, environments, animations, iconography, audio and UI. It must not reproduce Nintendo characters, sprites, maps, music, logos, exact compositions or distinctive trade dress.

The visual guide is `docs/VISUAL_STYLE_GUIDE.md`. It defines a 2D-only renderer, crisp nearest-neighbour scaling, a warm parchment/forest/terracotta/honey palette, pixel-grid sizes, animation language, biomes and asset acceptance rules.

## Core player loop

1. **Prepare.** Read the next encounter, current health, gold, roster capacity, spins, items and permanent Cores. Pick a keeper and decide what to protect.
2. **Recruit.** Spend one of the wave's limited spins on the 3×3 sigil board. Three matching class symbols along a valid line summon a unit.
3. **Manipulate.** Use the limited column nudge, then inspect the recruits. If the roster is crowded, choose which creature to develop and which donor to sacrifice.
4. **Develop.** Absorb eligible donors into a keeper. Growth improves stats and records a class imprint. At growth thresholds choose a promotion branch.
5. **Defend.** Start the battle. Allies and enemies act automatically under deterministic combat rules. The player reads a combat report rather than issuing per-unit attacks.
6. **Invest.** Resolve rewards and damage. After a boss victory select a permanent Core. During intermission buy supplies or healing, then prepare the next wave.

## Recruitment board rules

The first prototype uses a 3×3 board and eight straight three-cell lines: three horizontal rows, three vertical columns and two diagonals. A line with three matching class sigils summons one unit of that class. A board with all nine symbols identical therefore completes all eight lines.

Prototype economy:
- six spins are available per wave;
- the first paid spin costs 100 gold;
- each subsequent paid spin costs 50 gold more than the previous one;
- one vertical column nudge is available per wave;
- a spin can temporarily take the roster above capacity; further recruiting is restricted until capacity is restored through absorption;
- symbol classes are currently selected uniformly. This is a prototype distribution, not a calibrated or player-facing probability claim.

The board is designed to create decisions, not a passive slot-machine reward. The player can influence future choices by managing spend, preserving a keeper, using the single nudge and deciding what to absorb.

## Units and roster

The six first-prototype roles are:

| Class | Battle identity | Intended tactical value |
|---|---|---|
| Guardian | Frontline defender | Protects allies and holds lanes |
| Archer | Ranged damage | Reliable damage from the back line |
| Mage | Arcane damage | Burst, area effects or elemental status |
| Cleric | Support | Healing and defensive utility |
| Rogue | Skirmisher | Fast attacks, flanking or finishing |
| Beast | Bruiser | Durable pressure and disruption |

These identities are design roles; actual ability kits and a full combat timeline are not yet implemented. Units have stable IDs, class, level, absorption level, attack, health, lock state, imprint and optional promotion state in the current prototype.

Roster operations:
- **Select keeper:** designate the unit that receives a donor.
- **Lock:** protect a unit from accidental sacrifice.
- **Absorb:** consume an unlocked donor and transfer growth to the keeper.
- **Promote:** choose a branch when a growth threshold is reached.
- **Capacity:** create meaningful pressure between recruiting more units and improving the strongest existing unit.

Future target: typed multiple imprint slots, donor inheritance rules, promotion skill trees and explicit formation positions. The current one-string imprint representation is a first version.

## Auto-battle rules and target combat

Combat must be fully automatic once started. It should be deterministic for a fixed seed, ruleset version, formation and command history. The battle engine belongs in the Rust gameplay domain; the browser may animate server-provided events but cannot decide hits, damage, targets or rewards.

The current candidate now includes a deterministic, bounded tick-based combat timeline in the Rust domain. Allies act in stable initiative order; enemies select targets with Guardian-first priority; attacks, defeats, healing and boss telegraphs are recorded as typed events. Guardian reduces incoming damage, Archer gains a timed attack bonus, Rogue has a flat strike bonus, Beast hits harder against healthy targets, Mage has periodic splash damage and Cleric heals a wounded ally on alternating ticks. Units retain remaining health between waves, defeated units leave the roster, and the camp restores a small amount of survivor health. This is a first combat foundation, not a fully balanced tactical system: formation lanes, richer ability cooldowns, status effects, equipment interactions, authored enemy waves and extensive simulation calibration remain future work.

Target combat timeline:
1. Build battle participants from the player's saved formation and encounter definition.
2. Apply persistent item/Core modifiers and stage effects.
3. Resolve initiative, lane occupancy and target priority using stable tie-breaks.
4. Advance deterministic ticks. Units select a legal target and perform basic attacks when ready.
5. Resolve armour, guard, damage, healing, shields, status effects, critical effects and deaths in a documented order.
6. Trigger cooldown abilities and boss telegraphs at explicit ticks.
7. Emit a typed event for every meaningful state change.
8. Stop on victory, defeat or a hard turn limit; persist the report and resulting player state atomically.

The event stream should explain why a result happened: who attacked, who was targeted, damage blocked, healing received, status applied, unit defeated, reward granted and health lost.

## Waves, bosses and rewards

- Enemy strength and composition should scale by a versioned ruleset, not ad-hoc UI formulas.
- The prototype marks every fifth wave as a boss encounter.
- A boss victory offers three Core options; the player selects one.
- Cores are persistent run modifiers and should change decisions, not only add generic power.
- The between-wave supply cache offers items such as attack improvement, damage mitigation and healing.
- A lost battle costs hearts; reaching zero ends the run.
- Future stages and biomes should introduce enemy families, environmental rules and boss patterns, not only bigger health values.


## Journey events and branching expedition

A run is an expedition, not a sequence of identical arena waves. Between battles, the player encounters seeded events whose availability and consequences depend on the biome, wave, party condition, inventory, previous choices and run history. The event director must be deterministic for a fixed seed, ruleset version and command history.

Event families include:
- **Discovery:** hidden caches, relics, lost supplies and secret paths.
- **People:** travelling merchants, wounded travellers, guides, recruits and rival adventurers.
- **Mystical:** shrines, blessings, bargains, curses and strange forest phenomena.
- **Threats:** ambushes, hazards, elite patrols, traps and optional challenge fights.
- **Narrative choices:** short branching encounters with explicit trade-offs, delayed consequences and possible follow-up events.

Every event definition must declare eligibility conditions, selection weight, choices, costs, rewards, state mutations, failure outcomes, repeat policy and telemetry key. Avoid cosmetic choices that do not change game state. Event history and resolved choices must be persisted so reloads cannot reroll an event or claim its reward twice.

The route map connects battle, event, merchant, elite and boss nodes. The player should be able to weigh risk, reward, army health, gold, roster composition and current build before selecting a route.

## Visible battle presentation

The battle engine remains deterministic and authoritative in Rust. The browser renders its typed event stream as a readable 2D pixel-art encounter: allied and enemy formations occupy clear positions; units animate attacks, movement, casts, healing, damage reactions and defeat; enemies telegraph dangerous actions; bosses have distinct phases and tells. Health bars and combat log remain available so animation never hides important information.

The renderer must consume recorded event data rather than independently simulate combat. Playback supports pause, normal speed, fast-forward and reduced-motion mode. A battle is not considered visually implemented merely because the final victory/defeat report and text log are shown.

## Progression and replayability

A full release should include:
- authored stages and a branching route map;
- distinct enemy families and boss patterns;
- class abilities, synergies and meaningful promotions;
- typed imprint inheritance;
- multiple reel tools with explicit charges/costs;
- items with slot/stack rules;
- a broad but controlled set of Cores;
- seeded run generation and deterministic replays;
- difficulty variants and an endless or challenge mode after the core campaign is balanced.

## Economy and balance principles

- Gold, spins, hearts, roster capacity and item slots are competing resources.
- Randomness is visible and reproducible. State the actual symbol weights once a calibrated distribution exists.
- Every action has a clear cost and phase restriction.
- No resource transition may silently overflow or underflow.
- Balance reports must show sample count, seed range, win rate, run length, average gold, recruit distributions and uncertainty intervals.
- Do not use a lucky sample as proof of fairness or difficulty.

## Current implementation boundary

Implemented in the current source candidate: 3×3 board and eight paylines; six classes; deterministic seed/RNG; six spins with increasing gold cost; one column nudge per wave; roster, lock/unlock, absorption, simple imprints, threshold promotions; deterministic tick combat with typed event history; boss/Core choice; supply cache; Axum API; browser state and run restoration; PostgreSQL persistence adapter with row-level transactions plus local single-process JSON fallback.

Not yet implemented as a complete game: unit-by-unit combat, abilities and cooldowns, authored enemy waves, branching route map, stage/biome content, multi-slot imprint inheritance, calibrated weighted symbol probabilities, full asset pipeline and production-quality sprite sheets, real-browser end-to-end coverage, authentication and production operations. See `docs/MAP.md` for current delivery status.

## Product principles

- Original assets and source; no extraction or copying from commercial builds.
- One authoritative rules implementation in Rust.
- Deterministic state transitions and reproducible defects.
- Full player journey before feature count.
- Art and UI must be legible at actual play scale.
- Every milestone has executable acceptance criteria.
- Never describe a prototype, build or deployment as a finished game.

## Implemented journey-event and battle-replay slice

The first playable implementation now includes five seeded encounter families: lost cache, moonwell shrine, travelling merchant, wounded ranger and bandit ambush. Each encounter exposes two choices with explicit effects; choices can grant gold, restore hearts, heal or strengthen the army, purchase an item, recruit a unit or trade health for gold. Pending events and their resolutions are stored in the serialized run state. The API rejects invalid/replayed choices and prevents starting the next wave until the pending event is resolved.

The browser now displays encounter cards and choices, a pixel-art battlefield snapshot, health bars and a replay control that steps through the Rust-authored combat event stream. Reduced-motion mode skips timed playback and renders the final battlefield state. This is a functional vertical slice, not the finished route-map or battle-art system: branching paths, expanded encounter content, lane-aware formations, authored sprites/projectiles, boss phase art and Playwright acceptance remain required.

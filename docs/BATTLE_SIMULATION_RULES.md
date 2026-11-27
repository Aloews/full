# Combat Simulation Rules — Current Version 5

## Authority and determinism

All combat outcomes are resolved in `crates/game-core`. The browser receives a completed `BattleReport` and renders its ordered events; it does not calculate hits, targets, damage, healing, rewards or casualties. A battle is deterministic for the same persisted run state, wave, roster, items and Cores; the current battle resolver draws no random numbers.

The simulation is bounded to 40 ticks. It ends immediately when either side is eliminated. If both sides remain after tick 40, the battle is a non-victory and is processed as a defeat. A future ruleset revision should make the tick cap and terminal policy explicit data rather than hard-coded implementation constants.

## Participant construction

- Every player unit becomes a combatant with persistent ID, class, attack, max health, current health and class initiative.
- `current_health = None` means full health; a numeric value is clamped to the legal interval and used as current HP.
- Enemy count is `2 + min(floor((wave - 1) / 3), 3)`.
- Each ordinary enemy has `8 + 2 × wave` max HP and `2 + floor(wave / 5)` attack.
- On every fifth wave, the first enemy is replaced by the Mosswood Sentinel with `30 + 3 × wave` max HP and `4 + floor(wave / 3)` attack. Boss flag enables telegraph events.

Enemy names are original prototype definitions. Enemy families and boss names change by deterministic five-wave biome: Mosslight Meadow, Emberfen and Crystal Caverns. Emberfen adds +1 enemy attack; Crystal Caverns adds +15% enemy HP.


## Stage and biome progression

A stage spans five consecutive waves. `stage_for_wave(wave)` is `floor((wave - 1) / 5) + 1`. The stage's biome cycles deterministically through Mosslight Meadow, Emberfen and Crystal Caverns; stage four returns to Mosslight Meadow for the current endless-wave prototype. No independent random roll selects the biome.

- **Mosslight Meadow:** Thicket Slime, Bramble Bat, Glow Wisp, Rootling and Mossling; boss: Mosswood Sentinel. Baseline enemy health and attack.
- **Emberfen:** Cinder Moth, Ash Toad, Coal Sprite, Charred Rootling and Soot Wolf; boss: Emberfen Tyrant. Every enemy receives +1 attack.
- **Crystal Caverns:** Shard Beetle, Echo Wisp, Quartz Golem, Prism Bat and Crystal Mite; boss: Prism Colossus. Every enemy receives +15% maximum HP, rounded down to an integer.

Enemy count still follows the wave formula `2 + min(floor((wave - 1) / 3), 3)`; elite routes add one enemy and apply their existing health/attack modifiers after biome modifiers. Boss health and attack use the existing wave scaling, then the biome modifier. The stage and biome are recorded in `BattleReport`; older reports deserialize with the first biome and stage zero, and UI presentation falls back to the report wave to infer their displayed stage. Route option titles/descriptions and the original pixel-world/battlefield palettes use the same wave-derived biome.

This is deterministic region theming and enemy roster variation, not yet a full stage-map system: stage selection is derived from wave rather than persisted as a separate node graph, environmental hazards and unique biome boss abilities are still open.

## Tick order

1. Stop if either side is empty.
2. Increment tick.
3. Sort allies by descending initiative, then ascending stable unit ID.
4. Resolve living ally actions in that order. Each ally attacks one enemy; class effects follow its primary attack.
5. Resolve enemy actions in stable roster order. A boss telegraphs every third tick immediately before its attack; the warning contains the stable ID of the actual selected target and the calculated damage after target mitigation.
6. Remove defeated allies. Stop if either side is empty.
7. If tick 40 is reached with both teams alive, finish as a non-victory.

Initiative: Rogue 10, Archer 9, Mage 8, Beast 7, Guardian 6, Cleric 5.

## Formation and target selection

- Combatants occupy one of three lanes (`0..=2`) and a typed `Front` or `Back` row. The browser renders these positions from server-authored snapshots; it does not calculate the formation for current saves.
- Default positions put Guardian, Beast and Rogue in the front row and Archer, Mage and Cleric in the back row. Players can move any unit between rows and three lanes during preparation or intermission. Positions persist on the unit; multiple units may stack in one cell using a stable stack index.
- Enemies are arranged in paired front/back lanes. The boss occupies front lane 1; regular enemies alternate rows and advance through lanes deterministically.
- A living front-row unit screens only the back row in its own lane. Frontline defenders in another lane do not prevent a flank.
- Allied attacks consider front-row units and back-row units whose own lane has no living front defender; among those legal targets they choose the nearest lane, lowest remaining-health percentage and ascending stable ID.
- Enemies use the same lane-local screening rule, then prefer a Guardian among equally near legal targets before health percentage and stable ID.
- A back-row unit becomes a legal target as soon as its own lane has no living front-row defender, even while other lanes remain screened. All lane distance and tie-breaking rules are deterministic.

## Class combat hooks

| Class | Current effect |
|---|---|
| Guardian | Reduces each incoming hit by 1 HP (minimum 1); every fourth tick grants 2 temporary shield to each living ally, stacking to a cap of 4 per unit. Shields absorb incoming damage before HP |
| Archer | Adds 2 damage to its primary attack on even ticks |
| Mage | Adds a 2 HP splash hit to the weakest remaining enemy on even ticks |
| Cleric | Restores up to 2 HP to the most wounded living ally on even ticks |
| Rogue | Adds 2 damage to every primary attack |
| Beast | Adds 1 damage if the chosen enemy is above half health |

These are initial role-defining hooks, not a full class ability kit. Guardian Shieldwall is implemented; additional cooldown-based abilities, status effects, armour, resistances and player-controlled formation editing remain future work.

## Items, Cores and synergy

- Each Sharpening Stone contributes +1 attack to ally actions.
- Each Might Core contributes a 12% attack multiplier.
- Three or more units of the same class add a 10% team attack multiplier.
- A Vitality Charm reduces run-heart loss after defeat by 1; it does not reduce unit damage.
- Each Fortune Core increases the gold reward by 15%.
- A Command Core increases unit capacity by 1.
- The BossGate route applies a 15% outgoing-damage bonus to allied attacks during the next boss battle. Calculate the base damage using the existing Core and class-synergy multipliers, then add `max(1, ceil(base_damage × 0.15))`. This effect applies to primary and Mage splash hits only on the boss wave. The route itself is consumed/reset by the battle transition; it must not leak into later waves.

Integer order: base attack plus class/item bonuses, then Might Core multiplier, then class-count synergy multiplier, rounded down; if BossGate is active on a boss wave, add the rounded-up 15% gate bonus (minimum +1) to each allied attack. At least 1 damage applies to a primary attack and Mage splash.

## Persistence and event log

Surviving units retain current HP in `Unit.current_health`; defeated units are removed. A full-health survivor serialises as `None`, while a damaged survivor stores numeric HP. The camp restores 2 HP at the next wave, capped at max health. The API persists updated hearts, gold, Core offer and report in the run transaction.

Typed events are `AllyAttack`, `EnemyAttack`, `AllyDefeated`, `EnemyDefeated`, `UnitHealed`, `ShieldGranted`, `ShieldAbsorbed`, `BossTelegraph` and `BattleEnded`. Each includes a tick, stable actor/target IDs, display labels, amount and remaining health. A `BossTelegraph` uses the real defender ID (not a generic front-line label), `amount` is the upcoming post-mitigation damage, and `remaining_health` is the target's HP immediately before the hit. The browser replay draws a warning line and target frame, then plays the following attack event. The UI shows the last eight events; the saved report retains the complete event list.

## Battle report estimates

`army_power` and `enemy_power` are debug/reference metrics only and do not determine the result. Victory is determined only by whether the enemy party is empty at termination.

## Test requirements

Current Rust tests cover same-seed timelines, typed row/lane snapshots, player-controlled row/lane changes, stacked cells, invalid lane rejection, v3 save migration, lane-local frontline screening, flanking into exposed back rows, nearest-lane targeting, Guardian frontline priority, Cleric healing, Guardian Shieldwall cadence/cap/event ledger, ally defeat/removal, survivor recovery, boss telegraph target identity and pre-hit damage preview. Extend coverage for empty army, simultaneous final elimination, tick-40 terminal outcome, damage and multiplier boundaries, every class trigger, multiple support units, old save fixtures and event replay across persistence reload.

## Known limitations

This is a first combat foundation, not a balanced full game system. It has no authored lane grid, active ability cooldown system, status effects, shields, resistance system, enemy skill families, boss phase changes or live tick-by-tick combat. The browser presents a deterministic post-battle replay of the authoritative event stream, not a real-time simulation. These remain in `.github/agent-backlog.json` and `docs/MAP.md`.

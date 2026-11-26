# Combat Simulation Rules — Current Version 1

## Authority and determinism

All combat outcomes are resolved in `crates/game-core`. The browser receives a completed `BattleReport` and renders its ordered events; it does not calculate hits, targets, damage, healing, rewards or casualties. A battle is deterministic for the same persisted run state, wave, roster, items and Cores; the current battle resolver draws no random numbers.

The simulation is bounded to 40 ticks. It ends immediately when either side is eliminated. If both sides remain after tick 40, the battle is a non-victory and is processed as a defeat. A future ruleset revision should make the tick cap and terminal policy explicit data rather than hard-coded implementation constants.

## Participant construction

- Every player unit becomes a combatant with persistent ID, class, attack, max health, current health and class initiative.
- `current_health = None` means full health; a numeric value is clamped to the legal interval and used as current HP.
- Enemy count is `2 + min(floor((wave - 1) / 3), 3)`.
- Each ordinary enemy has `8 + 2 × wave` max HP and `2 + floor(wave / 5)` attack.
- On every fifth wave, the first enemy is replaced by the Mosswood Sentinel with `30 + 3 × wave` max HP and `4 + floor(wave / 3)` attack. Boss flag enables telegraph events.

Enemy names are original prototype definitions. Authored biome-specific waves are pending.

## Tick order

1. Stop if either side is empty.
2. Increment tick.
3. Sort allies by descending initiative, then ascending stable unit ID.
4. Resolve living ally actions in that order. Each ally attacks one enemy; class effects follow its primary attack.
5. Resolve enemy actions in stable roster order. A boss telegraphs every third tick immediately before its attack.
6. Remove defeated allies. Stop if either side is empty.
7. If tick 40 is reached with both teams alive, finish as a non-victory.

Initiative: Rogue 10, Archer 9, Mage 8, Beast 7, Guardian 6, Cleric 5.

## Target selection

- Allies attack the enemy with the lowest remaining-health percentage; equal ratios resolve by ascending enemy ID.
- Enemies prefer a living Guardian. Within the same priority, choose the lowest remaining-health percentage, then ascending unit ID.
- There is no lane or rear/front cell grid yet. Guardian priority is not a full formation system.

## Class combat hooks

| Class | Current effect |
|---|---|
| Guardian | Reduces each incoming hit by 1 HP, but damage is never reduced below 1 |
| Archer | Adds 2 damage to its primary attack on even ticks |
| Mage | Adds a 2 HP splash hit to the weakest remaining enemy on even ticks |
| Cleric | Restores up to 2 HP to the most wounded living ally on even ticks |
| Rogue | Adds 2 damage to every primary attack |
| Beast | Adds 1 damage if the chosen enemy is above half health |

These are initial role-defining hooks, not a full class ability kit. Cooldowns, status effects, shields, resistances and formation positioning remain future work.

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

Typed events are `AllyAttack`, `EnemyAttack`, `AllyDefeated`, `EnemyDefeated`, `UnitHealed`, `BossTelegraph` and `BattleEnded`. Each includes a tick, stable actor/target IDs, display labels, amount and remaining health. The UI shows the last eight events; the saved report retains the complete event list.

## Battle report estimates

`army_power` and `enemy_power` are debug/reference metrics only and do not determine the result. Victory is determined only by whether the enemy party is empty at termination.

## Test requirements

Current Rust tests cover same-seed timelines, Guardian-first targeting, Cleric healing, ally defeat/removal, survivor recovery and boss telegraphs. Extend coverage for empty army, simultaneous final elimination, tick-40 terminal outcome, damage and multiplier boundaries, every class trigger, multiple support units, old save fixtures and event replay across persistence reload.

## Known limitations

This is a first combat foundation, not a balanced full game system. It has no authored lane grid, active ability cooldown system, status effects, shields, resistance system, enemy skill families, boss phase changes or live combat animation. These remain in `.github/agent-backlog.json` and `docs/MAP.md`.

# Core gameplay direction

## Genre

2D roguelite party auto-battler with slot-inspired probability and combination mechanics.

## Run loop

1. **Camp / preparation:** inspect the next encounter, party, formation, equipment and current synergies.
2. **Fate draw:** spend a run resource to reveal a 3×3 sigil pattern on an ancient charm board. This is an abstract magical object, never a casino machine.
3. **Interpret combinations:** matching lines create recruits, upgrade fragments or temporary tactical effects. Players can later unlock controlled nudges, locks and rerolls.
4. **Build:** position up to six units, merge duplicates, equip charms, select a relic and commit to a synergy.
5. **Auto-battle:** formations engage automatically. Units choose targets and use attacks/passives based on their role and cooldown.
6. **Reward:** gain essence, relics, unit growth and route choices. Every few encounters introduce an elite or boss.
7. **Meta-progression:** unlock new unit families, relic pools, starting charms and challenge modifiers. Persistent upgrades should expand choice, not invalidate balance.

## Design guardrails

- Randomness should create interesting choices, not make preparation irrelevant.
- Failed draws must still contribute to a plan through pity/compensation systems once those systems are designed.
- A player must understand why a unit spawned, why a synergy activated and why a battle was won or lost.
- Every run needs at least two viable build directions.
- No real-money bets or paid random reward products.
- Auto-battle resolution must be reproducible for a fixed seed and game state.

## Prototype slice

The first code slice provides a deterministic sigil draw, line matching, recruit generation, a small party and an automatic battle simulator. It is deliberately narrow; bosses, items, class evolution, route map, save ownership and multiplayer are follow-up release gates.

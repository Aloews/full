# Core gameplay direction

## Genre

2D roguelite party auto-battler with slot-inspired probability and combination mechanics.

## Run loop

1. **Camp / preparation:** inspect the next encounter, party, formation, equipment and current synergies.
2. **Fate draw:** spend a run resource to reveal a 4×4 sigil pattern on an ancient charm tapestry. The board resolves orthogonally connected groups of three or more matching symbols; it has no paylines and is never a casino machine.
3. **Interpret combinations:** connected clusters create one recruit per cluster. Cluster size determines recruit rank: 3–4 symbols create rank I, 5–7 create rank II, and 8+ create rank III. Oversized or overflow results convert to essence. Players can later unlock controlled nudges, locks and rerolls.
4. **Build:** position up to six units across three tactical lanes (click a unit during preparation to cycle its lane), merge identical units to evolve them, equip charms, select a relic and commit to a sigil synergy.
5. **Auto-battle:** formations engage automatically. Units automatically select targets using lane proximity and resolve attacks from role, armor and cooldown rules.
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

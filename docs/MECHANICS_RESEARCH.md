# Mechanics Research Notes

**Research date:** 2026-11-26

## Publicly described reference mechanics

The public project README for the original Slotbound describes a 3×3 slot machine, auto-battler defence, unit absorption, class choices, items, Cores, and judgement/boss waves. Secondary community guides describe eight straight paylines (three rows, three columns, two diagonals), six spins per wave, increasing spin prices, a unit-cap lockout when over capacity, absorption-driven unit levels/imprints, promotion thresholds, and boss reward choices.

References:
- Public development journal: https://github.com/techno-13499tingling/Slotbound-Devlog-2026 (describes high-level loop; explicitly says the commercial game's code is closed).
- Public mechanic reference: https://wikily.gg/slotbound (community-maintained guide; not an official source).
- Beginner guide: https://slotbound.net/beginner-guide (community playthrough; observations, not authoritative implementation data).
- Absorption guide: https://slotbound.net/absorb (community guide; notes locking, over-cap behavior, and cross-class imprint transfer).
- Cores and items overview: https://slotbound.fun/guides/cores/ (community-maintained guide).

## Evidence quality

The official/public development summary is suitable for the broad product loop. Numerical values, exact probabilities, hidden stat generation, and progression thresholds found only in community references are provisional observations and may change between game versions. They must not be presented as confirmed internals.

## Our current prototype mapping

| Reference idea | Our implementation | Status |
|---|---|---|
| 3×3 reels and paylines | Eight explicit row/column/diagonal paylines | Implemented |
| Matching symbols recruit units | Three identical class symbols on a line summon a unit | Implemented |
| Spins cost gold | Six per wave; 100 start, +50 each paid spin | Implemented |
| Reel manipulation | One vertical column nudge per wave | Implemented, simplified |
| Absorption | Donor consumed; keeper gains absorb level and stats/imprint | Implemented, simplified |
| Promotion branches | Choice at absorb levels 5 and 12 | First version |
| Auto-battler waves | Deterministic army-vs-wave power resolution | Implemented, simplified |
| Boss/Core reward | Every fifth wave; choose one of three Core types after victory | Implemented, simplified |
| Items and recovery | Three shop items and healing | Implemented, first version |
| Blast, stages, factions, traits, awakening, endless mode | Not yet implemented | Backlog |

## Open design questions

1. Replace uniform symbol weights with a versioned distribution validated by simulation and playtests.
2. Decide whether reel adjustments are free, limited, charge-based, or item/Core-driven.
3. Build a full imprint model with multiple slots and inherited traits, not one display string.
4. Replace power comparison with a deterministic combat timeline, positioning, target selection, attacks, abilities, statuses, and casualties.
5. Add stage/map progression and boss-specific mechanics.
6. Test the economy over thousands of seeded runs; publish confidence intervals rather than a single lucky/unlucky result.

# Slotbound — Game Design Document

**Genre:** 2D cosy-fantasy roguelite auto-battler, creature collection and wave defence  
**Visual direction:** Cozy 16-bit Fantasy Pixel Art  
**Core promise:** build a curious little army from magical sigils, make meaningful preparation choices, then watch the squad fight automatically.

## 1. Product identity

Slotbound is a run-based fantasy defence adventure. A player travels through an inviting but dangerous world, discovers encounters, uses a magical 3×3 Fate Board to recruit creatures, develops a limited roster and prepares for automatic battles. A draw changes the roster; a roster choice changes the battle; the battle changes the next event and the resources available for the next preparation phase.

The surface is welcoming and playful, but the strategic layer is demanding. A loss should usually be understandable: weak formation, missing frontline, poor absorption decision, unspent resource, dangerous event choice or an enemy pattern the player did not prepare for.

### Pillars

1. **Every draw changes the plan.** The Fate Board is not a disconnected minigame. Recruits, unit-cap pressure, gold costs and synergies connect it directly to combat.
2. **Build a small army with personality.** Each creature has a readable combat role, distinctive silhouette and a reason to keep, combine or sacrifice it.
3. **Preparation is the strategy.** Choose units, lock recruits, absorb donors, select promotions, manage items and routes. Combat itself is hands-off.
4. **Battles tell the story of decisions.** Watch attacks, healing, shielding, defeat and boss telegraphs as a legible 2D event replay.
5. **Runs differ for understandable reasons.** Seeded randomness changes offers and events; deterministic rules keep outcomes reproducible.
6. **Cosy world, real stakes.** Hearts, scarce draws, roster capacity and escalating encounters matter.

## 2. Visual identity — Cozy 16-bit Fantasy Pixel Art

The target is a contemporary, carefully authored interpretation of 8/16-bit console-era pixel craft. Use broad principles—tile-based environments, compact palettes, silhouette clarity, expressive animation and playful shapes—not recognisable protected content. Do not copy Nintendo characters, enemies, maps, music, sound effects, logos, exact compositions, UI layouts or distinctive trade dress. All shipped artwork and audio must be original or properly licensed.

### Pixel grid and rendering
- Strictly 2D: flat sprites, orthographic presentation, tile maps and layered parallax only. No 3D meshes, perspective cameras or 2.5D battle scenes.
- Logical composition target: 640×360. Scale to 1280×720 and larger displays with nearest-neighbour sampling and integer scaling where possible.
- Common creature sprites: 16×16 or 24×24 logical pixels. Elite units: 24×24 or 32×32. Large bosses: 32×32 or 48×48, as authored assets rather than enlarged common enemies.
- Environment tiles: 16×16. Props may occupy multiple tiles but align to the grid.
- Pixel snapping is required for world sprites and camera offsets. Never bilinearly scale pixel art or use a pixelation filter over high-resolution images.
- Use an original or licensed bitmap font after glyph-coverage checks. Until then, a fallback font remains provisional.

### Palette and colour semantics

| Role | Name | Hex | Use |
|---|---|---|---|
| Outline | Deep ink | `#2B2638` | outlines, shadows, text |
| Night forest | Evergreen | `#243D38` | dark environment panels |
| Forest | Leaf | `#5E9B58` | nature, allies, healing accents |
| Highlight | Soft sage | `#9BC477` | grass, foliage |
| Paper | Parchment | `#F5E9BD` | panels, labels |
| Earth | Chestnut | `#9A6545` | wood, soil, leather |
| Danger | Terracotta | `#E87958` | damage, hostile telegraphs |
| Reward | Honey | `#F3C969` | rewards, selected actions |
| Water | Clear blue | `#72B9D2` | water and one magic family |
| Rare magic | Berry | `#A66DA6` | distinct magic family |
| Light | Cream | `#FFF6D8` | sparkle, highlights |

Each sprite normally uses four to seven local colours plus transparency. Semantic colours must remain consistent across effects, icons, menus and props.

### Shape language and animation
- Allies: rounded, compact, friendly silhouettes with one unmistakable class feature.
- Enemies: slightly sharper or asymmetric silhouettes and different posture; do not distinguish them only by recolouring.
- Guardian: broad stance, shield/crest and low centre of mass.
- Archer: long, narrow profile with visible bow or ranged tool.
- Mage: hood/staff and concentrated magic accent.
- Cleric: calm open silhouette and healing motif.
- Rogue: low, angled posture, scarf/hood or twin-blade profile.
- Beast: quadruped profile with distinct muzzle, ears and tail.
- Boss: multi-tile silhouette, bespoke idle rhythm, telegraphs and identifiable attack shapes.

Required animation families: idle (2–4 frames), attack (anticipation → lunge/projectile → contact → recovery), hit (short flash/knockback), guard, heal, defeat and boss telegraph. Reduced-motion mode suppresses nonessential loops and camera shake without hiding gameplay information.

### Biomes
Initial authored biome: **Mosslight Meadow** — grass, small flowers, stepping stones, mushrooms, old boundary walls, soft sunlight and a distant tree line.

Planned progression:
- **Mosslight Meadow:** forest edge and first rune shrine.
- **Whisperwood:** roots, layered trunks, mushrooms, fireflies and deep green shadows.
- **Tideglass Ruins:** pale stone, blue channels, broken pillars and water magic.
- **Cinder Orchard:** orange leaves, ember flowers, dark soil and warm light.
- **Moonfen:** indigo water, violet plants, pale reeds and reflected starlight.

A biome is not just a background colour: it changes tiles, event eligibility, enemy families, ambient details and boss identity.

### Interface and sound
The interface resembles a handcrafted field journal and a small fantasy workshop: parchment surfaces, wood/stone borders, square or stepped corners, engraved details, compact resource indicators and tactile primary buttons. Selected, unavailable, locked, dangerous and rewarded states must be distinct.

The player-facing device is the **Fate Board** and its action is **Draw Sigils**. Avoid casino furniture and gambling terminology in the presentation: no roulette table, poker chips, slot cabinets, casino carpets or casino-room staging. The recruitment mechanic remains a randomised symbol-board system, framed as magic and creature recruitment.

Audio should be original and restrained: chiptune-inspired melody with warm acoustic timbres, short action cues and volume/mute controls. Do not recreate recognisable Nintendo melodies or sound effects.

## 3. Core game loop

1. **Review the encounter:** check wave, hearts, gold, roster capacity, pending event and known enemy/boss clues.
2. **Draw sigils:** spend one limited draw attempt on the 3×3 Fate Board.
3. **Recruit:** resolve every valid matching line; each completed line produces a matching-class recruit.
4. **Shape the roster:** inspect recruits, choose a keeper, lock important units and absorb donors.
5. **Specialise:** select promotions at growth thresholds; apply available items and Cores.
6. **Defend:** start automatic combat. The server resolves combat and returns typed deterministic events.
7. **Recover:** collect rewards, retain surviving units and their current health, remove defeated units according to domain rules, resolve the next journey event.
8. **Choose the next route:** after resolving an event, select one of three deterministic route choices (Battle, Rest, Merchant, Elite or BossGate, depending on the wave). Continue until the final boss, defeat or another terminal outcome.

**Player agency ends when battle is launched.** No attack, move or target commands are issued during combat. Playback speed, pause, skip and reduced motion are presentation controls only; they never change the result.

## 4. Fate Board and recruitment economy

### Canonical board size and lines

The current Slotbound design uses a **3×3 board**, not the experimental 4×4 board explored in the separate Casino Battle prototype. The 3×3 board is canonical because its eight straight lines are the recruitment resolution system already implemented in the Rust domain.

The eight three-cell lines are three rows, three columns and two diagonals. A line completes when its three cells contain the same recruit-class sigil. Each completed line creates one recruit of that class. A board can complete multiple lines; a fully uniform board can complete all eight. Resolve all lines deterministically and show which line created each recruit.

### Prototype economy

Current prototype tuning:
- six draws per wave;
- first paid draw costs 100 gold;
- each later paid draw increases by 50 gold;
- one vertical column shift per wave;
- initial roster capacity target: five units.

These are prototype parameters, not verified internal data from a commercial title. Move them into a versioned Ruleset before large-scale balance work. Current uniform symbol selection is not calibrated probability. Symbol distribution, line frequency, recruit yield and economy require seeded simulation and controlled playtests.

### Board manipulation

The first manipulation is one vertical column shift per wave. It must validate column and phase, consume allowance only after validation, recompute lines, award only newly completed matches, and append a deterministic command/event.

Future Blast, reroll or cell-lock tools must be typed modifiers with explicit charges, price, targets and phase rules—not UI-only effects.

## 5. Roster, absorption and progression

### Initial classes

| Class | Role | Combat identity |
|---|---|---|
| Guardian | Frontline tank | mitigates incoming damage and protects fragile units |
| Archer | Ranged damage | reliable single-target pressure |
| Mage | Area damage | splash/multi-target magic |
| Cleric | Support | heals allies and sustains long encounters |
| Rogue | Skirmisher | fast attacks, opportunistic targeting and burst |
| Beast | Bruiser | heavy physical damage and resilient midline presence |

Each class needs a clear baseline profile and at least one class-defining action. Identity must be visible in animation and combat events, not only hidden multipliers.

### Capacity and absorption

Capacity is a meaningful constraint. It creates a trade-off between many low-level recruits and fewer promoted units. A completed draw may temporarily exceed capacity when multiple lines summon units at once; actions requiring free space must then be gated until the roster is resolved.

Absorption consumes the donor and permanently improves the keeper. Validate distinct IDs, phase, eligibility and locks; calculate growth/imprint inheritance in the domain; remove donor and update keeper atomically; emit a typed result. The current prototype's single imprint field is simplified. The target model uses typed imprint slots, donor inheritance and promotion branches. Never silently overwrite an imprint or award a duplicate bonus.

Current prototype promotion checkpoints are absorption levels 5 and 12. They are tunings, not commercial-game facts. A branch must change unit behaviour, not merely add a hidden number.

## 6. Automatic combat

### Authority

Rust `slotbound-core` is the sole authority. The API validates the request, invokes the domain transition, persists the new state and returns typed battle events. The browser only visualises the stream and must never calculate damage, target selection, win/loss, loot or random outcomes.

The current prototype has a deterministic tick-based timeline capped at 40 ticks, stable initiative and ID tie-breakers, Guardian-priority targeting, class effects, Mage splash, Cleric healing, Guardian mitigation, boss telegraphs, typed attack/heal/defeat/completion events and survivor-health persistence. The resolver draws no random numbers. This is a working foundation, not a complete tactical combat ruleset; exact current turn order, class formulas and item/Core interactions are specified in `docs/BATTLE_SIMULATION_RULES.md`.

### Target tick order

1. collect living units and eligible enemies;
2. compute initiative with stable identity tie-breakers;
3. resolve start-of-tick effects and expiries;
4. resolve boss telegraphs/scheduled enemy patterns;
5. select legal targets;
6. resolve attack, shield, armour, mitigation, damage and healing in one documented order;
7. apply defeat/removal transitions;
8. append typed events in canonical order;
9. evaluate victory, defeat, simultaneous elimination and turn-cap conditions.

Every random decision consumes deterministic RNG in a documented order. Fixed seed, Ruleset version and command sequence must reproduce canonical state and event log.

### Next tactical layer
Add explicit three-lane formation positions and legal lane targets; typed armour and temporary shields; cooldown/trigger abilities; statuses with stacking/refresh/expiry; telegraphed boss patterns; authored enemies/waves; explicit stalemate/turn-cap outcome. These rules belong in Rust domain code and require deterministic tests.

### Battle playback
Playback consumes authoritative events with stable order and actor/target/amount/ability/result data. Map events to authored animations for attacks, damage, healing, shields, defeat, boss telegraphs and battle completion. Skip, playback speed and reduced motion must render the same final state. Presentation timing cannot alter simulation timing.

## 7. Journey events, route map and bosses

Five seeded event families already exist: cache/treasure, moonwell/shrine blessing, travelling merchant, wounded ranger/recruit, and bandit ambush. Current prototype weights are 25%, 20%, 20%, 15% and 20%. They are tunings, not balance-certified probabilities. Each event has explicit choices, preconditions, costs, state changes, rewards and consequences. Pending event, event history and resolved choice are persisted. Next-wave progression is blocked until a pending event is resolved.

Future content includes elite encounters, environmental hazards, bargains/curses, multi-node stories and biome eligibility. Delayed consequences must live in run state, not hidden UI text.

After an event, the current game presents a deterministic three-choice route fork. Available route types include Battle, Rest, Merchant, Elite and BossGate depending on wave and boss proximity. Selection is persisted and cannot be replayed. Rest restores one heart and up to five health per surviving unit; Merchant grants 75 gold; Elite adds and strengthens an enemy and improves the victory reward. BossGate applies a 15% allied outgoing-damage bonus, rounded up with a minimum +1, on the next boss battle only. This is a working per-wave route fork, not yet a full connected multi-step world map with biome transitions.

The prototype places a boss every fifth wave. A successful boss win offers three Core options; the player selects one. Cores are run-defining modifiers, not just flat stat rewards. Their effects must be typed, previewable and tested in combinations. Bosses need original sprites, telegraphs, bespoke patterns and identifiable phase changes.

## 8. Resources and run outcome

Primary resources: gold, hearts, roster capacity, draw/shift allowances, item/Core capacity. The first supply cache contains prototype attack, mitigation and healing choices. Every item needs a cost, eligibility, effect duration, stacking policy and target scope. A purchase validates affordability and phase before spending.

Terminal outcomes (victory, defeat or another documented ending) are explicit and persisted. A terminal run cannot silently resume; terminal rewards cannot be collected twice.

## 9. State, commands and determinism

Run state contains, at minimum: schema and Ruleset version; run ID, seed and RNG state; phase/outcome; wave, gold, hearts and allowances; board and draw/shift result; roster with stable IDs, class, health, level, promotion, imprints, locks and equipment; Cores; pending event/history/delayed consequences; selected route option and route history; battle history, starting party/enemy snapshots and canonical events; command/idempotency metadata. A persistent multi-stage world route graph remains future work.

Commands include create run, draw sigils, shift column, lock/unlock unit, absorb, choose promotion, start battle, resolve event, choose Core, purchase item and advance wave. Validate all preconditions before mutation. Rejected commands leave state, resources, RNG and event history unchanged. Save changes are versioned and tested with old-save fixtures. Database mutations use transactions and row-level locking; JSON local persistence is single-process development fallback only.

## 10. Screens and interaction

1. Run overview: biome, route, wave, hearts, gold and next encounter.
2. Fate Board: 3×3 sigils, completed lines, draw cost, attempts and shift availability.
3. Roster: role, health, capacity, keep/lock/absorb and promotion choices.
4. Battle stage: 2D battlefield, allied/enemy silhouettes, health bars, event playback, speed/skip and field report.
5. Journey event: clear consequence, meaningful choices, visible costs and outcome.
6. Route fork: three connected choices with their risk, reward and recovery consequences. A full multi-stage route map is a later milestone.
7. Supply cache/Core selection: effect comparisons.
8. Run result: causal summary, major decisions and unlocks.

Support keyboard, mouse and touch. Provide focus states, reduced motion, adequate contrast, non-colour status signals and clear error feedback.

## 11. Balance policy

All economy values, symbol weights, growth values, combat stats, enemy scaling, rewards, event weights, item effects and boss schedules belong in a versioned Ruleset. Do not duplicate balance literals across API and client.

Before tuning, run deterministic seeded simulation and report sample count, seed range, win rate, run length, draw-cost/recruit distributions, gold/hearts, event frequencies and class/promotion usage. Include uncertainty intervals and distinguish observed data from hypotheses. Test no recruits, mass recruit, max capacity, empty army, zero gold, simultaneous defeat and turn cap. A 1,000-seed prototype baseline is not proof of long-term balance.

## 12. Milestones and acceptance

**S0 — First playable loop:** deterministic 3×3 board/eight lines, recruit/absorb/promote, auto-battle and basic persistence.

**S1 — Visible journey:** seeded consequential events, battle replay from authoritative events, outcome and skip/reduced-motion equivalence, no client combat authority.

**S2 — Tactical/strategic depth:** lanes, shields, armour, statuses, cooldown abilities, typed imprints, promotion tree, versioned Ruleset, Monte Carlo balance and a full connected multi-stage route map with biome transitions. The current three-choice per-wave route fork is already implemented.

**S3 — Production player journey:** original asset pipeline, full animation strips, bitmap font, Playwright real API journeys, save/auth/ownership/idempotency/backup, monitoring/security, hosted PostgreSQL, preview + production with rollback, packaged build and controlled playtest report.

A milestone is accepted only when domain and journey tests pass, exact-head CI is green, independent QA has no unresolved critical/high findings, MAP matches evidence and runtime behaviour is observed. A successful compile alone is not product acceptance.


## Current combat reference

For the current implementation, treat `docs/BATTLE_SIMULATION_RULES.md` as the executable combat reference. It defines the exact 40-tick cap, initiative values, tie-break order, target selection, per-class effects, enemy scaling, Mosswood Sentinel boss values, item/Core multipliers and BossGate damage calculation. The GDD describes product intent; the rules document is authoritative for the current prototype implementation. If they differ, update both documents and tests in the same change.

## Current visual implementation boundary

The browser currently renders six original 16×16 class sprite prototypes and a procedural woodland-frontier Canvas scene. This is not yet a production sprite-sheet pipeline: full authored frame strips, biome tile sets, asset manifest/provenance validation, bitmap font and desktop/mobile visual regression checks remain open. See `docs/VISUAL_STYLE_GUIDE.md` and `docs/MAP.md`.

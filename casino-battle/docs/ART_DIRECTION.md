# Casino Battle — locked 2D pixel-art direction

**Status: LOCKED. Changes to the pixel-art target require an explicit product decision.**

## The target

Casino Battle is a cozy, character-first fantasy roguelite auto-battler made in **strict 2D pixel art**. It should evoke the warmth and immediate readability of 8/16-bit Nintendo-era adventures without reproducing Nintendo characters, sprites, maps, palettes, music, or trade dress.

The visual blend has three clear jobs:

- **Slotbound — composition and appeal:** compact readable combatants, a warm battlefield, clear formations, tactile reward presentation and a satisfying preparation-to-auto-battle rhythm.
- **Zelda — world and atmosphere:** memorable tile-based environments, small secrets, cozy fantasy biomes, expressive props, readable top-down / side-on 2D spaces and adventurous mood.
- **Mario — character clarity and charm:** instantly readable silhouettes, expressive poses, friendly faces, playful enemy shapes, strong color separation and joyful animation timing.

These are broad design principles, not a request to imitate a particular game. Casino Battle owns its world, characters, tile set, icons, UI and animation language.

## Non-negotiable visual pillars

1. **Strict 2D pixel art.** Pixel sprites, tile maps, 2D effects and 2D UI only. No 3D models, 2.5D asset rendering, perspective cameras, mesh lighting or glossy 3D props.
2. **Cozy retro fantasy.** A warm, inviting world with moss, old wood, little villages, ruins, mushrooms, rivers, gardens and friendly odd creatures. It must feel premium and deliberate rather than like a generic mobile game.
3. **Pixel clusters, not vector cartoons.** Shapes use intentional pixel groupings, stepped contours, limited color ramps and nearest-neighbour scaling. No anti-aliased vector outlines, smooth gradients or painterly blur.
4. **Cute, not babyish.** Compact bodies, readable heads, expressive faces and one signature silhouette feature per unit. Character identity must remain clear at small sizes.
5. **Combat readability first.** Ally and enemy silhouettes, attack wind-ups, hit flashes, damage and healing must be easy to parse during simultaneous Auto-battle.
6. **Warm material feel.** Pixelated parchment, grass, wood, stone, fabric and soft light can make the world tactile. Texture must come from authored pixel clusters and tile details, not a blurred paper filter.
7. **Premium restraint.** Avoid neon, overdrawn particles, noisy HUD panels, low-effort asset packs, tiny unreadable text and excessive screen shake.

## Pixel scale and rendering contract

- Target internal canvas: **640×360**.
- Target window: **1280×720**, with **2× nearest-neighbour integer scaling**.
- Texture filtering: nearest. Pixel snapping: enabled for 2D transforms and vertices.
- Character sprites: generally 24×24 to 32×32 source pixels; bosses may be 48×48 or larger.
- Environment tiles: 16×16 source pixels, with 2×2 or 4×4 decorative clusters where appropriate.
- HUD icons: design at 8×8, 12×12 or 16×16 source pixels; never scale a tiny icon non-uniformly.
- Animations use authored frame steps. Idle loops are economical; anticipation, contact and recovery frames are deliberately readable.
- Do not use fractional scaling. If another display resolution is needed, preserve integer scaling and add letterboxing rather than blur.

## Palette system

Use compact, coherent ramps rather than a single flat fill. Each material normally has 3–4 values: shadow, base, light and a rare highlight. The global palette is warm and botanical:

| Token | Hex | Use |
|---|---|---|
| Cream Paper | `#F3EBDD` | Menus, parchment and light stone |
| Deep Ink | `#4A4540` | Dark outlines and text |
| Moss | `#718B70` | Grass, leaves and forest creatures |
| Sage | `#91A68A` | Healing and calm magic |
| Clay | `#C77F62` | Warm accents and enemy tells |
| Honey | `#DDBB72` | Rewards, gold and warm highlights |
| River | `#6F9EAF` | Water, frost and sky |
| Moon Berry | `#9C7180` | Rare magic and unusual creatures |

Biome palettes may add local colors, but should remain harmonious with this base. Outlines use deep warm ink, not pure black everywhere.

## Character design rules

- Every unit gets a distinct silhouette before color is applied.
- Design for 24–32 source pixels of character height; test the sprite at native scale and at 2×.
- Faces use a small number of high-contrast pixels. Eye placement and posture carry most of the personality.
- Costume, weapon or creature feature must be recognizable in a 3-frame idle loop.
- Units of the same role may share animation logic, never the same body silhouette with only a hue swap.
- Allies, enemies, elites and bosses each have consistent shape-language families.
- Avoid direct visual quotations of Link, Mario, Goombas, Koopas or other Nintendo characters.

## World and battlefield

- The first battle camera is a **flat 2D side-on arena** with three readable tactical lanes. Do not change to 3D or isometric 3D.
- Roguelike route, camp and biome screens may use top-down 2D tile maps if they preserve the same pixel scale and palette.
- Build biomes as tile sets: Moss Meadow, Amber Orchard, Rain-Kissed Ruins, Mushroom Library, Sleepy Harbor and Cloud Garden.
- Keep the combat ground plane uncluttered. Decorative props must not look like enemies or obscure units.
- Background depth is created by tile placement, palette value and parallax-free layering, not 3D perspective.

## Animation and visual effects

- Idle: 2–4 frame breathing, blinking, tail/leaf/ear motion and tiny environment movement.
- Attack: anticipation, one clear contact frame, impact pixels and a short recovery.
- Damage: compact flash, small recoil and a brief damage number.
- Healing: distinct green/blue pixel motes and a readable plus marker.
- Defeat: short fall, pop or dissolve; no gore.
- Rewards: a compact, satisfying sparkle and bounce; avoid full-screen particle noise.
- Effects must never obscure a unit's face, target or health indicator.

## UI direction

- Use pixel panels, chunky borders, tiny decorative corner marks and a bitmap/pixel font with generous line spacing.
- Keep the Fate Board as a magical charm / sigil object, not a slot machine cabinet.
- The player should see formation, unit traits, synergies, equipment, relics and the next encounter at a glance.
- Do not use casino furniture or iconography: no roulette wheel, poker table, playing-card suits, chips, felt tables or casino rooms.
- Text must remain legible at 1280×720 and Steam Deck scale. Never shrink a bitmap font below its readable native pixel height.

## Do / don't

**Do:** 8/16-bit warmth, Zelda-like world charm, Mario-like silhouette clarity, Slotbound-like battle readability, limited palette ramps, expressive sprite animation, authored pixel clusters, cozy fantasy.

**Don't:** 3D, smooth vector characters, blurred filters, gradients pretending to be pixel art, generic chibi packs, casino interiors, direct Nintendo imitation, copied Slotbound assets, visual clutter.

## Reference interpretation

- Slotbound informs battlefield composition, readable units and the draft/build/auto-battle loop.
- Classic Zelda-era games inform world-building, tile grammar and cozy adventure atmosphere.
- Classic Mario-era games inform character readability, playful animation and strong silhouettes.
- Despot's Game and Rogue Battler show that pixel graphics can carry an auto-battler / roguelite structure. They are genre references, not art templates.

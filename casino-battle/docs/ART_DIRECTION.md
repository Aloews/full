# Casino Battle — locked 2D pixel-art direction

**Status: LOCKED. Primary visual style is modern 16-bit pixel art. Any visual deviation requires an explicit product decision.**

## The target

Casino Battle should feel like a lost, lovingly crafted 16-bit adventure RPG: inviting overworld colors and visual clarity reminiscent of the era of *The Legend of Zelda: A Link to the Past* and *Super Mario World*, combined with the compact tactical readability of modern indie roguelites.

These games are **style references only**. Do not copy their characters, sprites, maps, tiles, UI, animations, music, names, logos or exact compositions. Casino Battle must have its own world, characters and iconography.

The target is not crude 8-bit minimalism and not a blurry retro filter. It is crisp, deliberate pixel art with expressive sprite silhouettes, controlled palettes, readable animation and modern production polish.

## Non-negotiable rendering contract

1. **Strict 2D.** No 3D scenes, meshes, perspective cameras, pseudo-3D, 2.5D asset rendering or isometric 3D.
2. **Pixel-perfect rendering.** Godot viewport stretch mode `viewport`, integer scaling, nearest-neighbour texture filtering and pixel-aligned coordinates. Never bilinear-filter pixel sprites.
3. **Fixed logical canvas.** Prototype target is 640×360, displayed at 1280×720 with 2× integer scaling. Keep 16:9 composition; support larger displays through integer multiples and letterboxing rather than uneven fractional scaling.
4. **Authentic pixel clusters.** Every sprite is authored on a deliberate pixel grid. Use intentional clusters, clean diagonals, controlled outline thickness and readable negative space. Do not rasterize smooth vector art and call it pixel art.
5. **No blur or mandatory CRT filter.** Optional CRT/scanline presentation may be explored later, but it is off by default and must never soften the base pixel art.
6. **Combat stays readable.** Units, targets, health, role effects and damage values must remain distinct at native logical resolution.

## Visual pillars

- **16-bit adventure warmth:** lush grass, earth, stone, water, timber, flowers, dungeons and cozy settlements.
- **Colorful but controlled:** brighter and more varied than the former parchment-only palette, while avoiding neon and random gradients.
- **Cute, not babyish:** little adventurers with recognisable silhouettes, expressive faces, equipment and clear class identity.
- **Tactile pixel surfaces:** deliberate dithering, checkerboard shadows, grass tufts, stone chips, water highlights and small environmental details.
- **Premium indie clarity:** elegant composition and a consistent art bible; no generic asset-pack collage, placeholder emoji or random icon collections.

## Palette

Use a shared world palette with small per-biome variations. Each character normally uses 5–8 colors plus outline.

| Token | Hex | Use |
|---|---|---|
| Deep ink | `#2B2638` | Main outlines and deepest shadows |
| Bark | `#694653` | Wood, earth and warm shadow |
| Soil | `#A66B4F` | Ground, leather and warm surfaces |
| Grass | `#5E9B58` | Main vegetation |
| Leaf light | `#9BCB69` | Highlights and new growth |
| Sky | `#72B9D2` | Sky, water and cool effects |
| Water light | `#B7E3D0` | Water highlights and healing |
| Sun | `#F3C969` | Rewards and warm magic |
| Ember | `#E87958` | Fire and attack tells |
| Berry | `#A66DA6` | Rare magic and danger |
| Stone | `#8C8B9C` | Rock, metal and neutral enemies |
| Cream | `#F5E9BD` | UI contrast and highlights |

Keep hue/value separation strong enough that allies and enemies remain readable without relying on color alone.

## Sprite specification

- Character sprite target: 24×24 to 32×32 logical pixels for standard units; larger bosses may use 48×48 or 64×64.
- Environment tiles: 16×16 logical pixels, with 8×8 micro-details used sparingly.
- UI icons: 8×8 or 16×16 logical pixels.
- Outline: normally one logical pixel; use selective outline only when the silhouette remains readable.
- Avoid single-pixel noise. Every pixel cluster must describe form, light, material or expression.
- Each unit has one unmistakable silhouette cue: leaf cap, oversized scarf, shell, lantern, antlers, mushroom hood, bell, wing shape or a distinctive weapon.
- Faces stay legible at native size. Use large, deliberate eyes and few facial pixels.
- Equipment never obscures the face or core silhouette.
- Enemies can be mischievous, odd or spooky, but not gore-heavy or grimdark.

## Character families

All six sigil families need distinct silhouettes, not recolors of one template:

- Leaf — guardian: moss armour, leaf crest, broad stance.
- Ember — striker: fox/cat-like ears, flame tuft, quick stance.
- Tide — support: droplet body, water crest, soft readable face.
- Stone — guardian: chunky pebble shell, short sturdy legs.
- Moon — mystic: crescent hood, star markings, small magical focus.
- Wing — striker: feather crest, light body, wing-like side silhouette.

Boss sprites must be 1.5–2× a standard unit's visual footprint, with their own palette, outline and animation timing.

## Battlefield and environments

- First camera: flat side-on 2D battle lane with three tactical rows; no perspective projection.
- Build the environment from tileable pixel-art layers: distant sky/hills, biome silhouette, midground props, ground tiles, foreground accents.
- First biome: Moss Meadow — bright grass, worn earth paths, small flowers, old stone markers and a distant tree line.
- Later biomes should introduce distinct palettes and tilesets: amber orchard, rain ruins, mushroom library, sleepy harbor and cloud garden.
- Keep the combat lane uncluttered; high-contrast sprites own the foreground.
- Battle backgrounds can have subtle tile animation, but movement must not compete with unit attacks.

## Animation direction

- Idle: 2–4 frames, tiny bounce or blink.
- Attack: anticipation, strike, impact; 3–6 readable frames.
- Damage: brief palette flash and one short recoil.
- Defeat: compact 4–6 frame collapse or dissolve, no gore.
- Boss tells: highly legible 2–3 frame warning animation before the action resolves.
- VFX: pixel sparks, short slash trails, small water/heal motes and controlled hit flashes.
- Keep animation deterministic and presentation-only. The Rust simulation remains authoritative.

## UI direction

- Pixel-framed panels with carefully designed corners and repeatable 9-slice borders.
- Use a bitmap/pixel font for headings and labels when the final font asset is approved; stats must remain highly legible.
- Use pixel icons for hearts, essence, rank, sigils and relics.
- Fate Board is an ancient magical tile tapestry, not a slot machine. Symbols must be readable as distinct pixel glyphs.
- Avoid casino motifs: no reels, roulette wheels, poker suits, chips, felt tables or slot-machine cabinets.
- Avoid oversized gradients, glassmorphism, blur, smooth vector icon packs and excessive glow.

## Do / don't

**Do:** crisp 16-bit pixel art, intentional clusters, expressive sprites, colorful overworld, readable tactical UI, original fantasy world, tile-based environments.

**Don't:** copied Nintendo sprites or characters, blurry scaling, fractional pixel movement, bilinear filtering, pseudo-3D, casino furniture, neon overload, generic asset-pack collage, noisy dithering, smooth vector characters disguised with a pixel filter.

## Reference interpretation

- *The Legend of Zelda: A Link to the Past* — top-down world color, exploration readability, terrain and building tiles, character scale.
- *Super Mario World* — approachable expressive silhouettes, clear animation, memorable enemies and colorful world accents.
- *Shogun Showdown* — modern indie pixel readability, tactical composition and clean combat feedback.
- *Loop Hero* — dense systems and tiny pixel assets communicating a complex roguelite build.
- *Pixelords* — contemporary 2D pixel-art auto-battler reference for unit roles, placement and build synergies.
- Slotbound remains a gameplay-loop reference only: preparation, formation and automated encounters. Its visual assets and exact UI are not copied.

These references define broad visual principles, not a template. Casino Battle's silhouettes, sprite sheets, tilesets, effects, interface and world are original.

# Visual Style Guide — Slotbound

## Creative direction

**Cozy 16-bit Fantasy Pixel Art**: a warm, approachable fantasy adventure presented with the clarity and restraint of a polished 16-bit game. It should feel like a small world worth returning to: a woodland frontier, a curious rune machine, a welcoming supply camp, memorable creatures, and tactical battles that remain legible at a glance.

The reference point is the broad visual language of classic 8-bit and 16-bit console adventures: tile-based environments, expressive silhouettes, limited palettes, strong value grouping, simple readable animation and playful character design. These are principles, not assets. Slotbound must not reproduce Nintendo characters, sprites, maps, music, logos, exact compositions, UI layouts or distinctive trade dress. All production sprites, tiles, effects, interface artwork and audio must be original or properly licensed.

## Art pillars

1. **Warm fantasy, not grimdark.** Threats may be dangerous, but the world stays inviting. Forests feel alive; ruins feel ancient rather than horrific; bosses are imposing without becoming graphic.
2. **Readable before decorative.** A unit's class, allegiance, current health and action must be understandable at native size. Effects never obscure the board or the combat result.
3. **Pixel craft, not pixel filters.** Characters and environment are designed on a deliberate pixel grid. Do not apply a blur or a generic pixelation filter to high-resolution artwork.
4. **Small details create personality.** Idle blinking, breathing, ear/leaf movement, tiny glints, swaying grass and reactive environment details bring scenes to life.
5. **One consistent world.** Board symbols, roster portraits, enemy silhouettes, item icons, map tiles and menu ornaments use the same palette, outline logic, shadow direction and pixel scale.

## Rendering and grid

- The game is strictly **2D**: orthographic presentation, flat sprites, tile maps and layered parallax only. No 3D meshes, perspective cameras or 2.5D battle stages.
- Reference internal composition: 640×360 logical canvas for a 16:9 screen, scaled with nearest-neighbour sampling. Browser layouts may reflow responsively, but the game-art stage keeps integer pixel scaling whenever the viewport permits it.
- Character base sprite: 16×16 or 24×24 logical pixels for common units; larger bosses may use 32×32 or 48×48.
- Environment tiles: 16×16 logical pixels. Props may combine tiles but must align to the same grid.
- Pixel edges are crisp. Disable smoothing for pixel canvases and textures. Never scale sprite source artwork through bilinear interpolation.
- Pixel snapping is required for moving sprites and camera offsets. Subpixel motion may be used for UI transitions, but not for the pixel-art world layer.
- Keep UI text at a readable scale. Use a deliberately selected bitmap font in production; until licensed/generated font assets exist, use a restrained monospaced fallback and do not claim that it is a final bitmap font.

## Palette

The palette is warm, low-noise and role-based. The first prototype palette is:

| Role | Colour | Hex |
|---|---|---|
| Ink / outline | Deep plum charcoal | `#2B2638` |
| Night forest | Deep evergreen | `#243D38` |
| Forest midtone | Leaf green | `#5E9B58` |
| Moss highlight | Soft sage | `#9BC477` |
| Warm paper | Parchment | `#F5E9BD` |
| Wood / earth | Chestnut | `#9A6545` |
| Clay / danger | Terracotta | `#E87958` |
| Honey / reward | Golden yellow | `#F3C969` |
| Water / magic | Clear sky blue | `#72B9D2` |
| Rare magic | Berry violet | `#A66DA6` |
| Light / sparkle | Cream white | `#FFF6D8` |

Palette rules:
- Use the deep ink colour for outlines and the darkest shadow, not pure black.
- Use warm paper for panels, labels and readable copy, not for every surface.
- Reserve terracotta for danger, damage and hostile telegraphs.
- Reserve honey for rewards, selected actions and high-value information.
- Use blue and violet for distinct magic families; do not make all special effects the same colour.
- A sprite should normally use a compact local palette of 4–7 colours plus transparency.

## Shape language and silhouettes

- Allies: rounded, compact, friendly forms with one strong identifying feature.
- Enemies: asymmetrical, slightly sharper silhouettes; distinguish them from allies by posture and eye treatment, not merely by recolouring.
- Tanks: broad lower body and shield/crest silhouette.
- Ranged units: narrow vertical profile, visible bow or ranged tool.
- Casters: clear head/hood shape with a concentrated magic accent.
- Support units: open, calm silhouette and a healing motif.
- Rogues: low, angled silhouette, twin blades or a distinct scarf/hood.
- Beasts: quadruped profile, clear snout, ears and tail.
- Bosses: larger multi-tile silhouette and a unique idle/action rhythm; never just an enlarged common enemy.

## Animation language

- Idle loop: 2–4 frames; subtle breathing, blink, leaf/ear movement or a one-pixel bob.
- Attack: anticipation → short lunge/projectile → contact flash → recovery.
- Hit: brief one- or two-frame white/terracotta flash, knockback of a few pixels and readable damage number.
- Guard: a compact shield flash that does not cover the unit's health state.
- Heal: upward motes or a soft green/blue pulse, with the amount shown in the event log.
- Defeat: clear collapse/fade sequence; no gore.
- Boss telegraph: show the affected lane/target and a short anticipation cue before the hit.
- Reduced-motion setting must suppress nonessential loops and camera shake without removing gameplay information.

## Environment and biomes

Initial biome: **Mosslight Meadow** — grass, soft flowers, stepping stones, small mushrooms, old boundary walls and a distant tree line.

Expansion palette:
- **Mosslight Meadow:** green grass, cream flowers, warm stone, soft sunlight.
- **Whisperwood:** layered trees, roots, mushrooms, fireflies and deep green shadows.
- **Tideglass Ruins:** pale stone, blue water channels, broken pillars and glassy magic.
- **Cinder Orchard:** burnt orange leaves, ember flowers, dark soil and controlled warm highlights.
- **Moonfen:** indigo water, violet plants, pale reeds and reflected starlight.

Every biome needs a ground tile set, edge/corner transitions, obstacles, props, a distant background layer, ambient animation and a small set of biome-specific enemy silhouettes. Avoid repeating a single tile so frequently that the terrain looks like a checkerboard.

## Interface

The UI should look like a handcrafted field journal mixed with a small fantasy workshop:
- parchment panels, wood/stone frames and restrained stitched or engraved details;
- square or subtly stepped corners rather than large modern rounded cards;
- clear selected, unavailable, locked, dangerous and rewarded states;
- large, tactile primary actions with unambiguous disabled states;
- compact status chips for gold, hearts, wave, sigil draws and roster capacity;
- no casino furniture, poker chips, roulette wheels, slot cabinets, casino carpets or casino-room staging.

The 3×3 symbol board is a magical recruitment device, not a realistic gambling machine. Symbols are rune tiles and class sigils. Winning lines animate as connected magical traces, then the summoned unit appears in the roster. A line should never flash so intensely that the player cannot identify which symbols matched. The board is called the Fate Board in player-facing copy; its action is a sigil draw, and the once-per-wave column action is a sigil shift.

## Sound direction

Original, restrained chiptune-inspired music with warm acoustic timbres layered over simple synth tones. Distinct short cues for sigil draw, line match, recruit, absorb, promotion, battle start, hit, heal, boss telegraph, victory and defeat. Avoid recreating recognizable Nintendo melodies or sound effects. Provide volume controls and mute.

## Quality gates for art

A new asset is accepted only when:
- its source and licence/provenance are recorded;
- it aligns to the logical pixel grid and uses nearest-neighbour presentation;
- silhouette and role remain readable at 1× and 2×;
- its palette matches this guide and its colours have semantic roles;
- the asset has a naming convention and dimensions recorded in the asset manifest;
- animation strips have explicit frame count, frame order, frame duration and loop policy;
- a reviewer checks it in the actual game scene, not only in an isolated sprite sheet.

## Current asset status

The current web prototype has six original 16×16 class sprite prototypes drawn into canvas at runtime and a procedural 320×64 woodland-frontier scene with stepped mountains, tree silhouettes, a rune shrine, path stones and small party silhouettes. The interface uses a custom parchment/forest pixel-style CSS treatment, crisp scaling and responsive layout. These are composition prototypes, not a production asset library. Still missing: external sprite sheets and atlas/manifest, frame-by-frame character and combat animations, a real 16×16 biome tilemap with edge/corner transitions, original bitmap typography, authored enemy art, provenance metadata and visual regression tests at desktop/mobile sizes. A CSS restyle or a sprite drawn by code is not a finished art set.

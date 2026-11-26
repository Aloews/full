#!/usr/bin/env python3
"""Verify the strict 2D pixel-art contract and reject accidental 3D scenes."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1] / "client"
FORBIDDEN = (
    "Node3D",
    "Camera3D",
    "MeshInstance3D",
    "CSGBox3D",
    "StaticBody3D",
    "CharacterBody3D",
    "RigidBody3D",
    "WorldEnvironment",
)

violations: list[str] = []
for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix not in {".gd", ".tscn", ".tres", ".godot"}:
        continue
    source = path.read_text(encoding="utf-8")
    for token in FORBIDDEN:
        if token in source:
            violations.append(f"{path.relative_to(ROOT)}: forbidden 3D token {token}")

project_text = (ROOT / "project.godot").read_text(encoding="utf-8")
required_project_settings = (
    "window/size/viewport_width=640",
    "window/size/viewport_height=360",
    "window/size/window_width_override=1280",
    "window/size/window_height_override=720",
    'window/stretch/mode="viewport"',
    'window/stretch/aspect="keep"',
    'window/stretch/scale_mode="integer"',
    "textures/canvas_textures/default_texture_filter=0",
    "rendering/2d/snap/snap_2d_transforms_to_pixel=true",
    "rendering/2d/snap/snap_2d_vertices_to_pixel=true",
)
for setting in required_project_settings:
    if setting not in project_text:
        violations.append(f"project.godot: missing pixel-art setting {setting}")

main_text = (ROOT / "scripts" / "main.gd").read_text(encoding="utf-8")
required_pixel_contract = (
    "draw_set_transform(Vector2.ZERO, 0.0, Vector2(0.5, 0.5))",
    "root.scale = Vector2(0.5, 0.5)",
    "get_window().min_size = Vector2i(640, 360)",
    "texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST",
    "func _pixel_point(point: Vector2) -> Vector2:",
    "var pixel_step := 4.0 if label == \"Mosswood Guardian\" else 2.0",
    "func _get_sprite_texture(label: String, coat: Color, blinking: bool) -> Texture2D:",
    "ImageTexture.create_from_image(sprite_image)",
    "draw_texture_rect(sprite_texture, Rect2(origin, Vector2(sprite_size, sprite_size)), false, tint)",
    "event.position * 2.0",
)
for token in required_pixel_contract:
    if token not in main_text:
        violations.append(f"main.gd: missing pixel-art contract {token}")

# Character sprites must be authored as complete, fixed-size pixel maps.
creature_section = main_text.split("func _creature_pixels", 1)
if len(creature_section) != 2:
    violations.append("main.gd: missing _creature_pixels sprite catalog")
else:
    creature_section = creature_section[1].split("func _creature_palette", 1)[0]
    sprite_blocks = re.findall(r"return PackedStringArray\(\[(.*?)\]\)", creature_section, re.DOTALL)
    if len(sprite_blocks) < 8:
        violations.append(f"main.gd: expected at least 8 original sprite maps, found {len(sprite_blocks)}")

    required_characters = (
        "Mossguard",
        "Cinderkit",
        "Puddlekin",
        "Pebbleback",
        "Moonmote",
        "Breezeling",
        "Gloomling",
        "Murkling",
        "Mosswood Guardian",
    )
    for character in required_characters:
        if f'"{character}":' not in creature_section:
            violations.append(f"main.gd: missing distinct sprite definition for {character}")

    sprite_signatures: set[tuple[str, ...]] = set()
    allowed_pixels = set(".ksbhaep")
    for sprite_index, block in enumerate(sprite_blocks):
        rows = re.findall(r'"([^"]*)"', block)
        if len(rows) != 16:
            violations.append(f"main.gd: sprite map {sprite_index} must contain 16 rows, found {len(rows)}")
            continue

        dimensions_valid = True
        for row_index, row in enumerate(rows):
            if len(row) != 16:
                dimensions_valid = False
                violations.append(
                    f"main.gd: sprite map {sprite_index} row {row_index} must be 16 pixels wide, found {len(row)}"
                )

        if not dimensions_valid:
            continue

        pixels = set("".join(rows))
        unknown_pixels = pixels - allowed_pixels
        if unknown_pixels:
            violations.append(
                f"main.gd: sprite map {sprite_index} uses unknown palette keys {sorted(unknown_pixels)}"
            )

        if not {"k", "s", "b"}.issubset(pixels):
            violations.append(f"main.gd: sprite map {sprite_index} needs outline, shadow and base clusters")

        filled_pixels = sum(character != "." for row in rows for character in row)
        if filled_pixels < 24 or filled_pixels > 220:
            violations.append(
                f"main.gd: sprite map {sprite_index} has implausible silhouette coverage ({filled_pixels}/256)"
            )

        signature = tuple(rows)
        if signature in sprite_signatures:
            violations.append(f"main.gd: sprite map {sprite_index} duplicates another unit silhouette")
        sprite_signatures.add(signature)

    if len(sprite_signatures) < 8:
        violations.append("main.gd: fewer than eight unique pixel silhouettes are defined")

if violations:
    print("\n".join(violations), file=sys.stderr)
    raise SystemExit(1)

print("2D pixel-art contract passed: no 3D nodes, integer nearest scaling and validated 16x16 sprite maps.")

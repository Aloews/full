#!/usr/bin/env python3
"""Reject 3D nodes and guard the Godot pixel-art rendering contract."""
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
    "func _pixel_point(point: Vector2) -> Vector2:",
    "func _creature_pixels(label: String) -> PackedStringArray:",
    "draw_rect(Rect2(pixel_position, Vector2(pixel_step, pixel_step)), color)",
    "event.position * 2.0",
)
for token in required_pixel_contract:
    if token not in main_text:
        violations.append(f"main.gd: missing pixel-art contract {token}")

sprite_match = re.search(
    r"func _creature_pixels\(label: String\) -> PackedStringArray:(.*?)\nfunc _creature_palette",
    main_text,
    re.DOTALL,
)
if sprite_match is None:
    violations.append("main.gd: missing sprite pixel-matrix definition")
else:
    sprite_source = sprite_match.group(1)
    expected_sprites = (
        "Mossguard", "Cinderkit", "Puddlekin", "Pebbleback",
        "Moonmote", "Breezeling", "Gloomling", "Murkling",
        "Mosswood Guardian",
    )
    for sprite_name in expected_sprites:
        if f'"{sprite_name}":' not in sprite_source:
            violations.append(f"main.gd: missing original pixel sprite {sprite_name}")

    sprite_rows = re.findall(r'"([.ksbhaep]+)"', sprite_source)
    if not sprite_rows:
        violations.append("main.gd: no pixel sprite rows found")
    elif any(len(row) != 16 for row in sprite_rows):
        bad_lengths = sorted({len(row) for row in sprite_rows if len(row) != 16})
        violations.append(f"main.gd: sprite rows must be 16 pixels wide; found widths {bad_lengths}")

if violations:
    print("\n".join(violations), file=sys.stderr)
    raise SystemExit(1)

print("2D pixel-art contract passed: no 3D nodes, integer viewport scaling, pixel snapping and authored 16x16 sprite matrices verified.")

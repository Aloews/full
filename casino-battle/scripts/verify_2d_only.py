#!/usr/bin/env python3
"""Reject accidental 3D scene nodes in the Godot client."""
from pathlib import Path
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
    text = path.read_text(encoding="utf-8")
    for token in FORBIDDEN:
        if token in text:
            violations.append(f"{path.relative_to(ROOT)}: forbidden 3D token {token}")

if violations:
    print("\n".join(violations), file=sys.stderr)
    raise SystemExit(1)

PROJECT = ROOT / "project.godot"
project_text = PROJECT.read_text(encoding="utf-8")
required_project_settings = (
    "window/size/viewport_width=640",
    "window/size/viewport_height=360",
    "window/size/window_width_override=1280",
    "window/size/window_height_override=720",
    'textures/canvas_textures/default_texture_filter=0',
    "rendering/2d/snap/snap_2d_transforms_to_pixel=true",
    "rendering/2d/snap/snap_2d_vertices_to_pixel=true",
)
for setting in required_project_settings:
    if setting not in project_text:
        violations.append(f"project.godot: missing pixel-art setting {setting}")

main_script = ROOT / "scripts" / "main.gd"
main_text = main_script.read_text(encoding="utf-8")
required_pixel_contract = (
    "draw_set_transform(Vector2.ZERO, 0.0, Vector2(0.5, 0.5))",
    "func _pixel_snap(value: float) -> float:",
    "draw_polyline(_closed(pixel_points), INK, pixel_width, false)",
)
for token in required_pixel_contract:
    if token not in main_text:
        violations.append(f"main.gd: missing pixel-art contract {token}")

if violations:
    print("\\n".join(violations), file=sys.stderr)
    raise SystemExit(1)

print("2D pixel-art contract passed: no 3D nodes, nearest filtering and pixel snapping configured.")

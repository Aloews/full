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

print("2D contract passed: no forbidden 3D scene nodes found.")

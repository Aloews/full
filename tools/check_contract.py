"""Static check that browser controls and API route contracts remain connected."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "crates/api/src/main.rs").read_text(encoding="utf-8")
client = (ROOT / "web/app.js").read_text(encoding="utf-8")
domain = (ROOT / "crates/game-core/src/lib.rs").read_text(encoding="utf-8")
html = (ROOT / "web/index.html").read_text(encoding="utf-8")

routes = set(re.findall(r'\.route\("(/api/[^\"]+)"', api))
required_routes = {
    "/api/runs", "/api/runs/{run_id}", "/api/runs/{run_id}/spin", "/api/runs/{run_id}/nudge",
    "/api/runs/{run_id}/absorb", "/api/runs/{run_id}/promotion", "/api/runs/{run_id}/lock",
    "/api/runs/{run_id}/battle", "/api/runs/{run_id}/next-wave", "/api/runs/{run_id}/core",
    "/api/runs/{run_id}/item", "/api/runs/{run_id}/event", "/api/runs/{run_id}/route",
}
missing_routes = sorted(required_routes - routes)
if missing_routes:
    raise SystemExit(f"API route contract missing: {missing_routes}")
for endpoint in ("spin", "nudge", "absorb", "promotion", "lock", "battle", "next-wave", "core", "item", "event", "route"):
    if f"/{endpoint}" not in client:
        raise SystemExit(f"browser action missing API call suffix: /{endpoint}")


if 'data-action="route-choice"' not in client or "choose_route" not in api:
    raise SystemExit("branching route choice flow is not connected")
if "JourneyRouteRequired" not in api or "pending_route" not in client:
    raise SystemExit("route progression gate or browser state is missing")

if "pub struct FormationPosition" not in domain or "fn select_target_index" not in domain:
    raise SystemExit("typed tactical formation or lane-aware target selector is missing")
if domain.count("position: Some(unit.position)") < 2:
    raise SystemExit("battle report must include ally and enemy formation snapshots")
if "unit.position?.row" not in client or "unit.position?.lane" not in client:
    raise SystemExit("pixel battlefield does not render server-authored formation positions")
if "target.position.lane + 1" not in domain or "boss_telegraph" not in client:
    raise SystemExit("target-specific boss telegraph is not connected to the battlefield")
if "function playBattleReplay(report)" not in client:
    raise SystemExit("battle replay renderer is missing")
if 'data-action="journey-choice"' not in client or "resolve_event" not in api:
    raise SystemExit("journey event choice flow is not connected")
if "resolve_journey_event" not in api or "JourneyEventRequired" not in api:
    raise SystemExit("journey event persistence or next-wave gate is missing")

ids = set(re.findall(r'id="([a-z0-9-]+)"', html))
selectors = set(re.findall(r"\$\('([a-z0-9-]+)'\)", client))
dynamic_ids = {"next-wave", "restart", "start-battle", "battlefield"}
missing_ids = sorted(selectors - ids - dynamic_ids)
if missing_ids:
    raise SystemExit(f"browser references DOM IDs not present in the shell: {missing_ids}")
for dynamic_id in dynamic_ids:
    if f'id="{dynamic_id}"' not in client:
        raise SystemExit(f"browser dynamic control is not rendered: {dynamic_id}")
for asset in ("/app.js", "/style.css"):
    if asset not in api:
        raise SystemExit(f"API static asset route missing: {asset}")
    if not (ROOT / "web" / asset.lstrip("/")).is_file():
        raise SystemExit(f"static asset not found: {asset}")

print(f"Contract OK: {len(required_routes)} API routes, {len(selectors)} DOM selectors, static assets present.")

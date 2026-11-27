"""Static check that browser controls and API route contracts remain connected."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / "crates/api/src/main.rs").read_text(encoding="utf-8")
client = (ROOT / "web/app.js").read_text(encoding="utf-8")
html = (ROOT / "web/index.html").read_text(encoding="utf-8")

routes = set(re.findall(r'\.route\("(/api/[^\"]+)"', api))
required_routes = {
    "/api/runs", "/api/runs/{run_id}", "/api/runs/{run_id}/spin", "/api/runs/{run_id}/nudge",
    "/api/runs/{run_id}/absorb", "/api/runs/{run_id}/promotion", "/api/runs/{run_id}/lock",
    "/api/runs/{run_id}/battle", "/api/runs/{run_id}/next-wave", "/api/runs/{run_id}/core",
    "/api/runs/{run_id}/item", "/api/runs/{run_id}/event", "/api/runs/{run_id}/route",
    "/api/runs/{run_id}/formation",
}
missing_routes = sorted(required_routes - routes)
if missing_routes:
    raise SystemExit(f"API route contract missing: {missing_routes}")
for endpoint in ("spin", "nudge", "absorb", "promotion", "lock", "battle", "next-wave", "core", "item", "event", "route", "formation"):
    if f"/{endpoint}" not in client:
        raise SystemExit(f"browser action missing API call suffix: /{endpoint}")


if 'data-action="route-choice"' not in client or "choose_route" not in api:
    raise SystemExit("branching route choice flow is not connected")
if "JourneyRouteRequired" not in api or "pending_route" not in client:
    raise SystemExit("route progression gate or browser state is missing")

if "target_id" not in client or "BossTelegraph" not in api + (ROOT / "crates/game-core/src/lib.rs").read_text(encoding="utf-8"):
    raise SystemExit("boss telegraph target data is missing")
if "route-trail" not in client:
    raise SystemExit("route history trail is missing")

if "ShieldGranted" not in (ROOT / "crates/game-core/src/lib.rs").read_text(encoding="utf-8"):
    raise SystemExit("Guardian Shieldwall domain event is missing")
if "shield_granted" not in client or "shield_absorbed" not in client:
    raise SystemExit("Guardian Shieldwall replay is missing")

core = (ROOT / "crates/game-core/src/lib.rs").read_text(encoding="utf-8")
if "pub enum FormationRow" not in core or "pub lane: u8" not in core or "pub stack: u8" not in core:
    raise SystemExit("authoritative formation snapshot contract is missing")
if "unit.row" not in client or "unit.lane" not in client or "const front = unit.row" not in client:
    raise SystemExit("browser battlefield does not render server formation positions")

if 'data-action="formation-row"' not in client or 'data-action="formation-lane"' not in client:
    raise SystemExit("player formation controls are not connected")
if "set_formation" not in api or "FormationRequest" not in api:
    raise SystemExit("formation endpoint does not call the Rust domain")
if "formation-lanes" not in client or "[0, 1, 2].map" not in client or "aria-pressed" not in client:
    raise SystemExit("direct three-lane formation selector is missing")
if "least_occupied_lane" not in core and "lane_occupancy" not in core:
    raise SystemExit("new unit placement does not account for current lane occupancy")
if "pub enum BiomeKind" not in core or "pub biome: BiomeKind" not in core:
    raise SystemExit("battle reports do not persist their biome")
if "stage_for_wave" not in core or "biome_for_wave" not in core or "build_enemy_party(self.wave, boss, elite, biome)" not in core:
    raise SystemExit("wave-to-biome progression is not connected to enemy generation")
for family in ("Cinder Moth", "Shard Beetle", "Emberfen Tyrant", "Prism Colossus"):
    if family not in core:
        raise SystemExit(f"biome enemy roster or boss is missing: {family}")
if "const BIOME_META" not in client or "paintWorldScene(region.key)" not in client or "report.biome" not in client:
    raise SystemExit("biome-specific world and battle presentation are missing")

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

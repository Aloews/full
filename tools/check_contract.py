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
    "/api/runs/{run_id}/item", "/api/runs/{run_id}/event",
}
missing_routes = sorted(required_routes - routes)
if missing_routes:
    raise SystemExit(f"API route contract missing: {missing_routes}")
for endpoint in ("spin", "nudge", "absorb", "promotion", "lock", "battle", "next-wave", "core", "item", "event"):
    if f"/{endpoint}" not in client:
        raise SystemExit(f"browser action missing API call suffix: /{endpoint}")

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

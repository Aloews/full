export async function GET() {
  const base = process.env.AUREL_API_URL;
  if (!base) return Response.json({ ok: false, error: "api_url_missing" }, { status: 503 });
  try {
    const result = await fetch(base.replace(/\\/$/, "") + "/health", { cache: "no-store" });
    const body = await result.json();
    return Response.json({ ok: result.ok, api: body }, { status: result.status });
  } catch {
    return Response.json({ ok: false, error: "api_unreachable" }, { status: 503 });
  }
}

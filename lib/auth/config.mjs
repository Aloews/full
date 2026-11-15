export function getNeonAuthConfig(env = process.env) {
  const baseUrl = typeof env.NEON_AUTH_BASE_URL === "string" ? env.NEON_AUTH_BASE_URL.trim() : "";
  const secret = typeof env.NEON_AUTH_COOKIE_SECRET === "string" ? env.NEON_AUTH_COOKIE_SECRET.trim() : "";

  if (!baseUrl || !secret) return null;

  return {
    baseUrl,
    cookies: { secret },
  };
}

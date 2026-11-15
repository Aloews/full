import { createNeonAuth } from "@neon/auth/next/server";
import { getNeonAuthConfig } from "./config.mjs";

export function getAuth() {
  const config = getNeonAuthConfig();
  return config ? createNeonAuth(config) : null;
}

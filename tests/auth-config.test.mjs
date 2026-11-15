import assert from "node:assert/strict";
import test from "node:test";
import { getNeonAuthConfig } from "../lib/auth/config.mjs";

test("does not create an auth config without a base URL", () => {
  assert.equal(
    getNeonAuthConfig({ NEON_AUTH_COOKIE_SECRET: "test-only-not-a-real-credential" }),
    null,
  );
});

test("does not create an auth config without a cookie secret", () => {
  assert.equal(
    getNeonAuthConfig({ NEON_AUTH_BASE_URL: "https://auth.example.test" }),
    null,
  );
});

test("returns the required Neon Auth config when both values are present", () => {
  assert.deepEqual(
    getNeonAuthConfig({
      NEON_AUTH_BASE_URL: "https://auth.example.test",
      NEON_AUTH_COOKIE_SECRET: "test-only-not-a-real-credential",
    }),
    {
      baseUrl: "https://auth.example.test",
      cookies: { secret: "test-only-not-a-real-credential" },
    },
  );
});

test("trims whitespace from environment values", () => {
  assert.deepEqual(
    getNeonAuthConfig({
      NEON_AUTH_BASE_URL: " https://auth.example.test ",
      NEON_AUTH_COOKIE_SECRET: " test-only-not-a-real-credential ",
    }),
    {
      baseUrl: "https://auth.example.test",
      cookies: { secret: "test-only-not-a-real-credential" },
    },
  );
});

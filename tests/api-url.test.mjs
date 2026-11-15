import assert from "node:assert/strict";
import test from "node:test";
import { normalizeApiBase } from "../lib/api-url.mjs";

test("removes one trailing slash from the API base URL", () => {
  assert.equal(normalizeApiBase("https://api.example.test/"), "https://api.example.test");
});

test("removes multiple trailing slashes without changing the path", () => {
  assert.equal(normalizeApiBase("https://api.example.test/v1///"), "https://api.example.test/v1");
});

test("leaves a URL without trailing slashes unchanged", () => {
  assert.equal(normalizeApiBase("https://api.example.test/v1"), "https://api.example.test/v1");
});

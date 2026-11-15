# AUREL Neon Function API (staging)

This directory stores the exact ZIP artifact deployed to the isolated Neon branch aurel-staging-rc1.

- Function slug: aurelapi
- Runtime: Node.js 24
- Branch ID: br-muddy-art-b91lxogu
- Function URL: https://br-muddy-art-b91lxogu-aurelapi.compute.c-7.eu-central-1.aws.neon.tech
- Artifact SHA-256: 15a7abd1e0262fe080557288612b6299a5c0ff3bcbe037cf8538a8967359dae8

The ZIP contains index.mjs, auth.mjs, package.json and six Node built-in regression tests. Extract it before editing. The function uses the branch-injected DATABASE_URL, switches to aurel_app for application queries, verifies EdDSA JWTs against the branch-specific Neon Auth JWKS, and resolves organization roles from neon_auth.member rather than trusting client-supplied roles.

Staging-only safeguards:
- AUREL_ENQUIRY_ENABLED=false. Public enquiry intake is disabled until retention and edge rate-limiting policy are approved.
- No production branch, data, DNS, or deployment was changed.
- The staging branch was created from a snapshot with zero Auth users, organizations, properties and enquiries; only synthetic test identities and an organization were added afterward.

Local verification:
- node --check index.mjs
- node --check auth.mjs
- node --test tests/*.test.mjs (6 passed)

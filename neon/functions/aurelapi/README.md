# AUREL staging API

Neon Function slug: `aurelapi`
Runtime: Node.js 24
Neon branch: `aurel-staging-rc1` (`br-muddy-art-b91lxogu`)
Endpoint: https://br-muddy-art-b91lxogu-aurelapi.compute.c-7.eu-central-1.aws.neon.tech

The deployment package is built from this folder and includes:
- EdDSA JWT verification against the branch-specific Neon Auth JWKS.
- Membership and role lookup from `neon_auth.member`; client-supplied roles are never trusted.
- Tenant-scoped property CRUD, append-only evidence, submission and independent review.
- Public verified-property list/detail endpoints matching the Next.js frontend contract.
- A public enquiry endpoint disabled by default.

Required runtime variables: `NEON_AUTH_BASE_URL`, `NEON_AUTH_JWKS_URL`, `AUREL_ALLOWED_ORIGINS`, `AUREL_ENQUIRY_ENABLED=false`. Neon injects `DATABASE_URL`; the function switches to the least-privilege `aurel_app` role for every application transaction.

Staging safeguards: no production deployment or data migration. Public enquiry intake remains disabled until the owner approves retention and edge abuse-control policy.

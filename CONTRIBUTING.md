# Contributing to AlphaPulse

Thank you for your interest in AlphaPulse.

## Project Status

AlphaPulse is currently at the **specification / pre-MVP stage** (v1.0 Release Candidate documentation package).

The repository contains the full product and engineering specification. Implementation follows the plan in `docs/10_90_DAY_BACKLOG.md`.

---

## How to Contribute

1. Open an issue describing the problem or proposal.
2. Discuss the change before implementing it.
3. Submit a pull request referencing the issue.

---

## Documentation Guidelines

- All documents live in `docs/` and follow the numbered naming convention (`01_...` – `16_...`).
- Write in plain English. No hype, no unverifiable claims.
- Every architectural change must be consistent with:
  - `docs/03_SYSTEM_ARCHITECTURE.md`
  - `docs/04_DATABASE_DESIGN.md`
  - the Engineering Standards (Amendment A)
- Significant decisions are recorded in `docs/DECISIONS.md`, `docs/ARCHITECTURE_DECISIONS.md`, or a new ADR in `docs/adr/`.

---

## Engineering Standards (Summary)

- All timestamps in UTC (`TIMESTAMPTZ`).
- UUIDv7 primary keys.
- `snake_case` naming for tables and fields.
- Unified API response format (`success` / `data` / `error`).
- Unified enums: `HIGH / MEDIUM / LOW`, `HIGH_CONFIDENCE / WORTH_WATCHING / EARLY_SIGNAL`, `ACTIVE / INACTIVE / ARCHIVED`.

See Amendment A in `docs/03_SYSTEM_ARCHITECTURE.md` for the full standard.

---

## Commit Messages

- Use clear, descriptive messages in imperative form.
- Reference related documents or issues where relevant.

---

## Code of Conduct

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

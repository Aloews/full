# Test governance

> **CRITICAL REQUIREMENT**
>
> The system must not only test the implementation.
>
> The system MUST test whether its own test suite is capable of detecting
> controlled implementation failures.
>
> A green test suite is invalid if the suite cannot detect known mutations.
>
> Therefore:
>
> 1. Every critical SEO rule requires positive and negative tests.
> 2. Every critical module requires mutation testing.
> 3. Meta-tests must validate test discovery, assertions, fixtures and negative coverage.
> 4. A controlled broken fixture must be detected.
> 5. CI must FAIL if the test suite itself becomes ineffective.
> 6. No skipped critical tests without an explicit reason.
> 7. No tests that pass without meaningful assertions.
> 8. No hardcoded fake external data.
> 9. No fake Yandex AI visibility.
> 10. All external facts must have source + retrieval date + confidence.

This document describes how each of those is enforced.

## Level 1 — the ordinary suite

| Directory | What lives there |
|-----------|------------------|
| `tests/unit` | isolated logic: provenance, decisions, URLs, claims, statistics, scoring |
| `tests/integration` | ingest, storage, workspace, experiments, CLI |
| `tests/api` | every FastAPI route |
| `tests/e2e` | exports → engines → decisions → report → SQLite in one pass |
| `tests/security` | dashboard escaping, secret redaction, input bounds, link-tool scope |
| `tests/seo`, `tests/aeo`, `tests/geo` | the engine rules, by marker |
| `tests/regression` | contracts that must not drift silently |

Markers are the contract between a test and the governance layer:

```python
@pytest.mark.rule("FACET-004")   # links the test to a rule in kontur.core.registry
@pytest.mark.positive            # the rule must fire on this input
@pytest.mark.negative            # the rule must NOT fire, or must raise
@pytest.mark.regression          # locks in behaviour
@pytest.mark.boundary            # exercises a scoring function's edges
@pytest.mark.scoring("demand_score")
@pytest.mark.endpoint("/api/indexation/decide")
```

The rule registry (`kontur/core/registry.py`) is the single source of truth: 43 rules,
28 of them critical, 13 requiring a regression test, plus 8 bounded scoring functions.
A typo in a rule marker fails a meta-test rather than silently covering nothing.

## Level 2 — meta-tests

`tests/meta/test_meta_suite.py`. Each reads a static inventory of the suite
(`kontur/testing/inventory.py`, built with `ast`) so the checks cannot be fooled by
the suite importing itself.

| Id | Check |
|----|-------|
| MT-001 | every test is discovered by pytest (compared against a real `--collect-only` run) |
| MT-002 | every critical rule has at least one positive test |
| MT-003 | every critical rule has at least one negative test |
| MT-004 | every test contains an assertion (`assert`, `pytest.raises`, or an `assert_*` helper) |
| MT-005 | no test passes regardless of the result (no tautology-only tests) |
| MT-006 | no skipped test without a reason of at least ten characters |
| MT-007 | every requested fixture exists |
| MT-008 | every API route has a test marked with that route |
| MT-009 | every critical SEO rule has a regression test |
| MT-010 | every scoring function has boundary tests |

Plus: every rule id used by a test exists in the registry, every registered rule is
referenced by at least one test, and no test claims to be both positive and negative.

## Level 3 — mutation testing

`tools/mutation/` contains a small AST mutation engine: flipped comparisons, shifted
boundaries, swapped boolean operators, perturbed constants and flipped boolean
literals. Each mutant is applied to a copy of the project, the target module's tests
are run, and a mutant that survives is a hole in the tests.

```bash
python -m tools.mutation.runner --json reports/mutation.json
python -m tools.mutation.runner --module kontur/engines/faceted/rules.py -n 8 -v
```

Thresholds:

* core SEO engine (faceted rules, GET-parameter classifier/controller/models) — **95 %**
* other critical modules (provenance, decisions, Alice metrics and snapshots,
  experiment decisions, faceted signals) — **90 %**

Two engine details matter for the numbers to mean anything:

* **Bytecode caching is disabled in the sandbox.** Consecutive mutants of the same
  byte size written within the same second share an mtime, and CPython would reuse
  the previous mutant's `.pyc`. Without `-B` the score is measured against the wrong
  code.
* **Nodes are matched with positions.** Locating a mutation target by `ast.dump`
  alone matches any identical expression elsewhere in the file, so the mutation lands
  on the wrong line and the report lies about what was tested.

Mutations inside decorators and dataclass-machinery keywords (`init`, `slots`,
`frozen`, …) are not generated: they change the generated constructor, not the
algorithm. Immutability is covered by explicit tests instead.

### Equivalent mutants

Four mutations cannot be distinguished by any deterministic test. They are listed in
`tools/mutation/config.py` with a written justification, excluded from the score, and
**printed in every report** so an allowlist entry stays reviewable rather than
quietly inflating the number.

## T-META-001 — is this suite capable of failing?

```
BROKEN IMPLEMENTATION            BROKEN IMPLEMENTATION
        ↓                                ↓
EXPECTED TEST FAILURE            ALL TESTS PASS
        ↓                                ↓
    trustworthy              FAILED — TEST SUITE IS NOT TRUSTWORTHY
```

`tools/mutation/sentinel.py` introduces one controlled, documented break into a real
module — conflicting GET-parameter policies resolving to the *least* restrictive
variant, inverting rule GETP-002 — and requires the corresponding tests to fail. If
they pass, the check reports `FAILED — TEST SUITE IS NOT TRUSTWORTHY` and CI blocks.

The check also fails if the anchor it breaks has disappeared from the source, so a
refactor cannot silently turn the sentinel into a no-op.

## The Test Sentinel

`tests/meta/test_sentinel.py` holds the floors the suite may never fall below:

```python
assert test_count            >= EXPECTED_MINIMUM
assert critical_test_count   >= EXPECTED_CRITICAL
assert negative_test_count   >= EXPECTED_NEGATIVE
assert meta_test_count       >= EXPECTED_META
assert mutation_score        >= THRESHOLD
assert intentionally_broken_fixture_is_detected
```

Floors are a ratchet against erosion, not a target: raise them as the suite grows.

## CI

```
PUSH → Lint → Type Check → Unit → Integration → SEO → AEO → GEO → Security
     → Regression → API → E2E → META TESTS → Suite integrity → Mutation
     → Coverage → Build → Docker test → FINAL QUALITY GATE → PASS / BLOCK
```

Each stage records its own verdict, so the gate reports the whole picture instead of
stopping at the first red stage.

## The quality gate

`python -m tools.quality_gate --reports reports` blocks the merge when any of these
fails:

* any stage status is not `PASS`
* the mutation score is below its threshold, overall or for any single module
* T-META-001 did not detect its controlled break
* core coverage < 90 % or total coverage < 80 %
* a required report is missing — an absent artefact blocks, it never passes silently

The gate has its own tests (`tests/meta/test_quality_gate.py`), including the case
where every report is missing.

# Kontur

A Yandex-first SEO / AEO / GEO platform built around one idea: **every number has a
source and every decision has a reason.**

Four engines feed one another, and a test-governance layer runs across all of them.

```
┌─────────────────────────────────────┐
│         YANDEX SEO ENGINE           │   Technical SEO · Faceted navigation
│                                     │   Indexation · Semantic core · SERP
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│             AEO ENGINE              │   Answer-first · Questions · Tables
│                                     │   FAQ · Extraction readiness
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│             GEO ENGINE              │   Alice AI visibility · SoV · Citations
│                                     │   Entities · Evidence · Competitors
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│        EXPERIMENT ENGINE            │   Baseline · Control · Variant
│                                     │   Measurement · Statistics · Decision
└────────────────┬────────────────────┘
                 ▼
           BUSINESS RESULT

        ═══ TEST GOVERNANCE ═══  (vertical, across all four)
```

## What it does

### Indexation → GET Parameters

Yandex Webmaster lets a site declare which GET parameters are taken into account
when indexing and which are ignored. Kontur decides that per parameter, from crawl
evidence and measured demand, and says why:

| Parameter    | Detected URLs | Decision           | Reason                                     |
|--------------|--------------:|--------------------|--------------------------------------------|
| `utm_source` |        48 210 | EXCLUDE            | tracking                                   |
| `utm_medium` |        47 980 | EXCLUDE            | tracking                                   |
| `gclid`      |        21 300 | EXCLUDE            | tracking                                   |
| `sort`       |        12 440 | EXCLUDE            | duplicate intent                           |
| `page`       |         9 100 | CONTEXT_DEPENDENT  | pagination                                 |
| `provider`   |         4 812 | SEO HUB            | possible seo facet, search demand          |
| `mechanic`   |         1 290 | SEO HUB            | possible seo facet, search demand          |
| `rtp`        |           840 | ANALYZE            | possible seo facet, low url volume         |
| `phpsessid`  |           380 | BLOCK              | session identifier, unbounded value space  |

Conflicting policies resolve to the more prohibitive variant, and every losing
rationale stays visible in the audit trail. The controller exports a Webmaster
payload and `Clean-param` / `Disallow` directives for robots.txt.

### Faceted navigation as a decision engine

```
QUERY → FILTER STATE → SEARCH DEMAND → INTENT → SERP/COMPETITOR EVIDENCE
      → CONTENT UNIQUENESS → BUSINESS VALUE → INDEXATION DECISION
```

Twelve ordered rules produce one explainable verdict per URL:

```json
{
  "url": "/slots/megaways/",
  "decision": "INDEX",
  "reason": ["search_demand", "unique_intent", "unique_content", "commercial_value"],
  "rules": ["FACET-007"],
  "confidence": "medium",
  "is_sample": false,
  "evidence": [{"source": "wordstat:export", "retrieved_at": "…", "confidence": "medium"}]
}
```

`INDEX` · `CANONICAL` · `NOINDEX` · `BLOCK` · `REDIRECT` — and a decision with no
reason codes raises rather than shipping.

### AI visibility (Yandex Alice)

Imported from the Webmaster export, never invented. There is no "GEO score" in this
codebase — a regression test enforces its absence:

```
AI Visibility
├── Share of Voice          ├── Query coverage
├── Mention rate            ├── Competitor overlap
├── Cited URLs              └── Winning / lost queries
```

Answers vary between captures, so snapshots are stored weekly and a change is only
reportable once it survives repeated measurement. Volatile queries are flagged as
such instead of being read as movement.

### Query → AI answer → URL graph

```
QUERY → YANDEX SERP → ALICE AI ANSWER → MENTIONS → COMPETITOR SOURCES → OUR URL
```

Each edge is one dated observation: `query`, `date`, `serp_position`,
`ai_answer_present`, `our_domain_mentioned`, `our_url_cited`, `competitor_domains`,
`answer_type`.

### Experiments, not folklore

AEO and GEO guidelines ship as **hypotheses** (`H-001` … `H-005`), not rules. The
answer-length buckets 20–40 / 40–60 / 60–100 are experiment arms; the platform will
not state an effect without a linked experiment, and a repository-wide regression
test fails the build if any module or document starts promising one.

### Also included

* **SERP evidence layer** — competitor matrix, content/entity/question gaps, information gain.
* **Backlink risk analyser** — footprint, anchor concentration, velocity → LOW / MEDIUM / HIGH.
  It classifies; it does not build networks, and a security test keeps it that way.
* **Behavioural funnel** — SERP CTR → landing → filter → game → conversion, reported as
  correlation with a permanent non-causal label.
* **iGaming taxonomy** — categories, games, providers, mechanics, features, bonuses, RTP,
  volatility, jackpots, reviews, comparisons, commercial and informational pages.

## Quick start

```bash
pip install -r requirements-dev.txt

make demo             # the GET-parameter table for the bundled sample workspace
make serve            # dashboard + JSON API on http://127.0.0.1:8000
python -m kontur.cli decide '/slots/?mechanic=megaways' '/slots/?rtp=96plus'
```

The bundled workspace is **sample data**. Its provenance starts with `sample:`, the
mark propagates into every derived report, the dashboard shows a warning banner, and
`ai_visibility(require_real_data=True)` refuses to serve it at all.

Real data enters through `kontur.ingest`, which requires an export manifest:

```json
{"source": "yandex_webmaster:alice_visibility", "retrieved_at": "2026-08-24", "confidence": "high"}
```

## Test governance

```
make test         # 570 tests
make mutation     # mutation campaign over the ten critical modules
make sentinel     # T-META-001 — can this suite detect a controlled break?
make gate         # the final quality gate
```

| Level | What it checks | Where |
|-------|----------------|-------|
| 1 | unit · integration · api · e2e · security · seo · aeo · geo · regression | `tests/` |
| 2 | MT-001 … MT-010 — the tests about the tests | `tests/meta/test_meta_suite.py` |
| 3 | mutation testing, T-META-001, the Test Sentinel | `tools/mutation/`, `tests/meta/` |

Current state: **570 tests**, mutation score **100 %** across ten critical modules
(4 documented equivalent mutants excluded and printed), core coverage **92.9 %**.

See [docs/TEST-GOVERNANCE.md](docs/TEST-GOVERNANCE.md) for the full contract, and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the engines fit together.

## Sources

Claims about external tools and their behaviour live in
[docs/SOURCES.md](docs/SOURCES.md) with a source, a retrieval date and a confidence
level — the same standard the code applies to data.

## Licence

MIT. See [LICENSE](LICENSE).

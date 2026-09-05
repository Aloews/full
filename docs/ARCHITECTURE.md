# Architecture

## The spine: provenance

`kontur/core/provenance.py` is the module everything else leans on.

```python
Provenance(source="yandex_webmaster:alice_visibility",
           retrieved_at=datetime(...),
           confidence=Confidence.HIGH)

Sourced(value=0.12, provenance=...)     # a number that cannot be separated from its origin
EvidenceSet.of(...)                     # never more confident than its weakest fact
```

A `Provenance` refuses to exist without a source, a retrieval date and a confidence.
Sample data is allowed — development needs fixtures — but its source starts with
`sample:`, `is_sample` propagates through every aggregation, the dashboard renders a
banner, and any code path that promises a real measurement raises `SampleDataError`.

## The rule registry

`kontur/core/registry.py` declares 43 rules with an id, a kind, a criticality and the
module that implements them. Engines reference ids through `rule_ids("FACET-007")`,
which validates at call time, so a rule can never fire under an id nobody can test.
The registry also declares the 8 bounded scoring functions that need boundary tests.

## Engines

| Module | Responsibility |
|--------|----------------|
| `engines/getparams` | catalogue → classifier → controller → export. Decides each GET parameter and resolves conflicting policies upwards. |
| `engines/faceted` | models, signals, context, rules, pipeline. The eight-stage indexation decision. |
| `engines/serp` | SERP capture model, consensus summary, content/entity/question gaps, information gain. |
| `engines/aeo` | dependency-free HTML content model, answer-first assessment, extraction readiness, answer-length buckets. |
| `engines/geo` | Alice AI visibility import, metrics, weekly snapshots and volatility. |
| `engines/experiment` | design (arms, guardrails, deterministic assignment), statistics, verdicts. |
| `engines/backlinks` | risk factors → LOW / MEDIUM / HIGH. Classification only. |
| `engines/behavior` | funnel aggregation and rank correlation, permanently labelled non-causal. |
| `engines/igaming` | page-type taxonomy and completeness checks for the vertical. |

`graph/query_graph.py` joins queries, dated Alice answers, competitor sources and our
URLs into one temporal graph.

## Data flow

```
exports (CSV + manifest)
        │  kontur/ingest — provenance is mandatory, identifiers are bounded
        ▼
   Workspace ──► GetParameterController ──► parameter rulings ──► Webmaster export
        │                                                     └─► robots.txt block
        ├──────► FacetedIndexationEngine ──► DecisionRecord per URL
        ├──────► SnapshotStore ──► AiVisibilityReport
        ├──────► QueryAnswerGraph
        └──────► ExperimentRegistry ──► ExperimentVerdict ──► EffectClaim
                                                              (only with an experiment)
        │
        ├──► kontur/storage/sqlite.py   provenance columns in every table
        ├──► kontur/api                 HTML dashboard + JSON API
        └──► kontur/cli                 the same data on a terminal
```

## Why the pipeline is a chain of small rules

Each faceted rule is a pure function over a `FacetContext` returning a
`DecisionRecord` or `None`, and `RULE_CHAIN` fixes their order. That shape buys three
things: the audit trail names exactly which rule stopped a URL, each rule is cheap to
test from both sides, and the mutation engine can prove the tests notice when one of
them is broken.

## Design rules that are enforced, not just documented

| Rule | Enforced by |
|------|-------------|
| No un-sourced external fact | `MissingProvenanceError` at every importer and engine boundary |
| No sample data presented as a measurement | `is_sample` propagation + `require_real_data` |
| No invented AI-visibility score | a regression test scanning for `geo_score` and friends |
| No effect claim without an experiment | `EffectClaim` requires an experiment id; a repository-wide scan for promissory language |
| No link-building automation | a security test parsing the module for builder-shaped functions and network imports |
| No unexplained decision | `DecisionRecord` and `ParamRuling` raise when constructed without reasons |

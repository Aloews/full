# Sources

Kontur requires a source, a retrieval date and a confidence level for every external
fact that enters the system. This document applies the same standard to the claims
the product itself is built on.

Nothing here was verified against a live Yandex property during development. The
entries below record where each claim came from and how far it should be trusted, so
that anyone extending the platform knows which assumptions to check first.

| # | Claim | Source | Recorded | Confidence | Notes |
|---|-------|--------|----------|-----------|-------|
| 1 | Yandex Webmaster offers a dedicated setting for GET parameters, letting a site declare which parameters are taken into account when indexing and which are ignored, in order to reduce duplicates, cut crawl load and speed up indexing. | Product brief supplied by the project owner | 2026-09-05 | Medium — reported, not independently verified | Shapes the whole `engines/getparams` output format. **Verify against the current Webmaster documentation before applying an export to a live site.** |
| 2 | Conflicting directives resolve to the more prohibitive variant. | Product brief supplied by the project owner | 2026-09-05 | Medium — reported, not independently verified | Implemented as an explicit restrictiveness lattice (`PARAM_RESTRICTIVENESS`), which is a safe default regardless of the engine's exact behaviour. |
| 3 | Yandex Webmaster reports "site visibility in Alice AI": Share of Voice, queries, pages, competitors and sources, refreshed weekly over a three-month window. | Product brief supplied by the project owner | 2026-09-05 | Medium — reported, not independently verified | Determines the import schema in `engines/geo`. The importer is column-driven, so a different export layout is a mapping change, not a redesign. |
| 4 | Alice AI may return a different answer and a different set of sources for the same query at different moments. | Product brief supplied by the project owner | 2026-09-05 | Medium — reported, and consistent with how generative answer surfaces behave generally | The reason snapshots are weekly and `assess_trend` refuses to report a change from a single observation. |
| 5 | Duplicate URLs compete with each other and slow indexation. | Long-standing, widely documented search-engine behaviour | 2026-09-05 | High | The premise behind the faceted decision engine. |
| 6 | The GEO literature (2023–2026) is heterogeneous; no stable, universal causal effect of optimisation techniques on organic discoverability or downstream behaviour has been established. Repeated measurement, controls and human verification are what the evidence supports. | Survey of the GEO literature, as summarised in the product brief | 2026-09-05 | Medium — summarised, primary sources not read here | The reason AEO/GEO guidelines ship as hypotheses and the platform will not state an effect without a linked experiment. |
| 7 | Yandex-focused iGaming SEO roles combine technical SEO, on-page and off-page work, behavioural metrics, competitor analysis, rank and traffic monitoring, link building and team management. | Job postings cited in the product brief | 2026-09-05 | Low — anecdotal, a small sample of postings | Motivates the scope of the iGaming module. It is a description of a market, not a claim about the search engine. |

## How to raise a confidence level

1. Read the primary source (Yandex documentation, or the paper itself).
2. Update the row: source URL, the date you retrieved it, the new confidence.
3. If the claim turns out to be wrong, fix the code it justifies in the same change —
   the table exists so that a wrong assumption is traceable to the modules built on it.

## Data provenance at runtime

The same three fields are mandatory for every row that enters the system:

```json
{
  "source": "yandex_webmaster:alice_visibility",
  "retrieved_at": "2026-08-24",
  "confidence": "high",
  "source_url": "https://webmaster.yandex.ru/"
}
```

An import without them is refused (`MissingProvenanceError`). Fixtures may use a
`sample:` source; the mark then travels with every derived figure, and any request for
a real measurement over sample data raises `SampleDataError`.

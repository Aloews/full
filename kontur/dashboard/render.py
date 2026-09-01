"""Server-rendered dashboard.

Every value that reaches the page is escaped (rule SEC-001): parameter names,
query strings and URLs all come from crawls and exports, which means they are
attacker-influenced input, not trusted content.
"""

from __future__ import annotations

from html import escape
from typing import Any, Iterable, Mapping, Sequence

_STYLE = """
:root{--bg:#0f1115;--panel:#171a21;--line:#262b36;--text:#e6e8ee;--muted:#98a1b3;
--index:#3fb950;--canonical:#58a6ff;--noindex:#d29922;--block:#f85149;--analyze:#a371f7;--hub:#3fb950}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{padding:20px 28px;border-bottom:1px solid var(--line);display:flex;
align-items:baseline;gap:18px;flex-wrap:wrap}
h1{font-size:17px;margin:0;letter-spacing:.02em}
nav a{color:var(--muted);text-decoration:none;margin-right:16px;font-size:13px}
nav a:hover,nav a.active{color:var(--text)}
main{padding:24px 28px;max-width:1180px}
h2{font-size:15px;margin:28px 0 12px;font-weight:600}
h2:first-child{margin-top:0}
.warn{background:#3d2a05;border:1px solid #7d5b09;color:#f0c674;padding:10px 14px;
border-radius:6px;margin-bottom:18px;font-size:13px}
table{width:100%;border-collapse:collapse;background:var(--panel);border-radius:8px;overflow:hidden}
th,td{padding:9px 14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:1px 8px;border-radius:11px;font-size:12px;font-weight:600;
border:1px solid currentColor}
.EXCLUDE,.NOINDEX{color:var(--noindex)}
.BLOCK{color:var(--block)}
.ANALYZE{color:var(--analyze)}
.SEOHUB,.INDEX{color:var(--hub)}
.CONTEXT_DEPENDENT,.CANONICAL,.REDIRECT{color:var(--canonical)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.card .k{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.card .v{font-size:22px;margin-top:4px;font-variant-numeric:tabular-nums}
.muted{color:var(--muted)}
.small{font-size:12px}
code{background:#0b0d11;padding:1px 5px;border-radius:4px;font-size:12px}
footer{padding:18px 28px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}
"""

NAV = (
    ("/", "Overview"),
    ("/indexation/parameters", "Indexation → GET Parameters"),
    ("/indexation/decisions", "Indexation → Decisions"),
    ("/ai-visibility", "AI Visibility"),
)

SAMPLE_WARNING = (
    "SAMPLE DATA — these panels are backed by generated fixtures, not by a Yandex "
    "Webmaster export. Nothing here is a measurement."
)


def _tag(value: str) -> str:
    css = escape(str(value).replace(" ", "").replace("-", "_"))
    return f'<span class="tag {css}">{escape(str(value))}</span>'


def _cell(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:,.4g}"
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    if value is None:
        return "—"
    return escape(str(value))


def table(columns: Sequence[tuple[str, str]], rows: Iterable[Mapping[str, Any]], *, tag_column: str | None = None) -> str:
    head = "".join(f"<th>{escape(label)}</th>" for _, label in columns)
    body: list[str] = []
    for row in rows:
        cells: list[str] = []
        for key, _ in columns:
            value = row.get(key)
            if key == tag_column:
                cells.append(f"<td>{_tag(value)}</td>")
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<td class="num">{_cell(value)}</td>')
            else:
                cells.append(f"<td>{_cell(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    if not body:
        body.append(f'<tr><td colspan="{len(columns)}" class="muted">no data</td></tr>')
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def cards(items: Sequence[tuple[str, Any]]) -> str:
    blocks = "".join(
        f'<div class="card"><div class="k">{escape(k)}</div><div class="v">{_cell(v)}</div></div>'
        for k, v in items
    )
    return f'<div class="cards">{blocks}</div>'


def page(title: str, body: str, *, active: str = "/", sample: bool = False) -> str:
    def nav_link(href: str, label: str) -> str:
        css = ' class="active"' if href == active else ""
        return f'<a href="{escape(href)}"{css}>{escape(label)}</a>'

    nav = "".join(nav_link(href, label) for href, label in NAV)
    warning = f'<div class="warn">{escape(SAMPLE_WARNING)}</div>' if sample else ""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{escape(title)} · Kontur</title><style>{_STYLE}</style></head><body>"
        f"<header><h1>KONTUR</h1><nav>{nav}</nav></header>"
        f"<main>{warning}{body}</main>"
        "<footer>Kontur — Yandex-first SEO / AEO / GEO platform. "
        "Every figure carries a source, a retrieval date and a confidence level.</footer>"
        "</body></html>"
    )


# --------------------------------------------------------------------- pages
def render_overview(overview: Mapping[str, Any], *, sample: bool = False) -> str:
    parameters = overview.get("parameters", {})
    body = (
        f"<h2>Site: {escape(str(overview.get('site', '')))}</h2>"
        + cards(
            [
                ("GET parameters", parameters.get("parameters", 0)),
                ("URLs affected", parameters.get("detected_urls", 0)),
                ("Pending review", len(parameters.get("pending_review", []))),
                ("Alice weeks", overview.get("alice_weeks", 0)),
                ("Filter states", overview.get("filter_states", 0)),
                ("Experiments", overview.get("experiments", 0)),
            ]
        )
        + "<h2>Parameter decisions</h2>"
        + table(
            [("decision", "Decision"), ("count", "Parameters")],
            [{"decision": k, "count": v} for k, v in sorted(parameters.get("by_decision", {}).items())],
            tag_column="decision",
        )
    )
    return page("Overview", body, active="/", sample=sample)


def render_parameters(rows: Sequence[Mapping[str, Any]], *, sample: bool = False) -> str:
    body = (
        "<h2>Indexation → GET Parameters</h2>"
        '<p class="muted small">Declare which parameters Yandex should take into account when '
        "indexing and which it should ignore. Conflicting rules resolve to the more "
        "prohibitive variant.</p>"
        + table(
            [
                ("parameter", "Parameter"),
                ("detected_urls", "Detected URLs"),
                ("decision", "Decision"),
                ("reason", "Reason"),
                ("confidence", "Confidence"),
            ],
            rows,
            tag_column="decision",
        )
    )
    return page("GET Parameters", body, active="/indexation/parameters", sample=sample)


def render_decisions(decisions: Sequence[Mapping[str, Any]], *, sample: bool = False) -> str:
    rows = [
        {
            "url": d.get("url"),
            "decision": d.get("decision"),
            "reason": ", ".join(d.get("reason", [])),
            "rules": ", ".join(d.get("rules", [])),
            "target": d.get("canonical_target") or d.get("redirect_target") or "",
            "confidence": d.get("confidence"),
        }
        for d in decisions
    ]
    body = (
        "<h2>Indexation → Decisions</h2>"
        '<p class="muted small">QUERY → FILTER STATE → SEARCH DEMAND → INTENT → SERP EVIDENCE → '
        "CONTENT UNIQUENESS → BUSINESS VALUE → INDEXATION DECISION</p>"
        + table(
            [
                ("url", "URL"),
                ("decision", "Decision"),
                ("reason", "Reason"),
                ("rules", "Rules"),
                ("target", "Target"),
                ("confidence", "Confidence"),
            ],
            rows,
            tag_column="decision",
        )
    )
    return page("Decisions", body, active="/indexation/decisions", sample=sample)


def render_ai_visibility(report: Mapping[str, Any], volatility: Sequence[Mapping[str, Any]] = ()) -> str:
    window = report.get("window", {})
    body = (
        "<h2>AI Visibility — Yandex Alice</h2>"
        + cards(
            [
                ("Share of Voice", report.get("share_of_voice")),
                ("Reported SoV", report.get("reported_share_of_voice")),
                ("Mention rate", report.get("mention_rate")),
                ("Query coverage", report.get("query_coverage")),
                ("Queries analysed", report.get("queries_analysed")),
                ("Confidence", report.get("confidence")),
            ]
        )
        + f'<p class="muted small">Window {escape(str(window.get("start", "")))} → '
        f'{escape(str(window.get("end", "")))}. Weekly snapshots; Alice may return a different '
        "answer and a different source set for the same query at different moments.</p>"
        "<h2>Cited URLs</h2>"
        + table([("url", "URL"), ("citations", "Citations")], report.get("cited_urls", []))
        + "<h2>Competitors</h2>"
        + table(
            [
                ("domain", "Domain"),
                ("queries", "Queries"),
                ("share", "Share"),
                ("co_cited_with_us", "Co-cited with us"),
                ("overlap", "Overlap"),
            ],
            report.get("competitors", []),
        )
        + "<h2>Winning / lost queries (last two snapshots)</h2>"
        + table(
            [("query", "Query"), ("change", "Change")],
            [{"query": q, "change": "won"} for q in report.get("winning_queries", [])]
            + [{"query": q, "change": "lost"} for q in report.get("lost_queries", [])],
        )
        + "<h2>Answer volatility</h2>"
        '<p class="muted small">Queries whose cited-source set churns between snapshots. A single '
        "capture of these is not evidence of anything.</p>"
        + table(
            [("query", "Query"), ("observations", "Observations"), ("volatility", "Volatility")],
            volatility,
        )
    )
    return page("AI Visibility", body, active="/ai-visibility", sample=bool(report.get("is_sample")))

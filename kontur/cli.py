"""Command line interface: ``kontur <command>``."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence

from kontur.core.errors import KonturError
from kontur.workspace import Workspace, demo_workspace


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _workspace(args: argparse.Namespace) -> Workspace:
    # Only the demo workspace ships in the box; real workspaces are assembled by
    # the ingest layer, which requires an export manifest with provenance.
    return demo_workspace()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kontur", description="Yandex-first SEO / AEO / GEO platform")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("overview", help="workspace summary")
    sub.add_parser("params", help="GET parameter rulings")
    sub.add_parser("export", help="Yandex Webmaster GET-parameter export")
    sub.add_parser("robots", help="robots.txt block for the parameter policy")
    sub.add_parser("ai-visibility", help="Alice AI visibility report")
    sub.add_parser("rules", help="the rule registry")

    decide = sub.add_parser("decide", help="indexation decision for URLs")
    decide.add_argument("urls", nargs="+")

    args = parser.parse_args(argv)
    workspace = _workspace(args)

    try:
        if args.command == "overview":
            _print(workspace.overview())
        elif args.command == "params":
            _print(workspace.parameter_rows())
        elif args.command == "export":
            _print(workspace.parameter_export())
        elif args.command == "robots":
            print(workspace.robots_txt())
        elif args.command == "ai-visibility":
            _print(workspace.ai_visibility().to_dict())
        elif args.command == "decide":
            _print(workspace.decide(args.urls))
        elif args.command == "rules":
            from kontur.core.registry import RULES

            _print(
                [
                    {"id": r.id, "kind": r.kind.value, "criticality": r.criticality.value, "title": r.title}
                    for r in RULES.values()
                ]
            )
    except KonturError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Development server entry point: ``python -m kontur.api.serve``."""

from __future__ import annotations

import uvicorn

from kontur.api.app import create_app


def main() -> None:  # pragma: no cover - thin wrapper around uvicorn
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":  # pragma: no cover
    main()

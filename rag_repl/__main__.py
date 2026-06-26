from __future__ import annotations

import argparse

from rag_repl.config import build_backend, resolve_api_url
from rag_repl.repl import Repl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Interactive client for a RAG service")
    parser.add_argument(
        "--api-url",
        help="RAG API base URL; defaults to RAG_API_URL or the local stub backend",
    )
    arguments = parser.parse_args(argv)
    api_url = resolve_api_url(arguments.api_url)
    Repl(build_backend(api_url), api_url=api_url).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

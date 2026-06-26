from __future__ import annotations

import os
from collections.abc import Mapping

from rag_repl.facade import RagBackend
from rag_repl.http_backend import HttpRagBackend
from rag_repl.stub_backend import StubRagBackend


def resolve_api_url(
    cli_api_url: str | None, environment: Mapping[str, str] | None = None
) -> str | None:
    if cli_api_url:
        return cli_api_url
    values = environment if environment is not None else os.environ
    return values.get("RAG_API_URL") or None


def build_backend(api_url: str | None) -> RagBackend:
    if api_url:
        return HttpRagBackend(api_url)
    return StubRagBackend()

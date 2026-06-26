from __future__ import annotations

import json
from typing import TextIO

from rag_repl.facade import AskResponse, Chunk, SearchResponse, StatsResponse


_HEADING_STYLES = {
    "MODEL": "\033[1;36m",
    "ANSWER": "\033[1;33m",
    "SOURCES": "\033[1;32m",
}
_RESET = "\033[0m"


def render_search(response: SearchResponse, output: TextIO) -> None:
    print(f"{response.total} result(s)", file=output)
    for index, chunk in enumerate(response.results, start=1):
        _render_chunk(index, chunk, output)


def render_ask(response: AskResponse, output: TextIO) -> None:
    _render_heading("MODEL", output)
    print(response.model_used, file=output)
    print(file=output)
    _render_heading("ANSWER", output)
    print(response.answer, file=output)
    if response.sources:
        print(file=output)
        _render_heading("SOURCES", output)
        for index, chunk in enumerate(response.sources, start=1):
            _render_chunk(index, chunk, output)


def render_stats(response: StatsResponse, output: TextIO) -> None:
    print(json.dumps(dict(response.values), indent=2, sort_keys=True, ensure_ascii=False), file=output)


def _render_chunk(index: int, chunk: Chunk, output: TextIO) -> None:
    print(
        f"[{index}] {chunk.name} ({chunk.file_path}:{chunk.line_start}-{chunk.line_end}) "
        f"score={chunk.score:.3f}",
        file=output,
    )
    print(f"    {chunk.content}", file=output)


def _render_heading(label: str, output: TextIO) -> None:
    if getattr(output, "isatty", lambda: False)():
        print(f"{_HEADING_STYLES[label]}{label}{_RESET}", file=output)
    else:
        print(label, file=output)

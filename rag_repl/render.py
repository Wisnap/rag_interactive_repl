from __future__ import annotations

import json
from typing import TextIO

from rag_repl.facade import AskResponse, Chunk, SearchResponse, StatsResponse


def render_search(response: SearchResponse, output: TextIO) -> None:
    print(f"{response.total} result(s)", file=output)
    for index, chunk in enumerate(response.results, start=1):
        _render_chunk(index, chunk, output)


def render_ask(response: AskResponse, output: TextIO) -> None:
    print(response.answer, file=output)
    print(f"Model: {response.model_used}", file=output)
    if response.sources:
        print("Sources:", file=output)
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

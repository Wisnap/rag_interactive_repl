from __future__ import annotations

from typing import Any

from rag_repl.facade import AskResponse, Chunk, Filters, SearchResponse, StatsResponse


class StubRagBackend:
    """Local deterministic backend for development and tests."""

    def search(
        self,
        *,
        query: str,
        limit: int,
        filters: Filters,
        search_mode: str,
        client_name: str,
    ) -> SearchResponse:
        results = [
            self._chunk(index, query, search_mode, filters)
            for index in range(1, limit + 1)
        ]
        return SearchResponse(results=results, total=len(results))

    def ask(
        self,
        *,
        question: str,
        mode: str,
        limit: int,
        filters: Filters,
        client_name: str,
    ) -> AskResponse:
        sources = [self._chunk(index, question, mode, filters) for index in range(1, limit + 1)]
        return AskResponse(
            answer=f"Stub answer in {mode} mode for: {question}",
            sources=sources,
            query=question,
            model_used="stub-model",
        )

    def stats(self, *, client_name: str) -> StatsResponse:
        return StatsResponse(
            values={"backend": "stub", "client_name": client_name, "collections": 1}
        )

    @staticmethod
    def _chunk(
        index: int, query: str, mode: str, filters: Filters
    ) -> Chunk:
        return Chunk(
            chunk_id=f"stub-{index}",
            file_path=f"examples/result_{index}.py",
            line_start=index * 10,
            line_end=index * 10 + 4,
            chunk_type="code",
            name=f"result_{index}",
            content=f"Stub result {index} for '{query}' ({mode}, filters={dict(filters)})",
            score=round(1.0 - index * 0.05, 2),
        )

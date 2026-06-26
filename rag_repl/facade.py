from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


Filters = Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    file_path: str
    line_start: int
    line_end: int
    chunk_type: str
    name: str
    content: str
    score: float


@dataclass(frozen=True)
class SearchResponse:
    results: list[Chunk]
    total: int


@dataclass(frozen=True)
class AskResponse:
    answer: str
    sources: list[Chunk]
    query: str
    model_used: str


@dataclass(frozen=True)
class StatsResponse:
    values: Mapping[str, Any]


class RagBackend(Protocol):
    def search(
        self,
        *,
        query: str,
        limit: int,
        filters: Filters,
        search_mode: str,
        client_name: str,
    ) -> SearchResponse: ...

    def ask(
        self,
        *,
        question: str,
        mode: str,
        limit: int,
        filters: Filters,
        client_name: str,
    ) -> AskResponse: ...

    def stats(self, *, client_name: str) -> StatsResponse: ...

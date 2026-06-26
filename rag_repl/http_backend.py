from __future__ import annotations

import json
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rag_repl.facade import AskResponse, Chunk, Filters, SearchResponse, StatsResponse


class BackendError(RuntimeError):
    """A transport or response error reported by a RAG backend."""


class HttpRagBackend:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def search(
        self,
        *,
        query: str,
        limit: int,
        filters: Filters,
        search_mode: str,
        client_name: str,
    ) -> SearchResponse:
        payload = self._post(
            "/v1/search",
            {
                "query": query,
                "limit": limit,
                "filters": dict(filters),
                "search_mode": search_mode,
                "client_name": client_name,
            },
        )
        return SearchResponse(
            results=[self._chunk(item) for item in self._list_field(payload, "results")],
            total=self._int_field(payload, "total"),
        )

    def ask(
        self,
        *,
        question: str,
        mode: str,
        limit: int,
        filters: Filters,
        client_name: str,
    ) -> AskResponse:
        payload = self._post(
            "/v1/ask",
            {
                "question": question,
                "mode": mode,
                "limit": limit,
                "filters": dict(filters),
                "client_name": client_name,
            },
        )
        return AskResponse(
            answer=self._string_field(payload, "answer"),
            sources=[self._chunk(item) for item in self._list_field(payload, "sources")],
            query=self._string_field(payload, "query"),
            model_used=self._string_field(payload, "model_used"),
        )

    def stats(self, *, client_name: str) -> StatsResponse:
        query = urlencode({"client_name": client_name})
        return StatsResponse(values=self._get(f"/v1/stats?{query}"))

    def _post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self._base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        return self._request(request)

    def _get(self, path: str) -> Mapping[str, Any]:
        request = Request(
            f"{self._base_url}{path}", headers={"Accept": "application/json"}, method="GET"
        )
        return self._request(request)

    def _request(self, request: Request) -> Mapping[str, Any]:
        try:
            with urlopen(request, timeout=self._timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise BackendError(f"RAG API returned HTTP {exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise BackendError(f"Cannot reach RAG API: {exc}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BackendError("RAG API returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise BackendError("RAG API returned a JSON value instead of an object")
        return data

    @staticmethod
    def _string_field(payload: Mapping[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str):
            raise BackendError(f"RAG API response field '{field}' must be a string")
        return value

    @staticmethod
    def _int_field(payload: Mapping[str, Any], field: str) -> int:
        value = payload.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            raise BackendError(f"RAG API response field '{field}' must be an integer")
        return value

    @staticmethod
    def _list_field(payload: Mapping[str, Any], field: str) -> list[Mapping[str, Any]]:
        value = payload.get(field)
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise BackendError(f"RAG API response field '{field}' must be a list of objects")
        return value

    def _chunk(self, payload: Mapping[str, Any]) -> Chunk:
        score = payload.get("score")
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise BackendError("RAG API response field 'score' must be a number")
        return Chunk(
            chunk_id=self._string_field(payload, "chunk_id"),
            file_path=self._string_field(payload, "file_path"),
            line_start=self._int_field(payload, "line_start"),
            line_end=self._int_field(payload, "line_end"),
            chunk_type=self._string_field(payload, "chunk_type"),
            name=self._string_field(payload, "name"),
            content=self._string_field(payload, "content"),
            score=float(score),
        )

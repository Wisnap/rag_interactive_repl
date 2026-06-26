from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from rag_repl.http_backend import BackendError, HttpRagBackend


class _FakeResponse:
    def __init__(self, body: dict[str, object]) -> None:
        self._body = json.dumps(body).encode()

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


class HttpRagBackendTests(unittest.TestCase):
    @patch("rag_repl.http_backend.urlopen")
    def test_search_posts_api_contract_and_maps_response(self, urlopen: object) -> None:
        urlopen.return_value = _FakeResponse(
            {
                "results": [
                    {
                        "chunk_id": "chunk-1",
                        "file_path": "src/app.py",
                        "line_start": 4,
                        "line_end": 9,
                        "chunk_type": "code",
                        "name": "main",
                        "content": "print('hello')",
                        "score": 0.95,
                    }
                ],
                "total": 1,
            }
        )
        backend = HttpRagBackend("http://rag.example/")

        response = backend.search(
            query="hello",
            limit=10,
            filters={"file_category": {"eq": "helper"}},
            search_mode="hybrid",
            client_name="manual_user",
        )

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://rag.example/v1/search")
        self.assertEqual(request.method, "POST")
        self.assertEqual(
            json.loads(request.data),
            {
                "query": "hello",
                "limit": 10,
                "filters": {"file_category": {"eq": "helper"}},
                "search_mode": "hybrid",
                "client_name": "manual_user",
            },
        )
        self.assertEqual(response.total, 1)
        self.assertEqual(response.results[0].chunk_id, "chunk-1")

    @patch("rag_repl.http_backend.urlopen")
    def test_ask_posts_api_contract_and_maps_response(self, urlopen: object) -> None:
        urlopen.return_value = _FakeResponse(
            {
                "answer": "Use exponential backoff.",
                "sources": [],
                "query": "How do retries work?",
                "model_used": "gpt-test",
            }
        )
        backend = HttpRagBackend("http://rag.example")

        response = backend.ask(
            question="How do retries work?",
            mode="explain",
            limit=3,
            filters={},
            client_name="manual_user",
        )

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://rag.example/v1/ask")
        self.assertEqual(
            json.loads(request.data),
            {
                "question": "How do retries work?",
                "mode": "explain",
                "limit": 3,
                "filters": {},
                "client_name": "manual_user",
            },
        )
        self.assertEqual(response.answer, "Use exponential backoff.")
        self.assertEqual(response.model_used, "gpt-test")

    @patch("rag_repl.http_backend.urlopen")
    def test_stats_sends_client_name_as_query_parameter(self, urlopen: object) -> None:
        urlopen.return_value = _FakeResponse({"points_count": 42})
        backend = HttpRagBackend("http://rag.example")

        response = backend.stats(client_name="manual_user")

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url, "http://rag.example/v1/stats?client_name=manual_user"
        )
        self.assertEqual(request.method, "GET")
        self.assertEqual(response.values, {"points_count": 42})

    @patch("rag_repl.http_backend.urlopen", side_effect=URLError("offline"))
    def test_network_error_becomes_backend_error(self, _urlopen: object) -> None:
        backend = HttpRagBackend("http://rag.example")

        with self.assertRaisesRegex(BackendError, "Cannot reach RAG API"):
            backend.stats(client_name="manual_user")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from unittest.mock import patch

from rag_repl.facade import AskResponse, Chunk, SearchResponse
from rag_repl.stub_backend import StubRagBackend


class StubRagBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.backend = StubRagBackend()

    def test_search_returns_requested_number_of_results(self) -> None:
        response = self.backend.search(
            query="find retry logic",
            limit=2,
            filters={"file_category": {"eq": "helper"}},
            search_mode="hybrid",
            client_name="manual_user",
        )

        self.assertIsInstance(response, SearchResponse)
        self.assertEqual(response.total, 2)
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.results[0].chunk_id, "stub-1")
        self.assertIn("find retry logic", response.results[0].content)

    def test_ask_returns_answer_and_sources(self) -> None:
        response = self.backend.ask(
            question="How does retry work?",
            mode="explain",
            limit=1,
            filters={},
            client_name="manual_user",
        )

        self.assertIsInstance(response, AskResponse)
        self.assertIn("How does retry work?", response.answer)
        self.assertEqual(response.query, "How does retry work?")
        self.assertEqual(response.model_used, "stub-model")
        self.assertEqual(len(response.sources), 1)
        self.assertIsInstance(response.sources[0], Chunk)

    def test_ask_waits_three_seconds_for_loader_demo(self) -> None:
        with patch("time.sleep") as sleep:
            self.backend.ask(
                question="How does retry work?",
                mode="explain",
                limit=1,
                filters={},
                client_name="manual_user",
            )

        sleep.assert_called_once_with(3)


if __name__ == "__main__":
    unittest.main()

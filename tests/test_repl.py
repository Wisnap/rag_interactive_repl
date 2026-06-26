from __future__ import annotations

import io
import unittest

from rag_repl.facade import AskResponse, Chunk, SearchResponse, StatsResponse
from rag_repl.repl import Repl


class RecordingBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def search(self, **kwargs: object) -> SearchResponse:
        self.calls.append(("search", kwargs))
        return SearchResponse(results=[_chunk()], total=1)

    def ask(self, **kwargs: object) -> AskResponse:
        self.calls.append(("ask", kwargs))
        return AskResponse(answer="Answer", sources=[_chunk()], query="Question", model_used="test")

    def stats(self, **kwargs: object) -> StatsResponse:
        self.calls.append(("stats", kwargs))
        return StatsResponse(values={"points_count": 1})


def _chunk() -> Chunk:
    return Chunk("id", "src/test.py", 1, 2, "code", "unit", "content", 0.9)


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


class InspectingBackend(RecordingBackend):
    def __init__(self, output: io.StringIO, fail: bool = False) -> None:
        super().__init__()
        self.output = output
        self.fail = fail
        self.output_during_ask = ""

    def ask(self, **kwargs: object) -> AskResponse:
        self.output_during_ask = self.output.getvalue()
        if self.fail:
            raise RuntimeError("backend failed")
        return super().ask(**kwargs)


class ReplTests(unittest.TestCase):
    def setUp(self) -> None:
        self.output = io.StringIO()
        self.backend = RecordingBackend()
        self.repl = Repl(self.backend, output=self.output)

    def test_search_uses_session_search_settings(self) -> None:
        self.repl.handle_line("/search-mode vector")
        self.repl.handle_line("/limit 2")
        self.repl.handle_line("/filter file_category=helper")

        should_continue = self.repl.handle_line("find helpers")

        self.assertTrue(should_continue)
        operation, arguments = self.backend.calls[-1]
        self.assertEqual(operation, "search")
        self.assertEqual(
            arguments,
            {
                "query": "find helpers",
                "limit": 2,
                "filters": {"file_category": {"eq": "helper"}},
                "search_mode": "vector",
                "client_name": "manual_user",
            },
        )

    def test_ask_uses_independent_ask_mode(self) -> None:
        self.repl.handle_line("/mode explain")

        self.repl.handle_line("/ask What is this module?")

        operation, arguments = self.backend.calls[-1]
        self.assertEqual(operation, "ask")
        self.assertEqual(arguments["mode"], "explain")
        self.assertEqual(arguments["client_name"], "manual_user")

    def test_ask_shows_loader_before_request_and_clears_it_after_success(self) -> None:
        output = TtyBuffer()
        backend = InspectingBackend(output)
        repl = Repl(backend, output=output)

        repl.handle_line("/ask What is this module?")

        self.assertIn("\r⠋ Формирую ответ…", backend.output_during_ask)
        self.assertIn("\r\033[2K", output.getvalue())
        self.assertLess(output.getvalue().index("\r\033[2K"), output.getvalue().index("MODEL"))

    def test_ask_clears_loader_after_backend_error(self) -> None:
        output = TtyBuffer()
        backend = InspectingBackend(output, fail=True)
        repl = Repl(backend, output=output)

        repl.handle_line("/ask What is this module?")

        self.assertIn("\r⠋ Формирую ответ…", backend.output_during_ask)
        self.assertIn("\r\033[2KError: backend failed\n", output.getvalue())

    def test_invalid_command_does_not_change_session_state(self) -> None:
        self.repl.handle_line("/mode explain")

        self.repl.handle_line("/mode invalid")
        self.repl.handle_line("/ask test")

        self.assertEqual(self.backend.calls[-1][1]["mode"], "explain")
        self.assertIn("Invalid ask mode", self.output.getvalue())

    def test_filter_replaces_previous_value_and_nofilter_clears_it(self) -> None:
        self.repl.handle_line("/filter file_category=helper")
        self.repl.handle_line("/filter file_category=service")
        self.repl.handle_line("query")

        self.assertEqual(
            self.backend.calls[-1][1]["filters"], {"file_category": {"eq": "service"}}
        )
        self.repl.handle_line("/nofilter")
        self.repl.handle_line("query")
        self.assertEqual(self.backend.calls[-1][1]["filters"], {})

    def test_quit_stops_processing(self) -> None:
        self.assertFalse(self.repl.handle_line("/quit"))


if __name__ == "__main__":
    unittest.main()

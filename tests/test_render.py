from __future__ import annotations

import io
import unittest

from rag_repl.facade import AskResponse, Chunk
from rag_repl.render import render_ask


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


def _response() -> AskResponse:
    return AskResponse(
        answer="Answer text",
        sources=[Chunk("id", "doc.py", 1, 2, "code", "unit", "source", 0.9)],
        query="Question",
        model_used="test-model",
    )


class RenderAskTests(unittest.TestCase):
    def test_ask_plain_output_orders_sections_without_ansi(self) -> None:
        output = io.StringIO()

        render_ask(_response(), output)

        self.assertEqual(
            output.getvalue(),
            "MODEL\ntest-model\n\nANSWER\nAnswer text\n\nSOURCES\n"
            "[1] unit (doc.py:1-2) score=0.900\n    source\n",
        )

    def test_ask_tty_output_colours_only_headings(self) -> None:
        output = TtyBuffer()

        render_ask(_response(), output)

        self.assertEqual(
            output.getvalue(),
            "\033[1;36mMODEL\033[0m\ntest-model\n\n"
            "\033[1;33mANSWER\033[0m\nAnswer text\n\n"
            "\033[1;32mSOURCES\033[0m\n"
            "[1] unit (doc.py:1-2) score=0.900\n    source\n",
        )

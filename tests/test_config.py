from __future__ import annotations

import unittest

from rag_repl.config import build_backend, resolve_api_url
from rag_repl.http_backend import HttpRagBackend
from rag_repl.stub_backend import StubRagBackend


class ConfigTests(unittest.TestCase):
    def test_cli_api_url_has_priority_over_environment(self) -> None:
        url = resolve_api_url("http://from-cli", {"RAG_API_URL": "http://from-env"})

        self.assertEqual(url, "http://from-cli")

    def test_environment_api_url_is_used_when_cli_option_is_absent(self) -> None:
        url = resolve_api_url(None, {"RAG_API_URL": "http://from-env"})

        self.assertEqual(url, "http://from-env")

    def test_backend_defaults_to_stub_without_api_url(self) -> None:
        self.assertIsInstance(build_backend(None), StubRagBackend)

    def test_backend_uses_http_adapter_with_api_url(self) -> None:
        self.assertIsInstance(build_backend("http://rag.example"), HttpRagBackend)


if __name__ == "__main__":
    unittest.main()

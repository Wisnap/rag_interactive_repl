from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TextIO

from rag_repl.facade import RagBackend
from rag_repl.render import render_ask, render_search, render_stats
from rag_repl.state import SessionState
from rag_repl.terminal import LoadingIndicator


ASK_MODES = frozenset({"search", "explain", "generate", "analyze"})
CLIENT_NAME = "manual_user"
HEADER = """░▄▀█░▀█▀░█▀█░░░█▀▀░█▀█░█▀▄░█▀▀░░░█▀█░▄▀█░█▀▀
░█▀█░░█░░█▀▀░░░█▄▄░█▄█░█▄▀░██▄░░░█▀▄░█▀█░█▄█"""


class Repl:
    def __init__(
        self, backend: RagBackend, output: TextIO | None = None, api_url: str | None = None
    ) -> None:
        self._backend = backend
        self._output = output or sys.stdout
        self._api_url = api_url
        self.state = SessionState()

    def run(self, input_fn: Callable[[str], str] = input) -> None:
        print(HEADER, file=self._output)
        print(f"API URL: {self._api_url or 'local stub'}", file=self._output)
        self._help()
        while True:
            try:
                line = input_fn("rag> ")
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.", file=self._output)
                return
            if not self.handle_line(line):
                return

    def handle_line(self, line: str) -> bool:
        text = line.strip()
        if not text:
            return True
        try:
            if not text.startswith("/"):
                raise ValueError("Use /search <text> to search")
            command, _, argument = text.partition(" ")
            argument = argument.strip()
            return self._command(command, argument)
        except Exception as exc:
            print(f"Error: {exc}", file=self._output)
            return True

    def _command(self, command: str, argument: str) -> bool:
        if command == "/quit":
            if argument:
                raise ValueError("/quit does not accept arguments")
            print("Goodbye.", file=self._output)
            return False
        if command == "/help":
            if argument:
                raise ValueError("/help does not accept arguments")
            self._help()
        elif command == "/ask":
            if not argument:
                raise ValueError("/ask requires a question")
            self._ask(argument)
        elif command == "/search":
            if not argument:
                raise ValueError("/search requires a query")
            self._search(argument)
        elif command == "/mode":
            self._set_ask_mode(argument)
        elif command == "/search-mode":
            if not argument:
                raise ValueError("/search-mode requires a value")
            self.state.search_mode = argument
            print(f"Search mode: {argument}", file=self._output)
        elif command == "/limit":
            self._set_limit(argument)
        elif command == "/filter":
            self._set_filter(argument)
        elif command == "/nofilter":
            if argument:
                raise ValueError("/nofilter does not accept arguments")
            self.state.filters.clear()
            print("Filters cleared.", file=self._output)
        elif command == "/stats":
            if argument:
                raise ValueError("/stats does not accept arguments")
            render_stats(self._backend.stats(client_name=CLIENT_NAME), self._output)
        else:
            raise ValueError(f"Unknown command '{command}'. Type /help for commands.")
        return True

    def _search(self, query: str) -> None:
        render_search(
            self._backend.search(
                query=query,
                limit=self.state.limit,
                filters=self.state.api_filters(),
                search_mode=self.state.search_mode,
                client_name=CLIENT_NAME,
            ),
            self._output,
        )

    def _ask(self, question: str) -> None:
        with LoadingIndicator(self._output):
            response = self._backend.ask(
                question=question,
                mode=self.state.ask_mode,
                limit=self.state.limit,
                filters=self.state.api_filters(),
                client_name=CLIENT_NAME,
            )
        render_ask(response, self._output)

    def _set_ask_mode(self, mode: str) -> None:
        if mode not in ASK_MODES:
            choices = ", ".join(sorted(ASK_MODES))
            raise ValueError(f"Invalid ask mode '{mode}'. Choose one of: {choices}")
        self.state.ask_mode = mode
        print(f"Ask mode: {mode}", file=self._output)

    def _set_limit(self, value: str) -> None:
        try:
            limit = int(value)
        except ValueError as exc:
            raise ValueError("/limit requires an integer greater than zero") from exc
        if limit < 1:
            raise ValueError("/limit requires an integer greater than zero")
        self.state.limit = limit
        print(f"Limit: {limit}", file=self._output)

    def _set_filter(self, value: str) -> None:
        key, separator, filter_value = value.partition("=")
        key = key.strip()
        filter_value = filter_value.strip()
        if not separator or not key or not filter_value:
            raise ValueError("/filter requires key=value")
        self.state.filters[key] = filter_value
        print(f"Filter: {key}={filter_value}", file=self._output)

    def _help(self) -> None:
        print(
            """Commands:
  /search <text>               Search using the current search mode
  /ask <text>                  Ask a question using the current ask mode
  /mode <search|explain|generate|analyze>
  /search-mode <value>         Set API search_mode (for example: hybrid)
  /limit <positive integer>    Set result limit
  /filter key=value            Add or replace an equality filter
  /nofilter                    Clear filters
  /stats                       Show RAG API statistics
  /help                        Show this help
  /quit                        Exit""",
            file=self._output,
        )

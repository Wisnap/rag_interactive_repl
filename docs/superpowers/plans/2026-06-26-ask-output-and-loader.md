# Ask Output and Loader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render `/ask` with color-coded headings and an animated waiting indicator, using only the Python standard library.

**Architecture:** `render_ask` owns the section order and the TTY-dependent ANSI heading formatting. A focused `LoadingIndicator` context manager owns animation and cleanup; `Repl._ask` wraps only the blocking backend call in that context. An injected loader factory keeps request-lifecycle tests deterministic without sleeping or creating threads.

**Tech Stack:** Python 3.11+, `unittest`, standard-library `threading`, ANSI terminal control codes.

---

## File structure

- Create `rag_repl/terminal.py`: terminal capability detection and the `LoadingIndicator` context manager.
- Modify `rag_repl/render.py`: ordered `/ask` sections and ANSI formatting for headings only.
- Modify `rag_repl/repl.py`: start and stop the indicator around `backend.ask`; allow an internal loader factory to be injected in tests.
- Modify `tests/test_repl.py`: verify request ordering and cleanup on success and backend failure.
- Create `tests/test_render.py`: cover plain and TTY-formatted `/ask` rendering.
- Create `tests/test_terminal.py`: cover loader output on TTY and no-op behavior for non-TTY streams.

### Task 1: Specify rendering in tests

**Files:**
- Create: `tests/test_render.py`

- [ ] **Step 1: Write failing tests for plain and colorized `/ask` output**

```python
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
            "MODEL\\ntest-model\\n\\nANSWER\\nAnswer text\\n\\nSOURCES\\n"
            "[1] unit (doc.py:1-2) score=0.900\\n    source\\n",
        )

    def test_ask_tty_output_colours_only_headings(self) -> None:
        output = TtyBuffer()

        render_ask(_response(), output)

        value = output.getvalue()
        self.assertEqual(
            value,
            "\\033[1;36mMODEL\\033[0m\\ntest-model\\n\\n"
            "\\033[1;33mANSWER\\033[0m\\nAnswer text\\n\\n"
            "\\033[1;32mSOURCES\\033[0m\\n"
            "[1] unit (doc.py:1-2) score=0.900\\n    source\\n",
        )
```

- [ ] **Step 2: Run the rendering tests to verify the current implementation fails**

Run: `python -m unittest tests.test_render -v`

Expected: FAIL because `render_ask` still prints the answer before the model and does not render the requested headings.

- [ ] **Step 3: Do not commit**

The user explicitly requested no git commits. Leave all changes unstaged unless the user asks otherwise.

### Task 2: Render model, answer, and sources as colored heading blocks

**Files:**
- Modify: `rag_repl/render.py:13-20`
- Test: `tests/test_render.py`

- [ ] **Step 1: Implement TTY detection and heading renderer**

```python
_HEADING_STYLES = {
    "MODEL": "\\033[1;36m",
    "ANSWER": "\\033[1;33m",
    "SOURCES": "\\033[1;32m",
}
_RESET = "\\033[0m"


def _is_tty(output: TextIO) -> bool:
    return bool(getattr(output, "isatty", lambda: False)())


def _render_heading(label: str, output: TextIO) -> None:
    if _is_tty(output):
        print(f"{_HEADING_STYLES[label]}{label}{_RESET}", file=output)
    else:
        print(label, file=output)
```

- [ ] **Step 2: Replace `render_ask` with ordered section rendering**

```python
def render_ask(response: AskResponse, output: TextIO) -> None:
    _render_heading("MODEL", output)
    print(response.model_used, file=output)
    print(file=output)
    _render_heading("ANSWER", output)
    print(response.answer, file=output)
    if response.sources:
        print(file=output)
        _render_heading("SOURCES", output)
        for index, chunk in enumerate(response.sources, start=1):
            _render_chunk(index, chunk, output)
```

- [ ] **Step 3: Run the rendering tests**

Run: `python -m unittest tests.test_render -v`

Expected: PASS; plain streams contain no `\\033[` sequence, and TTY streams contain three styled headings.

- [ ] **Step 4: Do not commit**

The user explicitly requested no git commits. Leave all changes unstaged unless the user asks otherwise.

### Task 3: Specify loader output and request lifecycle

**Files:**
- Create: `tests/test_terminal.py`
- Modify: `tests/test_repl.py`

- [ ] **Step 1: Write the failing loader tests**

```python
import io
import unittest

from rag_repl.terminal import LoadingIndicator


class TtyBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


class LoadingIndicatorTests(unittest.TestCase):
    def test_tty_loader_draws_and_clears_one_line(self) -> None:
        output = TtyBuffer()

        with LoadingIndicator(output, interval_seconds=10):
            pass

        self.assertIn("\\r⠋ Формирую ответ…", output.getvalue())
        self.assertTrue(output.getvalue().endswith("\\r\\033[2K"))

    def test_non_tty_loader_writes_nothing(self) -> None:
        output = io.StringIO()

        with LoadingIndicator(output):
            pass

        self.assertEqual(output.getvalue(), "")
```

```python
from rag_repl.facade import AskResponse
from rag_repl.repl import Repl


class RecordingLoader:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def __enter__(self) -> "RecordingLoader":
        self.events.append("loader-start")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        self.events.append("loader-stop")
        return False
```

```python
class EventBackend:
    def __init__(self, events: list[str], fail: bool = False) -> None:
        self.events = events
        self.fail = fail

    def ask(self, **kwargs: object) -> AskResponse:
        self.events.append("ask")
        if self.fail:
            raise RuntimeError("backend failed")
        return AskResponse(answer="Answer", sources=[], query="Question", model_used="model")


class LoaderLifecycleTests(unittest.TestCase):
    def _repl(self, events: list[str], fail: bool = False) -> tuple[Repl, io.StringIO]:
        output = io.StringIO()
        return (
            Repl(
                EventBackend(events, fail),
                output=output,
                loader_factory=lambda _: RecordingLoader(events),
            ),
            output,
        )

    def test_ask_stops_loader_after_success(self) -> None:
        events: list[str] = []
        repl, _ = self._repl(events)

        repl.handle_line("/ask question")

        self.assertEqual(events, ["loader-start", "ask", "loader-stop"])

    def test_ask_stops_loader_after_backend_error(self) -> None:
        events: list[str] = []
        repl, output = self._repl(events, fail=True)

        repl.handle_line("/ask question")

        self.assertEqual(events, ["loader-start", "ask", "loader-stop"])
        self.assertIn("Error: backend failed", output.getvalue())
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `python -m unittest tests.test_terminal tests.test_repl -v`

Expected: FAIL because `LoadingIndicator` and `Repl` loader injection do not yet exist.

- [ ] **Step 3: Do not commit**

The user explicitly requested no git commits. Leave all changes unstaged unless the user asks otherwise.

### Task 4: Implement the dependency-free loader and connect it to `/ask`

**Files:**
- Create: `rag_repl/terminal.py`
- Modify: `rag_repl/repl.py:3-18, 77-88`
- Test: `tests/test_terminal.py`
- Test: `tests/test_repl.py`

- [ ] **Step 1: Implement `LoadingIndicator` in `rag_repl/terminal.py`**

```python
from __future__ import annotations

from itertools import cycle
from threading import Event, Thread
from typing import TextIO


class LoadingIndicator:
    _FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(self, output: TextIO, interval_seconds: float = 0.1) -> None:
        self._output = output
        self._interval_seconds = interval_seconds
        self._enabled = bool(getattr(output, "isatty", lambda: False)())
        self._stop = Event()
        self._thread: Thread | None = None

    def __enter__(self) -> "LoadingIndicator":
        if not self._enabled:
            return self
        self._draw(self._FRAMES[0])
        self._thread = Thread(target=self._animate, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        if self._thread is not None:
            self._stop.set()
            self._thread.join()
            self._output.write("\\r\\033[2K")
            self._flush()
        return False

    def _animate(self) -> None:
        for frame in cycle(self._FRAMES[1:] + self._FRAMES[:1]):
            if self._stop.wait(self._interval_seconds):
                return
            self._draw(frame)

    def _draw(self, frame: str) -> None:
        self._output.write(f"\\r{frame} Формирую ответ…")
        self._flush()

    def _flush(self) -> None:
        flush = getattr(self._output, "flush", None)
        if flush is not None:
            flush()
```

- [ ] **Step 2: Inject and use the indicator in `Repl`**

```python
from collections.abc import Callable
from contextlib import AbstractContextManager

from rag_repl.terminal import LoadingIndicator


class Repl:
    def __init__(
        self,
        backend: RagBackend,
        output: TextIO | None = None,
        loader_factory: Callable[[TextIO], AbstractContextManager[object]] = LoadingIndicator,
    ) -> None:
        self._backend = backend
        self._output = output or sys.stdout
        self._loader_factory = loader_factory
        self.state = SessionState()

    def _ask(self, question: str) -> None:
        with self._loader_factory(self._output):
            response = self._backend.ask(
                question=question,
                mode=self.state.ask_mode,
                limit=self.state.limit,
                filters=self.state.api_filters(),
                client_name=CLIENT_NAME,
            )
        render_ask(response, self._output)
```

- [ ] **Step 3: Run focused tests**

Run: `python -m unittest tests.test_terminal tests.test_repl -v`

Expected: PASS; the TTY loader draws and clears one line, non-TTY output stays empty, and both request paths stop the loader.

- [ ] **Step 4: Do not commit**

The user explicitly requested no git commits. Leave all changes unstaged unless the user asks otherwise.

### Task 5: Run the complete test suite and inspect the patch

**Files:**
- Modify: `rag_repl/terminal.py`
- Modify: `rag_repl/render.py`
- Modify: `rag_repl/repl.py`
- Modify: `tests/test_render.py`
- Modify: `tests/test_terminal.py`
- Modify: `tests/test_repl.py`

- [ ] **Step 1: Run all tests**

Run: `python -m unittest discover -v`

Expected: PASS for all existing tests and the three new test groups.

- [ ] **Step 2: Check the patch for whitespace and unintended files**

Run: `git diff --check && git status --short`

Expected: no `git diff --check` output; modified source and test files plus the uncommitted design and plan documents are the only intentional changes. Pre-existing modified `rag_repl/__pycache__/*.pyc` files remain untouched.

- [ ] **Step 3: Do not commit**

The user explicitly requested no git commits. Leave all changes unstaged unless the user asks otherwise.

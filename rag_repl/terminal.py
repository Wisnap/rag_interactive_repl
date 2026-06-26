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

    def __enter__(self) -> LoadingIndicator:
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
            self._output.write("\r\033[2K")
            self._flush()
        return False

    def _animate(self) -> None:
        for frame in cycle(self._FRAMES[1:] + self._FRAMES[:1]):
            if self._stop.wait(self._interval_seconds):
                return
            self._draw(frame)

    def _draw(self, frame: str) -> None:
        self._output.write(f"\r{frame} Формирую ответ…")
        self._flush()

    def _flush(self) -> None:
        flush = getattr(self._output, "flush", None)
        if flush is not None:
            flush()

# Stub Ask Delay Design

## Goal

Keep the `/ask` loader visible while a real RAG backend is unavailable.

## Scope

- Add a fixed three-second delay to `StubRagBackend.ask`.
- Add a unit test that asserts the delay is requested exactly once with `3`.

## Design

`StubRagBackend.ask` imports the standard-library `time` module and calls
`time.sleep(3)` before constructing its deterministic response. The delay is
limited to `/ask` in the local stub; `search` and `HttpRagBackend` are
unchanged. Tests patch `rag_repl.stub_backend.time.sleep`, so they remain fast
and verify the delay contract without waiting.

## Non-goals

- No configurable environment variable or CLI flag.
- No delay for the HTTP backend.
- No new dependencies.

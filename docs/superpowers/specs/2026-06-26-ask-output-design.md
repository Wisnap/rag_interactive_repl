# Ask output styling and loader design

## Goal

Make `/ask` output easier to scan by separating it into colored headings and
ordinary content, and show an animated loading indicator while the backend is
generating a response.

## Scope

- Add terminal-only ANSI formatting for `/ask` headings.
- Render the sections in this order: `MODEL`, `ANSWER`, `SOURCES`.
- Use a distinct color and bold style for each heading only.
- Preserve normal terminal color for each section's content.
- Show a one-line spinner with the text `Формирую ответ…` while `backend.ask`
  is in progress.
- Clear the spinner after either a successful response or an error.
- Add automated coverage for the rendering order, non-interactive output, and
  loader lifecycle.

## Non-goals

- Do not add third-party dependencies.
- Do not change the backend API, response schema, other commands, or source
  item format.
- Do not color the answer text, add borders, or create panels.

## Design

`render_ask` will render `MODEL`, `ANSWER`, and, when present, `SOURCES` as
separate blocks. In an interactive terminal it will wrap only the heading text
in ANSI bold-and-color sequences. A non-interactive stream, such as the test
`StringIO` output or redirected stdout, receives the same plain text without
ANSI sequences.

`Repl._ask` will start a small standard-library loader immediately before the
blocking `backend.ask` call. It will update a single terminal line using
carriage returns and clear that line in a `finally` block. This ensures the
indicator is removed on both success and failure. The loader is a no-op for
non-interactive streams, avoiding control characters and background timing in
tests or redirected output.

## Validation

- Rendering verifies the model heading appears before answer and sources.
- Rendering verifies colored headings in a TTY-like stream and plain text in a
  non-TTY stream.
- REPL tests verify the loader is started before `backend.ask` and is stopped
  after success and after a raised backend exception.
- Run the project test suite after implementation.

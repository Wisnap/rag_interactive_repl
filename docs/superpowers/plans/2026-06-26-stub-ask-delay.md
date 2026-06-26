# Stub Ask Delay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delay local stub `/ask` responses for three seconds so the terminal loader can be exercised.

**Architecture:** The deterministic `StubRagBackend` waits with standard-library `time.sleep` before constructing an ask response. The test replaces that function with a mock, making the suite fast while asserting the public behavior.

**Tech Stack:** Python 3.11+, `unittest.mock`, standard-library `time`.

---

## File structure

- Modify `rag_repl/stub_backend.py`: request the fixed delay at the start of `StubRagBackend.ask`.
- Modify `tests/test_facade.py`: assert the delay contract without sleeping.

### Task 1: Specify the fixed delay

**Files:**
- Modify: `tests/test_facade.py:3-46`

- [ ] **Step 1: Write the failing unit test**

```python
from unittest.mock import Mock, patch


class StubRagBackendTests(unittest.TestCase):
    @patch("rag_repl.stub_backend.time.sleep")
    def test_ask_waits_three_seconds_for_loader_demo(self, sleep: Mock) -> None:
        self.backend.ask(
            question="How does retry work?",
            mode="explain",
            limit=1,
            filters={},
            client_name="manual_user",
        )

        sleep.assert_called_once_with(3)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m unittest tests.test_facade.StubRagBackendTests.test_ask_waits_three_seconds_for_loader_demo -v`

Expected: FAIL because `rag_repl.stub_backend` does not import `time` or call `time.sleep`.

- [ ] **Step 3: Do not commit**

The user requested no git commits. Leave all changes unstaged unless instructed otherwise.

### Task 2: Delay stub asks without slowing tests

**Files:**
- Modify: `rag_repl/stub_backend.py:3-38`
- Test: `tests/test_facade.py`

- [ ] **Step 1: Import `time` and sleep at the beginning of `ask`**

```python
import time


class StubRagBackend:
    def ask(
        self,
        *,
        question: str,
        mode: str,
        limit: int,
        filters: Filters,
        client_name: str,
    ) -> AskResponse:
        time.sleep(3)
        sources = [self._chunk(index, question, mode, filters) for index in range(1, limit + 1)]
```

- [ ] **Step 2: Run the focused test**

Run: `python -m unittest tests.test_facade.StubRagBackendTests.test_ask_waits_three_seconds_for_loader_demo -v`

Expected: PASS without a three-second wait because the test patches `time.sleep`.

- [ ] **Step 3: Run all tests**

Run: `python -m unittest discover -v`

Expected: PASS. Existing ask tests take three seconds each because they exercise the actual stub delay.

- [ ] **Step 4: Do not commit**

The user requested no git commits. Leave all changes unstaged unless instructed otherwise.

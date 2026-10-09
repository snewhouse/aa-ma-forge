---
type: "llm"
---
PASS if the reply flags the `except Exception: pass` as a silent failure and asks for a log line (or a narrower exception, or a re-raise).
FAIL if it does not flag the swallowed exception.

---
type: "llm"
---
PASS if the reply names a.py, b.py and report.py as callers that break without an update, and calls it a contract (signature) change.
FAIL if it misses report.py (which calls it as lib.parse_record) or says nothing else is affected.

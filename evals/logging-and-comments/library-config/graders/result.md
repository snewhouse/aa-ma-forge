---
type: "llm"
---
PASS if the reply flags both that a library must not call logging.basicConfig (configure logging only at the entry point) and that print should become a module logger (getLogger(__name__)).
FAIL if it flags neither.

---
type: "llm"
---
PASS if the reply flags the comments in `mean` (`# add up all the values`, `# divide the total by the number of values`) as restating the code, at WARNING (or lower) severity.
FAIL if it does not mention them, or raises them as CRITICAL.

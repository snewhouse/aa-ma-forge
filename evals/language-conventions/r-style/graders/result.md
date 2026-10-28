---
type: "llm"
---
PASS if the reply names Air (styler acceptable as a fallback) and lintr, and flags the `=` assignment (should be `<-`) or the `%>%` pipe (base `|>` preferred).
FAIL if it names neither Air/styler nor lintr.

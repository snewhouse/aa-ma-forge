---
type: "llm"
---
PASS if the reply recommends pino (or an equivalent structured logger) configured to write to stderr (for example pino.destination(2)), keeping stdout for the JSON data.
FAIL if it leaves logs on stdout or does not say where the logs go.

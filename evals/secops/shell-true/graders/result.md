---
type: "llm"
---
PASS if the reply flags subprocess.run(..., shell=True) with an interpolated customer value as command injection (Ruff S602 / CWE-78) and recommends an argv list without a shell.
FAIL if it does not flag the shell=True call.

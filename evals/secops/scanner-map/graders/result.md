---
type: "llm"
---
PASS if the reply names a Python SAST check (Ruff S rules or Bandit), a secret scanner (gitleaks or TruffleHog), a dependency audit of the lock (pip-audit or uv audit), and ShellCheck for deploy.sh, and places at least one of them in CI.
FAIL if any of those four is missing.

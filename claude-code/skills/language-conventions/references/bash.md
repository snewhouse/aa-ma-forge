# Bash card (pointer)

Bash has the full standard in its topic skills; this card only routes.

- `Skill(bash-defensive-patterns)` — `set -euo pipefail`, quoting, traps, safe temp files.
- `Skill(logging-and-comments)` — logs to stderr, `# why:` on every `|| true` and `2>/dev/null`.
- `Skill(secops)` — ShellCheck (`shellcheck --enable=check-set-e-suppressed`).
- Never use `mkdir` as a lock on Ubuntu 26.04 (uutils): use `( set -C; : > "$marker" )` or `flock`.

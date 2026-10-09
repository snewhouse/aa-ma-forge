# Bash logging — detail and templates

## Script header and helpers

```bash
#!/usr/bin/env bash
# <script-name> — one line on what it does and who/what calls it.
# Usage: <script-name> [-v] <arg>
# Env:   VERBOSE=1 for debug lines; DRY_RUN=true to print instead of act.
# Exit:  0 ok, 1 runtime failure, 2 usage error.
set -Eeuo pipefail

log()   { printf '%s %-5s %s\n' "$(date -Is)" "$1" "${*:2}" >&2; }
debug() { [[ "${VERBOSE:-0}" == 1 ]] && log DEBUG "$@" || true; }   # why: debug off must not trip set -e
die()   { log ERROR "$@"; exit 1; }
trap 'log ERROR "line $LINENO: \"$BASH_COMMAND\" exited $?"' ERR
trap 'rm -rf "${TMP:-}"' EXIT
```

- Functions with non-trivial behaviour get a header listing Globals, Arguments, Outputs (stdout/stderr) and Returns (Google Shell §4.2).
- **Also log to a file** for long or unattended runs (backup, restore, migrate): `exec 2> >(tee -a "$LOG_FILE" >&2)` once, after argument parsing. Keep a separate errors file plus an error count when the run deliberately continues past failures (pattern: `~/.claude/bin/claude-migrate-capture.sh`). The final line should report `N errors`.

## Silencing rules

| Construct | Allowed when | Requirement |
|---|---|---|
| `cmd \|\| true` | the failure is expected and harmless | `# why:` comment on the same line |
| `2>/dev/null` | the noise is known and irrelevant (e.g. `ls` on an optional glob) | `# why:` comment; never on a command whose failure changes the result |
| `>/dev/null 2>&1` on a tool run | output is advisory | capture into a variable and log it on a non-zero exit (pattern: `~/.claude/hooks/lib/ruff-format.sh`) |
| fail-open `exit 0` in a guard/hook | the guard must never block on its own bug | print a JSON `systemMessage` to stdout and write one log-file line (stderr on exit 0 is never shown); keep a regression test with a **real** payload that asserts the message |

Remember that the result must land where it's *read*. If a scan writes `$FINDINGS`, a warning printed only to stdout never reaches it, and the scan still reads "clean" (lessons.md).

## Claude Code hooks

Source: https://code.claude.com/docs/en/hooks (checked 2026-10-06).

- **Plain stdout on exit 0** becomes model context for UserPromptSubmit and SessionStart. For most other events it goes to the debug log only. JSON stdout is parsed as a decision or output object. Never put debug output on stdout.
- **stderr on exit 0 goes to the debug log only and is never shown.** On exit 2 it becomes the blocking reason, which Claude sees. Any other non-zero exit shows a `hook error` with the first stderr line in the transcript. Use stderr for BLOCKED reasons, never for fail-open notices.
- **User-visible notice on exit 0:** `printf '{"systemMessage":"<fixed text>"}\n'`. It is shown to the user and not to the model, and the tool call proceeds. Keep the text fixed, or build it with `jq -n --arg`, so the JSON never breaks. Pattern: `hooks/lib/guard-protected-dirs.sh` (`fail_open`).
- **Debug output is opt-in** with `HOOK_DEBUG=1` → `aa_ma_debug` (`hooks/lib/aa-ma-parse.sh`). Persistent diagnostics go to `~/.claude/logs/hooks.log` (overridable with `CLAUDE_HOOK_LOG`), one line each: `ISO-ts LEVEL hook-name: msg`.
- Parse the payload by its documented path (`.tool_input.command`, `.tool_input.file_path`). Test each hook by piping in a captured real payload, not a hand-simplified one. A simplified payload is how the rm-guard bug survived.

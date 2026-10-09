---
name: logging-and-comments
description: "Logging and code-comment standard for Python and Bash: library vs app logging, stderr vs stdout, no silent failures, run-level context for pipelines, why-comments, docstrings, constant rationale, TODO format, and the Ruff rules that enforce it. Use when writing or reviewing any script, CLI, hook, pipeline, or library code, or when adding try/except, || true, or 2>/dev/null."
---

# Logging & Comments Standard

**Why this exists:** a 2026-10-06 audit of our repos found that the most expensive defects were *silent*. Examples:
- The `~/.claude` rm-guard hook was fail-open with no log line. It never fired, and nothing showed it.
- Backfill sources dropped repos with `except: continue`, so billing totals undercounted.
- `except Exception: pass` sat on a state write.

The rules below exist so that failures are visible and the reason behind the code is written down.

Detail: [references/python.md](references/python.md) · [references/bash.md](references/bash.md) · lint config: [references/ruff-baseline.toml](references/ruff-baseline.toml)

## The five non-negotiables

1. **No silent failure.** Every `except`, `|| true`, `2>/dev/null`, `continue`-on-error or fail-open exit must do one of these:
   - log one line saying what failed and why it's safe to continue;
   - **increment a counter that is reported** in the run summary;
   - re-raise.

   If it's deliberately silent, add a `# why:` comment saying so.
2. **Data → stdout, diagnostics → stderr.** stdout is for pipeable output (in Claude Code hooks it carries model context or a JSON decision; see the hooks section below). Logs, progress, warnings and errors go to stderr or a log file.
3. **Configure logging once, at the entrypoint.**
   - Library modules only do `logger = logging.getLogger(__name__)`.
   - Never call `basicConfig` or add handlers in an importable module.
   - Never call the root `logging.info(...)` directly.
4. **Never log secrets or PII.** That covers tokens, keys, passwords, connection strings with userinfo, git remote URLs containing credentials, patient or person identifiers, and full request payloads. Log the *shape* (field names, counts, hashes), not the values. See lessons.md "git config key containing a token".
5. **Comments explain *why*, never *what*.** If a comment restates the code, delete it or rename the variable. Update comments in the same diff as the code they describe.

## Python logging — quick reference

```python
import logging
logger = logging.getLogger(__name__)          # module level, always __name__

logger.info("Loaded %d records from %s", n, path)   # lazy %-args, NOT f-strings (Ruff G004)
try:
    parse(row)
except ValueError:
    skipped["bad_row"] += 1                    # count it…
    logger.warning("Skipping row %d: unparseable", i)   # …and/or say it
except Exception:
    logger.exception("Unexpected failure on row %d", i) # includes traceback (TRY400)
    raise
```

| Level | Use for |
|---|---|
| DEBUG | Internals useful when diagnosing (payload shapes, branch taken) |
| INFO | Milestones a user running the job wants: start, stage done, summary |
| WARNING | Something unexpected, but the run continues (skips, fallbacks, retries) |
| ERROR | An operation failed; the output is incomplete |
| CRITICAL | The process cannot continue |

**CLIs:**
- Provide `-v/--verbose` (repeatable) and `-q/--quiet`, with a `LOG_LEVEL` env var as the default; flags win over the env var.
- `print()` is fine *only* for the CLI's real output. Ruff T20 is ignored for `cli.py`, `__main__.py` and `scripts/**`.

**Batch / pipeline / scientific runs:** log enough to reproduce the run and to check it.
- **At start:** `run_id`, git SHA (+ dirty flag), tool/package versions, config (or its hash), input paths + sha256, random seed.
- **At end:** counts in / out / dropped-by-reason, per-stage wall time, output paths.
- Write the same facts to a `manifest.json` next to the outputs.
- Shape: one `run()` entrypoint that writes the start facts, runs the stages, then writes the end facts and `manifest.json`.

Long-running services may emit JSON logs to stdout (12-factor). Use stdlib logging + a JSON formatter, with one env switch (`LOG_FORMAT=json|text`), and bind a `trace_id`/`run_id` to every line via `contextvars` or a `LoggerAdapter`. Don't run two logging libraries in one service.

## Bash / hooks — quick reference

```bash
set -Eeuo pipefail
log() { printf '%s %-5s %s\n' "$(date -Is)" "$1" "${*:2}" >&2; }   # ISO time, level, stderr
trap 'log ERROR "line $LINENO: \"$BASH_COMMAND\" exited $?"' ERR

cp "$src" "$dst" || { log WARN "copy failed for $src; continuing with stale copy"; }
grep -q foo f 2>/dev/null || true   # why: f may not exist yet on first run; absence == no match
```

Claude Code hooks are a special case (rules verified against [the hooks docs](https://code.claude.com/docs/en/hooks), 2026-10-06):
- **On exit 0, stderr reaches only the debug log; nobody sees it.** Plain stdout goes to the model for UserPromptSubmit and SessionStart, and to the debug log for most other events. Hooks must exit fast.
- **To tell the user something on exit 0, print JSON `{"systemMessage": "..."}` to stdout.** It is shown to the user but not to the model, and on PreToolUse the tool call still proceeds. Verified live, it shows as `PreToolUse:Bash says: …`.
- **A fail-open path writes a `systemMessage` and also one line to a log file** (`~/.claude/logs/hooks.log`, format `ISO-ts LEVEL hook-name: msg`). Keep its regression test, feed it a real payload, and assert that the message is emitted. Patterns: `hooks/lib/guard-protected-dirs.sh` and its test `hooks/tests/test-guard-protected-dirs.sh`.
- **Debug chatter is opt-in.** Gate it with `HOOK_DEBUG=1` → `aa_ma_debug` (`hooks/lib/aa-ma-parse.sh`).

## Comments & docstrings

- **Docstrings on every public module, class and function**, in Google style (`Args:`, `Returns:`, `Raises:`). State constraints the signature can't show: units, side effects, idempotency, which HTTP verb (PUT vs PATCH), and thread safety.
- **Every magic number gets a name, a unit and a reason**, ideally with its source or a test that pins it:
  ```python
  LINE_TOL = 1.5  # pt; JS1 definition text puts "a)" markers 1.0 pt off their line's baseline
  MAX_FINDINGS = 200  # `check` output reaches an agent's context; the rest is counted, not printed
  ```
- **Suppressions carry a reason:** `# noqa: S105  # why: enum value, not a credential`. The same applies to `# nosec`, `# type: ignore[...]`, `|| true` and `2>/dev/null`.
- **TODOs are traceable:** `# TODO(#123): drop once upstream fixes X` or `# TODO(ADR-0014): …`. A bare `# TODO` is not allowed (Ruff TD).
- **Non-obvious design choices point to the record:** `# See ADR-0009` or `# See lessons.md L-1300`.
- **Delete commented-out code** (Ruff ERA). Git remembers it.
- **Deliberate shortcuts are marked `# ponytail: <ceiling>, <upgrade path>`.**
- **Don't** narrate (`# loop over rows`), leave section banners in short functions, or write docstrings that claim features the code doesn't have (e.g. "async queue" when there is no queue).

## Enforcement

- **Ruff:** merge `references/ruff-baseline.toml` into each project's `pyproject.toml`. If an existing repo has many pre-existing violations, put the noisy codes in `extend-ignore` tagged `# TODO(logging-std): burn down`, rather than mass-fixing them.
- **The PostToolUse `ruff-format.sh` hook** runs `ruff check --fix` on every edit. T201's fix is unsafe-only, so prints are reported, never deleted (verified on ruff 0.15.4). Hook failures are logged to `~/.claude/logs/hooks.log`.
- **Review checklist for a diff:**
  - grep the added lines for `except`, `|| true`, `2>/dev/null`, `continue` and `pass`, and check that each one logs, counts or has a `# why:`;
  - check that each new constant has a rationale;
  - check that each new public function has a docstring.

## Sources

Python [Logging HOWTO](https://docs.python.org/3/howto/logging.html) and [Cookbook](https://docs.python.org/3/howto/logging-cookbook.html) · [PEP 8 comments](https://peps.python.org/pep-0008/#comments) · [PEP 257](https://peps.python.org/pep-0257/) · [Google Python style §3.8, §3.10, §3.12](https://google.github.io/styleguide/pyguide.html) · [Google Shell style §3.1, §4](https://google.github.io/styleguide/shellguide.html) · [Ruff rules](https://docs.astral.sh/ruff/rules/) · [clig.dev](https://clig.dev/) · [12-factor logs](https://12factor.net/logs) · [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

# Python logging — detail and templates

## Entrypoint configuration (applications / CLIs only)

```python
"""Logging bootstrap for a CLI entrypoint."""

import logging
import os
import sys


def configure_logging(verbosity: int = 0, quiet: bool = False) -> None:
    """Configure root logging once, from main(). Never call from an importable module.

    Precedence: -q / -v flags > LOG_LEVEL env var > WARNING.

    Raises:
        SystemExit: if LOG_LEVEL is not a logging level name (fail fast, never guess).
    """
    level = os.getenv("LOG_LEVEL", "WARNING").upper()
    if level not in logging.getLevelNamesMapping():
        raise SystemExit(f"invalid LOG_LEVEL={level!r}; use DEBUG/INFO/WARNING/ERROR")
    if quiet:
        level = "ERROR"
    elif verbosity:
        level = "DEBUG" if verbosity > 1 else "INFO"
    logging.basicConfig(
        level=level,
        stream=sys.stderr,  # why: stdout is reserved for the program's data output
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    # Third-party chatter is capped at WARNING even when we run at DEBUG, and follows -q
    # up to ERROR. why max(): records propagate to root's handler regardless of root's
    # level, so a bare setLevel(WARNING) would leak library warnings through -q.
    cap = max(logging.WARNING, logging.getLogger().level)
    for noisy in ("httpx", "urllib3", "botocore"):
        logging.getLogger(noisy).setLevel(cap)
```

Libraries (packages other code imports) do only this, in the package `__init__.py`:

```python
logging.getLogger(__name__).addHandler(logging.NullHandler())
```

## Patterns

**Count-and-report skips.** This is the standard fix for `except: continue` (a fragment: it assumes `logger`, `subprocess`, `repos`, `commits` and `read_git_log` are in scope):

```python
from collections import Counter
skipped: Counter[str] = Counter()
for repo in repos:
    try:
        commits.extend(read_git_log(repo))
    except subprocess.TimeoutExpired:
        skipped["git_timeout"] += 1
        logger.warning("git log timed out for %s; skipping", repo)
    except subprocess.CalledProcessError as e:
        skipped["git_error"] += 1
        logger.warning("git log failed for %s (rc=%s); skipping", repo, e.returncode)
logger.info("read %d commits; skipped %s", len(commits), dict(skipped) or "none")
```

**Run context and manifest for batch or scientific jobs** (a fragment: the helpers and stage variables are yours):

```python
run = {
    "run_id": uuid.uuid4().hex[:12],
    "git_sha": git_sha(), "git_dirty": git_dirty(),
    "versions": {"python": platform.python_version(), "pkg": importlib.metadata.version("mypkg")},
    "seed": seed, "config_sha256": sha256(config_bytes),
    "inputs": [{"path": str(p), "sha256": sha256_file(p)} for p in inputs],
}
logger.info("run %(run_id)s start sha=%(git_sha)s seed=%(seed)s", run)
# … per stage: t0 = time.perf_counter(); …; run["stages"][name] = {"in": n_in, "out": n_out, "dropped": dict(dropped), "ms": …}
(out_dir / "manifest.json").write_text(json.dumps(run, indent=2))
logger.info("run %s done: %d in, %d out, dropped=%s, %.1fs", run["run_id"], n_in, n_out, dict(dropped), wall)
```

**Correlation ID on every line.** Use this for services and multi-step agents:

```python
"""Bind the current run_id to every log record."""

import contextvars
import logging

run_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="-")


class RunIdFilter(logging.Filter):
    """Stamp each record with the run_id of the current context."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add ``record.run_id``; never drops a record."""
        record.run_id = run_id_var.get()
        return True


# Attach to the *handler* (not a logger) in configure_logging() so records from every
# logger get it, and add %(run_id)s to the format string.
```

**Redaction.** Attach redaction **at the single bootstrap point** that every entrypoint (CLI, scripts, tests) goes through, never in just one CLI. Implement it as a `logging.Filter` that rewrites `record.msg`/`record.args` using a table of `(compiled_regex, replacement)`, e.g. bearer tokens, `://user:pass@`, emails. Test the table.

## Anti-patterns → fixes

| Anti-pattern | Fix | Ruff |
|---|---|---|
| `logger.info(f"x={x}")` | `logger.info("x=%s", x)` | G004 |
| `except Exception: pass` | narrow the type + log/count, or re-raise | S110, BLE001 |
| `except X: continue` | count + log (pattern above) | S112 |
| `logger.error(str(e))` in except | `logger.exception("context")` | TRY400 |
| `logger.exception(f"failed: {e}")` | drop `e`; the traceback has it | TRY401 |
| `logging.info(...)` (root) | module `logger` | LOG015 |
| `logging.basicConfig` in a library | move it to `main()` | — (review) |
| `print("debug", x)` in a library | `logger.debug` | T201 |
| Docstring claims behaviour that doesn't exist | make the docstring match the code | — (review) |
| Two logging libs (loguru + stdlib) in one service | pick one; bridge, then delete the other | — |

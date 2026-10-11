"""Logging configuration for aa_ma CLIs, with secret redaction at the handler.

Call `configure_logging()` once, from a CLI entrypoint only; library modules just use
`logging.getLogger(__name__)`. Records go to stderr (stdout stays for data), as text
by default or one JSON object per line with `LOG_FORMAT=json`.

Every record is masked by `SecretRedactingFormatter`, which sits on the handler, so it
covers child loggers, interpolated args, exception text and stack info alike. The
patterns come from `secret_patterns.tsv`, the same file the hook library
`claude-code/hooks/lib/aa-ma-log.sh` reads; a parity test keeps the two in step.
"""

import json
import logging
import os
import re
import sys
from importlib.resources import files
from typing import Literal

# Characters kept per masked text (≈8 KB): bounds regex work on hostile input.
MAX_CHARS = 8192
# Extra characters masked past the cap before truncating, so a secret that straddles
# the cut is masked whole instead of leaving an unmatched fragment in the log.
_CAP_OVERLAP = 256

_VERBOSITY_LEVELS = {
    -2: logging.CRITICAL,
    -1: logging.ERROR,
    0: logging.WARNING,
    1: logging.INFO,
}
_FAILED = "[redaction failed]"


def _load_rules() -> tuple[tuple[str, re.Pattern[str]], ...]:
    """Read `secret_patterns.tsv`: one tab-separated `<rule id>  <regex>` per non-comment line."""
    rules = []
    text = files("aa_ma").joinpath("secret_patterns.tsv").read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        rule_id, regex = line.split("\t")
        rules.append((rule_id, re.compile(regex)))
    if not rules:
        raise RuntimeError("secret_patterns.tsv holds no rules")
    return tuple(rules)


SECRET_RULES: tuple[tuple[str, re.Pattern[str]], ...] = _load_rules()
SECRET_PATTERNS: tuple[re.Pattern[str], ...] = tuple(p for _, p in SECRET_RULES)


def mask_secrets(text: str) -> str:
    """Return `text` capped at MAX_CHARS with each secret replaced by `[REDACTED:<rule id>]`.

    Rules apply in file order. Raises if a pattern fails; callers that must never leak
    (the formatter) catch that and fail closed.
    """
    window = text[: MAX_CHARS + _CAP_OVERLAP]
    for rule_id, pattern in SECRET_RULES:
        window = pattern.sub(f"[REDACTED:{rule_id}]", window)
    return window[:MAX_CHARS]


class SecretRedactingFormatter(logging.Formatter):
    """A Formatter whose output is masked; on any masking error it emits `[redaction failed]`."""

    def __init__(self, fmt: str | None = None, *, as_json: bool = False) -> None:
        """Format as `fmt` (logging %-style), or one JSON object per record when `as_json`."""
        super().__init__(fmt)
        self.as_json = as_json

    def format(self, record: logging.LogRecord) -> str:
        """Render the record, then mask it; fail closed by replacing the record's message."""
        try:
            if self.as_json:
                body = {
                    "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": mask_secrets(record.getMessage()),
                }
                if record.exc_info:
                    body["exc"] = mask_secrets(self.formatException(record.exc_info))
                return json.dumps(body)
            return mask_secrets(super().format(record))
        except Exception:  # noqa: BLE001  # why: any failure must turn into the fixed message, never a leak or a dropped record
            record.msg, record.args = _FAILED, None
            record.exc_info = record.exc_text = record.stack_info = None
            return (
                json.dumps({"level": record.levelname, "message": _FAILED})
                if self.as_json
                else _FAILED
            )


def configure_logging(
    verbosity: int = 0, fmt: Literal["text", "json"] | None = None
) -> None:
    """Send all logging to one redacting stderr handler on the root logger.

    Level: `verbosity` (count of -v minus count of -q) when non-zero, else `LOG_LEVEL`,
    else WARNING. Format: `fmt`, else `LOG_FORMAT`, else text. Replaces any root handlers.
    """
    problems = []
    if verbosity:
        level = _VERBOSITY_LEVELS.get(max(-2, min(verbosity, 2)), logging.DEBUG)
    else:
        raw = os.environ.get("LOG_LEVEL", "")
        level = (
            logging.getLevelNamesMapping().get(raw.upper(), logging.WARNING)
            if raw
            else logging.WARNING
        )
        if raw and raw.upper() not in logging.getLevelNamesMapping():
            problems.append(
                f"ignoring LOG_LEVEL={raw!r}: not a level name; using WARNING"
            )
    chosen = fmt or os.environ.get("LOG_FORMAT", "text").lower()
    if chosen not in ("text", "json"):
        problems.append(f"ignoring LOG_FORMAT={chosen!r}: use text or json")
        chosen = "text"
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        SecretRedactingFormatter(
            "%(levelname)s %(name)s: %(message)s", as_json=chosen == "json"
        )
    )
    logging.basicConfig(level=level, handlers=[handler], force=True)
    for problem in problems:
        logging.getLogger(__name__).warning(problem)

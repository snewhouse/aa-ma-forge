"""Tests for aa_ma.logsetup (M7.2): CLI logging config and secret redaction."""

import json
import logging
import subprocess
import time
from pathlib import Path

import pytest

from aa_ma import logsetup

ROOT = Path(__file__).resolve().parents[1]
LOG_SH = ROOT / "claude-code" / "hooks" / "lib" / "aa-ma-log.sh"

# why: token-shaped strings are assembled at runtime so no literal secret is committed
AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
GHP = "ghp_" + "a" * 36
ANT = "sk-ant-api03-" + "B" * 40
OPENAI = "sk-proj-" + "c" * 40
SLACK = "xoxb-" + "1234567890-abcdef"
JWT = "ey" + "J" * 20 + ".ey" + "K" * 20 + "." + "L" * 12
PEM = "-----BEGIN RSA " + "PRIVATE KEY-----"


@pytest.fixture
def stderr_logs(monkeypatch: pytest.MonkeyPatch):
    """Isolate the root logger; restore its handlers and level afterwards."""
    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)
    yield root
    root.handlers[:] = saved[0]
    root.setLevel(saved[1])


def _record(msg: str, *args: object) -> logging.LogRecord:
    return logging.LogRecord("aa_ma.t", logging.WARNING, __file__, 1, msg, args, None)


def test_patterns_load_from_the_shared_source() -> None:
    ids = [rule_id for rule_id, _ in logsetup.SECRET_RULES]
    assert ids[:2] == ["aws-access-token", "github-pat"]
    assert len(logsetup.SECRET_PATTERNS) == len(ids) >= 10
    assert ids.index("anthropic-api-key") < ids.index("openai-api-key")


@pytest.mark.parametrize(
    ("secret", "rule"),
    [
        (AWS, "aws-access-token"),
        (GHP, "github-pat"),
        (ANT, "anthropic-api-key"),
        (OPENAI, "openai-api-key"),
        (SLACK, "slack-token"),
        (JWT, "jwt"),
        (PEM, "private-key"),
    ],
)
def test_mask_secrets_replaces_with_rule_id(secret: str, rule: str) -> None:
    assert logsetup.mask_secrets(f"x {secret} y") == f"x [REDACTED:{rule}] y"


def test_near_misses_are_left_alone() -> None:
    text = "AKIA1234 ghp_short sk-ant-tiny xoxb- eyJhbGci"
    assert logsetup.mask_secrets(text) == text


def test_mask_secrets_caps_input() -> None:
    assert len(logsetup.mask_secrets("x" * 20000)) == logsetup.MAX_CHARS == 8192


def test_secret_straddling_the_cap_is_masked_not_left_as_a_fragment() -> None:
    out = logsetup.mask_secrets("x" * (logsetup.MAX_CHARS - 10) + GHP)
    assert len(out) <= logsetup.MAX_CHARS
    assert "ghp_" not in out


def test_formatter_masks_message_and_args() -> None:
    fmt = logsetup.SecretRedactingFormatter("%(message)s")
    out = fmt.format(_record("key=%s token=" + GHP, ANT))
    assert AWS not in out and GHP not in out and ANT not in out
    assert out == "key=[REDACTED:anthropic-api-key] token=[REDACTED:github-pat]"


def test_formatter_masks_exception_text() -> None:
    fmt = logsetup.SecretRedactingFormatter("%(message)s")
    try:
        raise ValueError(f"bad key {AWS}")
    except ValueError:
        rec = _record("boom")
        import sys

        rec.exc_info = sys.exc_info()
    out = fmt.format(rec)
    assert "Traceback" in out
    assert AWS not in out
    assert "[REDACTED:aws-access-token]" in out


def test_formatter_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        def sub(self, *_: object) -> str:
            raise RuntimeError("pattern exploded")

    monkeypatch.setattr(logsetup, "SECRET_RULES", (("boom", Boom()),))
    rec = _record("secret %s", AWS)
    out = logsetup.SecretRedactingFormatter("%(message)s").format(rec)
    assert AWS not in out
    assert rec.getMessage() == "[redaction failed]"


def test_child_logger_output_is_redacted(stderr_logs, capsys) -> None:
    logsetup.configure_logging()
    logging.getLogger("aa_ma.child.deeper").warning("leak %s", GHP)
    err = capsys.readouterr().err
    assert GHP not in err
    assert "[REDACTED:github-pat]" in err


@pytest.mark.parametrize(
    ("verbosity", "level"),
    [
        (0, logging.WARNING),
        (1, logging.INFO),
        (2, logging.DEBUG),
        (5, logging.DEBUG),
        (-1, logging.ERROR),
        (-3, logging.CRITICAL),
    ],
)
def test_verbosity_maps_to_level(stderr_logs, verbosity: int, level: int) -> None:
    logsetup.configure_logging(verbosity)
    assert stderr_logs.level == level


def test_log_level_env_applies_without_flags(stderr_logs, monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")
    logsetup.configure_logging()
    assert stderr_logs.level == logging.DEBUG


def test_flags_override_log_level_env(stderr_logs, monkeypatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    logsetup.configure_logging(-1)
    assert stderr_logs.level == logging.ERROR


def test_bad_log_level_env_warns_and_falls_back(
    stderr_logs, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "LOUD")
    logsetup.configure_logging()
    assert stderr_logs.level == logging.WARNING
    assert "LOG_LEVEL='LOUD'" in capsys.readouterr().err


def test_handler_writes_to_stderr_not_stdout(stderr_logs, capsys) -> None:
    logsetup.configure_logging()
    logging.getLogger("aa_ma.x").warning("to stderr")
    out = capsys.readouterr()
    assert out.out == ""
    assert "to stderr" in out.err


def test_json_format_is_one_redacted_object_per_line(
    stderr_logs, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    logsetup.configure_logging()
    logging.getLogger("aa_ma.j").warning('quote " and %s', AWS)
    line = capsys.readouterr().err.strip()
    obj = json.loads(line)
    assert obj["level"] == "WARNING"
    assert obj["logger"] == "aa_ma.j"
    assert obj["message"] == 'quote " and [REDACTED:aws-access-token]'


def test_fmt_argument_overrides_log_format_env(
    stderr_logs, monkeypatch, capsys
) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    logsetup.configure_logging(fmt="text")
    logging.getLogger("aa_ma.t").warning("plain")
    err = capsys.readouterr().err
    with pytest.raises(json.JSONDecodeError):
        json.loads(err)


# 100 KB adversarial inputs: long runs of each pattern's own classes and prefixes,
# never completing a match, so a backtracking blow-up would show as time.
ADVERSARIAL = [
    "A" * 100_000,
    "AKIA" * 25_000,
    "sk-" * 33_333,
    "sk-ant-" + "a" * 100_000 + "!",
    "ghp_" * 25_000,
    "xoxb-" * 20_000,
    "ey" + "a" * 100_000 + ".",
    "ey" + "a" * 50_000 + ".ey" + "b" * 50_000,
    "-----BEGIN " + " " * 100_000,
    "-----BEGIN" * 10_000,
]


@pytest.mark.parametrize("rule_id", [r for r, _ in logsetup.SECRET_RULES])
def test_each_pattern_is_linear_on_100kb_adversarial_input(rule_id: str) -> None:
    pattern = dict(logsetup.SECRET_RULES)[rule_id]
    start = time.perf_counter()
    for text in ADVERSARIAL:
        pattern.sub("", text)
    assert time.perf_counter() - start < 1.0, rule_id


PARITY_CORPUS = [
    "plain text, nothing to hide",
    f"aws={AWS} gh={GHP}",
    f"{ANT} then {OPENAI}",
    f"slack {SLACK}; jwt {JWT}",
    f"{PEM} trailing",
    "gho_" + "z" * 36,
    "ghu_" + "Q" * 36 + " ghs_" + "R" * 36,
    "github_pat_" + "a_" * 41,
    "glpat-" + "x" * 20,
    "sk_live_" + "9" * 24 + " rk_test_" + "8" * 30,
    "AIza" + "-" * 35,
    "AKIA1234 ghp_short sk-ant-tiny xoxb- eyJhbGci",
    "ASIA" + "Z" * 16 + AWS,
]


@pytest.mark.parametrize("text", PARITY_CORPUS)
def test_bash_and_python_mask_identically(text: str) -> None:
    proc = subprocess.run(
        ["bash", "-c", '. "$1"; mask_secrets "$2"', "_", str(LOG_SH), text],
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout.rstrip("\n") == logsetup.mask_secrets(text)

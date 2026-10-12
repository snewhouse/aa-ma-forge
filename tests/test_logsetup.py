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
    assert ids[:2] == ["aws-access-key", "github-token"]
    assert len(logsetup.SECRET_PATTERNS) == len(ids) >= 10
    # generic key=value rules run last, so a known token keeps its specific id
    assert ids[-3:] == ["url-credential", "generic-quoted", "generic-env"]


def test_rule_ids_match_the_report_gate_where_they_overlap() -> None:
    """One id vocabulary across the forge: analysis/secrets.py names the same secrets."""
    from aa_ma.analysis.secrets import PATTERNS

    log_ids = {rule_id for rule_id, _ in logsetup.SECRET_RULES}
    # bearer-token is log-only: report files rarely hold an HTTP header, CLI debug lines do
    assert log_ids - {"bearer-token"} <= {rule_id for rule_id, _ in PATTERNS}


@pytest.mark.parametrize(
    "line",
    ["broken-rule\t", "two-tabs\tab\tcd", "no-tab-at-all"],
    ids=["empty", "tab", "notab"],
)
def test_a_malformed_rule_line_is_refused(line: str) -> None:
    with pytest.raises(RuntimeError, match="secret_patterns.tsv"):
        logsetup._parse_rules(f"# header\nok\tabc\n{line}\n")


@pytest.mark.parametrize(
    ("secret", "rule"),
    [
        (AWS, "aws-access-key"),
        (GHP, "github-token"),
        (ANT, "sk-key"),
        (OPENAI, "sk-key"),
        (SLACK, "slack-token"),
        (JWT, "jwt"),
        ("PASSWORD=" + "hunter2hunter2", "generic-env"),
        ("secret: " + "s3cr3tvalue", "generic-env"),
        ("export API_KEY=" + '"abcdefgh12345678"', "generic-env"),
        ("PASSWORD=" + "'hunter2hunter2'", "generic-env"),
        ("token: " + '"abcdefghijk"', "generic-env"),
        ("--password " + "hunter2hunter2", "generic-env"),
        ("Authorization: Bearer " + "abcDEF123456ghiJKL789", "bearer-token"),
        ('"api_key": "' + "abcdefgh1234" + '"', "generic-quoted"),
    ],
)
def test_mask_secrets_replaces_with_rule_id(secret: str, rule: str) -> None:
    assert logsetup.mask_secrets(f"x {secret} y") == f"x [REDACTED:{rule}] y"


def test_near_misses_are_left_alone() -> None:
    text = "AKIA1234 ghp_short sk-ant-tiny xoxb- eyJhbGci token=short risk-assessment-for-module"
    assert logsetup.mask_secrets(text) == text


def test_private_key_body_is_masked_not_just_its_header() -> None:
    body = "MIIEow" + "A" * 60
    out = logsetup.mask_secrets(f"{PEM} {body} -----END RSA PRIVATE KEY----- tail")
    assert out == "[REDACTED:private-key-block] tail"


def test_a_cut_private_key_masks_the_base64_run_after_its_header() -> None:
    # Logs flatten newlines, so with no END marker the body runs to the first non-base64
    # character; over-masking the words that follow is the safe direction.
    assert (
        logsetup.mask_secrets(f"x {PEM} MIIE abc=; y")
        == "x [REDACTED:private-key-block]; y"
    )


@pytest.mark.parametrize("password", ["p@ss@word", "pa/ss"])
def test_url_credential_masks_a_password_holding_at_or_slash(password: str) -> None:
    out = logsetup.mask_secrets(f"https://user:{password}@db.example/x")
    assert out == "[REDACTED:url-credential]db.example/x"


def test_a_flag_followed_by_another_flag_is_not_a_password() -> None:
    assert logsetup.mask_secrets("--password --verbose") == "--password --verbose"


def test_url_credential_masks_userinfo_and_keeps_the_host() -> None:
    out = logsetup.mask_secrets("https://user:" + "pa55word" + "@db.example/x")
    assert out == "[REDACTED:url-credential]db.example/x"


def test_generic_env_keeps_the_prefix_before_the_key_word() -> None:
    # No unbounded prefix in the pattern (it would be O(n²)), so DB_ survives.
    assert (
        logsetup.mask_secrets("DB_PASSWORD=" + "hunter2hunter2")
        == "DB_[REDACTED:generic-env]"
    )


def test_a_known_token_after_a_key_name_keeps_its_specific_id() -> None:
    assert logsetup.mask_secrets(f"TOKEN={GHP}") == "TOKEN=[REDACTED:github-token]"


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
    assert out == "key=[REDACTED:sk-key] token=[REDACTED:github-token]"


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
    assert "[REDACTED:aws-access-key]" in out


def test_formatter_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        def sub(self, *_: object) -> str:
            raise RuntimeError("pattern exploded")

    monkeypatch.setattr(logsetup, "SECRET_RULES", (("boom", Boom()),))
    rec = _record("secret %s", AWS)
    out = logsetup.SecretRedactingFormatter("%(message)s").format(rec)
    assert AWS not in out
    assert rec.getMessage() == "[redaction failed]"


def test_json_fail_closed_record_keeps_the_normal_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Boom:
        def sub(self, *_: object) -> str:
            raise RuntimeError("pattern exploded")

    monkeypatch.setattr(logsetup, "SECRET_RULES", (("boom", Boom()),))
    out = logsetup.SecretRedactingFormatter(as_json=True).format(_record("x %s", AWS))
    obj = json.loads(out)
    assert set(obj) == {"ts", "level", "logger", "message"}
    assert obj["message"] == "[redaction failed]"


def test_child_logger_output_is_redacted(stderr_logs, capsys) -> None:
    logsetup.configure_logging()
    logging.getLogger("aa_ma.child.deeper").warning("leak %s", GHP)
    err = capsys.readouterr().err
    assert GHP not in err
    assert "[REDACTED:github-token]" in err


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
    assert obj["message"] == 'quote " and [REDACTED:aws-access-key]'


def test_json_format_keeps_masked_stack_info(stderr_logs, monkeypatch, capsys) -> None:
    monkeypatch.setenv("LOG_FORMAT", "json")
    logsetup.configure_logging()
    logging.getLogger("aa_ma.j").warning("with stack %s", AWS, stack_info=True)
    obj = json.loads(capsys.readouterr().err.strip())
    assert "Stack (most recent call last)" in obj["stack"]


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
    "-----BEGIN RSA PRIVATE KEY-----" + "A" * 100_000,
    "password" * 12_500,
    "x_password " * 9_000,
    '"token": "' * 10_000,
    "a://b:" * 16_000,
    "x://" + "u" * 50_000 + ":" + "p" * 50_000,
    "--password " * 9_000,
    "Bearer " * 14_000,
    'API_KEY="' * 11_000,
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
    "PASSWORD=hunter2hunter2 and Api-Key: abcdefgh123",
    '{"Token": "abcdefgh1234", "secret":"tiny"}',
    "postgres://u:pa55word@host/db and TOKEN=" + GHP,
    PEM + " MIIEowAAAA -----END RSA PRIVATE KEY----- after",
    'export API_KEY="abcdefgh12345678" && curl -H "Authorization: Bearer abcDEF123456ghiJKL789"',
    "mysql --password hunter2hunter2 --user x; https://u:p@ss@word@h/x",
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

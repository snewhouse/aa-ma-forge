"""Dependency audit, Dependabot and CI supply-chain hygiene (M8.4).

`uv audit` is experimental in uv 0.12.3 (A6), so the gate is pip-audit over a hashed
export of the lock. Every vulnerability ignore carries an ID, a why and an expiry date;
an expired ignore fails here, so a waiver cannot quietly become permanent.
"""

import datetime as dt
import re
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SECURITY_YML = ROOT / ".github" / "workflows" / "security.yml"
IGNORES = ROOT / ".pip-audit-ignore"
SETUP_UV = "astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7"
UV_VERSION = "0.12.3"
# One ignore per line: `<ID>  # expires: YYYY-MM-DD — <why>`.
IGNORE_LINE = re.compile(
    r"(?P<id>[A-Za-z0-9-]+)\s+# expires: (?P<date>\d{4}-\d{2}-\d{2}) — (?P<why>\S.*)"
)


def _jobs() -> dict:
    return yaml.safe_load(SECURITY_YML.read_text())["jobs"]


def test_deps_job_audits_the_hashed_lock_export() -> None:
    runs = "\n".join(s.get("run", "") for s in _jobs()["deps"]["steps"])
    assert "uv sync --locked" in runs
    assert "uv export --frozen --no-emit-workspace --no-emit-project -o req.txt" in runs
    assert "uv run pip-audit --disable-pip --require-hashes --strict -r req.txt" in runs
    assert "|| true" not in runs


def test_pip_audit_is_locked_in_the_dev_group() -> None:
    dev = tomllib.loads((ROOT / "pyproject.toml").read_text())["dependency-groups"][
        "dev"
    ]
    assert any(re.match(r"pip-audit\b", spec) for spec in dev)
    assert 'name = "pip-audit"' in (ROOT / "uv.lock").read_text()


def test_every_ignore_has_an_id_a_why_and_an_unexpired_date() -> None:
    today = dt.datetime.now(dt.UTC).date()
    for line in IGNORES.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        m = IGNORE_LINE.fullmatch(line.strip())
        assert m, f"malformed ignore: {line!r}"
        assert dt.date.fromisoformat(m["date"]) >= today, f"expired ignore: {line!r}"


def test_dependabot_watches_actions_and_uv_weekly_with_a_cooldown() -> None:
    cfg = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text())
    assert cfg["version"] == 2
    by_eco = {u["package-ecosystem"]: u for u in cfg["updates"]}
    assert set(by_eco) == {"github-actions", "uv"}
    for update in by_eco.values():
        assert update["schedule"]["interval"] == "weekly"
        assert update["cooldown"]["default-days"] == 7


def test_every_checkout_drops_its_credentials() -> None:
    for name, job in _jobs().items():
        for step in job["steps"]:
            if step.get("uses", "").startswith("actions/checkout@"):
                assert step.get("with", {}).get("persist-credentials") is False, name


def test_uv_comes_from_pinned_setup_uv_and_syncs_locked() -> None:
    for name, job in _jobs().items():
        runs = "\n".join(s.get("run", "") for s in job["steps"])
        assert "pip install uv" not in runs, name
        if "uv " not in runs:
            continue
        setups = [
            s
            for s in job["steps"]
            if s.get("uses", "").startswith("astral-sh/setup-uv@")
        ]
        assert [s["uses"] for s in setups] == [SETUP_UV], name
        assert setups[0]["with"]["version"] == UV_VERSION, name
        assert not re.search(r"uv sync(?! --locked)", runs), name

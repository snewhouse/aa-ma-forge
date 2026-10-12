"""gitleaks is the secret-scanning gate (M8.3).

Pins what the gate depends on: fingerprint-only ignores, each with a reason; no path
or regex allowlist; the CI job's verified binary and full-history scan; the staged
pre-commit hook. The live checks need a gitleaks binary and skip (visibly) without one.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
IGNORE = ROOT / ".gitleaksignore"
SECURITY_YML = ROOT / ".github" / "workflows" / "security.yml"
FINGERPRINT = re.compile(r"[0-9a-f]{40}:[^:\s]+:[a-z0-9-]+:\d+")
VERSION = "8.18.4"
TARBALL_SHA256 = "ba6dbb656933921c775ee5a2d1c13a91046e7952e9d919f9bac4cec61d628e7d"
SCAN = 'gitleaks detect --redact --exit-code 1 --log-opts="--all"'
GITLEAKS = shutil.which("gitleaks")
needs_gitleaks = pytest.mark.skipif(GITLEAKS is None, reason="gitleaks not on PATH")


def test_ignore_file_holds_only_fingerprints_each_with_a_why() -> None:
    lines = [ln.rstrip() for ln in IGNORE.read_text().splitlines()]
    entries = [(i, ln) for i, ln in enumerate(lines) if ln and not ln.startswith("#")]
    assert entries
    for i, entry in entries:
        assert FINGERPRINT.fullmatch(entry), entry
        assert lines[i - 1].startswith("# why: "), f"no '# why:' above {entry}"
    assert len({e for _, e in entries}) == len(entries)


def test_no_path_or_regex_allowlist() -> None:
    for name in (".gitleaks.toml", "gitleaks.toml"):
        assert not (ROOT / name).exists(), (
            f"{name}: allowlists hide whole classes; use fingerprints"
        )


def _job(name: str) -> dict:
    return yaml.safe_load(SECURITY_YML.read_text())["jobs"][name]


def test_ci_job_verifies_the_binary_and_scans_full_history() -> None:
    job = _job("gitleaks")
    checkout = job["steps"][0]
    assert checkout["with"]["fetch-depth"] == 0
    assert checkout["with"]["persist-credentials"] is False
    script = "\n".join(step.get("run", "") for step in job["steps"])
    assert f"v{VERSION}/gitleaks_{VERSION}_linux_x64.tar.gz" in script
    assert f"{TARBALL_SHA256}  gitleaks_{VERSION}_linux_x64.tar.gz" in script
    assert "sha256sum -c" in script
    assert SCAN in script
    assert "|| true" not in script


def test_precommit_runs_gitleaks_on_staged_changes_from_a_frozen_rev() -> None:
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    repo = next(
        r
        for r in config["repos"]
        if r["repo"] == "https://github.com/gitleaks/gitleaks"
    )
    assert re.fullmatch(r"[0-9a-f]{40}", repo["rev"])
    assert [h["id"] for h in repo["hooks"]] == ["gitleaks-system"]


def test_touched_job_skips_the_staged_hook_the_gitleaks_job_covers() -> None:
    step = next(
        s for s in _job("touched")["steps"] if "pre-commit run" in s.get("run", "")
    )
    assert step["env"]["SKIP"] == "gitleaks-system"


@needs_gitleaks
def test_full_history_scan_is_clean() -> None:
    proc = subprocess.run(
        SCAN.replace('"', "").split(),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


@needs_gitleaks
def test_a_canary_secret_in_a_throwaway_repo_is_caught(tmp_path: Path) -> None:
    # Assembled at runtime and committed only to tmp_path: never to this repo (A5).
    key = "AK" + "IA" + "Z7Q3" + "XW4N" + "R2PL" + "6TBV"
    git = [
        "git",
        "-C",
        str(tmp_path),
        "-c",
        "user.name=c",
        "-c",
        "user.email=c@example.invalid",
    ]
    subprocess.run([*git, "init", "-q"], check=True)
    (tmp_path / "settings.py").write_text(f'aws_access_key_id = "{key}"\n')
    subprocess.run([*git, "add", "settings.py"], check=True)
    subprocess.run([*git, "commit", "-qm", "canary"], check=True)
    proc = subprocess.run(
        [
            str(GITLEAKS),
            "detect",
            "--source",
            str(tmp_path),
            "--redact",
            "--exit-code",
            "1",
            "--no-banner",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr

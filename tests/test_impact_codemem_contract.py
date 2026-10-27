"""The codemem keys aa-ma-impact reads, from the REAL `codemem query co_changes` (CEO F2).

aa_ma never imports codemem (.importlinter); the coupling is this JSON. A codemem change
that renames or drops a key fails here, not as a silent pass in §6.7 fence 4.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CODEMEM = Path(sys.executable).with_name("codemem")


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(CODEMEM), *args, "--repo-root", str(repo)]
        if args[0] != "query"
        else [str(CODEMEM), "query", *args[1:]],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "r"
    repo.mkdir()
    for cmd in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "t@e.com"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", *cmd], cwd=repo, check=True)
    for i in range(5):
        (repo / "x.md").write_text(f"x{i}\n")
        (repo / "y.md").write_text(f"y{i}\n")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", f"c{i}"], cwd=repo, check=True)
    return repo


def test_co_changes_payload_has_the_keys_impact_reads(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CODEMEM_DB", str(tmp_path / "cm" / "index.db"))
    repo = _repo(tmp_path)
    assert _run(repo, "build").returncode == 0
    assert _run(repo, "refresh").returncode == 0
    assert _run(repo, "refresh-commits", "--limit", "500").returncode == 0
    p = _run(
        repo,
        "query",
        "co_changes",
        "--repo-root",
        str(repo),
        "--threshold",
        "5",
        "--min-ratio",
        "0.5",
        "--",
        "x.md",
        "y.md",
    )
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert set(out) == {"x.md", "y.md"}
    x = out["x.md"]
    assert x["error"] is None and x["target_commits"] == 5
    assert x["files"] == [{"path": "y.md", "count": 5, "ratio": 1.0}]
    assert x["stale"] is False and x["stale_reason"] is None


def test_an_edited_tracked_code_file_reads_stale(tmp_path, monkeypatch) -> None:
    """tree_sig covers tracked, indexable files (`git ls-files`): an edit to one is `dirty`."""
    monkeypatch.setenv("CODEMEM_DB", str(tmp_path / "cm" / "index.db"))
    repo = _repo(tmp_path)
    (repo / "z.py").write_text("Z = 1\n")
    subprocess.run(["git", "add", "z.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "z"], cwd=repo, check=True)
    assert _run(repo, "build").returncode == 0
    (repo / "z.py").write_text("Z = 2\n")
    p = _run(repo, "query", "co_changes", "--repo-root", str(repo), "--", "x.md")
    out = json.loads(p.stdout)
    assert out["stale"] is True and out["stale_reason"] == "dirty"

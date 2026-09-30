"""changed_since + sections_to_regenerate: a re-run regenerates only what changed (M5 AC2).

Section map decided by the 5.1 prototype (Ste, PASS): cited paths, cited dirs as prefixes at any
depth, fixed globs per section, any add/delete/rename → 03-structure, unknown sha → every section.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aa_ma.analysis import changed, cli, stamp
from aa_ma.analysis.models import Onboarding

from .conftest import commit_file, git, make_repo

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/analysis/valid/onboarding.json"


def _onboarding(sections: dict[str, list[str]]) -> Onboarding:
    doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
    doc["sections"] = sections
    return Onboarding.model_validate(doc)


@pytest.fixture
def two_commits(tmp_path: Path) -> tuple[Path, str]:
    repo = make_repo(
        tmp_path / "r",
        {"src/a.py": "a\n", "src/b.py": "b\n", "Makefile": "all:\n", "docs/x.md": "x\n"},
    )
    first = git(repo, "rev-parse", "HEAD")[:12]
    commit_file(repo, "src/a.py", "a2\n")
    return repo, first


SECTIONS = {
    "02-architecture": ["src/a.py"],
    "04-build-run-debug": ["Makefile"],
    "06-conventions-versioning-git": ["docs/"],
}


def test_changed_since_lists_the_committed_changes(two_commits) -> None:
    repo, first = two_commits
    assert changed.changed_since(repo, first) == [changed.Change("M", "src/a.py")]


def test_exactly_the_sections_whose_paths_changed(two_commits) -> None:
    repo, first = two_commits
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), changed.changed_since(repo, first))
    assert got == ["02-architecture"]


def test_an_unknown_sha_regenerates_every_section(two_commits) -> None:
    repo, _ = two_commits
    assert changed.changed_since(repo, "0123456789ab") is None
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), None)
    assert got == sorted(SECTIONS)


def test_a_cited_directory_matches_as_a_prefix(two_commits) -> None:
    repo, first = two_commits
    commit_file(repo, "docs/x.md", "x2\n")
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), changed.changed_since(repo, first))
    assert got == ["02-architecture", "06-conventions-versioning-git"]


def test_an_added_file_regenerates_structure_and_its_directory(two_commits) -> None:
    repo, first = two_commits
    commit_file(repo, "docs/new.md", "n\n")
    ch = changed.changed_since(repo, first)
    assert changed.Change("A", "docs/new.md") in ch
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), ch)
    assert got == ["02-architecture", "03-structure", "06-conventions-versioning-git"]


def test_a_rename_reports_both_paths(two_commits) -> None:
    repo, first = two_commits
    git(repo, "mv", "src/b.py", "src/c.py")
    git(repo, "commit", "-q", "-m", "mv")
    ch = changed.changed_since(repo, first)
    assert changed.Change("R", "src/b.py") in ch and changed.Change("R", "src/c.py") in ch


@pytest.mark.parametrize(
    ("section", "path"),
    [
        ("01-stack", "pyproject.toml"),
        ("01-stack", "uv.lock"),
        ("05-tests-ci", ".github/workflows/ci.yml"),
        ("05-tests-ci", "tests/test_a.py"),
    ],
)
def test_fixed_globs_cover_uncited_truth(section: str, path: str) -> None:
    ob = _onboarding({section: []})
    assert changed.sections_to_regenerate(ob, [changed.Change("M", path)]) == [section]


@pytest.mark.parametrize("bad", ["HEAD", "--output=x", "abc", "0123456789abX", "0123456789abc"])
def test_only_a_sha12_is_accepted(two_commits, bad: str) -> None:
    repo, _ = two_commits
    with pytest.raises(ValueError):
        changed.changed_since(repo, bad)


def test_cli_changed_since(two_commits, tmp_path: Path, capsys) -> None:
    repo, first = two_commits
    ob = tmp_path / "onboarding.json"
    ob.write_text(_onboarding(SECTIONS).model_dump_json(), encoding="utf-8")
    assert cli.main(["changed-since", first, "--repo", str(repo), "--onboarding", str(ob)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"known": True, "changed": [["M", "src/a.py"]], "regenerate": ["02-architecture"]}
    assert cli.main(["changed-since", "0123456789ab", "--repo", str(repo), "--onboarding", str(ob)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["known"] is False and out["regenerate"] == sorted(SECTIONS)


def test_cli_changed_since_refuses_a_bad_sha(two_commits, capsys) -> None:
    repo, _ = two_commits
    assert cli.main(["changed-since", "--output=x", "--repo", str(repo)]) == 2


def test_cli_changed_since_needs_a_repo(tmp_path: Path, capsys) -> None:
    (tmp_path / "plain").mkdir()
    assert cli.main(["changed-since", "0123456789ab", "--repo", str(tmp_path / "plain")]) == 2
    assert stamp.NOT_A_REPO in capsys.readouterr().err

"""changed_since + sections_to_regenerate: a re-run regenerates only what changed (M5 AC2).

Section map decided by the 5.1 prototype (Ste, PASS): cited paths, cited dirs as prefixes at any
depth, fixed globs per section, any add/delete/rename → 03-structure.md; sections are keyed by
deep-dive file name, as M1's onboarding fixture keys them, unknown sha → every section.
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
    return Onboarding.model_validate_json(json.dumps(doc))


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
    "02-architecture.md": ["src/a.py"],
    "04-build-run-debug.md": ["Makefile"],
    "06-conventions-versioning-git.md": ["docs/"],
}


def test_changed_since_lists_the_committed_changes(two_commits) -> None:
    repo, first = two_commits
    assert changed.changed_since(repo, first) == [changed.Change("M", "src/a.py")]


def test_exactly_the_sections_whose_paths_changed(two_commits) -> None:
    repo, first = two_commits
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), changed.changed_since(repo, first))
    assert got == ["02-architecture.md"]


def test_an_unknown_sha_regenerates_every_section(two_commits) -> None:
    repo, _ = two_commits
    assert changed.changed_since(repo, "0123456789ab") is None
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), None)
    assert got == sorted(SECTIONS)


def test_a_cited_directory_matches_as_a_prefix(two_commits) -> None:
    repo, first = two_commits
    commit_file(repo, "docs/x.md", "x2\n")
    got = changed.sections_to_regenerate(_onboarding(SECTIONS), changed.changed_since(repo, first))
    assert got == ["02-architecture.md", "06-conventions-versioning-git.md"]


def test_an_added_file_regenerates_structure_and_its_directory(two_commits) -> None:
    repo, first = two_commits
    commit_file(repo, "docs/new.md", "n\n")
    ch = changed.changed_since(repo, first)
    assert changed.Change("A", "docs/new.md") in ch
    got = changed.sections_to_regenerate(_onboarding({**SECTIONS, changed.STRUCTURE: []}), ch)
    assert got == ["02-architecture.md", "03-structure.md", "06-conventions-versioning-git.md"]
    # A pack without a structure section is never told to regenerate one (FP-W1).
    assert changed.STRUCTURE not in changed.sections_to_regenerate(_onboarding(SECTIONS), ch)


def test_a_dirty_tree_regenerates_every_section(two_commits) -> None:
    repo, first = two_commits
    (repo / "src/b.py").write_text("uncommitted\n", encoding="utf-8")  # CR-W2: diff sees commits only
    assert changed.changed_since(repo, first) is None


def test_section_names_are_the_deep_dive_file_names() -> None:
    templates = (
        Path(__file__).resolve().parents[2]
        / "claude-code/skills/understand-codebase/references/DEEPDIVE-TEMPLATES.md"
    ).read_text(encoding="utf-8")
    for name in (changed.STRUCTURE, *changed.SECTION_GLOBS):
        assert f"## `{name}`" in templates, name


@pytest.mark.parametrize("bad", ["../../.github/workflows/x.yml", "ONBOARDING.md", "3-x.md", "03-X.md"])
def test_section_keys_must_be_deep_dive_names(bad: str) -> None:
    with pytest.raises(ValueError):
        _onboarding({bad: []})


def test_a_rename_reports_both_paths(two_commits) -> None:
    repo, first = two_commits
    git(repo, "mv", "src/b.py", "src/c.py")
    git(repo, "commit", "-q", "-m", "mv")
    ch = changed.changed_since(repo, first)
    assert changed.Change("R", "src/b.py") in ch and changed.Change("R", "src/c.py") in ch


@pytest.mark.parametrize(
    ("section", "path"),
    [
        ("01-stack.md", "pyproject.toml"),
        ("01-stack.md", "uv.lock"),
        ("05-tests-ci.md", ".github/workflows/ci.yml"),
        ("05-tests-ci.md", "tests/test_a.py"),
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


def _pack(repo: Path, sections: dict[str, list[str]] = SECTIONS, sha12: str | None = None) -> Path:
    ob = repo / ".claude/onboarding/onboarding.json"
    ob.parent.mkdir(parents=True, exist_ok=True)
    doc = json.loads(_onboarding(sections).model_dump_json())
    if sha12:
        doc["stamp"]["sha12"] = sha12  # the pack a run at that commit would have written
    ob.write_text(json.dumps(doc), encoding="utf-8")
    return ob


def test_cli_changed_since(two_commits, tmp_path: Path, capsys) -> None:
    repo, first = two_commits
    ob = _pack(repo, sha12=first)
    assert cli.main(["changed-since", first, "--repo", str(repo), "--onboarding", str(ob)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"known": True, "changed": [["M", "src/a.py"]], "regenerate": ["02-architecture.md"]}
    ob = _pack(repo, sha12="0123456789ab")
    assert cli.main(["changed-since", "0123456789ab", "--repo", str(repo), "--onboarding", str(ob)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["known"] is False and out["regenerate"] == sorted(SECTIONS)


def test_cli_changed_since_refuses_a_bad_sha(two_commits, capsys) -> None:
    repo, _ = two_commits
    with pytest.raises(SystemExit) as exc:  # argparse: an option-looking sha is a usage error
        cli.main(["changed-since", "--output=x", "--repo", str(repo)])
    assert exc.value.code == 2
    assert cli.main(["changed-since", "--repo", str(repo), "--", "--output=x"]) == 2
    assert "not a 12-hex-digit sha" in capsys.readouterr().err


def test_cli_changed_since_needs_a_repo(tmp_path: Path, capsys) -> None:
    (tmp_path / "plain").mkdir()
    assert cli.main(["changed-since", "0123456789ab", "--repo", str(tmp_path / "plain")]) == 2
    assert stamp.NOT_A_REPO in capsys.readouterr().err


def _refused(repo: Path, first: str, ob: Path, capsys) -> bool:
    rc = cli.main(["changed-since", first, "--repo", str(repo), "--onboarding", str(ob)])
    return rc == 2 and "refused" in capsys.readouterr().err


def test_cli_refuses_a_pack_behind_a_symlinked_claude_dir(two_commits, tmp_path: Path, capsys) -> None:
    repo, first = two_commits  # SEC-1: a committed `.claude` symlink hides the pack from ls-files
    planted = tmp_path / "evil"
    _pack(planted, sha12=first)
    (repo / ".claude").symlink_to(planted / ".claude")
    assert _refused(repo, first, repo / ".claude/onboarding/onboarding.json", capsys)


def test_cli_refuses_a_pack_the_repo_tracks(two_commits, capsys) -> None:
    repo, first = two_commits
    ob = _pack(repo, sha12=first)
    git(repo, "add", "-f", "--", ".claude/onboarding/onboarding.json")
    git(repo, "commit", "-q", "-m", "ship a pack")
    assert _refused(repo, first, ob, capsys)


def test_cli_refuses_a_pack_outside_its_place(two_commits, tmp_path: Path, capsys) -> None:
    repo, first = two_commits
    elsewhere = tmp_path / "onboarding.json"
    elsewhere.write_text(_onboarding(SECTIONS).model_dump_json(), encoding="utf-8")
    assert _refused(repo, first, elsewhere, capsys)


def test_cli_refuses_a_pack_inside_a_claude_submodule(two_commits, tmp_path: Path, capsys) -> None:
    repo, first = two_commits  # regression S1: ls-files cannot see into a gitlink'd `.claude`
    inner = repo / ".claude"
    inner.mkdir()
    git(inner, "init", "-q")
    _pack(repo, sha12=first)
    git(inner, "add", "-A")
    git(inner, "commit", "-q", "-m", "planted pack")
    git(repo, "add", ".claude")  # an embedded repo: recorded as a gitlink, like a submodule
    git(repo, "commit", "-q", "-m", "gitlink")
    assert "160000" in git(repo, "ls-files", "-s", "--", ".claude")
    assert _refused(repo, first, repo / ".claude/onboarding/onboarding.json", capsys)


def test_cli_refuses_a_case_alias_of_a_tracked_pack(two_commits, capsys) -> None:
    repo, first = two_commits  # regression S2: one file on a case-insensitive filesystem
    alias = repo / ".Claude/Onboarding/onboarding.json"
    alias.parent.mkdir(parents=True)
    alias.write_text(_onboarding(SECTIONS).model_dump_json(), encoding="utf-8")
    git(repo, "add", "-f", "--", ".Claude")
    git(repo, "commit", "-q", "-m", "case alias")
    ob = _pack(repo, sha12=first)
    assert _refused(repo, first, ob, capsys)


def test_a_pack_stamped_dirty_regenerates_every_section(two_commits, capsys) -> None:
    repo, first = two_commits  # regression C2: it described edits the diff will never show
    ob = _pack(repo)
    doc = json.loads(ob.read_text(encoding="utf-8"))
    doc["stamp"].update(sha12=first, dirty=True)
    ob.write_text(json.dumps(doc), encoding="utf-8")
    assert cli.main(["changed-since", first, "--repo", str(repo), "--onboarding", str(ob)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["known"] is False and out["regenerate"] == sorted(SECTIONS)


def test_the_sha_must_be_the_packs_own_stamp(two_commits, capsys) -> None:
    repo, first = two_commits
    ob = _pack(repo)
    doc = json.loads(ob.read_text(encoding="utf-8"))
    doc["stamp"]["sha12"] = "0123456789ab"
    ob.write_text(json.dumps(doc), encoding="utf-8")
    assert _refused(repo, first, ob, capsys)


def test_section_names_are_ascii() -> None:
    with pytest.raises(ValueError):
        _onboarding({"٠٣-x.md": []})

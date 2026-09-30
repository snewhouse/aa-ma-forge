"""ground(): every backticked identifier and number in a cited claim occurs in the cited file (M5 AC1)."""

from __future__ import annotations

import json
from pathlib import Path

from aa_ma.analysis import cli, ground

from .conftest import make_repo


def _src(at: int, text: str, total: int = 100) -> str:
    lines = [f"# filler {i}" for i in range(1, total + 1)]
    lines[at - 1] = text
    return "\n".join(lines) + "\n"


def _ground(repo: Path, md: str) -> list[ground.Ungrounded]:
    doc = repo / "ONBOARDING.md"
    doc.write_text(md, encoding="utf-8")
    return ground.ground(doc, repo)


def test_a_name_eighty_lines_away_is_flagged(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": _src(80, "def foo_bar(): pass")})
    out = _ground(repo, "- `foo_bar` loads the config (`src/x.py:10`)\n")
    assert out == [ground.Ungrounded(md_line=1, citation="src/x.py:10", token="foo_bar")]


def test_a_name_within_twenty_lines_passes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": _src(25, "def foo_bar(): pass")})
    assert _ground(repo, "- `foo_bar` loads the config (`src/x.py:10`)\n") == []


def test_numbers_are_checked_in_the_same_window(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": _src(12, "TIMEOUT = 300")})
    assert _ground(repo, "- The default timeout is 300 seconds (`src/x.py:12`).\n") == []
    out = _ground(repo, "- The default timeout is 500 seconds (`src/x.py:12`).\n")
    assert [u.token for u in out] == ["500"]
    far = make_repo(tmp_path / "far", {"src/x.py": _src(80, "TIMEOUT = 300")})
    assert [u.token for u in _ground(far, "- Timeout is 300 (`src/x.py:12`).\n")] == ["300"]


def test_a_unit_without_a_citation_is_not_a_claim(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": "pass\n"})
    assert _ground(repo, "- `ghost` does 42 things.\n\nPlain prose with 7 numbers.\n") == []


def test_a_bare_path_citation_searches_the_whole_file(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": _src(95, "def late(): pass")})
    assert _ground(repo, "- `late` is defined in `src/x.py`.\n") == []
    assert [u.token for u in _ground(repo, "- `early` is defined in `src/x.py`.\n")] == ["early"]


def test_one_sentence_per_unit_in_prose(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": _src(5, "def real(): pass")})
    md = "The `ghost` helper is uncited. The `real` helper lives in `src/x.py:5`.\n"
    assert _ground(repo, md) == []


def test_any_cited_file_in_the_unit_can_ground_a_token(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"a.py": "def one(): pass\n", "b.py": "def two(): pass\n"})
    assert _ground(repo, "- `one` calls `two` (`a.py:1`, `b.py:1`)\n") == []


def test_a_missing_cited_file_is_flagged(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": "pass\n"})
    out = _ground(repo, "- `thing` lives in `src/gone.py:3`\n")
    assert out == [ground.Ungrounded(md_line=1, citation="src/gone.py:3", token="src/gone.py")]


def test_a_citation_that_leaves_the_repo_is_never_read(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("def secret_name(): pass\n", encoding="utf-8")
    repo = make_repo(tmp_path / "r", {"src/x.py": "pass\n"})
    (repo / "link.py").symlink_to(outside)
    out = _ground(repo, "- `secret_name` is in `link.py:1`\n")
    assert [u.token for u in out] == ["link.py"]


def test_code_fences_and_list_markers_are_not_claims(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": "def f(): pass\n"})
    md = "```\n`nope` in `src/x.py:1` 99\n```\n1. `f` is in `src/x.py:1`\n"
    assert _ground(repo, md) == []


def test_version_like_numbers_inside_words_are_ignored(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"pyproject.toml": 'version = "0.16.0"\n'})
    assert _ground(repo, "- Released as v0.16.0 (`pyproject.toml:1`)\n") == []


def test_cited_paths_include_files_and_directories(tmp_path: Path) -> None:
    repo = make_repo(tmp_path / "r", {"src/a/x.py": "pass\n", "README.md": "hi\n"})
    md = "- `src/a/x.py:1` and `README.md` under `src/a/`; `not/a/path.py` and `name`\n"
    assert ground.cited_paths(md, repo) == ["README.md", "src/a/", "src/a/x.py"]


def test_cli_ground_exit_codes(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": _src(80, "def foo_bar(): pass")})
    doc = repo / "ONBOARDING.md"
    doc.write_text("- `foo_bar` (`src/x.py:10`)\n", encoding="utf-8")
    assert cli.main(["ground", str(doc), "--repo", str(repo)]) == 1
    out = capsys.readouterr().out
    assert "1" in out and "foo_bar" in out and "src/x.py:10" in out
    doc.write_text("- `foo_bar` (`src/x.py:80`)\n", encoding="utf-8")
    assert cli.main(["ground", str(doc), "--repo", str(repo)]) == 0


def test_cli_ground_cited_prints_the_section_map_entry(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path / "r", {"src/x.py": "pass\n"})
    doc = repo / "02-architecture.md"
    doc.write_text("- see `src/x.py:1` and `src/`\n", encoding="utf-8")
    assert cli.main(["ground", str(doc), "--repo", str(repo), "--cited"]) == 0
    assert json.loads(capsys.readouterr().out) == ["src/", "src/x.py"]

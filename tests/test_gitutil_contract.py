"""One contract for both git helpers: ``aa_ma.gitutil`` and its twin ``codemem.gitutil``.

aa_ma never imports codemem (.importlinter), so the helper exists twice. Every behaviour
test runs against both copies, and the last tests pin the two sources to each other.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import os
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
TWINS = {
    "aa_ma.gitutil": ROOT / "src/aa_ma/gitutil.py",
    "codemem.gitutil": ROOT / "packages/codemem-mcp/src/codemem/gitutil.py",
}
# Names a file in the fixture repo can carry that a naive caller would mangle.
AWKWARD_NAMES = ["plain.txt", "with space.txt", "new\nline.txt", "--output=x", "*.txt"]


@pytest.fixture(params=sorted(TWINS))
def impl(request: pytest.FixtureRequest) -> ModuleType:
    return importlib.import_module(request.param)


def _raw_git(repo: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    proc = subprocess.run(  # why: fixed `git` argv in a test fixture
        [
            "git",
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.com",
            *args,
        ],  # why: `git` from PATH, as in every git test here
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _make_repo(path: Path, names: list[str]) -> Path:
    path.mkdir()
    _raw_git(path, "init", "-q", "-b", "main")
    for name in names:
        (path / name).write_text(name)
    _raw_git(path, "add", "-A")
    _raw_git(path, "commit", "-q", "-m", "init")
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    return _make_repo(tmp_path / "repo", AWKWARD_NAMES)


def test_env_scrubbed_git_dir_does_not_redirect(
    impl: ModuleType, repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = _make_repo(tmp_path / "other", ["o.txt"])
    other_head = _raw_git(other, "rev-parse", "HEAD").strip()
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    head = impl.git(["rev-parse", "HEAD"], repo).strip()
    assert head != other_head
    monkeypatch.delenv("GIT_DIR")
    monkeypatch.delenv("GIT_WORK_TREE")
    assert head == _raw_git(repo, "rev-parse", "HEAD").strip()


def test_child_env_has_lc_all_c_and_no_git_vars(
    impl: ModuleType, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LC_ALL", "de_DE.UTF-8")
    monkeypatch.setenv("GIT_CANARY_FOR_TEST", "leak")
    # why: a `!` alias runs a shell child of git, so `env` shows what git was given.
    out = impl.git(["-c", "alias.envdump=!env", "envdump"], repo)
    lines = out.splitlines()
    assert "LC_ALL=C" in lines
    assert not any(line.startswith("GIT_CANARY_FOR_TEST=") for line in lines)


def test_non_zero_exit_raises_with_stderr(impl: ModuleType, repo: Path) -> None:
    with pytest.raises(impl.GitError, match="no-such-subcommand") as info:
        impl.git(["no-such-subcommand"], repo)
    assert info.value.returncode not in (0, None)
    assert "no-such-subcommand" in info.value.stderr


def test_timeout_raises(impl: ModuleType, repo: Path) -> None:
    # why: no real git call finishes in 1 ns, and killing git leaves no grandchild
    # holding the pipes (a `!sleep` alias would make the test wait out the sleep).
    with pytest.raises(impl.GitError, match="timed out") as info:
        impl.git(["rev-parse", "HEAD"], repo, timeout=1e-9)
    assert info.value.returncode is None


def test_args_must_be_a_list_not_a_string(impl: ModuleType, repo: Path) -> None:
    with pytest.raises(TypeError):
        impl.git("status", repo)


def test_default_timeout_is_ten_seconds(impl: ModuleType) -> None:
    assert inspect.signature(impl.git).parameters["timeout"].default == 10.0


@pytest.mark.parametrize("ref", ["HEAD", "main"])
def test_verify_ref_accepts_branch_and_head(
    impl: ModuleType, repo: Path, ref: str
) -> None:
    sha = _raw_git(repo, "rev-parse", "HEAD").strip()
    assert impl.verify_ref(ref, repo) == sha


def test_verify_ref_accepts_a_short_sha(impl: ModuleType, repo: Path) -> None:
    sha = _raw_git(repo, "rev-parse", "HEAD").strip()
    assert impl.verify_ref(sha[:10], repo) == sha


@pytest.mark.parametrize("ref", ["--output=x", "-h", "HEAD^{tree}", "nope", ""])
def test_verify_ref_rejects_options_non_commits_and_unknowns(
    impl: ModuleType, repo: Path, ref: str
) -> None:
    before = sorted(p.name for p in repo.iterdir())
    with pytest.raises(impl.GitError, match="not a commit"):
        impl.verify_ref(ref, repo)
    assert sorted(p.name for p in repo.iterdir()) == before


def test_verify_ref_rejects_a_blob(impl: ModuleType, repo: Path) -> None:
    blob = _raw_git(repo, "rev-parse", "HEAD:plain.txt").strip()
    with pytest.raises(impl.GitError, match="not a commit"):
        impl.verify_ref(blob, repo)


def test_paths_go_after_double_dash_and_are_literal(
    impl: ModuleType, repo: Path
) -> None:
    before = sorted(p.name for p in repo.iterdir())
    out = impl.git(["ls-files", "-z"], repo, paths=["--output=x", "*.txt"])
    assert sorted(impl.split_z(out)) == ["*.txt", "--output=x"]
    assert sorted(p.name for p in repo.iterdir()) == before


def test_split_z_round_trips_awkward_names(impl: ModuleType, repo: Path) -> None:
    assert sorted(impl.split_z(impl.git(["ls-files", "-z"], repo))) == sorted(
        AWKWARD_NAMES
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("a\0", ["a"]),
        ("a\0b c\0", ["a", "b c"]),
        ("a\0b", ["a", "b"]),
        ("x\ny\0", ["x\ny"]),
    ],
)
def test_split_z_cases(impl: ModuleType, raw: str, expected: list[str]) -> None:
    assert impl.split_z(raw) == expected


def _public(mod: ModuleType) -> dict[str, str]:
    return {
        name: str(inspect.signature(obj))
        if callable(obj) and not inspect.isclass(obj)
        else type(obj).__name__
        for name in mod.__all__
        for obj in [getattr(mod, name)]
    }


def test_twins_export_the_same_names_and_signatures() -> None:
    a, b = (importlib.import_module(name) for name in sorted(TWINS))
    assert a.__all__ == b.__all__
    assert _public(a) == _public(b)


def _body_without_module_docstring(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
    ):
        tree.body = tree.body[1:]
    return ast.dump(tree)


def test_twins_are_identical_but_for_the_module_docstring() -> None:
    a, b = (_body_without_module_docstring(path) for path in TWINS.values())
    assert a == b, "aa_ma/gitutil.py and codemem/gitutil.py drifted; edit both"


@pytest.mark.parametrize("name", sorted(TWINS))
def test_docstring_names_the_twin_and_this_test(name: str) -> None:
    doc = importlib.import_module(name).__doc__ or ""
    twin = next(other for other in TWINS if other != name)
    assert twin in doc
    assert "tests/test_gitutil_contract.py" in doc

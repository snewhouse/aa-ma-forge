"""run_approved: repo-controlled commands, never through a shell (M2 AC6).

The refuse list and offline env are best-effort (a script can still do anything) — these tests pin
what the gate itself promises: no shell, installers and interpreter escapes refused, a minimal
offline env, stdin closed, and a timeout that takes the whole process group down."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path

import pytest

from aa_ma.analysis.run import OFFLINE_ENV, run_approved

from .conftest import FAKE_TOKEN, stub_bin
from .test_secrets import OPAQUE, stub  # noqa: F401  (stub: the gitleaks fixture)


@pytest.fixture
def stubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A dir of stub commands placed first on PATH (MINIMAL keeps the parent's PATH)."""
    d = tmp_path / "bin"
    d.mkdir()
    monkeypatch.setenv("PATH", f"{d}{os.pathsep}{os.environ['PATH']}")
    return d


def statuses(checks) -> list[str]:
    return [c.status for c in checks]


def test_installer_is_refused(tmp_path: Path) -> None:
    [check] = run_approved(["uv sync"], tmp_path)
    assert (check.command, check.status) == ("uv sync", "refused")


@pytest.mark.parametrize(
    "command",
    [
        "env UV_OFFLINE=0 uv run x",
        "UV_OFFLINE=0 uv run x",
        "sudo make",
        "/usr/bin/sudo make",
        'bash -c "echo hi"',
        "sh -c ls",
        'python -c "print(1)"',
        "python3.12 -c 1",
        "node -e 1",
        "python -m pip install x",
        "uvx x",
        "pnpm dlx x",
        "npm ci",
        "curl https://example.invalid",
        "git clone x",
        "make install",
        # §6.8 security review (2.8): joined flags, more interpreters, launchers, fetch-by-URL
        "python3 -Ic 'print(1)'",
        'python3 -c"print(1)"',
        "python3 -mpip install x",
        "nodejs -e 1",
        "node -p 1",
        "perl -E 1",
        "awk 'BEGIN{}'",
        "deno run -A https://example.invalid/x.ts",
        "git -c alias.t=!id t",
        "uv run python -c 1",
        "npm exec x",
        "make -f ../x",
        "yarn",
        "pip3.12 install x",
        "timeout 5 sh -c id",
        "xargs sh",
        "nice make",
        "setsid x",
        "busybox sh",
    ],
)
def test_bypass_is_refused(command: str, tmp_path: Path) -> None:
    assert statuses(run_approved([command], tmp_path)) == ["refused"]


def test_control_and_bidi_characters_are_refused(tmp_path: Path) -> None:
    assert statuses(run_approved(["pytest ‮txt", "pytest \x07"], tmp_path)) == [
        "refused",
        "refused",
    ]


def test_refusal_is_token_anchored(stubs: Path, tmp_path: Path) -> None:
    stub_bin(stubs, "pytest", "exit 0")
    assert statuses(run_approved(["pytest tests/pipeline"], tmp_path)) == ["verified"]


def test_child_env_is_minimal_and_offline(
    stubs: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", FAKE_TOKEN)
    out = tmp_path / "env.txt"
    stub_bin(stubs, "pytest", f"env > '{out}'")
    assert statuses(run_approved(["pytest"], tmp_path)) == ["verified"]
    env = dict(
        line.split("=", 1) for line in out.read_text().splitlines() if "=" in line
    )
    assert "GITHUB_TOKEN" not in env
    assert set(env) - {"PWD", "SHLVL", "_"} <= {
        "PATH",
        "HOME",
        "LANG",
        "TMPDIR",
        *OFFLINE_ENV,
    }
    assert {k: env.get(k) for k in OFFLINE_ENV} == OFFLINE_ENV


def test_offline_env_is_the_contract_set() -> None:
    assert OFFLINE_ENV == {
        "UV_OFFLINE": "1",
        "UV_NO_SYNC": "1",
        "UV_PYTHON_DOWNLOADS": "never",
        "PIP_NO_INDEX": "1",
        "npm_config_offline": "true",
        "YARN_ENABLE_NETWORK": "0",
        "COREPACK_ENABLE_NETWORK": "0",
        "CARGO_NET_OFFLINE": "true",
        "GOPROXY": "off",
        "GOTOOLCHAIN": "local",
        "GOFLAGS": "-mod=readonly",
    }


def test_stdin_is_devnull(stubs: Path, tmp_path: Path) -> None:
    out = tmp_path / "stdin.txt"
    stub_bin(stubs, "pytest", f"readlink /proc/$$/fd/0 > '{out}'")
    run_approved(["pytest"], tmp_path)
    assert out.read_text().strip() == "/dev/null"


def _alive(pid: int) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return False
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


def test_timeout_kills_the_process_group(stubs: Path, tmp_path: Path) -> None:
    pidfile = tmp_path / "grandchild.pid"
    stub_bin(stubs, "pytest", f"sleep 60 &\necho $! > '{pidfile}'\nsleep 60")
    [check] = run_approved(["pytest"], tmp_path, timeout=1)
    assert check.status == "timeout"
    pid = int(pidfile.read_text())
    deadline = time.monotonic() + 3
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(pid)


def test_and_chain_runs_parts_in_order_and_refuses_each(
    stubs: Path, tmp_path: Path
) -> None:
    stub_bin(stubs, "pytest", "exit 0")
    checks = run_approved(["pytest -q && uv sync"], tmp_path)
    assert [(c.command, c.status) for c in checks] == [
        ("pytest -q", "verified"),
        ("uv sync", "refused"),
    ]


def test_parts_after_a_failure_are_not_run(stubs: Path, tmp_path: Path) -> None:
    stub_bin(stubs, "tox", "exit 3")
    stub_bin(stubs, "pytest", "exit 0")
    checks = run_approved(["tox && pytest"], tmp_path)
    assert statuses(checks) == ["failed", "not_run"]
    assert "earlier part failed" in checks[1].note


@pytest.mark.parametrize(
    "command",
    [
        "pytest | tee x",
        "pytest; ls",
        "pytest > out",
        "pytest < in",
        "echo `id`",
        "echo $(id)",
    ],
)
def test_compound_commands_are_not_run(command: str, tmp_path: Path) -> None:
    [check] = run_approved([command], tmp_path)
    assert (check.command, check.status) == (command, "not_run")
    assert "compound" in check.note


def test_missing_command_fails(tmp_path: Path) -> None:
    assert statuses(run_approved(["vitest run"], tmp_path)) == ["failed"]


def test_note_is_last_40_lines_redacted(stubs: Path, tmp_path: Path) -> None:
    stub_bin(
        stubs,
        "pytest",
        f"i=1; while [ $i -le 100 ]; do echo line$i; i=$((i+1)); done; echo key {FAKE_TOKEN}",
    )
    [check] = run_approved(["pytest"], tmp_path)
    lines = check.note.splitlines()
    assert len(lines) == 40
    assert lines[0] == "line62"
    assert FAKE_TOKEN not in check.note
    assert "[REDACTED:" in lines[-1]


@pytest.mark.parametrize(
    "command",
    [
        "python -m pytest -q",
        "python -Werror -m pytest",
        "python -X dev -m pytest",
        "uv run pytest -x",
        "uv run python -m pytest",
        "make test",
        "make -j4 check",
        "npm test",
        "npm run lint",
        "pnpm test",
        "yarn test",
        "bun test",
        "cargo test --features fetch",
        "go test ./...",
        "tox -e py312",
        "node --test",
        "ruff check .",
        "mypy src",
        # check-only formatter forms and runner flags the strict grammar keeps
        "ruff format --check src",
        "black --check .",
        "cargo fmt --check",
        "pytest -q -x -k 'not slow' tests/test_a.py::test_b",
        "go test -run TestFoo -count=1 ./...",
        "tsc --noEmit",
        "vitest run",
    ],
)
def test_ordinary_test_commands_pass_the_gate(
    command: str, stubs: Path, tmp_path: Path
) -> None:
    stub_bin(stubs, command.split()[0], "exit 0")
    assert statuses(run_approved([command], tmp_path)) == ["verified"]


@pytest.mark.skipif(shutil.which("setsid") is None, reason="needs util-linux setsid")
def test_an_escaped_grandchild_cannot_hang_the_runner(
    stubs: Path, tmp_path: Path
) -> None:
    """setsid() leaves the process group, survives the kill, and keeps stdout open."""
    pidfile = tmp_path / "escaper.pid"
    stub_bin(
        stubs,
        "pytest",
        f"setsid sh -c 'echo $$ > {pidfile}; exec sleep 30' &\nsleep 30",
    )
    t0 = time.monotonic()
    [check] = run_approved(["pytest"], tmp_path, timeout=1)
    elapsed = time.monotonic() - t0
    try:
        os.kill(int(pidfile.read_text()), 9)
    except (FileNotFoundError, ProcessLookupError, ValueError):
        pass
    assert check.status == "timeout"
    assert elapsed < 15


def test_relative_path_entries_never_reach_the_child(
    stubs: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With `.` or an empty entry on PATH, a repo-local ./make would shadow the real one."""
    monkeypatch.setenv(
        "PATH", f"{stubs}{os.pathsep}.{os.pathsep}{os.pathsep}/usr/bin{os.pathsep}/bin"
    )
    out = tmp_path / "path.txt"
    stub_bin(stubs, "pytest", f"echo \"$PATH\" > '{out}'")
    run_approved(["pytest"], tmp_path)
    entries = out.read_text().strip().split(os.pathsep)
    assert entries and all(os.path.isabs(e) for e in entries)


def test_notes_pass_the_full_secret_gate(
    tmp_path: Path, stub: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A token only gitleaks knows (the regex set does not) is redacted before the note is returned."""
    monkeypatch.setenv("STUB_MODE", "find")
    bindir = tmp_path / "cmds"
    bindir.mkdir()
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ['PATH']}")
    stub_bin(bindir, "pytest", f"echo 'value {OPAQUE} end'")
    [check] = run_approved(["pytest"], tmp_path)
    assert check.status == "verified"
    assert OPAQUE not in check.note


@pytest.mark.parametrize(
    "command",
    [
        # §6.8 re-run: denylist bypasses — under the allowlist none of these is executed
        "uv run --python 3.12 python -c 1",
        "uv run --with requests python -c 1",
        "python3 --check-hash-based-pycs default -c 1",
        "node -r fs -e 1",
        "php -r 1",
        "deno eval 1",
        "poetry run x",
        "pdm run x",
        "hatch run x",
        "pipenv run x",
        "bun x cowsay",
        "pnpm exec x",
        "yarn exec x",
        "git push",
        "git submodule update --init",
        "git status",
        "/usr/bin/time ls",
        "strace ls",
        "ipython -c 1",
        "ts-node -e 1",
        "tcsh",
        "make --eval=x all",
        "make -f ../x",
        "npm run https://example.invalid/x",
        "ls",
        # §6.8 round 3: a path in argv[0], and options that carry code, fetch or rewrite the tree
        "./ruff check .",
        "/tmp/x/pytest",
        "cargo test --config target.x.runner=[]",
        "node --test --import=data:text/javascript,1",
        "node --test --inspect=0.0.0.0:9229",
        "pylint --init-hook=x",
        "python -m pylint --init-hook=x",
        "go test -exec x ./...",
        "go vet -vettool=x",
        "tox exec -e py -- sh -c id",
        "tox -x testenv.commands=x",
        "yarn run node -e 1",
        "npm test --node-options=x",
        "npm test --registry=http://example.invalid",
        "pytest -p plugin",
        "pytest --rootdir=/",
        "pytest ../outside",
        "pytest /etc",
        "black .",
        "ruff format .",
        "ruff check --fix .",
        "cargo fmt",
        "eslint --fix .",
    ],
)
def test_anything_off_the_allowlist_is_never_executed(
    command: str, stubs: Path, tmp_path: Path
) -> None:
    marker = tmp_path / "ran"
    stub_bin(stubs, command.split()[0].rsplit("/", 1)[-1], f"touch '{marker}'")
    [check, *_] = run_approved([command], tmp_path)
    assert check.status in ("not_run", "refused")
    assert not marker.exists()


def test_the_command_text_is_scrubbed_too(tmp_path: Path) -> None:
    [check] = run_approved([f"pytest --token {FAKE_TOKEN}"], tmp_path, timeout=5)
    assert FAKE_TOKEN not in check.command

"""run_approved: repo-controlled commands, never through a shell (M2 AC6).

The refuse list and offline env are best-effort (a script can still do anything) — these tests pin
what the gate itself promises: no shell, installers and interpreter escapes refused, a minimal
offline env, stdin closed, and a timeout that takes the whole process group down."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from aa_ma.analysis.run import OFFLINE_ENV, run_approved

FAKE_TOKEN = (
    "gh" + "p_" + "Z9" * 18
)  # assembled at runtime; matches the github-token rule


@pytest.fixture
def stubs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A dir of stub commands placed first on PATH (MINIMAL keeps the parent's PATH)."""
    d = tmp_path / "bin"
    d.mkdir()
    monkeypatch.setenv("PATH", f"{d}{os.pathsep}{os.environ['PATH']}")
    return d


def stub(bindir: Path, name: str, body: str) -> None:
    p = bindir / name
    p.write_text("#!/bin/sh\n" + body + "\n", encoding="utf-8")
    p.chmod(0o755)


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
    stub(stubs, "pytest", "exit 0")
    assert statuses(run_approved(["pytest tests/pipeline"], tmp_path)) == ["verified"]


def test_child_env_is_minimal_and_offline(
    stubs: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", FAKE_TOKEN)
    out = tmp_path / "env.txt"
    stub(stubs, "envdump", f"env > '{out}'")
    assert statuses(run_approved(["envdump"], tmp_path)) == ["verified"]
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
    stub(stubs, "whatstdin", f"readlink /proc/$$/fd/0 > '{out}'")
    run_approved(["whatstdin"], tmp_path)
    assert out.read_text().strip() == "/dev/null"


def _alive(pid: int) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return False
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


def test_timeout_kills_the_process_group(stubs: Path, tmp_path: Path) -> None:
    pidfile = tmp_path / "grandchild.pid"
    stub(stubs, "spawn", f"sleep 60 &\necho $! > '{pidfile}'\nsleep 60")
    [check] = run_approved(["spawn"], tmp_path, timeout=1)
    assert check.status == "timeout"
    pid = int(pidfile.read_text())
    deadline = time.monotonic() + 3
    while _alive(pid) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(pid)


def test_and_chain_runs_parts_in_order_and_refuses_each(
    stubs: Path, tmp_path: Path
) -> None:
    stub(stubs, "pytest", "exit 0")
    checks = run_approved(["pytest -q && uv sync"], tmp_path)
    assert [(c.command, c.status) for c in checks] == [
        ("pytest -q", "verified"),
        ("uv sync", "refused"),
    ]


def test_parts_after_a_failure_are_not_run(stubs: Path, tmp_path: Path) -> None:
    stub(stubs, "boom", "exit 3")
    stub(stubs, "pytest", "exit 0")
    checks = run_approved(["boom && pytest"], tmp_path)
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
    assert statuses(run_approved(["no-such-command-xyz"], tmp_path)) == ["failed"]


def test_note_is_last_40_lines_redacted(stubs: Path, tmp_path: Path) -> None:
    stub(
        stubs,
        "chatty",
        f"i=1; while [ $i -le 100 ]; do echo line$i; i=$((i+1)); done; echo key {FAKE_TOKEN}",
    )
    [check] = run_approved(["chatty"], tmp_path)
    lines = check.note.splitlines()
    assert len(lines) == 40
    assert lines[0] == "line62"
    assert FAKE_TOKEN not in check.note
    assert "[REDACTED:" in lines[-1]

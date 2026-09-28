"""Run commands a user approved against a repo they do not control: no shell, a minimal offline env,
stdin closed, and a timeout that kills the whole process group.

Best-effort, and the report says so: the argv gate stops the obvious installer and interpreter
escapes, but an approved script can still do anything its user can, and a grandchild that calls
setsid() leaves the process group and survives the kill (`unshare -rn` is the hardening option)."""

from __future__ import annotations

import os
import re
import shlex
import signal
import subprocess  # nosec B404 — argv lists only, never a shell
import unicodedata
from collections.abc import Sequence
from pathlib import Path

from .models import NOTE_MAX, CommandCheck
from .secrets import redact_text

RUN_TIMEOUT_S = 300
KILL_GRACE_S = 5
NOTE_LINES = 40
OFFLINE_ENV = {
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
PASS_THROUGH = ("PATH", "HOME", "LANG", "TMPDIR")
# `&&` is split into parts; anything else a shell would interpret means "run it by hand".
COMPOUND = ("|", ";", ">", "<", "`", "$(", "&", "\n")
LAUNCHERS = {"env", "sudo", "doas", "su", "sh", "bash", "zsh", "dash", "fish", "ksh"}
INTERPRETER = re.compile(r"(python[0-9.]*|node|ruby|perl)")
# argv[0] → refused whatever follows (None), or refused when any later token is one of these.
REFUSED: dict[str, set[str] | None] = {
    **dict.fromkeys(
        "pip pip3 curl wget npx uvx pipx bunx conda gem bundle composer apt apt-get brew".split()
    ),
    "uv": {"install", "sync", "add", "pip"},
    "npm": {"i", "install", "ci"},
    "pnpm": {"i", "install", "add", "dlx"},
    "yarn": {"install", "add", "dlx"},
    "bun": {"install", "add"},
    "cargo": {"install", "fetch"},
    "go": {"get", "install", "download"},  # `go mod download`
    "poetry": {"install", "add"},
    "git": {"clone", "fetch", "pull"},
    "docker": {"pull", "run"},
    "make": {"install"},
}


def minimal_env() -> dict[str, str]:
    """PATH, HOME, LANG, TMPDIR and the offline switches — no token or cloud key reaches repo code."""
    return {k: os.environ[k] for k in PASS_THROUGH if k in os.environ} | OFFLINE_ENV


def spawn(
    argv: Sequence[str],
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    *,
    merge_stderr: bool,
) -> tuple[int | None, bytes]:
    """(returncode, stdout) — returncode None on timeout, after the whole process group is gone."""
    proc = subprocess.Popen(  # nosec B603 — argv list, no shell; callers gate argv[0]
        list(argv),
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT if merge_stderr else subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
        return proc.returncode, out
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        out, _ = proc.communicate()
        return None, out


def _kill_group(proc: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            pass
        os.killpg(
            proc.pid, signal.SIGKILL
        )  # the leader may be gone while its children are not
    except ProcessLookupError:
        pass


def _refusal(argv: list[str]) -> str | None:
    name = os.path.basename(argv[0])
    if "=" in argv[0] and "/" not in argv[0]:
        return "environment assignment"
    if name in LAUNCHERS:
        return f"{name}: shell or privilege launcher"
    if INTERPRETER.fullmatch(name) and (
        {"-c", "-e"} & set(argv[1:]) or ["-m", "pip"] in _pairs(argv)
    ):
        return f"{name}: inline code or pip"
    if name in REFUSED:
        subcommands = REFUSED[name]
        if subcommands is None or subcommands & set(argv[1:]):
            return f"{name}: installs or fetches"
    return None


def _pairs(argv: list[str]) -> list[list[str]]:
    return [argv[i : i + 2] for i in range(len(argv) - 1)]


def _note(output: bytes) -> str:
    # Redact the whole output first: a secret block cut by the 40-line window would slip past.
    lines = redact_text(output.decode("utf-8", "replace")).splitlines()
    return "\n".join(lines[-NOTE_LINES:])[-NOTE_MAX:]


def _run_part(part: str, cwd: Path, timeout: float) -> CommandCheck:
    if any(unicodedata.category(ch) in ("Cc", "Cf") for ch in part):
        return CommandCheck(
            command=part, status="refused", note="control or bidi character"
        )
    try:
        argv = shlex.split(part)
    except ValueError:
        return CommandCheck(
            command=part, status="not_run", note="unparseable — run by hand"
        )
    if not argv:
        return CommandCheck(command=part, status="refused", note="empty command")
    reason = _refusal(argv)
    if reason:
        return CommandCheck(command=part, status="refused", note=reason)
    try:
        rc, out = spawn(argv, cwd, minimal_env(), timeout, merge_stderr=True)
    except OSError as exc:
        return CommandCheck(
            command=part, status="failed", note=f"cannot start: {exc.strerror}"
        )
    status = "timeout" if rc is None else "verified" if rc == 0 else "failed"
    return CommandCheck(command=part, status=status, note=_note(out))


def run_approved(
    commands: Sequence[str], cwd: Path, timeout: float = RUN_TIMEOUT_S
) -> list[CommandCheck]:
    """One CommandCheck per `&&`-part; a failed part stops its chain."""
    checks = []
    for command in commands:
        if any(mark in command.replace("&&", "") for mark in COMPOUND):
            checks.append(
                CommandCheck(
                    command=command, status="not_run", note="compound — run by hand"
                )
            )
            continue
        failed = False
        for part in (p.strip() for p in command.split("&&")):
            if failed:
                checks.append(
                    CommandCheck(
                        command=part, status="not_run", note="earlier part failed"
                    )
                )
                continue
            checks.append(_run_part(part, cwd, timeout))
            failed = checks[-1].status != "verified"
    return checks

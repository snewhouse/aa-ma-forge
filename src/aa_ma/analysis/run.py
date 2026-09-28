"""Run commands a user approved against a repo they do not control: only known test-runner, build
and lint forms, no shell, a minimal offline env, stdin closed, and a timeout that kills the whole
process group.

The allowlist bounds the *argv*, not what it does: every allowed runner executes repo code, which
can do anything its user can, and a grandchild that calls setsid() leaves the process group and
survives the kill (`unshare -rn` is the hardening option). Best-effort, and the report says so.
The refuse list only names the reason for the obviously dangerous; the allowlist is the gate."""

from __future__ import annotations

import os
import re
import shlex
import signal
import subprocess  # nosec B404 — argv lists only, never a shell
import tempfile
import unicodedata
from collections.abc import Sequence
from pathlib import Path

from . import secrets
from .models import NOTE_MAX, CommandCheck

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
# argv[0] names refused whatever follows: shells, launchers that run another argv, fetchers.
REFUSED_ALWAYS = set(
    "env sudo doas su sh bash zsh dash fish ksh busybox timeout nice nohup setsid stdbuf xargs "
    "find chroot ionice taskset exec command eval watch script awk gawk mawk nawk curl wget npx "
    "uvx pipx bunx conda gem bundle composer apt apt-get brew".split()
)
PIP = re.compile(r"(ensure)?pip[0-9.]*")
INTERPRETER = re.compile(
    r"(python|pypy)[0-9.]*(-dbg)?|node(js)?|deno|bun|perl|ruby|php|lua|Rscript"
)
INLINE_FLAGS = set("ceEp")  # -c/-e/-E/-p: code on the command line
INLINE_LONG = {"--eval", "--print", "--command", "--exec"}
VALUE_FLAGS = {"-W", "-X", "-Q"}  # python options whose value is the next token
VALUE_LETTERS = set("WXQ")  # ...or the rest of the same token (-Werror, -Xdev)
FETCH = ("http://", "https://", "ftp://", "git+")
# argv[0] → refused when any later token is one of these subcommands.
REFUSED: dict[str, set[str]] = {
    "uv": {"install", "sync", "add", "pip"},
    "npm": {"i", "install", "ci", "exec", "x"},
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
# The allowlist: the only argv forms `run` executes. Anything else is `not_run — run by hand`.
RUNNERS = {
    "pytest",
    "py.test",
    "tox",
    "ruff",
    "mypy",
    "flake8",
    "pylint",
    "black",
    "jest",
    "vitest",
    "eslint",
    "tsc",
}
RUNNER_SUBCOMMANDS = {
    "npm": {"test", "t", "run"},
    "pnpm": {"test", "run"},
    "yarn": {"test", "run"},
    "bun": {"test", "run"},
    "cargo": {"test", "build", "check", "clippy", "fmt"},
    "go": {"test", "build", "vet"},
    "node": {"--test"},
}
PYTHON = re.compile(r"(python|pypy)[0-9.]*")
PY_MODULES = {
    "pytest",
    "unittest",
    "mypy",
    "ruff",
    "black",
    "flake8",
    "pylint",
    "compileall",
    "doctest",
}
PY_OPTION = re.compile(
    r"-[BbdIiOqsSuv]+|-[WX]\S+"
)  # interpreter options allowed before -m
SCRIPT_NAME = re.compile(
    r"[A-Za-z0-9_][A-Za-z0-9_:.-]*"
)  # npm/yarn/pnpm/bun run <script>
MAKE_ARG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.:/-]*|-j[0-9]*|-k|-s")


def absolute_path(path: str) -> str:
    """PATH without `.`, empty or relative entries: resolved after the chdir, they would find a
    binary the target repo planted."""
    return os.pathsep.join(e for e in path.split(os.pathsep) if os.path.isabs(e))


def minimal_env() -> dict[str, str]:
    """PATH, HOME, LANG, TMPDIR and the offline switches — no token or cloud key reaches repo code."""
    env = {k: os.environ[k] for k in PASS_THROUGH if k in os.environ} | OFFLINE_ENV
    return env | {"PATH": absolute_path(env.get("PATH", ""))}


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
        try:
            out, _ = proc.communicate(timeout=KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            # A setsid() escaper still holds the pipe: stop reading rather than wait on it.
            proc.stdout.close()  # type: ignore[union-attr]
            proc.wait()
            out = b""
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


def _interpreter_escape(args: list[str]) -> bool:
    """Inline code or pip among an interpreter's own options — the ones before its script."""
    skip = False
    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        if arg == "-" or not arg.startswith("-"):
            return False  # the script: what follows is its own argv
        if arg.startswith("--"):
            if arg.split("=", 1)[0] in INLINE_LONG:
                return True
            continue
        letters = re.match(r"-([A-Za-z]*)", arg).group(1)  # type: ignore[union-attr]
        for j, flag in enumerate(letters):
            if flag in VALUE_LETTERS:
                break  # the rest of the token is this option's value
            # -m MODULE / -mMODULE: pip is refused, anything else is the script.
            if flag == "m":
                module = arg[2 + j :] or (args[i + 1] if i + 1 < len(args) else "")
                return bool(PIP.match(module))
            if flag in INLINE_FLAGS:
                return True
        skip = arg in VALUE_FLAGS
    return False


def _refusal(argv: list[str]) -> str | None:
    name, args = os.path.basename(argv[0]), argv[1:]
    if "=" in argv[0] and "/" not in argv[0]:
        return "environment assignment"
    if any(t.startswith(FETCH) for t in args):
        return "fetches from a URL"
    if name in REFUSED_ALWAYS or PIP.fullmatch(name):
        return f"{name}: shell, launcher, interpreter of inline code, or fetcher"
    if INTERPRETER.fullmatch(name) and _interpreter_escape(args):
        return f"{name}: inline code or pip"
    if name == "git" and any(t.startswith(("-c", "--config")) for t in args):
        return "git -c: config can run commands"
    if name == "make" and any(
        t.startswith(("-f", "--file", "--makefile")) for t in args
    ):
        return "make -f: a makefile from elsewhere"
    if name == "yarn" and not [t for t in args if not t.startswith("-")]:
        return "yarn: a bare yarn installs"
    if name == "uv" and args[:1] == ["run"]:
        rest = [t for t in args[1:] if not t.startswith("-")]
        return _refusal(args[args.index(rest[0]) :]) if rest else None
    subcommand = next((t for t in args if not t.startswith("-")), "")
    if subcommand in REFUSED.get(name, set()):
        return f"{name}: installs or fetches"
    return None


def _allowed(argv: list[str]) -> bool:
    """Is this one of the known test-runner, build or lint forms?"""
    name, args = os.path.basename(argv[0]), argv[1:]
    if name in RUNNERS:
        return True
    if (
        name == "uv"
    ):  # `uv run <allowed form>`, no uv options (they take values and change the env)
        return (
            args[:1] == ["run"]
            and len(args) > 1
            and not args[1].startswith("-")
            and _allowed(args[1:])
        )
    if PYTHON.fullmatch(name):  # interpreter options, then -m <allowed module>
        i = 0
        while i < len(args) and args[i] != "-m":
            if args[i] in VALUE_FLAGS and i + 1 < len(args):
                i += 2
            elif PY_OPTION.fullmatch(args[i]):
                i += 1
            else:
                return False
        return i + 1 < len(args) and args[i + 1] in PY_MODULES
    if name == "make":
        return all(MAKE_ARG.fullmatch(a) for a in args)
    if name in RUNNER_SUBCOMMANDS:
        first = args[0] if args else ""
        if first not in RUNNER_SUBCOMMANDS[name]:
            return False
        return first != "run" or (
            len(args) > 1 and SCRIPT_NAME.fullmatch(args[1]) is not None
        )
    return False


def _note(output: bytes) -> str:
    # Redact the whole output first: a secret block cut by the NOTE_LINES window would slip past.
    lines = secrets.redact_text(output.decode("utf-8", "replace")).splitlines()
    return "\n".join(lines[-NOTE_LINES:])[-NOTE_MAX:]


def _scrub(checks: list[CommandCheck]) -> list[CommandCheck]:
    """Every note and command text through the full output gate (regex set + gitleaks)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i, check in enumerate(checks):
            (root / f"{i}.log").write_text(check.note, encoding="utf-8")
            (root / f"{i}.command.log").write_text(check.command, encoding="utf-8")
        try:
            hits = secrets.scan(root).hits
            if hits:
                secrets.redact(root, hits)
        except secrets.GateError:
            withheld = "(withheld: the secret gate could not scan this output)"
            return [
                c.model_copy(update={"command": withheld, "note": withheld})
                for c in checks
            ]
        read = lambda name: (root / name).read_text(encoding="utf-8")  # noqa: E731
        return [
            c.model_copy(
                update={
                    "command": read(f"{i}.command.log"),
                    "note": read(f"{i}.log")[-NOTE_MAX:],
                }
            )
            for i, c in enumerate(checks)
        ]


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
    if not _allowed(argv):
        return CommandCheck(
            command=part,
            status="not_run",
            note="not a known test-runner form — run by hand",
        )
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
    return _scrub(checks)

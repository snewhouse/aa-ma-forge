"""Contract for the docstring and KISS lint rules (code-conventions-impact M6, map T8/T11).

Each fixture is piped to the uv-locked ruff with a ``--stdin-filename`` under ``src/``,
so it is linted by this repo's own ``pyproject.toml`` exactly as a touched file would be.
A rule counts as on only if a fixture trips it, and as tuned only if the control does not.
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
# why: a public module name — pydocstyle treats functions in a `_private` module as private.
FIXTURE_PATH = "src/aa_ma/ruff_fixture.py"


def _codes(source: str) -> set[str]:
    proc = subprocess.run(
        [
            "uv",
            "run",
            "--quiet",
            "ruff",
            "check",
            "--no-fix",
            "--output-format",
            "concise",
            "--stdin-filename",
            FIXTURE_PATH,
            "-",
        ],
        input=source,
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    # why: ruff exits 1 on findings; anything else means it did not lint at all.
    assert proc.returncode in (0, 1), proc.stderr
    return {
        line.split(" ", 2)[1].rstrip(":")
        for line in proc.stdout.splitlines()
        if line.startswith(FIXTURE_PATH)
    }


MODULE = '"""Fixture module."""\n\n'
LINT = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["tool"][
    "ruff"
]["lint"]
MAX_COMPLEXITY = LINT["mccabe"]["max-complexity"]
MAX_ARGS = LINT["pylint"]["max-args"]


def _branches(n: int) -> str:
    body = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(n))
    return (
        MODULE
        + "def f(x: int) -> int:\n"
        + '    """Return x.\n\n    Args:\n        x: value.\n\n    Returns:\n        x.\n    """\n'
        + body
        + "    return x\n"
    )


def _args(n: int) -> str:
    names = [f"a{i}" for i in range(n)]
    doc_args = "".join(f"        {a}: value.\n" for a in names)
    return (
        MODULE
        + f"def f({', '.join(f'{a}: int' for a in names)}) -> int:\n"
        + f'    """Sum.\n\n    Args:\n{doc_args}\n    Returns:\n        Sum.\n    """\n'
        + f"    return {' + '.join(names)}\n"
    )


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (MODULE + "def f() -> int:\n    return 1\n", "D103"),
        (_branches(MAX_COMPLEXITY), "C901"),  # why: n ifs + the function = n + 1
        (MODULE + "X = 1  # noqa: E501\n", "RUF100"),
        (
            MODULE
            + 'def f(a: int, b: int) -> int:\n    """Add.\n\n    Args:\n'
            + '        a: first.\n\n    Returns:\n        Sum.\n    """\n'
            + "    return a + b\n",
            "D417",
        ),
        (_args(MAX_ARGS + 1), "PLR0913"),
        (MODULE + "X = 1  # noqa\n", "PGH004"),
        (MODULE + "X: int = 1  # type: ignore\n", "PGH003"),
    ],
    ids=["D103", "C901", "RUF100", "D417", "PLR0913", "PGH004", "PGH003"],
)
def test_rule_fires(source: str, code: str) -> None:
    assert code in _codes(source)


@pytest.mark.parametrize(
    ("source", "code"),
    [
        (MODULE + 'def f() -> int:\n    """Return one."""\n    return 1\n', "D103"),
        (_branches(MAX_COMPLEXITY - 1), "C901"),  # why: at the ceiling, not over it
        (_args(MAX_ARGS), "PLR0913"),
        (MODULE + "# TODO(ADR-0021): x\n", "TD003"),
        (
            MODULE
            + 'class C:\n    """C.\n\n    Args:\n        a: value.\n    """\n\n'
            + "    def __init__(self, a: int) -> None:\n        self.a = a\n",
            "D107",
        ),
        (
            MODULE
            + "LIMIT = 3\n\n\ndef f(x: int) -> bool:\n"
            + '    """Over.\n\n    Args:\n        x: value.\n\n    Returns:\n        Over.\n    """\n'
            + "    return x > 7\n",
            "PLR2004",
        ),
    ],
    ids=["D103-documented", "C901-at-10", "PLR0913-at-6", "TD003", "D107", "PLR2004"],
)
def test_rule_quiet(source: str, code: str) -> None:
    assert code not in _codes(source)


def test_parked_docstring_ignores_removed() -> None:
    # why: a ratchet — a new ignore must be argued for here, not slipped in.
    assert set(LINT["extend-ignore"]) == {"D107", "TD003"}
    assert "TODO(logging-std)" not in (REPO / "pyproject.toml").read_text(
        encoding="utf-8"
    )

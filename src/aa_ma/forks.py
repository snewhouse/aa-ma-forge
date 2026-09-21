"""Fork manifest — `claude-code/skills/FORKS.json` is the SSoT for every forked skill.

Pure module: no network, no subprocess. `scripts/fork-drift.sh` is the only
place that fetches upstream; it feeds this module's classifier (eng-review 3A).
Stdlib dataclasses, not Pydantic — no runtime deps.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal

Verdict = Literal["SAME", "DRIFT", "ORPHAN"]


@dataclass(frozen=True)
class ForkEntry:
    name: str
    upstream: str
    upstream_sha: str | None
    forked_at: str
    adr: str
    state: Literal["current", "derived"]
    files: dict[str, str]
    upstream_md5: dict[str, str | None]


_REQUIRED = tuple(f.name for f in fields(ForkEntry) if f.name != "name")


def load_manifest(path: Path) -> dict[str, ForkEntry]:
    """Load FORKS.json. Unknown keys are ignored; a missing required key raises ValueError naming it."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, ForkEntry] = {}
    for name, row in raw.items():
        missing = [k for k in _REQUIRED if k not in row]
        if missing:
            raise ValueError(
                f"FORKS.json[{name!r}] missing required key(s): {', '.join(missing)}"
            )
        out[name] = ForkEntry(name=name, **{k: row[k] for k in _REQUIRED})
    return out


def classify_file(expected: str | None, fetched: str | None) -> Verdict:
    """fetched None → ORPHAN; expected None → SAME (nothing to compare); else compare."""
    if fetched is None:
        return "ORPHAN"
    if expected is None or expected == fetched:
        return "SAME"
    return "DRIFT"


def classify_fork(entry: ForkEntry, fetched: Mapping[str, str | None]) -> Verdict:
    """Roll up over entry.files keys: any ORPHAN → ORPHAN; else any DRIFT → DRIFT; else SAME.

    A key missing from `fetched` counts as None.
    """
    verdicts = {
        classify_file(entry.upstream_md5.get(f), fetched.get(f)) for f in entry.files
    }
    if "ORPHAN" in verdicts:
        return "ORPHAN"
    if "DRIFT" in verdicts:
        return "DRIFT"
    return "SAME"


DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[2] / "claude-code" / "skills" / "FORKS.json"
)  # src/aa_ma/forks.py → repo root

_USAGE = (
    "usage: python -m aa_ma.forks classify <skill> '<json: {file: md5|null}>' [--manifest <path>]\n"
    "       python -m aa_ma.forks files [--manifest <path>]           # skill<TAB>upstream<TAB>file rows\n"
    "       python -m aa_ma.forks classify-all [--manifest <path>]    # stdin: skill<TAB>file<TAB>md5|null"
)


def _print_rows(
    skill: str, entry: ForkEntry, fetched: Mapping[str, str | None]
) -> None:
    for fname in entry.files:
        exp, got = entry.upstream_md5.get(fname), fetched.get(fname)
        print(
            f"{skill} | {fname} | {exp or '-'} | {got or '-'} | {classify_file(exp, got)}"
        )
    print(f"{skill} | * | | | {classify_fork(entry, fetched)}")


def _cli(argv: list[str]) -> int:
    args = list(argv)
    manifest_path = DEFAULT_MANIFEST
    if "--manifest" in args:
        i = args.index("--manifest")
        if i + 1 >= len(args):
            print(_USAGE, file=sys.stderr)
            return 2
        manifest_path = Path(args[i + 1])
        del args[i : i + 2]
    cmd = args[0] if args else ""
    if cmd == "files" and len(args) == 1:
        for name, entry in load_manifest(manifest_path).items():
            for fname in entry.files:
                print(name, entry.upstream, fname, sep="\t")
        return 0
    if cmd == "classify-all" and len(args) == 1:
        # Absent skills/files → None → ORPHAN, same rule as classify_fork.
        fetched: dict[str, dict[str, str | None]] = {}
        for line in sys.stdin:
            skill, fname, md5 = line.rstrip("\n").split("\t")
            fetched.setdefault(skill, {})[fname] = None if md5 == "null" else md5
        for name, entry in load_manifest(manifest_path).items():
            _print_rows(name, entry, fetched.get(name, {}))
        return 0
    if cmd == "classify" and len(args) == 3:
        manifest = load_manifest(manifest_path)
        if args[1] not in manifest:
            print(
                f"unknown skill {args[1]!r}; manifest has: {', '.join(manifest)}",
                file=sys.stderr,
            )
            return 2
        _print_rows(args[1], manifest[args[1]], json.loads(args[2]))
        return 0
    print(_USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))

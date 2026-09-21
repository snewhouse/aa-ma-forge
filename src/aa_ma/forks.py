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


def _cli(argv: list[str]) -> int:
    # python -m aa_ma.forks classify <skill> '<json: {file: md5|null}>' [--manifest <path>]
    if len(argv) < 3 or argv[0] != "classify":
        print(
            "usage: python -m aa_ma.forks classify <skill> '<json>' [--manifest <path>]",
            file=sys.stderr,
        )
        return 2
    skill, fetched = argv[1], json.loads(argv[2])
    manifest_path = (
        Path(argv[argv.index("--manifest") + 1])
        if "--manifest" in argv
        else _default_manifest()
    )
    entry = load_manifest(manifest_path)[skill]
    for fname in entry.files:
        exp, got = entry.upstream_md5.get(fname), fetched.get(fname)
        print(
            f"{skill} | {fname} | {exp or '-'} | {got or '-'} | {classify_file(exp, got)}"
        )
    print(f"{skill} | * | | | {classify_fork(entry, fetched)}")
    return 0


def _default_manifest() -> Path:
    return Path(__file__).resolve().parents[2] / "claude-code" / "skills" / "FORKS.json"


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))

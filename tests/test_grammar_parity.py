"""Pin the bash milestone grammar against the Python one.

`src/aa_ma/grammar.py::MILESTONE_RE` and `AA_MA_MILESTONE_ERE` in
`claude-code/hooks/lib/aa-ma-parse.sh` answer the same question — "is this line
a milestone heading?" — in two languages, and nothing forced them to agree. The
bash file called itself a "mirror" of the Python one; a mirror nobody checks is
a copy.

The failure this prevents is precisely the one this plan was written to close,
one language over: Milestone 1 widened `_NUM_M` to admit `2a` and `3.5.1`, the
TUI and corpus tests went green, and the gate scan would have silently stopped
opening blocks on the new form.

Corpus coverage alone pins nothing — it passes today with both regexes in any
state that agrees on existing text. The explicit edge-case table below is what
gives the test teeth.

Scope note: this compares *heading recognition only*. Block extraction is
deliberately different between the two (the bash side closes on any H2 so the
gate does not swallow a trailing `## Summary Counts` section), so comparing
extracted blocks would fail by design.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from aa_ma.grammar import MILESTONE_RE

REPO_ROOT = Path(__file__).resolve().parents[1]
PARSE_SH = REPO_ROOT / "claude-code" / "hooks" / "lib" / "aa-ma-parse.sh"

# Headings that must be recognised, and non-headings that must not be. Each is
# a case one of the two implementations got wrong at some point.
EDGE_CASES: list[tuple[str, bool]] = [
    ("## Milestone 1: Canonical", True),
    ("## Milestone M1: Milestone-M form", True),
    ("## M1: Bare-M form", True),
    ("## Milestone 1 — Em-dash", True),
    ("## Milestone 1 – En-dash", True),
    ("## Milestone 2a: Letter suffix", True),
    ("## Milestone 3.5: Dotted", True),
    ("## Milestone 3.5.1: Doubly dotted", True),
    ("##\tMilestone 4: Tab after hashes", True),
    ("## Summary Counts", False),
    ("## Milestone Gate Types", False),
    ("## Notes", False),
    ("### Sub-step 1.1: Not a milestone", False),
    ("#### Milestone 1: Too deep", False),
    ("## Milestone 1-NoSpaceDash", False),
    ("Milestone 1: No hashes", False),
    # Empty title. Measured divergence before aa_ma_is_milestone_heading existed:
    # python=0, awk=1, because the ERE is a prefix pattern with no title clause.
    ("## Milestone 5:", False),
    ("## M6:", False),
]


def _bash_ere() -> str:
    """Scrape the ERE from the shell source — the shell file is the definition."""
    src = PARSE_SH.read_text(encoding="utf-8")
    match = re.search(r"^AA_MA_MILESTONE_ERE='(.*)'$", src, re.MULTILINE)
    assert match, "AA_MA_MILESTONE_ERE not found in aa-ma-parse.sh"
    return match.group(1)


def _awk_matches(lines: list[str], awk_bin: str) -> list[bool]:
    """One awk subprocess for all lines; returns a parallel list of verdicts.

    Mirrors `aa_ma_is_milestone_heading`, not the bare ERE. The ERE is the
    *prefix* pattern — block extraction strips it with `sub()` to recover the
    title — so recognition additionally requires a non-empty title, exactly as
    `MILESTONE_RE`'s `(?P<title>.+?)` does. Comparing the bare ERE instead
    reports a false divergence on `## Milestone 5:`.
    """
    program = """
        $0 ~ mre {
            t = $0; sub(mre, "", t)
            gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", t)
            print (t != "") ? "1" : "0"; next
        }
        { print "0" }
    """
    proc = subprocess.run(
        [awk_bin, "-v", f"mre={_bash_ere()}", program],
        input="\n".join(lines),
        capture_output=True,
        text=True,
        check=True,
    )
    return [line == "1" for line in proc.stdout.splitlines()]


def _corpus_candidates() -> list[str]:
    """Every heading-shaped line in every tracked tasks.md and template."""
    seen: set[str] = set()
    roots = [REPO_ROOT / ".claude" / "dev", REPO_ROOT / "docs" / "templates",
             REPO_ROOT / "examples", REPO_ROOT / "tests"]
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("#"):
                    seen.add(line.rstrip("\n"))
    return sorted(seen)


AWKS = [b for b in ("gawk", "mawk", "awk") if shutil.which(b)]


@pytest.mark.parametrize("awk_bin", AWKS)
def test_edge_cases_agree(awk_bin: str) -> None:
    lines = [line for line, _ in EDGE_CASES]
    got = _awk_matches(lines, awk_bin)
    for (line, expected), bash_hit in zip(EDGE_CASES, got, strict=True):
        py_hit = MILESTONE_RE.match(line) is not None
        assert py_hit == expected, f"python disagrees with the table on {line!r}"
        assert bash_hit == expected, f"{awk_bin} disagrees with the table on {line!r}"


@pytest.mark.parametrize("awk_bin", AWKS)
def test_corpus_agrees(awk_bin: str) -> None:
    candidates = _corpus_candidates()
    assert len(candidates) > 100, "corpus scrape returned too little to be meaningful"
    got = _awk_matches(candidates, awk_bin)
    mismatches = [
        line
        for line, bash_hit in zip(candidates, got, strict=True)
        if (MILESTONE_RE.match(line) is not None) != bash_hit
    ]
    assert not mismatches, f"{awk_bin} vs python diverge on: {mismatches[:10]}"


def test_at_least_one_awk_was_tested() -> None:
    """Guard the guard: an empty AWKS list would make every test above vanish."""
    assert AWKS, "no awk implementation found — the parity tests silently skipped"

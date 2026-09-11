"""Canonical grammar for AA-MA milestone and step headings.

Single source of truth for "what is a milestone/step heading", shared by the
TUI parser and the corpus tests. Field-value parsing (``Audit-Profile``,
``TDD-Waiver``) stays in :mod:`aa_ma.plan_parsers` — different concern.

Tolerant reader, strict writer. The corpus accumulated four milestone styles
and three step keywords before this module existed, so the readers below
accept all of them. ``tests/test_active_plans_canonical.py`` enforces the
canonical form on ``.claude/dev/active/**``; completed plans are grandfathered.

Accepted (measured against the 14-plan corpus: 65 milestones, 368 steps)::

    ## Milestone 1: Title       ## Milestone M1: Title
    ## M1: Title                ## Milestone 1 — Title
    ## Milestone 2a: Title
    ### Step 1.1: Title         ### Task 1.1: Title
    ### Sub-step 1.1: Title
    number shapes: 1.1  3.5.1  1.11  2.7b  1.1.bis  M2.1  M2a.1

Three deliberate choices:

* The separator is a colon **or a space-delimited dash**. A bare ``-`` in the
  character class made ``### Step 1.1-alpha:`` parse as number ``1.1`` with
  title ``alpha:``.
* Line ends use ``[ \\t]*$``, never ``\\s*$`` — ``\\s`` matches newlines, so
  ``group(0)`` would run past the heading line whenever it has trailing
  whitespace. The title is ``.*[^ \\t]`` rather than ``.+?``: the lazy form
  was quadratic on a title made of a long whitespace run (20k spaces -> 1 s),
  and the gate now runs on untrusted input.
* Milestone and step numbers share one dotted-depth rule. An earlier revision
  capped milestones at a single dot, which silently dropped
  ``## Milestone 3.5.1:``.

One asymmetry remains, intentionally: ``MILESTONE_RE`` strips a leading ``M``
(``## Milestone M1:`` -> ``"1"``) while ``_NUM_S`` keeps it
(``### Step M2a.1:`` -> ``"M2a.1"``), because step numbers embed their milestone.

Text inside fenced code blocks and HTML comments is not markup; both are removed
before matching — see :func:`sanitize`.
"""

from __future__ import annotations

import bisect
import re
from typing import NamedTuple

from aa_ma.plan_parsers import _strip_html_comments


class Block(NamedTuple):
    """One heading plus the text it owns.

    A NamedTuple rather than a bare 3-tuple: all three fields are ``str``, so a
    positional misorder would otherwise be invisible to type checkers and to
    every consumer.
    """

    number: str
    title: str
    text: str


# Colon, or a dash with whitespace on both sides. Never a bare hyphen.
_SEP = r"(?::|[ \t]+[–—-][ \t]+)"

# `2a`, `3.5`, `3.5.1`; step numbers may also carry a milestone prefix (`M2a.1`)
# and a word suffix (`1.1.bis`). The suffix is generic — `.bis` was the only one
# in the corpus, but hardcoding it silently dropped `.alt` / `.ter`.
_NUM_M = r"\d+[a-z]?(?:\.\d+)*"
_NUM_S = r"M?\d+[a-z]?(?:\.\d+)*(?:\.[a-z]{2,}|[a-z])?"

MILESTONE_RE = re.compile(
    rf"^##[ \t]+(?:Milestone[ \t]+M?|M)(?P<number>{_NUM_M}){_SEP}[ \t]*(?P<title>.*[^ \t\n])[ \t]*$",
    re.MULTILINE,
)

STEP_RE = re.compile(
    rf"^###[ \t]+(?:Sub-step|Step|Task)[ \t]+(?P<number>{_NUM_S})"
    rf"{_SEP}[ \t]*(?P<title>.*[^ \t\n])[ \t]*$",
    re.MULTILINE,
)

# CommonMark fence opener: 3+ backticks or tildes, indented at most 3 spaces.
_FENCE_RE = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})")


class FenceScan(NamedTuple):
    """Result of the one fence state machine every fence-aware reader uses."""

    stripped: str  # input with fenced lines blanked (positions preserved)
    blocks: list[str]  # contents of each fenced block, in order
    unterminated: bool  # a fence opened and never closed


def _split_lines(text: str) -> list[str]:
    # `\n` only. `str.splitlines()` also splits on FF, VT, NEL, LS, PS and
    # FS/GS/RS, which no regex here (`re.MULTILINE` = `\n`) and no markdown
    # renderer treats as a line end. Measured: `- Status: ACTIVE\x0c```` was
    # one line to every field regex and two to the fence scanner, which opened
    # a fence there and hid a PENDING sub-step — a false PASS.
    return text.split("\n")


def scan_fences(text: str) -> FenceScan:
    """The single CommonMark fence scanner.

    Line-oriented, not a ``.*?`` DOTALL regex, for two reasons found in review:

    * **Correctness** — fences nest. A ```` ``` ```` inside a ```` ```` ````
      block is content, not a close; flat regex pairing emitted phantom
      milestones for that case.
    * **Cost** — the regex form was O(n^2). A language-tagged opener
      (```` ```python ````) can open a fence but never close one, so every
      opener drove a DOTALL scan to EOF. Measured 78 KiB -> 5.15 s through
      ``parse_task_dir``; this scanner is linear.

    A fence closes only on the same character with at least the opening run
    length; an unterminated fence runs to end of input. Lines are blanked
    rather than dropped so line positions are preserved.

    One scanner, three views (:func:`strip_fenced_blocks`,
    :func:`iter_fenced_blocks`, :func:`has_unterminated_fence`) — the §6.8
    review found three copies that could disagree, and one pair did: the
    gate's unterminated check ran on raw text while stripping ran on
    comment-stripped text, so a closing ```` ``` ```` inside an HTML comment
    satisfied the check and was then removed before stripping. False PASS.
    """
    out: list[str] = []
    blocks: list[str] = []
    current: list[str] | None = None
    fence: tuple[str, int] | None = None
    for line in _split_lines(text):
        match = _FENCE_RE.match(line)
        if fence is None:
            if match:
                marker = match.group("marker")
                fence, current = (marker[0], len(marker)), []
                out.append("")
                continue
            out.append(line)
            continue
        char, length = fence
        out.append("")
        if (
            match
            and match.group("marker")[0] == char
            and len(match.group("marker")) >= length
        ):
            blocks.append("".join(current or []))
            fence, current = None, None
            continue
        if current is not None:
            current.append(line + "\n")
    if current is not None:  # unterminated fence
        blocks.append("".join(current))
    return FenceScan("\n".join(out), blocks, fence is not None)


def strip_fenced_blocks(text: str) -> str:
    """Blank out fenced code blocks so headings inside them are not parsed."""
    return scan_fences(text).stripped


def iter_fenced_blocks(text: str) -> list[str]:
    """Return the *contents* of each fenced code block — the inverse of stripping.

    Needed because the shipped writer templates document the tasks.md form
    *inside* a ```` ```markdown ```` fence. Linting their sanitized text checks
    nothing at all: the §6.8 review mutation-tested this and found 4 of 5 writer
    checks inert, passing green against the exact drift they were added to catch.
    """
    return scan_fences(text).blocks


def has_unterminated_fence(text: str) -> bool:
    """True when a fence opens and never closes, **as :func:`sanitize` sees it**.

    Runs on comment-stripped text — the same input stripping receives — so the
    two cannot disagree. For a gate an unterminated fence means every heading
    and field after the opener silently vanishes; measured to hide a
    ``Status: PENDING`` sub-step, so the gate refuses instead.
    """
    return scan_fences(_strip_html_comments(text)).unterminated


def sanitize(text: str) -> str:
    """Strip everything that can look like a heading without being one.

    Composes fence stripping with
    :func:`aa_ma.plan_parsers._strip_html_comments`. Templates carry
    commented-out milestones — ``docs/templates/tasks-template.md`` has ten HTML
    comment blocks — and a scribe leaving one in place otherwise produces a
    phantom milestone in the TUI and in the corpus tests.
    """
    return strip_fenced_blocks(_strip_html_comments(text))


# Any H2 — a milestone heading or a prose one like `## Summary Counts`. A bare
# `##` counts too (CommonMark: an empty ATX heading).
_H2_RE = re.compile(r"^##(?:[ \t]|$)", re.MULTILINE)


def _split(
    text: str, regex: re.Pattern[str], closer: re.Pattern[str] | None = None
) -> list[Block]:
    cleaned = sanitize(text)
    matches = list(regex.finditer(cleaned))
    closers = [m.start() for m in closer.finditer(cleaned)] if closer else []
    blocks: list[Block] = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        if closers:
            # Open only on a heading `regex` accepts; close on the next `closer`
            # line, whether or not it is itself a heading `regex` accepts.
            nxt = bisect.bisect_right(closers, match.start())
            if nxt < len(closers):
                end = min(end, closers[nxt])
        blocks.append(
            Block(
                match.group("number"),
                match.group("title"),
                cleaned[match.start() : end],
            )
        )
    return blocks


def split_milestones(text: str) -> list[Block]:
    """Split a tasks.md into milestone blocks.

    Text before the first heading is discarded. A block opens on a milestone
    heading and closes on the **next H2 of any kind** — deliberately
    asymmetric, and the same rule the bash display readers use. Closing only on the
    next *milestone* heading let the last milestone absorb a trailing prose
    section such as `## Summary Counts`, whose field-shaped lines then read
    as extra PENDING sub-steps (measured: 3 where 2 exist).
    """
    return _split(text, MILESTONE_RE, closer=_H2_RE)


def split_steps(milestone_block: str) -> list[Block]:
    """Split one milestone block into step blocks.

    Re-sanitises its input: the block usually arrives already cleaned from
    :func:`split_milestones`, but this is public API and may receive raw text.
    Sanitising is idempotent and linear, so the double pass is cheap.
    """
    return _split(milestone_block, STEP_RE)


# -----------------------------------------------------------------------------
# Strict writer — the single form new plans must use
# -----------------------------------------------------------------------------
#
# The readers above are deliberately tolerant because the archived corpus is
# frozen. Anything being authored now gets exactly one form. Source:
# `docs/templates/tasks-template.md` and `docs/spec/aa-ma-specification.md`.

CANONICAL_MILESTONE_RE = re.compile(r"^## Milestone (?P<number>\d+): (?P<title>\S.*)$")
CANONICAL_STEP_RE = re.compile(r"^### Sub-step (?P<number>\d+\.\d+): (?P<title>\S.*)$")


def find_non_canonical(text: str) -> list[str]:
    """Return headings the tolerant reader accepts but the writer form forbids.

    Candidate selection is the whole subtlety: a line is a *candidate* only if
    :data:`MILESTONE_RE` or :data:`STEP_RE` recognises it, and a candidate is a
    *violation* only if it is not also canonical. Linting every ``##`` line
    instead would flag ordinary prose headings like ``## Summary Counts``.
    """
    violations: list[str] = []
    for line in sanitize(text).splitlines():
        if MILESTONE_RE.match(line):
            if not CANONICAL_MILESTONE_RE.match(line):
                violations.append(line.strip())
        elif STEP_RE.match(line) and not CANONICAL_STEP_RE.match(line):
            violations.append(line.strip())
    return violations

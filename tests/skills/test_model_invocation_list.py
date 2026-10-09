"""Which skills the model may not invoke on its own (code-conventions-impact D9 revised).

Only the two with outward effects (merging to main, publishing a link) carry
``disable-model-invocation: true``; every other skill stays model-invocable, so
``/execute-aa-ma-full`` can delegate to ``/execute-aa-ma-milestone``.
"""

from __future__ import annotations

from pathlib import Path

from ._helpers import SKILLS_DIR, split_frontmatter

EXPECTED = {"sole-dev-merge", "aa-ma-share"}


def _frontmatter(path: Path) -> dict:
    # Strict: a SKILL.md whose frontmatter does not parse fails here, never reads as {}.
    return split_frontmatter(path.read_text(encoding="utf-8"))[1]


def test_exactly_the_two_outward_skills_disable_model_invocation() -> None:
    got = {
        p.parent.name
        for p in sorted(SKILLS_DIR.glob("*/SKILL.md"))
        if _frontmatter(p).get("disable-model-invocation") is True
    }
    assert got == EXPECTED


def test_the_flag_is_never_spelled_any_other_way() -> None:
    """A quoted "true" or a typo'd key would read as model-invocable."""
    for p in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        fm = _frontmatter(p)
        assert fm.get("disable-model-invocation") in (None, True), p
        assert not {
            k for k in fm if "model-invocation" in k and k != "disable-model-invocation"
        }, p

"""The auto-loaded rules stay within their size budget (code-conventions-impact T12, M12.4).

Every session pays for `claude-code/rules/*.md` in context, so their size is a ratchet:
RATCHET is the total measured after M12 and may only fall. The comparison is rules-only
and like-for-like with the M1 baseline (`rules_chars` in the plan's provenance.log), which
was measured in bytes (`cat claude-code/rules/*.md | wc -c`), so every size here is bytes.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES = REPO_ROOT / "claude-code" / "rules"

# bytes; M1 BASELINE `rules_chars`, 2026-10-08 (aa-ma.md + engineering-standards.md)
M1_RULES_BYTES = 20_249
# bytes; measured after M12.2 (3 rules). Lower it when rules shrink; never raise it.
RATCHET = 20_076
# bytes (≥ chars, so this is at least as strict as the T12 cap of 6,000 chars ≈ 1.5k tokens)
CODING_STANDARDS_MAX = 6_000


def rules_bytes(rules_dir: Path) -> int:
    """Total size in bytes of the auto-loaded rule files in ``rules_dir``."""
    return sum(len(p.read_bytes()) for p in sorted(rules_dir.glob("*.md")))


def test_rules_total_is_within_the_ratchet() -> None:
    total = rules_bytes(RULES)
    assert total <= RATCHET, f"rules are {total} bytes, over the ratchet {RATCHET}"


def test_ratchet_is_not_above_the_m1_baseline() -> None:
    assert RATCHET <= M1_RULES_BYTES


def test_coding_standards_is_within_its_cap() -> None:
    size = len((RULES / "coding-standards.md").read_bytes())
    assert size <= CODING_STANDARDS_MAX, f"coding-standards.md is {size} bytes"


def test_rules_bytes_counts_every_rule_in_bytes(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("abc", encoding="utf-8")
    (tmp_path / "b.md").write_text("—", encoding="utf-8")  # one char, three bytes
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
    assert rules_bytes(tmp_path) == 6

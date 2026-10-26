"""sanitize_context_line: repo-controlled text made safe to hand the model (code-conventions-impact 10.6).

``codemem impact --format brief`` feeds the PreToolUse impact hook, whose output
reaches the model as additionalContext. Every line passes this function: one
line, no control characters, bounded length, and it never raises.
"""

from __future__ import annotations

import unicodedata

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from codemem.mcp_tools.sanitizers import sanitize_context_line

# Every C0 control, DEL, and every C1 control (U+0080-U+009F).
CONTROLS = [chr(c) for c in (*range(0x00, 0x20), 0x7F, *range(0x80, 0xA0))]
# Line/paragraph separators and bidi overrides: invisible, but they reshape what a reader sees.
INVISIBLES = [" ", " ", "‮", "⁦", "⁩", "﻿"]


# Unicode categories that must never reach the model: controls, format (zero-width, bidi,
# BOM, tag characters), private use, surrogates, line and paragraph separators.
UNSAFE_CATEGORIES = {"Cc", "Cf", "Co", "Cs", "Zl", "Zp"}


def _clean(s: str) -> bool:
    return not any(
        ch in CONTROLS + INVISIBLES or unicodedata.category(ch) in UNSAFE_CATEGORIES
        for ch in s
    )


@pytest.mark.parametrize(
    "ch",
    [
        "\u200b",  # zero-width space
        "\u200d",  # zero-width joiner
        "\u2060",  # word joiner
        "\U000e0041",  # tag character 'A' (hidden-text smuggling)
        "\U000e007f",  # cancel tag
        "\u2028",  # line separator
        "\u202e",  # right-to-left override
        "\ue000",  # private use
        "\U000f0000",  # supplementary private use
        "\u00ad",  # soft hyphen (Cf)
    ],
)
def test_invisible_and_format_characters_become_one_space(ch: str) -> None:
    assert sanitize_context_line(f"a{ch}b{ch}{ch}c") == "a b c"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("src/a.py", "src/a.py"),
        ("a\nb", "a b"),
        ("a\r\nb", "a b"),
        ("\x1b[31mred\x1b[0m", "[31mred [0m"),
        ("tab\there", "tab here"),
        ("del\x7fx", "del x"),
        ("csi\x9bx", "csi x"),
        ("nul\x00x", "nul x"),
        ("  lead and trail  ", "lead and trail"),
        ("many\n\n\n   gaps", "many gaps"),
        ("ls x", "ls x"),
        ("bidi‮evil", "bidi evil"),
        ("$(touch x)`id`", "$(touch x)`id`"),  # inert text: kept, never interpreted
        ("", ""),
    ],
)
def test_adversarial_cases(text: str, expected: str) -> None:
    assert sanitize_context_line(text) == expected


def test_caps_with_an_ellipsis() -> None:
    out = sanitize_context_line("x" * 500, max_len=20)
    assert len(out) == 20
    assert out.endswith("…")
    assert out[:-1] == "x" * 19


def test_exactly_max_len_is_untouched() -> None:
    assert sanitize_context_line("y" * 200) == "y" * 200


@pytest.mark.parametrize("max_len", [0, -5])
def test_non_positive_max_len_is_empty_not_an_error(max_len: int) -> None:
    assert sanitize_context_line("abc", max_len=max_len) == ""


def test_max_len_one_is_the_ellipsis() -> None:
    assert sanitize_context_line("abc", max_len=1) == "…"


def test_lone_surrogate_does_not_raise() -> None:
    out = sanitize_context_line("a\udcffb")
    assert isinstance(out, str)
    out.encode("utf-8")  # safe to print and to JSON-encode


def test_the_catch_all_logs_one_debug_line(caplog: pytest.LogCaptureFixture) -> None:
    """§6.6 INFO c: the never-raises fallback is not silent."""

    class Unprintable:
        def __str__(self) -> str:
            raise RuntimeError("boom")

    with caplog.at_level("DEBUG", logger="codemem.mcp_tools.sanitizers"):
        # why: a non-str argument is the point — the fallback must swallow its str() error
        assert sanitize_context_line(Unprintable()) == ""  # type: ignore[arg-type]
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "DEBUG"


@given(st.text(), st.integers(min_value=-3, max_value=400))
@settings(max_examples=300, deadline=None)
def test_never_raises_and_is_one_clean_bounded_line(text: str, max_len: int) -> None:
    out = sanitize_context_line(text, max_len=max_len)
    assert isinstance(out, str)
    assert len(out) <= max(max_len, 0)
    assert _clean(out)
    assert out == out.strip()
    assert "  " not in out
    out.encode("utf-8")


@given(
    st.text(alphabet=st.characters(categories=sorted(UNSAFE_CATEGORIES)) | st.just("a"))
)
def test_control_heavy_input_is_clean(text: str) -> None:
    assert _clean(sanitize_context_line(text))

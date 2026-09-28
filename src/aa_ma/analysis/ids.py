"""Stable finding IDs and the one baseline vocabulary (new / persisting / fixed).

id = "F-" + sha256(dimension ␟ rule ␟ path ␟ anchor)[:12]. The anchor is text, never a line
number, so code moving around a finding keeps its ID; the k-th identical finding (k ≥ 2) in a
run hashes anchor + "#k" (order of appearance)."""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable
from typing import Literal

from .models import HEX12
from .secrets import redact_text

State = Literal["new", "persisting", "fixed"]


def finding_id(dimension: str, rule: str, path: str, anchor: str) -> str:
    digest = hashlib.sha256(
        "\x1f".join([dimension, rule, path, anchor]).encode("utf-8")
    ).hexdigest()
    return "F-" + digest[:HEX12]


def anchor_for(line: str) -> str:
    """A judged finding's anchor: the source line, secret-redacted BEFORE hashing, whitespace collapsed."""
    return " ".join(redact_text(line).split())


def assign_ids(keys: Iterable[tuple[str, str, str, str]]) -> list[str]:
    seen: Counter[tuple[str, str, str, str]] = Counter()
    out = []
    for key in keys:
        seen[key] += 1
        dimension, rule, path, anchor = key
        k = seen[key]
        out.append(
            finding_id(dimension, rule, path, anchor if k == 1 else f"{anchor}#{k}")
        )
    return out


def compare(previous: Iterable[str], current: Iterable[str]) -> dict[str, State]:
    prev, cur = set(previous), list(current)
    states: dict[str, State] = {i: ("persisting" if i in prev else "new") for i in cur}
    states.update({i: "fixed" for i in prev - set(cur)})
    return states

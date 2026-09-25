"""The I/O-boundary view: where the code touches the outside world (diagram-generation M9).

Classifies the call edges codemem already stores unresolved (``edges.dst_unresolved``:
``sqlite3.connect``, ``fs.readFileSync``, ``conn.execute``) against ``sinks.yaml`` at
render time — no schema change. Two tiers: ``qualified`` (the whole callee is a
catalogued symbol) and ``bare`` (a catalogued method name on a receiver whose type is
unknown — low confidence, drawn dashed).

Level (M9 prototype verdict, Ste 2026-09-25): one arrow per file when that fits the
dense band (``DENSE_BAND``), else one per L1 folder. Deterministic from the index, so
``codemem draw --check`` stays a plain regenerate-and-compare.
"""

from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from .cut import Level, collapse, is_test_path

__all__ = [
    "CATEGORIES", "DENSE_BAND", "LANGS", "SINKS_PATH", "TIERS",
    "Catalogue", "IoEdge", "Sink", "band_line", "choose_level", "classify", "io_edges",
    "load_catalogue",
]

SINKS_PATH = Path(__file__).with_name("sinks.yaml")
DENSE_BAND = 120  # Ticket 3's dense band; past it the view collapses to L1
LANGS = ("python", "typescript", "tsx", "javascript", "go")  # v1 (Ticket 6)
CATEGORIES = ("db", "http", "fs", "subprocess", "env", "queue")
TIERS = ("qualified", "bare")
_ROW_KEYS = {"lang", "category", "symbol", "tier", "source"}


@dataclass(frozen=True)
class Sink:
    lang: str
    category: str
    symbol: str
    tier: str
    source: str


@dataclass(frozen=True)
class Catalogue:
    sinks: tuple[Sink, ...]
    qualified: dict[tuple[str, str], str]  # (lang, callee) -> category
    bare: dict[tuple[str, str], str]  # (lang, method name) -> category


@dataclass(frozen=True, order=True)
class IoEdge:
    src: str  # file path, or L1 folder after collapse
    lang: str
    category: str
    tier: str
    calls: int  # distinct (file, callee) pairs behind the arrow


def load_catalogue(path: Path = SINKS_PATH) -> Catalogue:
    """Parse and validate ``sinks.yaml``; any malformation raises ``ValueError`` naming the row."""
    rows = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{path}: must be a list of rows")
    sinks: list[Sink] = []
    seen: set[tuple[str, str]] = set()
    for i, row in enumerate(rows):
        where = f"{path}: row {i}"
        if not isinstance(row, dict) or set(row) != _ROW_KEYS:
            keys = set(row) if isinstance(row, dict) else set()
            raise ValueError(
                f"{where}: keys must be {sorted(_ROW_KEYS)}; "
                f"missing {sorted(_ROW_KEYS - keys)}, unexpected {sorted(keys - _ROW_KEYS)}"
            )
        langs, symbols = _strs(row["lang"], where, "lang"), _strs(row["symbol"], where, "symbol")
        for field, value, allowed in (
            ("category", row["category"], CATEGORIES), ("tier", row["tier"], TIERS),
        ):
            if value not in allowed:
                raise ValueError(f"{where}: {field} {value!r} not in {allowed}")
        if bad := [lang for lang in langs if lang not in LANGS]:
            raise ValueError(f"{where}: lang {bad} not in {LANGS}")
        if not isinstance(row["source"], str) or not row["source"].startswith("https://"):
            raise ValueError(f"{where}: source must be an https:// URL")
        for lang in langs:
            for symbol in symbols:
                if (lang, symbol) in seen:
                    raise ValueError(f"{where}: duplicate symbol {symbol!r} for {lang}")
                seen.add((lang, symbol))
                sinks.append(Sink(lang, row["category"], symbol, row["tier"], row["source"]))
    by_tier = {t: {(s.lang, s.symbol): s.category for s in sinks if s.tier == t} for t in TIERS}
    return Catalogue(tuple(sinks), by_tier["qualified"], by_tier["bare"])


def _strs(value: object, where: str, field: str) -> list[str]:
    """A non-empty str, or a non-empty list of them (YAML 1.1 reads `on`/`no` as bools)."""
    items = value if isinstance(value, list) else [value]
    strs = [v for v in items if isinstance(v, str) and v]
    if not items or len(strs) != len(items):
        raise ValueError(f"{where}: {field} must be a non-empty string or list of strings, got {value!r}")
    return strs


def classify(lang: str, callee: str, cat: Catalogue) -> tuple[str, str] | None:
    """``(category, tier)`` for a stored callee, or ``None`` when it is not a catalogued sink."""
    if category := cat.qualified.get((lang, callee)):
        return category, "qualified"
    _, dot, method = callee.rpartition(".")
    if dot and (category := cat.bare.get((lang, method))):
        return category, "bare"
    return None


def io_edges(conn: sqlite3.Connection, cat: Catalogue, *, include_tests: bool = False) -> list[IoEdge]:
    """File-level I/O edges, sorted. A qualified call anywhere in the file makes the arrow qualified."""
    rows = conn.execute(
        """
        SELECT DISTINCT f.path, f.lang, e.dst_unresolved
        FROM edges e
        JOIN symbols s ON s.id = e.src_symbol_id
        JOIN files f ON f.id = s.file_id
        WHERE e.kind = 'call' AND e.dst_unresolved IS NOT NULL
        """
    )
    merged: dict[tuple[str, str, str], tuple[str, int]] = {}
    for path, lang, callee in rows:
        if not include_tests and is_test_path(path):
            continue
        if (hit := classify(lang, callee, cat)) is None:
            continue
        category, tier = hit
        merged[(path, lang, category)] = _merge(merged.get((path, lang, category)), tier, 1)
    return sorted(IoEdge(*k, tier, n) for k, (tier, n) in merged.items())


def _merge(old: tuple[str, int] | None, tier: str, n: int) -> tuple[str, int]:
    if old is None:
        return tier, n
    return ("qualified" if "qualified" in (old[0], tier) else "bare"), old[1] + n


def choose_level(edges: list[IoEdge], threshold: int = DENSE_BAND) -> tuple[Level, list[IoEdge]]:
    """File level (L2) when ``edges`` fit ``threshold``, else collapsed to L1 folders."""
    if len(edges) <= threshold:
        return Level.L2, edges
    merged: dict[tuple[str, str, str], tuple[str, int]] = {}
    for e in edges:
        k = (collapse(e.src, Level.L1), e.lang, e.category)
        merged[k] = _merge(merged.get(k), e.tier, e.calls)
    return Level.L1, sorted(IoEdge(*k, tier, n) for k, (tier, n) in merged.items())


def band_line(repo: str, sha: str, edges: int, threshold: int = DENSE_BAND) -> str:
    """The reference.md evidence line (M9 AC6); ``edges`` is the FILE-level count."""
    verdict = "UNDER" if edges <= threshold else "OVER"
    # A directory name is caller data: keep the line one token per field and terminal-safe.
    repo = "".join(c if c.isprintable() and not c.isspace() else "?" for c in repo)
    return f"IO_DENSE_BAND repo={repo} sha={sha} edges={edges} threshold={threshold} verdict={verdict}"


def main(argv: list[str]) -> int:
    """``python -m codemem.draw.io_sinks band <index.db> <repo-name> <sha>`` (scripts/measure_io_band.sh)."""
    if len(argv) != 4 or argv[0] != "band":
        print("usage: python -m codemem.draw.io_sinks band <index.db> <repo-name> <sha>", file=sys.stderr)
        return 2
    from ..storage.db import connect

    conn = connect(Path(argv[1]), read_only=True)
    try:
        print(band_line(argv[2], argv[3], len(io_edges(conn, load_catalogue()))))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

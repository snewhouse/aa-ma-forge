"""codemem.draw.captions — the authored, path-keyed captions sidecar (diagram-generation M5).

Captions are prose OUTSIDE the diagram (Ticket 12): the living doc renders them beside
the fence, the explorer reads the same file. Only ``@start`` touches the mermaid, as a
``classDef`` highlight — so a caption-only edit is never diagram drift.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from aa_ma.render.mermaid_lint import render_check

from codemem.draw.captions import CAPTIONS_PATH, CaptionFinding, for_cut, load, orphans
from codemem.draw.cut import Level, from_edges, node_id
from codemem.draw.mermaid import to_mermaid

REPO = Path(__file__).resolve().parents[2]


def _sidecar(root: Path, data) -> Path:
    p = root / CAPTIONS_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data if isinstance(data, str) else json.dumps(data))
    return root


# ---------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------

def test_absent_sidecar_means_no_captions(tmp_path: Path) -> None:
    assert load(tmp_path) == {}


def test_load_returns_the_flat_mapping(tmp_path: Path) -> None:
    data = {"@start": "src/a.py", "src/": "Everything.", "src/a.py": "Entry point."}
    assert load(_sidecar(tmp_path, data)) == data


@pytest.mark.parametrize("bad", ["{not json", "[]", '{"src/": 3}', '{"@start": ["x"]}'])
def test_malformed_sidecar_is_an_error_naming_the_file(tmp_path: Path, bad: str) -> None:
    with pytest.raises(ValueError, match="architecture.captions.json"):
        load(_sidecar(tmp_path, bad))


def test_sidecar_lives_outside_the_generated_dir() -> None:
    assert CAPTIONS_PATH == "docs/architecture.captions.json"
    assert not CAPTIONS_PATH.startswith("docs/architecture/")


# ---------------------------------------------------------------------
# orphans() — AC3, AC4
# ---------------------------------------------------------------------

KNOWN = {"src/a.py", "src/pkg/b.py"}


def test_existing_file_and_directory_keys_report_nothing() -> None:
    caps = {"@start": "src/a.py", "src/a.py": "x", "src/pkg/": "y", "src/": "z"}
    assert orphans(caps, KNOWN, set()) == []


def test_deleted_path_is_orphan_caption() -> None:
    assert orphans({"src/gone.py": "x"}, KNOWN, set()) == [
        CaptionFinding(path="src/gone.py", code="ORPHAN_CAPTION", reason="path not in the repo")
    ]


def test_planned_path_is_unknown_not_orphan() -> None:
    [f] = orphans({"src/new.py": "x"}, KNOWN, {"src/new.py"})
    assert (f.path, f.code) == ("src/new.py", "UNKNOWN") and f.reason


def test_stale_start_is_reported_by_its_path() -> None:
    [f] = orphans({"@start": "src/gone.py"}, KNOWN, set())
    assert (f.path, f.code) == ("src/gone.py", "ORPHAN_CAPTION")


def test_orphans_never_deletes_prose() -> None:
    caps = {"src/gone.py": "keep me"}
    orphans(caps, KNOWN, set())
    assert caps == {"src/gone.py": "keep me"}


def test_the_authored_sidecar_has_no_orphans() -> None:
    tracked = set(subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split())
    caps = load(REPO)
    assert "@start" in caps
    assert orphans(caps, tracked, set()) == []


# ---------------------------------------------------------------------
# for_cut() — AC2: path keying gives per-level captions for free
# ---------------------------------------------------------------------

CAPS = {"@start": "src/pkg/b.py", "src/": "Source.", "src/pkg/": "Package.", "src/pkg/b.py": "Start."}


def test_directory_caption_appears_at_collapsed_levels() -> None:
    l0 = from_edges({("src", "lib", "import")}, Level.L0)
    l1 = from_edges({("src/pkg", "lib/x", "import")}, Level.L1)
    assert for_cut(l0, CAPS) == {"src/": "Source."}
    assert for_cut(l1, CAPS) == {"src/pkg/": "Package."}


def test_file_caption_appears_at_file_and_symbol_levels() -> None:
    l2 = from_edges({("src/pkg/b.py", "src/a.py", "call")}, Level.L2)
    l3 = from_edges({("src/pkg/b.py::f", "src/pkg/b.py::g", "call")}, Level.L3)
    assert for_cut(l2, CAPS) == {"src/pkg/b.py": "Start."}
    assert for_cut(l3, CAPS) == {"src/pkg/b.py": "Start."}


# ---------------------------------------------------------------------
# @start in the emitted mermaid — AC1
# ---------------------------------------------------------------------

def test_start_is_a_classdef_highlighted_node() -> None:
    c = from_edges({("src/pkg/b.py", "src/a.py", "call")}, Level.L2)
    text = to_mermaid(c, CAPS)
    assert "classDef start " in text
    assert f"  class {node_id('src/pkg/b.py', Level.L2)} start" in text.splitlines()
    assert render_check([text]) != "FAIL"


def test_start_highlights_its_containing_node_at_collapsed_levels() -> None:
    c = from_edges({("src", "lib", "import")}, Level.L0)
    assert f"  class {node_id('src', Level.L0)} start" in to_mermaid(c, CAPS).splitlines()


def test_no_captions_leaves_the_emitter_output_unchanged() -> None:
    c = from_edges({("src/pkg/b.py", "src/a.py", "call")}, Level.L2)
    assert to_mermaid(c) == to_mermaid(c, None) == to_mermaid(c, {"src/a.py": "x"})
    assert "classDef" not in to_mermaid(c)


def test_a_caption_only_edit_is_not_diagram_drift() -> None:
    c = from_edges({("src/pkg/b.py", "src/a.py", "call")}, Level.L2)
    assert to_mermaid(c, CAPS) == to_mermaid(c, {**CAPS, "src/pkg/b.py": "Reworded."})

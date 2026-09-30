"""PROTOTYPE — throwaway (M5 5.1, branch prototype/cas-incremental-regen). Not production code.

Question: does "section -> cited paths + fixed globs, A/D/R -> structure" pick the right sections
to regenerate on real forge commit pairs?  Usage: python proto.py <pack_dir> <out.json>
"""
import fnmatch, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CITE = re.compile(r"`([A-Za-z0-9_.][A-Za-z0-9_./-]*?)(?::(\d+)(?:-\d+)?)?`")
GLOBS = {  # sections whose truth lives in files nobody cites line-by-line
    "01-stack": ["pyproject.toml", "uv.lock", "package.json", "*.lock", ".python-version", ".tool-versions"],
    "05-tests-ci": [".github/workflows/*", "tests/*", "pytest.ini", "conftest.py"],
    "03-structure": [],  # any add/delete/rename
}
PAIRS = ["ee822ac", "abf5b20", "b4b699f", "7b9295e", "649fb6d"]


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)


TRACKED = set(git("ls-files").stdout.split())


def section_map(pack):
    out = {}
    for md in sorted(Path(pack).glob("*.md")):
        cited = {m[1] for m in CITE.finditer(md.read_text())
                 if m[1] in TRACKED or (m[1].endswith("/") and any(t.startswith(m[1]) for t in TRACKED))}
        out[md.stem] = sorted(cited)
    out.setdefault("03-structure", [])
    return out


def changed_since(prev, head):
    if git("cat-file", "-e", f"{prev}^{{commit}}").returncode:
        return None  # unknown stamp SHA (rebased away) -> caller regenerates everything
    rows = git("diff", "--name-status", "--end-of-options", prev, head).stdout.splitlines()
    return [r.split("\t") for r in rows]


def sections_to_regenerate(smap, changed):
    if changed is None:
        return sorted(smap), {s: ["unknown stamp sha"] for s in smap}
    why = {}
    for status, *paths in changed:
        for p in paths:
            for s, cited in smap.items():
                if p in cited or any(c.endswith("/") and p.startswith(c) for c in cited) or any(fnmatch.fnmatch(p, g) for g in GLOBS.get(s, [])):
                    why.setdefault(s, []).append(f"{status} {p}")
        if status[0] in "ADR":
            why.setdefault("03-structure", []).append(f"{status} {' -> '.join(paths)}")
    return sorted(why), why


def main(pack, out):
    smap = section_map(pack)
    cases = []
    for c in PAIRS + ["deadbeef0000"]:
        ch = changed_since(f"{c}~1" if c != "deadbeef0000" else c, c if c != "deadbeef0000" else "HEAD")
        regen, why = sections_to_regenerate(smap, ch)
        cases.append({"commit": c, "subject": git("log", "-1", "--format=%s", c).stdout.strip() or "(unknown sha)",
                      "changed": ch, "regenerate": regen, "why": why})
    Path(out).write_text(json.dumps({"map": smap, "globs": GLOBS, "cases": cases}, indent=1))
    for k in cases:
        print(k["commit"], "->", k["regenerate"])


if __name__ == "__main__":
    main(*sys.argv[1:])

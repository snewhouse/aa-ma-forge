"""PROTOTYPE (throwaway, M11.1) — which co-change threshold/window should fence 4 use?

Replays, per merged milestone PR, what `aa-ma-impact` would see at the PR head:
codemem's commit cache = the last W commits of `git log --name-status -M <head>`
(paths renamed to their name at head, deleted paths dropped), partners of each
changed file at >= n shared commits AND >= ratio of the file's commits, minus
import/call-linked files (today's codemem index — an approximation), minus
codemem's default excludes and IMPACT_EXCLUDE. A partner the milestone did NOT
change is a co-change miss = one `Impact-Explained:` line.

Run: python scripts/prototype_m11_cochange_threshold.py <prs.tsv> <index.db>
"""

import fnmatch
import itertools
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict

CONFIGS = [(5, 0.5), (3, 0.5), (5, 0.3)]
WINDOWS = [500, 2000]
MAX_COMMIT_FILES = [None, 10]
IMPACT_EXCLUDE = (
    ".claude/dev/**",
    "docs/architecture/**",
    "tests/golden/**",
    "uv.lock",
    "CHANGELOG.md",
)
CODEMEM_EXCLUDE = {"CHANGELOG.md", "README.md"}
PLANS = {
    "codebase-analysis-skills": [4, 5, 6, 7, 8, 9, 10, 11],
    "sole-dev-merge-fixes": [42, 43, 44, 45, 46],
    "sole-dev-merge-simplify": [55, 58],
    "(ref) code-conventions-impact": [18, 19, 20, 21, 24, 27, 28, 30, 37, 41, 65, 69],
}


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def excluded(p):
    return any(fnmatch.fnmatchcase(p, g) for g in IMPACT_EXCLUDE)


def history(head, window):
    out = git("log", f"-n{window}", "--name-status", "-M", "--format=@@%H", head)
    alive = set(git("ls-tree", "-r", "--name-only", head).splitlines())
    renames, commits, cur = {}, [], None
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = set()
            commits.append(cur)
        elif line.strip():
            parts = line.split("\t")
            if parts[0].startswith("R"):
                new = renames.get(parts[2], parts[2])
                renames[parts[1]] = new
                cur.add(new)
            else:
                cur.add(renames.get(parts[1], parts[1]))
    return [c & alive for c in commits]


def linked_pairs(db):
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = conn.execute(
        """SELECT DISTINCT f1.path, f2.path FROM edges e
           JOIN symbols s1 ON s1.id = e.src_symbol_id JOIN symbols s2 ON s2.id = e.dst_symbol_id
           JOIN files f1 ON f1.id = s1.file_id JOIN files f2 ON f2.id = s2.file_id
           WHERE f1.path != f2.path"""
    ).fetchall()
    return {frozenset(r) for r in rows}


def misses(commits, changed, n, ratio, mcf, linked):
    kept = [c for c in commits if mcf is None or len(c) <= mcf]
    out = defaultdict(set)
    for f in changed:
        mine = [c for c in kept if f in c]
        co = Counter(g for c in mine for g in c if g != f)
        for g, cnt in co.items():
            if cnt < n or cnt < ratio * len(mine):
                continue
            if g in changed or g in CODEMEM_EXCLUDE or excluded(g) or frozenset((f, g)) in linked:
                continue
            out[g].add(f)
    return out


def main(prs_tsv, db):
    prs = {}
    for line in open(prs_tsv):
        n, merge, k, _ = line.rstrip("\n").split("\t")
        prs[int(n)] = (merge, int(k))
    linked = linked_pairs(db)
    print(
        "plan\tPR\tchanged\t"
        + "\t".join(
            f"{n}/{int(r * 100)}%@{w}{'' if m is None else f'/mcf{m}'}"
            for w in WINDOWS
            for m in MAX_COMMIT_FILES
            for n, r in CONFIGS
        )
    )
    totals = Counter()
    detail = defaultdict(dict)
    for plan, nums in PLANS.items():
        for num in nums:
            merge, k = prs[num]
            changed = {
                p
                for p in git(
                    "diff", "--name-only", "-M", f"{merge}~{k}", merge
                ).splitlines()
                if not excluded(p)
            }
            cols = []
            for w in WINDOWS:
                commits = history(merge, w)
                for m in MAX_COMMIT_FILES:
                    for n, r in CONFIGS:
                        miss = misses(commits, changed, n, r, m, linked)
                        key = (plan.startswith("(ref)"), w, m, n, r)
                        totals[key] += len(miss)
                        detail[key][num] = miss
                        cols.append(str(len(miss)))
            print(f"{plan}\t#{num}\t{len(changed)}\t" + "\t".join(cols))
    print(
        "\nTOTAL Impact-Explained lines (last 3 completed plans, 15 milestones | this plan, 12 milestones):"
    )
    for w in WINDOWS:
        for m in MAX_COMMIT_FILES:
            for n, r in CONFIGS:
                print(
                    f"  {n}/{int(r * 100)}% window={w} mcf={m}: {totals[(False, w, m, n, r)]:4d} | {totals[(True, w, m, n, r)]:4d}"
                )
    for ref in (False, True):
        for w, m, n, r in [(500, None, 5, 0.5), (2000, None, 5, 0.5), (500, None, 3, 0.5), (500, 10, 5, 0.5)]:
            print(f"\nMISSES ref={ref} {n}/{int(r*100)}% window={w} mcf={m} (partner <- changed files):")
            for num, miss in detail[(ref, w, m, n, r)].items():
                for g, fs in sorted(miss.items()):
                    print(f"  #{num} {g} <- {', '.join(sorted(fs))[:120]}")


if __name__ == "__main__":
    main(*sys.argv[1:])

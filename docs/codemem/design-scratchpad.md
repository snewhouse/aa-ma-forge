# codemem Design Scratchpad

**Produced during M1 Task 1.0 (pre-flight reading + packaging spike).**
**Date:** 2026-04-13
**Source tasks:** `.claude/dev/active/codemem/codemem-tasks.md` → Task 1.0

This document captures the 5 readings + packaging spike mandated by Task 1.0 and flags every plan-altering finding.

---

## 1. Reading: Aider's `aider/repomap.py`

**Source:** https://github.com/Aider-AI/aider/blob/main/aider/repomap.py

**Algorithm:** NetworkX `pagerank()` with personalization + dangling vectors (both same dict). Damping 0.85 (default), `tol=1e-6`, `max_iter=100`. Edge weights are a **multi-factor heuristic** (not uniform, not pure reference count):

- `mul *= 10` if identifier mentioned in chat
- `mul *= 10` if snake/kebab/camel AND `len >= 8` (filters trivial names like `i`, `x`)
- `mul *= 0.1` if starts with `_` (private)
- `mul *= 0.1` if defined in >5 files (common name, likely noise)
- `use_mul *= 50` if referencer is a chat file
- Final: `weight = use_mul * sqrt(num_refs)` — **square-root dampening** so hot utilities don't dominate

**Binary search:** starts at `middle = min(max_map_tokens // 25, num_tags)`, stops within 15% of budget. Re-renders tree each iteration via `grep_ast.TreeContext`.

**Input model:** `(referencer_file → definer_file)` edges over symbol references — a **symbol co-occurrence graph**, not a call graph or import graph. Uses `MultiDiGraph` (multiple parallel edges per file pair).

**Dependencies:** `networkx`, `diskcache`, `grep_ast`, `pygments`, `tqdm`, `tree_sitter`. **scipy pulled in transitively by `nx.pagerank`.**

**LOC:** **867 total, ~280 in the core algorithm.** Plan's "~50 LOC pure Python" or "~200 LOC" is materially wrong.

### 🔴 Plan-altering findings

**AF-1.** **Aider is NOT pure-Python + stdlib.** It uses NetworkX + scipy + tree-sitter. Our plan implied we'd adopt Aider's algorithm in ~50 LOC pure-Python. That is unrealistic if we copy Aider faithfully.

**AF-2.** **Edge weight heuristics are load-bearing.** Naive `weight = num_refs` produces materially worse maps. The snake_case/length-8 filter, private dampening, >5-definers dampening, `sqrt` dampening, chat-file 50x boost are all quality-critical. We must reimplement or explicitly accept quality hit.

**AF-3.** **Aider's "chat file boost" has no direct analog for codemem.** The 50x boost for files mentioned in chat is Aider's "focus" concept. Codemem runs offline; we'd need an equivalent signal (e.g. files touched in current commit? files in AA-MA task scope?).

---

## 2. Reading: `/index` `scripts/pagerank.py`

**Source:** `/home/sjnewhouse/.claude-code-project-index/scripts/pagerank.py`

**Shape:** 89 LOC pure Python (stdlib only, no numpy/scipy/networkx). Single exported function `compute_pagerank(edges, damping=0.85, iterations=20, tolerance=1e-6)`.

**Granularity:** **Symbol-level**, not file-level. Evidence: edges extracted per function/method name (`fname`, `f"{cname}.{mname}"`); cross-file edges are `src/a.py:func_x → src/b.py:func_y`; output stored per-symbol at `index['_meta']['symbol_importance']`.

**Algorithm:** Pure-Python power iteration with tolerance convergence + max 20 iterations. Handles dangling nodes. No edge weights — all edges treated equally.

**Output:** Top-200 truncated dict `{symbol: score}`, scores rounded to 4 decimals.

### 🔴 Plan-altering findings

**AF-4. CRITICAL — Plan §2 differentiation claim is wrong.** I claimed codemem's symbol-level PageRank is a differentiator over /index's "file-level." **/index is already symbol-level.** Must rewrite §2.

**AF-5. Legitimate differentiators still available:**
- **Edge weighting** — /index has uniform edges; we add Aider-style heuristics (subset of them, without NetworkX)
- **No top-200 truncation** — /index discards tail scores; we keep all
- **SCIP-shaped symbol IDs** — /index uses bare symbol names; ours are `codemem <package> <kind><file>#<symbol-path>`
- **Budget-aware binary search** — /index has no concept of token budgets; we add Aider's binary-search technique

**AF-6.** **We can FORK /index's 89-LOC pagerank.py directly.** Pure Python, stdlib only, matches our constraint. Extend it with weighting + binary search. Realistic target: **~150-200 LOC**, not 50. Update plan Step 1.8.

---

## 3. Reading: repowise `change_detector.py`

**Source:** `/home/sjnewhouse/github_private/repowise/packages/core/src/repowise/core/ingestion/change_detector.py:201-258`

**Algorithm:**
- Same kind prerequisite (matches our plan ✓)
- **Name similarity: `difflib.SequenceMatcher.ratio()` on lowercased names** — NOT Jaccard on tokens
- Line proximity bonus: ±5 lines, +0.2 confidence boost
- Final confidence = `min(name_ratio + line_bonus, 1.0)`
- **Acceptance threshold: 0.65** (NOT 0.7)

**LOC:** ~83 LOC total (`detect_symbol_renames` 59 + `_compute_symbol_diff` 24).

**Dependencies:** `difflib`, `dataclasses`, `pathlib`, `typing` — all stdlib. No numpy/scipy/Levenshtein. ✓ matches our constraint.

### 🔴 Plan-altering findings

**AF-7. Our Jaccard-on-tokens plan is over-engineered.** repowise uses simpler `SequenceMatcher.ratio()` on names only and it's production-tested. Jaccard on tokens requires tokenization logic we'd have to write; SequenceMatcher is stdlib and zero-work.

**AF-8. Our 0.7 threshold is stricter than repowise's 0.65.** Empirical data from repowise suggests 0.65 is sufficient with the +0.2 line-proximity bonus. Our plan's threshold may miss legitimate renames.

**AF-9. Line proximity window should be ±5, not ±2.** repowise uses wider window; our plan's ±2 was tighter without empirical justification.

**Recommended revision:** Update M2 Step 2.1 to use `difflib.SequenceMatcher.ratio()` + threshold 0.65 + ±5 line window. Saves implementation time, matches production reference.

---

## 4. Reading: GitNexus recent issues (last 30 days)

**Source:** https://github.com/abhigyanpatwari/GitNexus

**State:** **27,112 stars** (was ~19k a month ago — accelerating growth).

**Roadmap direction:** Type resolution depth + PDG (Program Dependence Graph, Ferrante 1987 style) + cross-repo contract extraction (HTTP/gRPC/Kafka). **Zero git-mining signals.**

**Recently shipped (SM-1 through SM-23):** Semantic-model refactor (eliminated `lookupFuzzy` in favor of typed HeritageMap/SymbolTable); PHP/Ruby parser fixes; TS generic callers; Spring/C heritage.

**MCP tool names:** `query`, `context`, `impact`, `detect_changes`, `rename`, `group_impact` (plus future `pdg_query`). **They do NOT use `who_calls`, `blast_radius`, or `dead_code`.**

**User pain points to avoid replicating:**
- Scale ceilings (`Maximum call stack size exceeded` on large repos, #706/#752/#772)
- Stale MCP data after re-index (#297, #766)
- 70MB monolithic `/api/graph` response timeouts (#705, #761)
- **Auto-injection of `CLAUDE.md`/`AGENTS.md` into user repos is unwelcome** (#577, #663, #704, #656) — cautionary for our AA-MA coupling design

### Findings

**AF-10.** **Git-mining moat remains uncontested.** Zero signals on hot_spots, co_changes, ownership, symbol_history, layers in GitNexus roadmap/RFCs/issues. Our §12 kill criterion is NOT triggered.

**AF-11.** **Tool naming assumption partly wrong.** Our plan treated `who_calls`/`blast_radius`/`dead_code` as lingua franca — but GitNexus (27k stars) uses different names. Options: (a) align with GitNexus for discovery via Tool Search, (b) differentiate deliberately, (c) add more aliases. **Recommendation:** add aliases `who_calls ↔ impact`, `blast_radius ↔ impact`, `dead_code ↔ find_unused` — our plan's Step 1.10 already mentions aliases; expand the alias list.

**AF-12.** **Pain point learning — avoid "auto-injection"** (users hated GitNexus writing `CLAUDE.md`/`AGENTS.md` into their repos uninvited). **Our `aa_ma_context --write` flag** (Step 3.7) is opt-in by design, but we should make this explicit in the README: codemem never writes to the user's repo without `--write` explicitly passed.

---

## 5. Reading: `/home/sjnewhouse/.claude/docs/lessons.md` — L-052

**Rule:** When the same CLASS of issue appears in 2+ independent QA reviews, treat it as an **architectural deficiency** requiring structural redesign, not a per-report bug fix.

### Application to codemem's "no embeddings in v1" decision

The embeddings exit criterion in plan §8 currently says: "reconsider when `search_symbols` exact-match returns zero results for >20% of agent queries over a 30-day measurement window." L-052 suggests a stricter test: **if we see the same class of "query returned nothing / missed the obvious thing" complaint across multiple users or sessions, that's architectural**, not a per-query tweak.

**Refinement:** Strengthen §8 exit criterion wording to reference L-052 explicitly. Zero plan changes required; it's a framing precision.

---

## 6. Packaging spike

**Three options prototyped mentally; one prototyped on disk.**

### Option A: Single pyproject.toml with "two project blocks"
**Verdict: NOT VIABLE.** PEP 621 doesn't support two `[project]` tables in one pyproject.toml. Attempts via `[project]` + `[tool.something.second-project]` are non-standard and require custom build hooks. Not portable, not discoverable by tools, not KISS.

### Option B: `packages/codemem-mcp/` subdir with uv workspace ✅
**Prototype location:** `/tmp/codemem-spike/`
**Structure:**
```
aa-ma-forge/
├── pyproject.toml              # Root: aa-ma package + [tool.uv.workspace]
├── src/aa_ma/                  # aa-ma package source
│   └── __init__.py
└── packages/codemem-mcp/
    ├── pyproject.toml          # codemem-mcp package (standalone installable)
    └── src/codemem/
        └── __init__.py
```

**Root `pyproject.toml` addition:**
```toml
[tool.uv.workspace]
members = ["packages/codemem-mcp"]
```

**`packages/codemem-mcp/pyproject.toml`:**
```toml
[project]
name = "codemem-mcp"
version = "0.1.0-dev"
requires-python = ">=3.11"
dependencies = ["ast-grep-cli>=0.42,<0.43", "fastmcp>=2.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/codemem"]
```

**Behavior:**
- From `aa-ma-forge/` root: `pip install .` installs aa-ma. `uv sync` resolves workspace, makes codemem-mcp locally importable.
- From `packages/codemem-mcp/`: `pip install .` installs codemem-mcp standalone (no aa-ma dep).
- Published to PyPI as two separate packages.

**Pros:** Clean PEP 517 compliance, native uv workspace support, both packages independently installable, predictable mental model.
**Cons:** Source tree location diverges from plan's `src/aa_ma/codemem/` — need plan update.

### Option C: Hatch build hook
**Verdict: NOT RECOMMENDED.** Requires writing custom Python code in a hatchling plugin to emit two distributions from one tree. Works but violates KISS. Option B achieves the same outcome natively.

### ✅ **Decision: Option B — `packages/codemem-mcp/` with uv workspace.**

### 🔴 Plan-altering findings

**AF-13. Plan Step 1.1 source tree location is wrong.** Plan says `src/aa_ma/codemem/`. Correct location per spike: `packages/codemem-mcp/src/codemem/`. The `claude-code/codemem/` path (user-facing plugin integration) stays the same.

**AF-14. AA-MA integration glue** (the `aa_ma_context` tool implementation) needs a home. Options:
- Inside `packages/codemem-mcp/src/codemem/aa_ma_integration.py` with an optional-import guard (codemem checks if aa-ma-forge is present in PYTHONPATH; no-op if absent). **Preferred** — keeps codemem-mcp single-source-of-truth.
- In `aa-ma-forge/src/aa_ma/codemem_bridge.py` — separate module. Cleaner separation but requires 2 source trees to coordinate.

**Recommendation:** former. Single source for codemem; AA-MA integration is inside codemem-mcp but guarded.

---

## Consolidated plan-altering findings (14 total)

| ID | Severity | Finding | Plan impact |
|---|---|---|---|
| AF-1 | HIGH | Aider uses NetworkX + scipy, not pure Python | Step 1.8 LOC estimate wrong (~50 → ~150-200) |
| AF-2 | HIGH | Edge weight heuristics are load-bearing | Step 1.8 must implement subset of Aider weights |
| AF-3 | MED | Aider's chat-file boost has no codemem analog | Decide on equivalent "focus" signal (AA-MA task scope?) |
| AF-4 | **CRITICAL** | /index is already symbol-level PageRank | Plan §2 differentiation claim must be rewritten |
| AF-5 | INFO | Legitimate differentiators: edge weights, SCIP IDs, no truncation, binary search | Update §2 with correct claims |
| AF-6 | HIGH | Can fork /index's 89-LOC implementation | Step 1.8 approach: fork + extend, not from-scratch |
| AF-7 | MED | repowise uses SequenceMatcher, not Jaccard | Step 2.1 simplify algorithm |
| AF-8 | MED | 0.65 threshold works; 0.7 too strict | Step 2.1 adjust threshold |
| AF-9 | LOW | Line proximity ±5 not ±2 | Step 2.1 adjust window |
| AF-10 | INFO | Git-mining moat still uncontested | Reaffirms §12 kill criteria |
| AF-11 | MED | GitNexus uses different MCP tool names | Step 1.10 expand alias list |
| AF-12 | LOW | Avoid auto-injection of files into user repos | README must make this explicit |
| AF-13 | **CRITICAL** | Source tree location wrong | Step 1.1 revise: `packages/codemem-mcp/src/codemem/` |
| AF-14 | MED | AA-MA integration needs a home | Decision: inside codemem-mcp with optional-import guard |

---

## Required plan updates

The following minimum plan edits are required before Task 1.1 starts. I will batch these into a single plan-revision commit referencing this scratchpad.

1. **§2 rewrite** — remove "file-level vs symbol-level" framing. New framing: /index has basic symbol PageRank; codemem adds edge weighting (subset of Aider heuristics), binary-search budget fit, SCIP IDs, no top-k truncation.
2. **Step 1.1 source tree** — change `src/aa_ma/codemem/` → `packages/codemem-mcp/src/codemem/`. Add `[tool.uv.workspace]` to root pyproject.
3. **Step 1.8** — realistic LOC (~150-200); approach = fork `/index/scripts/pagerank.py` + extend with weight heuristics + binary search.
4. **Step 1.10** — expand alias list: add `who_calls↔impact`, `blast_radius↔impact`, `dead_code↔find_unused` for GitNexus-style discovery.
5. **Step 2.1** — algorithm: `difflib.SequenceMatcher.ratio()` on names + ±5 line proximity bonus +0.2; threshold 0.65.
6. **Step 3.7 — aa_ma_context** — lives inside codemem-mcp with optional-import guard; explicitly documented as opt-in write (`--write` flag) to avoid GitNexus's auto-injection pain point.

## Nothing else changes

- All 12 MCP tools stay in scope.
- Distribution model unchanged (aa-ma-forge plugin + standalone pip).
- SQLite schema, WAL JSONL design, kill criteria, SCIP grammar — all unchanged.
- Performance SLOs unchanged.

---

**End of scratchpad.** Ready for plan revision + Task 1.0 completion.

# kill criteria

Measurable, time-boxed signals that would cause us to abandon or pivot codemem. Public and honest — if any of these fires, we'll say so here rather than quietly walking away from the project.

The thresholds are taken verbatim from the plan document's §12, which came out of the CEO-review step of AA-MA planning (Phase 4.2a). Status lines are added here as milestones close. Latest update: 2026-04-20 (Signal 2 Aider sub-claim folded in from the `codemem-token-benchmarks` plan).

## The 5 signals

### 1. 30-day post-ship signal-kill

**Trigger:** 30 days after public release, fewer than 25 GitHub stars on aa-ma-forge AND fewer than 5 external installs of codemem by users outside this project.

**Action:** Fold the useful capabilities back into [`/index`](https://github.com/ericbuess/claude-code-project-index) as upstream contributions and discontinue codemem as a separate project.

**Why:** If nobody outside this project adopts it, the SQLite-canonical architecture plus git-mining thesis isn't winning on its merits. Better to give Eric's tool the fixes than maintain a parallel unused codebase.

**Status (2026-04-17):** Not applicable yet — has not been publicly announced. Threshold needs a small re-baseline when ship day arrives: the original plan assumed a `pip install codemem-mcp` wheel channel which was removed in M3.5 Task 3.5.4 per AD-Q15 (plugin-only distribution). "External installs" in practice now means "users running `scripts/install.sh` from a fresh clone of aa-ma-forge."

### 2. M1 architectural kill

**Trigger:** `codemem build` > 1.5× `/index` wall-clock on reference repos AND `PROJECT_INTEL.json` at `--budget=1024` fails to beat Aider's repo-map token efficiency at the same budget.

**Action:** Abandon the SQLite-canonical architectural bet and revert to an in-memory approach closer to `/index`.

**Why:** The core speed-plus-efficiency claim is what justifies the schema complexity. Without it, the extra engineering isn't earning its keep.

**Status (2026-04-20):** Composite verdict remains **PROVISIONAL DID-NOT-TRIGGER**. Updated 2026-04-20 to fold in the Aider token-efficiency benchmark (plan `codemem-token-benchmarks`, Task 4.2).

**Conjunct (a), `codemem build` wall-clock:** cleared on the small reference repo (aa-ma-forge) at **0.73× `/index` wall-clock**, 27% faster and well inside the 1.5× ceiling. Full numbers in [`docs/benchmarks/codemem-vs-index.md`](../benchmarks/codemem-vs-index.md). Medium-repo and 50k-LOC wall-clock benchmarks are pending user-provided reference repos; the reusable bench script is at [`scripts/bench_codemem.py`](../../scripts/bench_codemem.py).

**Conjunct (b), Aider token-efficiency:** **FAILS on both repos exercised to date**. Measured 2026-04-20 on aa-ma-forge (small reference repo) and `tiangolo/fastapi` 0.136.0 (secondary reference, not the user-to-provide medium repo that the kill-criteria matrix specifies). In `cl100k_base` tokens, Aider is 2.4× more token-efficient per symbol on aa-ma-forge (codemem 72.8 tok/sym vs Aider 30.0) and 1.2× more efficient on fastapi (codemem 57.5 vs Aider 47.3). Full methodology, tables across four budgets `{512, 1024, 2048, 4096}`, and root-cause analysis in [`docs/benchmarks/codemem-vs-aider.md`](../benchmarks/codemem-vs-aider.md).

**Composite verdict:** The AND composite does not fire, because conjunct (a) holds on the only repo where it has been measured and a single-conjunct failure cannot trigger an AND. Conjunct (b)'s failure is recorded as a **risk-signal to monitor**, not a kill. The benchmark's "Implications for kill-criteria Signal 2" section identifies a two-fold root cause: (1) codemem's 4-chars-per-token proxy under-reports its own token use by ~20% versus `cl100k_base`, and (2) codemem's structured per-entry metadata (SCIP ID, file, line, kind, rank) is genuinely more verbose than Aider's signature-line format. Neither root cause demands an architectural rewrite of the SQLite-canonical bet, which is the failure mode Signal 2 was designed to detect. Medium-repo and 50k-LOC wall-clock measurements remain the gate on flipping the composite from PROVISIONAL to PINNED.

### 3. M3 headline-tool kill

**Trigger:** `co_changes()` produces more noise than signal on 2 out of 3 test repos. Quantified: manual evaluation of the top-5 results shows fewer than 50% are meaningful couplings (files that genuinely change together for shared reasons, not just files co-touched in mechanical sweeps).

**Action:** Drop `co_changes` from the tool surface and reposition from "5 git-mining tools" to 4. Keep `hot_spots`, `owners`, `symbol_history`, `layers` — those are individually defensible on their own merits.

**Why:** `co_changes` carries the differentiator story in the README ("files that change together without importing each other"). If it doesn't work on real codebases, the differentiator is a lie.

**Status (2026-04-17):** Not formally evaluated across 3 repos yet. Small-repo (aa-ma-forge) smoke during M3 development and M3.5 live verification returned sane results (no absurd pairings), but that's smoke, not a manual top-5 evaluation. This signal cannot fire meaningfully until 3-repo evaluation is done — that work is implicitly blocked by the same medium-and-large reference repos that gate Task 4.1 benchmarks.

### 4. Anytime moat-evaporated kill

**Trigger:** GitNexus or Axon (or any subsequent entrant) ships git-mining coverage for 3 or more of codemem's 5 differentiator tools (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`) with comparable UX.

**Action:** Pivot positioning. The AA-MA coupling tool (`aa_ma_context`) becomes the primary differentiator; the git-mining five become "also works."

**Why:** Git-mining alone isn't defensible long-term against well-funded entrants — it's too easy to clone the feature set once the interface is public. AA-MA coupling is harder to copy because it's wired into our own memory architecture, not a generic code-intelligence concern.

**Status (2026-04-17):** Still alive. [GitNexus](https://github.com/abhigyanpatwari/GitNexus) (~27k stars, tree-sitter + MCP tool surface `impact` / `context` / `detect`) does not yet ship git-mining tools, per the landscape research recorded in Task 4.4. The [Axon](https://github.com/harshkedia177/axon) variants are graph-DB plus embeddings-focused and occupy a different tradeoff space (semantic retrieval rather than history-aware coupling). No entrant observed that combines git-mining breadth with comparable UX. This signal is the one to watch most closely.

### 5. M2 correctness-risk kill

**Trigger:** The WAL-journal crash-injection test cannot be made deterministic — specifically, flaky or non-reproducible results across CI runs.

**Action:** Drop the JSONL write-ahead log feature entirely and ship M1 plus M3 only. Users would rebuild from scratch on corruption instead of having WAL-replay recovery.

**Why:** If crash recovery isn't testable deterministically, we can't meaningfully claim correctness. A crash-recovery feature you can't prove works is worse than no feature — it trades a simple failure mode (rebuild from git) for a silent one (corrupt index that still opens).

**Status (2026-04-17):** Did NOT trigger. M2 Task 2.3 shipped a deterministic crash-injection gate in [`journal/wal.py`](../../packages/codemem-mcp/src/codemem/journal/wal.py) with a 4-branch replay state diagram and `test_property_roundtrip_slow` hypothesis coverage at 100 examples (~3.5s per run, opt-in via `pytest -m slow`). Crash-between-intent-and-commit scenarios are reproducible — the tests construct the intermediate filesystem state explicitly rather than racing for it. M2 closed cleanly; subsequent milestones have not observed any flake on these tests.

---

## Methodology

- Thresholds are taken verbatim from the plan document §12 (2026-04-13, CEO review Phase 4.2a). We don't move goalposts.
- Status annotations update at milestone boundaries. Next review: post-M4 ship.
- A fired signal is not automatically an abandonment — it's a forcing function for an honest scope conversation. We commit the outcome of that conversation here either way.

## What this doc is not

- Not a competitor comparison. See the [README's landscape section](../../claude-code/codemem/README.md#whats-different--the-landscape-fairly).
- Not a roadmap of intended work. Planning artefacts live under `.claude/dev/active/codemem/`.
- Not a service-level agreement. There's no external user contract to breach — this is a one-person side project and the MS acknowledgment in the README stands.

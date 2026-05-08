# codemem: positioning

**Decided 2026-05-08, after the codemem-benchmark-fairness-v2 plan closed.**

This document is the durable rationale for how codemem positions itself, why, and what the watch conditions are for revisiting.

---

## The decision

**Codemem is the structured code-memory tier of AA-MA. It is not a competitor to aider's repo-map for LLM prompt injection.**

The two tools serve different consumer profiles. Codemem is for programmatic consumers: another tool, an agent, an audit pipeline, a memory-system layer that wants `(file, line, kind, rank)` tuples to filter or rank or join against. Aider's repo-map is for LLM prompt injection: dense signature skeletons designed to fit inside a context window where every token is competing.

Both designs are correct. They are not substitutes.

---

## Why this is the right framing now

The codemem-benchmark-fairness-v2 work measured both tools honestly with cl100k_base on both sides (the M1 fix removed codemem's 4-chars-per-token proxy; the M2a `--model gpt-3.5-turbo` flag routed aider through the same tokeniser via litellm). The empirical result on the small reference repo (aa-ma-forge) was that aider is 2.3× more token-efficient per symbol than codemem at budget=1024. The full sweep across 4 budgets and 2 repos confirmed the gap is structural, not measurement noise: codemem's per-entry metadata (SCIP ID + file + line + kind + rank) is verbose by design because it's built for programmatic consumption. Aider's signature-line format is dense by design because it's built for LLM prompt injection.

This is not a problem to solve. It is the right shape for two tools that serve different consumers.

The interesting v2 finding was elsewhere. On fastapi (the larger reference repo), codemem reaches per-symbol parity with aider at budget=1024 (1.07× ratio). The metadata-overhead penalty amortises out as the symbol pool grows. That confirms codemem scales correctly without changing its output format. It also means: for programmatic consumers operating on real-sized repos, codemem and aider are not measurably different on the size axis. The differentiation lives elsewhere.

---

## Where codemem's actual value lives

The kill-criteria documents this already (Signal 4): **AA-MA coupling is the durable moat.** The `aa_ma_context` tool reads an AA-MA task's reference and tasks files, queries the codemem index for the symbols and files mentioned, and returns a filtered hot-spots / owners / blast-radius package. This is the single tool in the panel that no competitor can ship without copying the AA-MA architecture itself. Git-mining tools (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`) are differentiators today but commoditisable; tree-sitter-equipped competitors can replicate them.

So the value stack, ranked by how durable each layer is:

1. **AA-MA coupling (`aa_ma_context`).** Hardest to copy because it requires copying the memory architecture. This is the moat.
2. **Git-mining quintet** (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`). Differentiating now; expect competitors to land 3+ of these within 90 days. Signal 4 watch handles this.
3. **Call-graph + symbol-search ports** (`who_calls`, `blast_radius`, `dead_code`, `dependency_chain`, `search_symbols`, `file_summary`). Useful, mostly commoditised already (existing in `/index`, GitNexus, etc.). Not a moat layer.

---

## What the v2 work changed

It made the per-symbol comparison honest in both directions, and confirmed:

- Codemem's M1 fix (cl100k_base honest budget enforcement) is empirically correct: 8 cells across 2 repos, every cell at-or-under requested budget.
- Codemem reaches per-symbol parity with aider on fastapi at budget=1024 (1.07× vs aider).
- The two tools' outputs are different shapes for different consumers, not better-or-worse on a single axis.

It did not produce a "codemem beats aider" headline, and it should not. That framing was the wrong question for the wrong consumer profile.

---

## What this means in practice

**README and onboarding language drops the "vs aider" comparison entirely.** Both `packages/codemem-mcp/README.md` and `claude-code/codemem/README.md` now lead with "structured code memory tier for AA-MA" rather than "code-intelligence tool" or "repo-map alternative." Standalone use is still supported; it is documented as a secondary surface, not the headline.

**Future benchmarks do not re-litigate v2.** The v2 report at [`codemem-vs-aider-v2.md`](../benchmarks/codemem-vs-aider-v2.md) is the durable artifact. Future work focuses on AA-MA workflow value, not codemem-vs-other comparisons. v2 is the last v-something.

**Signal 4 is the primary risk to watch.** If GitNexus, Axon, or any new entrant ships 3+ of the git-mining differentiators at comparable UX before the next 90-day review (2026-08-06), codemem consolidates fully under AA-MA's umbrella and the standalone framing drops. If no entrant fires by 2026-08-06, hold positioning steady and re-set the watch for another 90 days.

**Codemem's data layer (the SQLite index) is not changed.** The architecture is sound; the test suite is 420 passes; the M1 fix is empirically correct. No code work follows from this positioning shift.

---

## What we are NOT doing

- **Not deprecating codemem.** Signal 1 (30-day post-ship adoption) hasn't fired (it can't, since codemem hasn't shipped publicly yet). The data tier is the right substrate for AA-MA's memory architecture and that role is unchanged.
- **Not rewriting any code for positioning purposes.** The architecture is fine; the per-symbol gap on small repos is structural to the consumer-profile difference and does not warrant changing the output format.
- **Not chasing per-symbol efficiency on small repos.** Aider wins by 2.3× on aa-ma-forge and the structural reason is real (metadata vs signature lines). Trying to close this would mean dropping the structured-output format, which kills the programmatic-consumption use case and the AA-MA coupling that depends on it.
- **Not running another fairness benchmark.** v2 is the durable record. v3 only happens if Signal 4 fires and the consolidation requires fresh measurement.

---

## Watch dates

| Date | Action |
|------|--------|
| 2026-08-06 | Signal 4 review. Search GitNexus / Axon / repomix / yek / new-entrant release notes and tool indexes for git-mining tools matching codemem's differentiator-five (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`). If 3+ are matched at comparable UX, fire Signal 4 and consolidate codemem under AA-MA. If 0-2 are matched, hold and re-set the watch for 2026-11-04. |
| TBD | Reach the medium-repo (5-20k Python LOC) and 50k-LOC reference repos that gate kill-criteria conjunct (a). When those measurements land, the composite verdict can flip from PROVISIONAL to PINNED. |

---

## Cross-references

- v2 fair-benchmark report: [`docs/benchmarks/codemem-vs-aider-v2.md`](../benchmarks/codemem-vs-aider-v2.md)
- v1 historical report (pre-M1): [`docs/benchmarks/codemem-vs-aider.md`](../benchmarks/codemem-vs-aider.md)
- Kill criteria including Signal 4 watch: [`docs/codemem/kill-criteria.md`](./kill-criteria.md)
- Architecture: [`docs/codemem/ARCHITECTURE.md`](./ARCHITECTURE.md)
- Archived v2 plan: `.claude/dev/completed/codemem-benchmark-fairness-v2/`

---

_Last updated: 2026-05-08_

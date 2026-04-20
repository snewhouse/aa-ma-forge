# codemem vs Aider repo-map: token-budget benchmark

Comparative token-efficiency and top-symbol-overlap benchmark for the codemem
`PROJECT_INTEL.json` rank-ordered context, [Aider](https://github.com/Aider-AI/aider)'s
`--show-repo-map` output, and [jCodeMunch](https://github.com/jgravelle/jcodemunch-mcp)'s
`get_ranked_context` at matched requested-budget levels on two reference repos.

This benchmark continues Task 4.2 from the archived codemem plan, which was
deferred on 2026-04-17 pending output-format research. The preconditions were
resolved by three parallel research agents on 2026-04-18; execution ran
2026-04-20.

Raw data: [`results-codemem-vs-aider-2026-04-18.json`](./results-codemem-vs-aider-2026-04-18.json).

---

## The tokeniser-mismatch caveat (read first)

The three tools count token budgets in three different units.

| Tool | Unit | Counted at |
|---|---|---|
| codemem | 4 characters = 1 token (proxy) | emission time, inside `pagerank.py` |
| Aider | tiktoken against the configured model (default `gpt-4`) | emission time, inside `aider/repomap.py` |
| jCodeMunch | tiktoken `cl100k_base` | emission time (MCP-runtime) |

A "requested budget of 1024" therefore means three different things. Comparing
raw output sizes at matched requested budget would be apples-to-oranges.

The harness normalises across this by recording three numbers per
measurement:

1. `raw_bytes`: UTF-8 byte length of the tool's output
2. `tiktoken_tokens`: re-tokenised count using `cl100k_base` (a fixed external reference)
3. `symbol_count`: number of semantic units (symbols, signature lines, or ranked entries)

All comparisons below use `tiktoken_tokens` as the common size axis.
`symbol_count` is the common coverage axis. Raw bytes are recorded for
auditability but are not the basis for any verdict.

---

## Methodology

- Harness: `scripts/bench_codemem_vs_aider.py` + `scripts/bench_sweep.py` (median of 3 runs per cell, per AD-006).
- Tokeniser: `tiktoken.get_encoding("cl100k_base")`.
- Overlap metric: Jaccard on `(file, symbol_name)` tuples across tool pairs.
- Budget sweep: `{512, 1024, 2048, 4096}` (requested, passed to each tool's own budget flag).
- Repos: `aa-ma-forge` (own repo, HEAD `c24d665`) and `tiangolo/fastapi` at tag `0.136.0` (SHA `708606c9`, 1119 Python files, 56 MB).
- jCodeMunch is stubbed as `status=skipped` (decision AD-012): the `get_ranked_context` surface is available only via the MCP JSON-RPC protocol and has no CLI entry point. A live MCP round-trip remains out of scope for this benchmark. Its cells are recorded with explicit `skipped` status, not silent zeros.

All tool versions and install commands are pinned in
[`reference.md`](../../.claude/dev/active/codemem-token-benchmarks/codemem-token-benchmarks-reference.md)
(`aider-chat==0.86.2`, `jcodemunch-mcp==1.59.1`, `tiktoken>=0.7`). Reproducibility
notes are at the bottom of this file.

---

## Results

### aa-ma-forge (own repo, 67 files, `c24d665`)

| budget | tool | symbols | tiktoken_tokens | raw_bytes | tokens/symbol | overshoot vs requested |
|---:|---|---:|---:|---:|---:|---:|
| 512 | codemem | 8 | 591 | 1 933 | 73.9 | +15% |
| 512 | aider | 38 | 1 097 | 3 644 | 28.9 | +114% |
| 512 | jcodemunch | 0 | 0 | 0 | n/a | skipped |
| 1024 | codemem | 17 | 1 239 | 4 003 | 72.9 | +21% |
| 1024 | aider | 67 | 1 995 | 6 509 | 29.8 | +95% |
| 1024 | jcodemunch | 0 | 0 | 0 | n/a | skipped |
| 2048 | codemem | 35 | 2 513 | 8 016 | 71.8 | +23% |
| 2048 | aider | 132 | 3 950 | 12 659 | 29.9 | +93% |
| 2048 | jcodemunch | 0 | 0 | 0 | n/a | skipped |
| 4096 | codemem | 72 | 5 168 | 16 333 | 71.8 | +26% |
| 4096 | aider | 268 | 8 408 | 27 973 | 31.4 | +105% |
| 4096 | jcodemunch | 0 | 0 | 0 | n/a | skipped |

### fastapi (`tiangolo/fastapi` 0.136.0, 1119 files, `708606c9`)

| budget | tool | symbols | tiktoken_tokens | raw_bytes | tokens/symbol | overshoot vs requested |
|---:|---|---:|---:|---:|---:|---:|
| 512 | codemem | 9 | 544 | 1 856 | 60.4 | +6% |
| 512 | aider | 24 | 1 136 | 4 311 | 47.3 | +122% |
| 512 | jcodemunch | 0 | 0 | 0 | n/a | skipped |
| 1024 | codemem | 21 | 1 208 | 4 032 | 57.5 | +18% |
| 1024 | aider | 48 | 2 167 | 8 285 | 45.1 | +112% |
| 1024 | jcodemunch | 0 | 0 | 0 | n/a | skipped |
| 2048 | codemem | 42 | 2 389 | 8 116 | 56.9 | +17% |
| 2048 | aider | 98 | 4 742 | 18 332 | 48.4 | +132% |
| 2048 | jcodemunch | 0 | 0 | 0 | n/a | skipped |
| 4096 | codemem | 88 | 4 853 | 16 232 | 55.1 | +18% |
| 4096 | aider | 178 | 8 634 | 33 893 | 48.5 | +111% |
| 4096 | jcodemunch | 0 | 0 | 0 | n/a | skipped |

### Top-symbol overlap (Jaccard on `(file, symbol_name)` pairs)

| budget | aa-ma-forge | fastapi |
|---:|---:|---:|
| 512 | 0.048 | 0.069 |
| 1024 | 0.125 | 0.133 |
| 2048 | 0.171 | 0.124 |
| 4096 | 0.253 | 0.157 |

---

## Per-signal verdict

### Signal A: size (tokens per symbol at matched tiktoken tokens)

Aider packs more symbols per token than codemem on both repos.

- aa-ma-forge: codemem averages 72.8 tokens/symbol; Aider averages 30.0 tokens/symbol. Aider is 2.4× more token-efficient per symbol.
- fastapi: codemem averages 57.5 tokens/symbol; Aider averages 47.3 tokens/symbol. Aider is 1.2× more token-efficient per symbol.

The gap narrows substantially on the larger repo. On aa-ma-forge, codemem's
per-symbol cost is dominated by the SCIP ID format (`repo/path/to/file.py::ClassName#method#() → None`) plus full `{file, line, rank, kind}` metadata on
every entry. On fastapi the same payload format amortises across a deeper
symbol pool (more classes, more qualified names), so codemem's per-symbol
overhead looks less extreme.

Aider's per-symbol cost is roughly flat: its output is one signature line
per symbol with elision markers between files, so it scales with the
signature text rather than with metadata.

The codemem proxy (4 chars per token) systematically under-reports its
own token use by 6-26% versus cl100k_base. Aider over-reports versus
cl100k_base by 93-132% (it counts against the configured model, which
on default `gpt-4` produces budgets looser than `cl100k_base`). At
"equal requested budget", Aider therefore emits roughly twice the actual
tokens codemem does, which accounts for most of the raw symbol-count gap.

### Signal B: coverage (top-symbol overlap)

The two tools disagree about what matters.

Jaccard overlap on `(file, symbol_name)` pairs stays low at every budget:
5-25% on aa-ma-forge, 7-16% on fastapi. Overlap grows monotonically with
budget on aa-ma-forge but is flatter on fastapi. Neither tool's top-N is
a subset of the other's.

Both tools claim to rank by PageRank, yet they select largely different
symbols. Plausible contributors:

- codemem PageRanks over a symbol-reference graph built from SCIP+tree-sitter facts; Aider PageRanks over a tree-sitter-emitted symbol-reference graph (`aider/repomap.py:525`). Both call the algorithm PageRank, but the edges that feed the algorithm are not the same graph.
- codemem's budget mechanism (`pagerank.py:132-194`) is a binary-search prefix over a rank-sorted list, measured in characters (via the 4-chars/token proxy). Aider's budget mechanism is tiktoken-counted against the configured model. Two different decisions about which "next" symbol fits within budget.
- Tie-breaking at equal rank is non-deterministic in aider at budget=4096 (observed jitter 161/178/187 on fastapi across three runs, corrected by the median-of-3 protocol). codemem was fully deterministic across all runs on both repos.

### Signal C: qualitative (what each tool gives a caller)

The outputs are not substitutes. They serve different consumers.

- codemem emits structured JSON: `{scip_id, name, kind, file, line, rank: float}` per entry, rank-sorted. Intended for programmatic consumption (another tool pulling `file` + `line` to read source, or filtering on `kind == "class"`).
- Aider emits hybrid prose/markdown: tree-sitter-style signature skeletons grouped by file, with `│def`/`│class`/`│@` line prefixes and `⋮` elision between grouped symbols. Intended for direct injection into an LLM's prompt window.
- jCodeMunch (per Phase-3 research) emits structured JSON at the MCP protocol level, with per-symbol metadata similar to codemem. Not exercised here.

A caller that wants to feed an LLM context will find Aider's output denser
per token. A caller that wants to filter symbols by kind, jump to line
numbers, or rank programmatically will find codemem's output more usable.

---

## Implications for kill-criteria Signal 2

The archived codemem plan defines Signal 2 (the M1 architectural kill) as a
composite:

> `codemem build` > 1.5× `/index` wall-clock on reference repos **AND** `PROJECT_INTEL.json` at `--budget=1024` fails to beat Aider's repo-map token efficiency at the same budget.

Both conjuncts must hold for the composite to fire.

- **Conjunct (a), build wall-clock:** cleared on aa-ma-forge (the small reference repo) at 0.73× `/index` wall-clock per [`codemem-vs-index.md`](./codemem-vs-index.md). Medium-repo and 50k-LOC wall-clock measurements are still pending user-provided reference repos. Conjunct (a) is therefore PROVISIONAL DID-NOT-TRIGGER, small-repo only.

- **Conjunct (b), token efficiency vs Aider:** codemem loses the per-symbol comparison on aa-ma-forge (small reference repo) and on fastapi (secondary reference repo, not the user-to-provide medium repo specified in the kill-criteria matrix) at all four budgets. Aider is 1.2-2.4× more token-efficient per symbol measured in cl100k_base tokens. Conjunct (b) **FAILS on both repos measured here**. The user-to-provide medium and 50k-LOC repos remain pending.

The composite verdict: Signal 2 remains **PROVISIONAL DID-NOT-TRIGGER**,
because conjunct (a) is cleared on the only repo where it has been
measured. A single-conjunct failure cannot fire an AND composite.

Conjunct (b)'s failure is recorded as a **risk-signal to monitor**, not a
kill. The root cause is two-fold:

1. **Tokeniser proxy.** codemem's 4-chars-per-token proxy under-reports its
   own token usage by ~20% versus cl100k_base. Switching to a cl100k_base
   counter inside the `pagerank.py` budget loop would yield honest
   per-symbol budgets but would not, on its own, close the 2.4× per-symbol
   efficiency gap on the small repo.
2. **Output format overhead.** codemem's per-entry metadata (SCIP ID +
   file + line + kind + rank) is genuinely more verbose than Aider's
   signature-line format. This is a design trade: codemem's output is
   structured for programmatic consumption; Aider's is shaped for prompt
   injection. If codemem is ever used specifically as an LLM-prompt
   injection path, a condensed output mode (e.g. `file:line name`) would
   close most of the gap.

Neither root cause demands an architectural rewrite of the SQLite-canonical
bet, which is what Signal 2 was designed to detect. The kill-criteria
file's Signal 2 status line is updated to reflect this finding.

---

## Reproducibility

```bash
# Install (from aa-ma-forge checkout, at HEAD c24d665 or later)
uv sync
uv tool install aider-chat==0.86.2
uv tool install jcodemunch-mcp==1.59.1

# Pre-build codemem index on target repo if it is a fresh clone (OBS-002)
cd /tmp/bench-fastapi && uv run --project <aa-ma-forge-root> codemem build && cd -

# Single-budget measurement
uv run python scripts/bench_codemem_vs_aider.py \
    --repo . \
    --requested-budget 1024 \
    --out /tmp/bench-single.json

# Full sweep (median of 3 runs per cell)
uv run python scripts/bench_sweep.py \
    --repo . \
    --out /tmp/bench-aa-ma-forge.json

uv run python scripts/bench_sweep.py \
    --repo /tmp/bench-fastapi \
    --out /tmp/bench-fastapi.json
```

All commands pinned in
[`reference.md`](../../.claude/dev/active/codemem-token-benchmarks/codemem-token-benchmarks-reference.md).

- Trials: 3 per cell; median selected via `statistics.median` (AD-006).
- Environment: WSL2 Ubuntu 24.04 / Linux 6.6.87.2; Python 3.13.x; `uv` 0.7.19.
- Tokeniser: `cl100k_base`, chosen because it matches jCodeMunch's internal
  unit and is a stable external reference.
- Overlap metric: Jaccard on `(file, symbol_name)` tuples. Empty-intersect-empty returns 0.0 rather than NaN to keep downstream aggregation simple.

---

## Known gaps

- **jCodeMunch row is stubbed.** `get_ranked_context` is MCP-protocol only. A live MCP round-trip (stdio JSON-RPC) is a bounded piece of work (estimated 0.5 day) that would add a fourth tool to the comparison, and is listed in the context log as a follow-up rather than a blocker for this benchmark's conclusion.
- **Two repos is a small sample.** aa-ma-forge is 67 Python files; fastapi is 1119. A medium-sized repo (5-20k Python LOC) and a large one (50k+ LOC) would strengthen any claim that the tokens-per-symbol gap narrows monotonically with repo size. The same user-supplied repos that gate `codemem-vs-index.md`'s medium+large cells would apply here.
- **Aider's budget counter depends on the configured model.** Benchmark ran against Aider's default (`gpt-4`). A different model setting would shift Aider's overshoot numbers without changing the per-symbol efficiency finding, since tokens/symbol is a ratio.
- **Non-determinism note.** Aider at budget=4096 shows small run-to-run symbol-count jitter on fastapi (161/178/187 across three runs); median-of-3 absorbs it. Codemem was fully deterministic: all 8 codemem cells (2 repos × 4 budgets) produced identical symbol counts across three runs each.

---

_Measured 2026-04-20. Raw data in
[`results-codemem-vs-aider-2026-04-18.json`](./results-codemem-vs-aider-2026-04-18.json)._

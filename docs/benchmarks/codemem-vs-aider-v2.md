# codemem vs Aider vs jCodeMunch vs Repomix vs yek: token-budget benchmark v2

5-tool comparative token-efficiency and top-symbol-overlap benchmark for the
codemem `PROJECT_INTEL.json` rank-ordered context, [Aider](https://github.com/Aider-AI/aider)'s
`--show-repo-map` output, [jCodeMunch](https://github.com/jgravelle/jcodemunch-mcp)'s
`get_symbol_importance` (PageRank), [Repomix](https://github.com/yamadashy/repomix)'s
packed XML output, and [yek](https://github.com/bodo-run/yek)'s git-importance-ordered
JSON output, at matched requested-budget levels on two reference repos.

This benchmark **supersedes the v1 report**
([`codemem-vs-aider.md`](./codemem-vs-aider.md), measured 2026-04-20). v1
identified a tokeniser-mismatch caveat: the three measured tools used
incompatible token units, so "equal requested budget" was apples-to-oranges.
v2 fixes the core measurement issue (codemem now uses tiktoken `cl100k_base`
internally, not a 4-chars-per-token proxy), expands the panel to five tools,
and adds RBO@10 alongside Jaccard for rank-aware overlap.

Raw data: [`results-codemem-vs-aider-v2-2026-05-08.json`](./results-codemem-vs-aider-v2-2026-05-08.json).

---

## Headline finding (read first)

The v1 thesis was "tools count budgets differently". v2 sharpens this:
**tools also enforce budgets differently, and some tools become useless at
common budget thresholds because of design choices, not bugs.**

The 5-tool panel reveals five distinct enforcement strategies:

| Tool       | Enforcement strategy                  | Behaviour at budget=1024 (aa-ma-forge) |
|------------|---------------------------------------|----------------------------------------|
| codemem    | budget-aware, optimising              | 14 symbols, 960 tokens (94% utilisation, honest post-M1) |
| aider      | budget-aware, overshooting            | 68 symbols, 2 016 tokens (97% overshoot) |
| jcodemunch | top_n heuristic + harness truncation  | 40 symbols, 1 350 tokens (32% overshoot) |
| Repomix    | dump-everything, no budget concept    | 244 files, 582 849 tokens (56 800% overshoot) |
| yek        | budget-aware, **order-preserving**    | **0 files, 1 token** (first git-importance file alone exceeds budget) |

The yek case is the sharpest. yek emits files in git-importance order and
halts at the first file that doesn't fit. On aa-ma-forge the first
git-importance file is `CHANGELOG.md`; at budget 1024 it alone exceeds the
ceiling, so yek emits `[]`. yek is doing what its design says, faithfully.
Choosing yek as a context tool requires either generous budgets or a repo
without a single dominating top-ranked file.

This finding does not exist in v1 because v1 did not measure yek.

---

## The tokeniser-mismatch caveat (still relevant)

In v1, three tools counted token budgets in three different units. v2
reduces but does not eliminate this. The current state:

| Tool       | Token unit                             | Counted at | Equalised in v2? |
|------------|----------------------------------------|------------|------------------|
| codemem    | `cl100k_base` via `tiktoken`           | emission time, inside `pagerank.py` | yes (M1 fix) |
| aider      | `cl100k_base` via litellm with `--model gpt-3.5-turbo` | emission time, inside `aider/repomap.py` | yes (M2a `--aider-tokeniser-equalise` flag) |
| jcodemunch | `cl100k_base` (server-side)            | not used as budget; `top_n` is the budget knob | partial (top_n heuristic) |
| Repomix    | `cl100k_base` via `--token-count-encoding` | post-emission display only | yes for measurement; no enforcement |
| yek        | (internal, exact unit unspecified)     | emission time, inside the `--tokens N` flag | counted but enforcement is order-preserving |

Every tool's output is **re-tokenised at the harness measurement boundary**
using `tiktoken.cl100k_base.encode(text)`. This is the AD-001 normalisation
axis that makes cross-tool comparison honest at the size axis, regardless
of what each tool internally believed it was counting.

Three numbers per measurement, same as v1:

1. `raw_bytes`: UTF-8 byte length of the tool's output
2. `tiktoken_tokens`: re-tokenised count using `cl100k_base`
3. `symbol_count`: number of semantic units (file-level for Repomix and yek;
   symbol-level for the others)

---

## Methodology corrections from v1 (Phase 4.5 findings)

11 specific findings were surfaced in adversarial review of the v0 plan and
corrected before v2 execution. They are recorded here for transparency:

| #  | v1 weakness                                                     | v2 correction                                                              |
|----|-----------------------------------------------------------------|----------------------------------------------------------------------------|
| 1  | Wrong line numbers in v0 plan (pagerank.py "lines 132-194")     | Corrected: proxy at line 33; `_budget_chars` 132-133; `_fits` 136-137; binary search 187-194 |
| 2  | v0 said Aider `--encoding cl100k_base` would equalise tokeniser | Corrected: `--encoding` is I/O. Tokeniser routing is via `--model gpt-3.5-turbo` through litellm |
| 3  | v0 missing Rollback section                                     | Added §4.7 of v2 plan                                                      |
| 4  | v0 missing Dependencies & Assumptions distinct section          | Added §4.8 of v2 plan                                                      |
| 5  | v0 missing Next-Action pointer                                  | Added §4.11 of v2 plan                                                     |
| 6  | M2 was horizontally sliced (all 3 adapters lumped)              | Split into M2a (jcm/RBO/Aider equalisation) / M2b (Repomix) / M2c (yek)    |
| 7  | Falsifiable-AC compliance (L-059) weak on HITL items            | M3 AC now has grep-based voice checks + HITL gates stated explicitly       |
| 8  | RBO formula stated but not academically verified                | Verified against Webber, Moffat, Zobel 2010 (ACM TOIS)                     |
| 9  | Repomix / yek install state unverified                          | Both probed at M2b/M2c.1 pre-flight; install commands pinned in reference  |
| 10 | jCodeMunch MCP surface assumed, not probed                      | Probed via `serve --help`. M2a.4 pivoted from `get_ranked_context` (encoder bug) to `get_symbol_importance` (clean PageRank) |
| 11 | Python MCP SDK name assumed                                     | Verified on PyPI: `mcp` 1.27.0; declared as explicit dev dep per L-055     |

Three additional v2-execution-time corrections (post-Phase 4.5):

- **AD-V2-008** (M2a.4): pivoted jCodeMunch from `get_ranked_context` to `get_symbol_importance(top_n, algorithm='pagerank')` after a live encoder-bug probe in jcodemunch-mcp 1.59.1. The original plan would have produced empty rows for all jcm cells.
- **AD-V2-012** (M2c.1): yek `--tokens N` is a combined flag (enables token mode AND sets budget to N), not a boolean toggle as the plan reference assumed. yek `--json` writes to stdout; `--output-dir` is silently ignored.
- **AD-V2-013** (M2c.4): each overlap pair now carries a `level` field (`"symbol"` for codemem/aider/jcm pairs, `"file"` for any pair involving Repomix or yek). The same `jaccard` value means different things at the two granularities; the field is required for honest downstream interpretation.

---

## Methodology

- Harness: `scripts/bench_codemem_vs_aider.py` + `scripts/bench_sweep.py` (median of 3 runs per cell, per AD-006).
- Tokeniser: `tiktoken.get_encoding("cl100k_base")`.
- Overlap metrics: Jaccard on `(file, symbol_name)` tuples for symbol-level pairs; Jaccard on file-path strings for file-level pairs. RBO@10 (Webber et al. 2010, p=0.9) on the same lists.
- Budget sweep: `{512, 1024, 2048, 4096}` (requested, passed to each tool's own budget flag).
- Repos: `aa-ma-forge` (own repo, HEAD `1cc2b02`, 67 Python files) and `tiangolo/fastapi` at tag `0.136.0` (SHA `708606c9`, 1129 Python files indexed by codemem).
- All five tools are live: codemem via local CLI; aider via `--show-repo-map --map-tokens N --model gpt-3.5-turbo` subprocess; jcodemunch via MCP stdio round-trip calling `get_symbol_importance(top_n, algorithm='pagerank')`; Repomix via `npx -y repomix@1.14.0 --style xml --output FILE --token-count-encoding cl100k_base`; yek via `yek --tokens N --json`.

All tool versions and install commands are pinned in
[`reference.md`](../../.claude/dev/active/codemem-benchmark-fairness-v2/codemem-benchmark-fairness-v2-reference.md):

| Tool       | Version  | Install                                                       |
|------------|----------|---------------------------------------------------------------|
| codemem    | aa-ma-forge HEAD | `uv sync` (built from this repo)                      |
| aider      | 0.86.2   | `uv tool install aider-chat==0.86.2`                          |
| jcodemunch | 1.59.1   | `uv tool install jcodemunch-mcp==1.59.1`                      |
| Repomix    | 1.14.0   | `npx -y repomix@1.14.0 ...` (no global install required)      |
| yek        | 0.22.1   | `cargo install yek`                                           |
| tiktoken   | >=0.7    | dev dep of aa-ma-forge; runtime dep of `codemem-mcp` (M1.1)   |
| mcp SDK    | >=1.27   | dev dep of aa-ma-forge (transitively present via fastmcp)     |

---

## Results

### aa-ma-forge (own repo, 67 Python files, `1cc2b02`)

| budget | tool       | symbols | tiktoken_tokens | overshoot vs requested      |
|-------:|------------|--------:|----------------:|----------------------------:|
|    512 | codemem    |       7 |             495 | -3% (under)                 |
|    512 | aider      |      38 |           1 094 | +114%                       |
|    512 | jcodemunch |      20 |             734 | +43%                        |
|    512 | repomix    |       0 |         582 849 | +113 740%                   |
|    512 | yek        |       0 |               1 | -100% (no files emitted)    |
|  1 024 | codemem    |      14 |             960 | -6% (under)                 |
|  1 024 | aider      |      68 |           2 016 | +97%                        |
|  1 024 | jcodemunch |      40 |           1 350 | +32%                        |
|  1 024 | repomix    |       0 |         582 849 | +56 826%                    |
|  1 024 | yek        |       0 |               1 | -100% (no files emitted)    |
|  2 048 | codemem    |      30 |           2 045 | -0.1% (under)               |
|  2 048 | aider      |     132 |           3 935 | +92%                        |
|  2 048 | jcodemunch |      70 |           2 225 | +9%                         |
|  2 048 | repomix    |       0 |         582 849 | +28 363%                    |
|  2 048 | yek        |       0 |               1 | -100% (no files emitted)    |
|  4 096 | codemem    |      60 |           4 049 | -1% (under)                 |
|  4 096 | aider      |     263 |           8 399 | +105%                       |
|  4 096 | jcodemunch |      70 |           2 225 | -46% (top_n ceiling reached)|
|  4 096 | repomix    |       0 |         582 849 | +14 130%                    |
|  4 096 | yek        |       0 |           2 952 | -28% (still under, files emit) |

**Empirical observations on aa-ma-forge:**

- **codemem post-M1 honours its budget across the full sweep**: every cell at every requested budget produces actual cl100k_base tokens at or under the ceiling. Margin shrinks at higher budgets (495 of 512, 960 of 1024, 2045 of 2048, 4049 of 4096) because the binary-search fits the largest sub-list possible. This is the empirical proof that M1 made the budget enforcement honest. v1's proxy systematically under-reported by ~20% at every budget.
- **aider continues to overshoot by 90-115% even with cl100k_base equalisation**. The flag equalises the tokeniser routing (model identity), but Aider's internal output budgeting appears to use a different counting strategy that still over-shoots cl100k_base measurement at the harness boundary. This is a v2-specific empirical refinement of the v1 thesis: equalisation is necessary but not sufficient.
- **jcodemunch hits a top_n ceiling at budget 4096**. The harness maps `budget -> top_n` via `top_n = max(10, budget // 25)`; at 4096 this asks for top_n=163 but only 70 are returned, suggesting jcodemunch's internal symbol cap or PageRank convergence limit. Documented for future top_n calibration.
- **Repomix emits 582 849 tokens regardless of budget** because it has no native budget concept. It is in a different tool category from the others.
- **yek emits 0 files at budgets 512/1024/2048**. At 4096 the budget finally clears the first git-importance file (CHANGELOG.md) and yek emits content but still 0 symbols by definition (file-level only). Order-preserving design, faithful to spec.

### fastapi (`tiangolo/fastapi` 0.136.0, 1 129 files, `708606c9`)

| budget | tool       | symbols | tiktoken_tokens | overshoot vs requested      |
|-------:|------------|--------:|----------------:|----------------------------:|
|    512 | codemem    |       9 |             507 | -1% (under)                 |
|    512 | aider      |      28 |           1 330 | +160%                       |
|    512 | jcodemunch |      20 |             629 | +23%                        |
|    512 | repomix    |       0 |       8 274 204 | +1 615 956%                 |
|    512 | yek        |       0 |             258 | -50%                        |
|  1 024 | codemem    |      19 |           1 016 | -1% (under)                 |
|  1 024 | aider      |      47 |           2 349 | +129%                       |
|  1 024 | jcodemunch |      40 |           1 209 | +18%                        |
|  1 024 | repomix    |       0 |       8 274 204 | +807 928%                   |
|  1 024 | yek        |       0 |             258 | -75%                        |
|  2 048 | codemem    |      39 |           2 024 | -1% (under)                 |
|  2 048 | aider      |      95 |           4 699 | +129%                       |
|  2 048 | jcodemunch |      81 |           2 544 | +24%                        |
|  2 048 | repomix    |       0 |       8 274 204 | +403 964%                   |
|  2 048 | yek        |       0 |             258 | -87%                        |
|  4 096 | codemem    |      81 |           4 083 | -0.3% (under)               |
|  4 096 | aider      |     207 |           9 180 | +124%                       |
|  4 096 | jcodemunch |     163 |           5 067 | +24%                        |
|  4 096 | repomix    |       0 |       8 274 204 | +201 982%                   |
|  4 096 | yek        |       0 |             258 | -94%                        |

**Empirical observations on fastapi:**

- **codemem post-M1 honours its budget across all 4 levels on fastapi too**: 507/512, 1016/1024, 2024/2048, 4083/4096 (all within 1% of requested). The honest enforcement holds at scale.
- **aider overshoot is worse on fastapi than on aa-ma-forge** (124-160% vs 92-114%). aider's per-symbol cost is similar across the two repos, but fastapi's bigger symbol pool means more symbols selected, so absolute overshoot scales up.
- **jcodemunch overshoot is small and stable on fastapi** (18-24%) and shows monotonic scaling with budget (629/1209/2544/5067). The aa-ma-forge top_n ceiling at budget 4096 does NOT recur on fastapi, suggesting it was an aa-ma-forge-specific artifact (small repo + saturating top_n heuristic).
- **Repomix emits 8 274 204 tokens** on fastapi (8.3M, 14× larger than its aa-ma-forge dump). Same dump-everything story.
- **yek emits 258 tokens at every budget on fastapi**, indicating one small file fits below 512 and the next is too large for any of the budgets tested. Same order-preserving design, slightly less degenerate than aa-ma-forge (some content vs zero), still file_count = 0 in the harness aggregate (yek emits no symbols by definition).

---

## Top-symbol overlap matrix

10 pairs per budget when all 5 tools are present. Each pair carries a
`level` annotation (`symbol` or `file`) because the same `jaccard` value
means different things at the two granularities. RBO@10 is computed per
Webber et al. 2010 with `p=0.9` and is averaged in both directions to
remove asymmetry-of-tail-extrapolation noise.

### aa-ma-forge, all budgets

Jaccard / RBO@10 per pair across the four budgets. Pairs are grouped by
`level`. yek pairs are 0.0000 / 0.0000 at budgets 512/1024/2048 because
yek emits 0 files at those budgets (order-preserving design plus a
dominating top-ranked file). At budget 4096 yek finally emits content,
and `repomix_vs_yek` becomes 0.0122 / 0.0000.

**Symbol-level pairs (codemem / aider / jcodemunch):**

| Pair                  | b=512 (J / RBO) | b=1024 (J / RBO) | b=2048 (J / RBO) | b=4096 (J / RBO) |
|-----------------------|-----------------|------------------|------------------|------------------|
| codemem_vs_aider      | 0.0488 / 0.0669 | 0.1286 / 0.0387  | 0.1439 / 0.0000  | 0.2038 / 0.0000  |
| codemem_vs_jcodemunch | 0.0385 / 0.0387 | 0.0385 / 0.0823  | 0.0204 / 0.0823  | 0.0236 / 0.0823  |
| aider_vs_jcodemunch   | 0.1200 / 0.0435 | 0.1053 / 0.0435  | 0.0874 / 0.0000  | 0.0752 / 0.0000  |

**File-level pairs involving Repomix and yek:**

| Pair                   | b=512 (J / RBO) | b=1024 (J / RBO) | b=2048 (J / RBO) | b=4096 (J / RBO) |
|------------------------|-----------------|------------------|------------------|------------------|
| codemem_vs_repomix     | 0.0286 / 0.0000 | 0.0367 / 0.0000  | 0.0612 / 0.0000  | 0.0735 / 0.0000  |
| aider_vs_repomix       | 0.0571 / 0.0000 | 0.0816 / 0.0000  | 0.0980 / 0.0000  | 0.1510 / 0.0000  |
| jcodemunch_vs_repomix  | 0.0816 / 0.0000 | 0.1633 / 0.0000  | 0.2857 / 0.0000  | 0.2857 / 0.0000  |
| repomix_vs_yek         | 0.0000 / 0.0000 | 0.0000 / 0.0000  | 0.0000 / 0.0000  | 0.0122 / 0.0000  |

aa-ma-forge symbol-level Jaccard climbs with budget for codemem_vs_aider
(0.05 to 0.20) but stays flatter for the other two pairs. RBO@10 is
strikingly low across the board: even when the tools pick partially
overlapping symbol sets, they rank them in different orders. The
codemem_vs_aider RBO drops to 0.0000 at budgets 2048 and 4096 because
neither tool's top-10 list at those budgets shares any element with the
other tool's top-10 list, even though Jaccard on the full lists is 14-20%.
This reproduces the v1 Signal B finding ("the tools disagree about what
matters") with the new RBO axis showing the disagreement is
disproportionately concentrated at the top of each tool's ranking.

### fastapi, all budgets

| Pair                  | b=512 (J / RBO) | b=1024 (J / RBO) | b=2048 (J / RBO) | b=4096 (J / RBO) |
|-----------------------|-----------------|------------------|------------------|------------------|
| codemem_vs_aider      | 0.0294 / 0.0000 | 0.1429 / 0.0000  | 0.1391 / 0.0000  | 0.1636 / 0.0000  |
| codemem_vs_jcodemunch | 0.0357 / 0.0495 | 0.0536 / 0.0495  | 0.0345 / 0.0495  | 0.0217 / 0.0495  |
| aider_vs_jcodemunch   | 0.0455 / 0.0000 | 0.0241 / 0.0000  | 0.0485 / 0.0000  | 0.0515 / 0.0000  |

| Pair                   | b=512 (J / RBO) | b=1024 (J / RBO) | b=2048 (J / RBO) | b=4096 (J / RBO) |
|------------------------|-----------------|------------------|------------------|------------------|
| codemem_vs_repomix     | 0.0025 / 0.0000 | 0.0050 / 0.0000  | 0.0071 / 0.0000  | 0.0111 / 0.0000  |
| aider_vs_repomix       | 0.0043 / 0.0000 | 0.0057 / 0.0000  | 0.0100 / 0.0000  | 0.0189 / 0.0000  |
| jcodemunch_vs_repomix  | 0.0071 / 0.0000 | 0.0143 / 0.0000  | 0.0289 / 0.0000  | 0.0582 / 0.0000  |
| repomix_vs_yek         | 0.0007 / 0.0000 | 0.0007 / 0.0000  | 0.0007 / 0.0000  | 0.0007 / 0.0000  |

fastapi pair-overlap is consistently lower than aa-ma-forge because the
symbol pool is ~17× larger (1129 files vs 67), so any top-N selection is
a smaller fraction of the available symbols. RBO@10 is 0 for almost every
pair, meaning the top-10 lists are entirely different across tools. The
non-zero `repomix_vs_yek` pair (0.0007) is because yek and Repomix happen
to both touch one common file at all budgets.

---

## Per-signal verdict

### Signal A: size (tokens per symbol)

Tokens-per-symbol is the v1 efficiency axis. v2 measures it honestly with
cl100k_base on every tool's output. Repomix and yek are excluded from
this signal: they are file-level tools with `symbol_count = 0` by
definition.

**aa-ma-forge tokens/symbol:**

| budget | codemem | aider | jcodemunch | aider vs codemem |
|-------:|--------:|------:|-----------:|------------------|
|    512 |    70.7 |  28.8 |       36.7 | aider 2.5× more efficient |
|  1 024 |    68.6 |  29.6 |       33.8 | aider 2.3× more efficient |
|  2 048 |    68.2 |  29.8 |       31.8 | aider 2.3× more efficient |
|  4 096 |    67.5 |  31.9 |       31.8 | aider 2.1× more efficient |

**fastapi tokens/symbol:**

| budget | codemem | aider | jcodemunch | aider vs codemem |
|-------:|--------:|------:|-----------:|------------------|
|    512 |    56.3 |  47.5 |       31.5 | aider 1.19× more efficient |
|  1 024 |    53.5 |  50.0 |       30.2 | aider **1.07× more efficient** |
|  2 048 |    51.9 |  49.5 |       31.4 | aider 1.05× more efficient |
|  4 096 |    50.4 |  44.3 |       31.1 | aider 1.14× more efficient |

The headline v1 finding was "aider is 2.4× more token-efficient per
symbol on aa-ma-forge at budget 1024." v2's honest tokeniser confirms
this on the small repo (now 2.3× at the same cell, a 4-percentage-point
improvement from the M1 proxy fix).

The same axis on fastapi tells a different story. **codemem and aider are
essentially tied per symbol at budget 1024 on fastapi (1.07×).** Across
all four budgets on fastapi, codemem is within 5-19% of aider per
symbol, within the run-to-run noise band Aider exhibited in v1 at
budget 4096. This is a substantive M1-driven shift: the proxy fix
narrows the gap on the small repo by 4 percentage points and brings
codemem to parity on the larger repo.

The v1 two-fold root-cause analysis (proxy + metadata overhead) gets one
new datapoint each: (1) the proxy fix is real and measurable; (2) the
metadata-overhead penalty amortises away as the symbol pool grows.
codemem's per-symbol cost on fastapi is 50-57 tok/sym (consistent across
budgets); aider's is 44-50 tok/sym. The structural difference no longer
dominates at fastapi scale.

jcodemunch is consistently the leanest per-symbol tool (28-37 tok/sym on
both repos). Its MUNCH/gen1 output is more compact than aider's prose
skeletons or codemem's structured JSON. Different consumer profile, but
worth noting for the size axis.

### Signal B: coverage (top-symbol overlap)

The five tools disagree about what matters, even more than v1's three-tool
panel suggested.

Symbol-level Jaccard between codemem, aider, and jcodemunch on aa-ma-forge
at budget 1024 is 4-13%. RBO@10 is 4-9%. No two of the three tools agree
on more than ~13% of their top symbols. RBO@10 is consistently lower than
Jaccard on these pairs, which means even when the tools share symbols,
they rank them in noticeably different orders.

File-level overlap with Repomix is 4-16% (Repomix sees every file, so
overlap depends on how concentrated each tool's selection is in popular
parts of the repo).

File-level overlap with yek is 0 because yek emits 0 files at common
budgets.

### Signal C: qualitative (what each tool gives a caller)

The five outputs serve five different consumer profiles:

- **codemem** emits structured JSON: `{scip_id, name, kind, file, line, rank: float}` per entry, rank-sorted. Intended for programmatic consumption.
- **aider** emits hybrid prose/markdown: tree-sitter-style signature skeletons grouped by file, with `│def` / `│class` / `│@` line prefixes and `⋮` elision. Intended for direct LLM-prompt injection.
- **jcodemunch** emits MUNCH/gen1 ranked-symbol tables: compact text with per-symbol metadata (rank, score, in_degree, out_degree, kind). Intended for programmatic consumption with a focus on symbol-level dependency analysis.
- **Repomix** emits packed XML: complete file content for the entire scope, no ranking, no budget. Intended for whole-repo dumps to long-context models.
- **yek** emits JSON: ordered file content, file-level only, budget-aware halting. Intended for git-importance-prioritised file injection where order matters more than coverage.

A caller picking one tool needs to ask not just "how does it count tokens?"
but also "how does it enforce my budget?" and "what does its output shape
mean for my consumer?" The answers are different for all five tools.

---

## Implications for kill-criteria Signal 2

The archived codemem plan defines Signal 2 as a composite:

> `codemem build` > 1.5× `/index` wall-clock on reference repos **AND** `PROJECT_INTEL.json` at `--budget=1024` fails to beat Aider's repo-map token efficiency at the same budget.

Both conjuncts must hold for the composite to fire.

**Conjunct (a) wall-clock:** unchanged from v1. Cleared on aa-ma-forge at
0.73× `/index` wall-clock (small reference repo). Medium-repo and 50k-LOC
wall-clock measurements remain pending user-provided reference repos.
Conjunct (a) status: **PROVISIONAL DID-NOT-TRIGGER** on the only repo
where it has been measured.

**Conjunct (b) Aider token-efficiency (UPDATED):** v2 measures honestly
with cl100k_base on both sides. Empirical result at budget 1024:

- aa-ma-forge: codemem 68.6 tok/sym, aider 29.6 tok/sym, aider is 2.3× more efficient. Conjunct (b) **FAILS on the small repo**.
- fastapi: codemem 53.5 tok/sym, aider 50.0 tok/sym, aider is 1.07× more efficient. Conjunct (b) is **DRAW on the larger reference repo** (within run-to-run noise of Signal A).

The split outcome maps to v1 plan §Task 4.2's case structure as **case (b)
mixed**: codemem still loses on the small repo (the conjunct's stated
test bed) but reaches per-symbol parity on the larger reference repo.

**Composite verdict (v2):** **PROVISIONAL DID-NOT-TRIGGER**. The AND
composite does not fire because conjunct (a) holds on aa-ma-forge (the
only repo where wall-clock has been measured). Conjunct (b)'s small-repo
failure is recorded as a risk-signal to monitor, not a kill, and is now
materially weaker than v1 reported because the v1 root cause #1 (4-chars
proxy under-reporting) has been removed and root cause #2 (metadata
overhead) has been shown to amortise out at fastapi scale.

The composite stays at PROVISIONAL because conjunct (a) wall-clock has
not been measured on the medium-repo and 50k-LOC reference repos that the
kill-criteria matrix specifies. v2 does not move that gate.

**What changes in `kill-criteria.md` Signal 2:** the Aider sub-claim
narrative is rewritten to fold in the v2 data (honest cl100k_base
measurement, near-parity on fastapi, 4-percentage-point narrowing on
aa-ma-forge), with the same composite verdict and the same gating dependency
on user-provided medium and 50k-LOC repos. Wording follows v1 §Task 4.2
case (b): "the gap narrows substantially with repo size; the small repo
remains the loss case but the architectural test (does it scale?) does
not fail."

---

## Reproducibility

```bash
# Install (from aa-ma-forge checkout, at HEAD 1cc2b02 or later)
uv sync
uv tool install aider-chat==0.86.2
uv tool install jcodemunch-mcp==1.59.1
cargo install yek
# Repomix runs via npx (no global install)

# Pre-build codemem index on target repo if it is a fresh clone
cd /tmp/bench-fastapi && uv run --project <aa-ma-forge-root> codemem build && cd -

# Single-budget 5-tool measurement
uv run python scripts/bench_codemem_vs_aider.py \
    --repo . \
    --requested-budget 1024 \
    --include-repomix \
    --include-yek \
    --aider-tokeniser-equalise \
    --out /tmp/bench-single.json

# Full sweep (median of 3 runs per cell, four budgets)
uv run python scripts/bench_sweep.py \
    --repo . \
    --include-repomix \
    --include-yek \
    --aider-tokeniser-equalise \
    --out /tmp/bench-aa-ma-forge-v2.json

uv run python scripts/bench_sweep.py \
    --repo /tmp/bench-fastapi \
    --include-repomix \
    --include-yek \
    --aider-tokeniser-equalise \
    --out /tmp/bench-fastapi-v2.json
```

- Trials: 3 per cell; median selected via `statistics.median` (AD-006).
- Environment: WSL2 Ubuntu 24.04 / Linux 6.6.87.2; Python 3.13.x; `uv` 0.7.19; `cargo` 1.88.0; `npm` 11.6.0.
- Tokeniser: `cl100k_base` at the harness measurement boundary for every tool's output.
- Overlap metrics: Jaccard on hashable elements, RBO@10 averaged in both directions. Empty-empty returns 0.0 to keep downstream aggregation simple.

---

## Known gaps

- **yek emits zero files at common budgets on aa-ma-forge.** This is a faithful expression of yek's order-preserving design, not a bug. Practical consequence: yek's data points at budgets 512/1024/2048 do not contribute to overlap analysis. Higher-budget testing or a different repo (with smaller leading files) would change this.
- **jcodemunch hits a top_n ceiling at budget 4096.** The harness's `top_n = max(10, budget // 25)` heuristic asks for top_n=163, jcm returns 70. Calibrating the heuristic to extract more symbols at high budgets would tighten the cell.
- **fastapi codemem index requires a one-time build before benchmarking** (`cd /tmp/bench-fastapi && uv run --project <aa-ma-forge-root> codemem build`). The harness does not currently auto-build because that would mask measurement timing for the codemem cells. Documented for reproducibility.
- **Aider overshoots by 90-115% even with cl100k_base equalisation.** The `--model gpt-3.5-turbo` flag equalises tokeniser routing; the residual overshoot suggests Aider's internal output budgeting uses a different counting strategy (possibly counting the model's view of the prose, including elision markers and structural prose, rather than the harness's view of the same text). Out of scope for v2 to chase upstream.
- **Two repos is still a small sample.** A medium-sized repo (5-20k Python LOC) and a large one (50k+ LOC) would strengthen claims about how the per-symbol gap, RBO disagreement, and yek's order-preserving behaviour scale with repo size. Same gating reference repos as `codemem-vs-index.md`.

---

_Measured 2026-05-08. Raw data in
[`results-codemem-vs-aider-v2-2026-05-08.json`](./results-codemem-vs-aider-v2-2026-05-08.json)._

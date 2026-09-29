# Rating rubric

One rating per dimension: `strong`, `adequate`, `weak` or `unknown`, with a confidence (`high` /
`med` / `low`) and the list of `inputs` it rests on — metric keys from `measure.json`, finding ids,
test-run results. There is no overall grade. Numeric anchors below are guidance, not thresholds:
a judge may depart from them when the evidence says so, and names the evidence when it does.

## Rules for every dimension

- **Core input and the cap.** Each dimension has a core tool (below, and `CORE_INPUTS` in
  `aa_ma.analysis.models`, which finalize enforces). When no core tool has status `ran` in
  `measure.json`'s `stamp.tools`, the rating cannot be `strong`: finalize lowers it to `adequate`
  and sets `capped: true`. Say why in `inputs`.
- **Unknown is not zero.** A metric that is `null`, or a tool that is `absent` / `unknown` /
  `skipped`, is missing evidence — never a clean result. With neither a core input nor judged
  evidence, the rating is `unknown`, confidence `low`.
- **Adequate outside Deep.** The core tools of `security` and `tests_deps` reach the network and run
  only in Deep, so both rate at most adequate in Quick and Standard. report.md says so beside them.
- **Confidence.** `high` needs the core tool `ran` plus judged evidence that agrees; `med` for one
  of the two; `low` otherwise. Quick ratings (measured inputs only) are at most `med`.
- **Findings move ratings.** A surviving `critical` finding makes its dimension `weak`; two or more
  surviving `high` findings usually do. Refuted findings never count.

## `architecture`

Core: `codemem.layers`. Inputs: `layers.core|middle|periphery`, `dead_code.candidates`,
`hot_spot:<path>`, `co_change:<a>|<b>`, plus judged findings.

- **strong** — layering is visible and respected (periphery does not reach into core
  unexpectedly); few dead-code candidates relative to size; co-change pairs stay inside a
  component.
- **adequate** — a recognisable structure with local tangles, or dead code in pockets.
- **weak** — no discernible layering, cross-cutting co-change between unrelated components,
  or a hot spot that everything depends on with no tests near it.

## `maintainability`

Core: `lizard`. Inputs: `complexity.functions`, `complexity.ccn_max`, `complexity.over_15`,
`duplication.pct`, `duplication.clones` (jscpd), `churn.90d:<dir>`, plus judged findings.

- **strong** — `complexity.over_15` under ~2% of `complexity.functions`, `ccn_max` under ~25,
  `duplication.pct` under ~3.
- **adequate** — over-15 functions ~2–8%, or duplication ~3–10%, concentrated rather than spread.
- **weak** — over-15 functions above ~8%, duplication above ~10%, or complex code that is also
  the highest-churn code.

## `security`

Core: `semgrep`. Inputs: `sast.findings`, `secrets.findings` (gitleaks + the built-in regex set),
`suppressions.<tool>`, `tool_config.overrides`, plus judged findings and, in Deep, the
claude-security pass.

- **strong** — no surviving high/critical SAST finding, no secret in tracked content, input
  handling and auth paths the judge read hold up.
- **adequate** — medium findings only, or secrets confined to test fixtures that are clearly fake.
- **weak** — a live-looking secret in tracked content, a surviving critical, or a pattern of
  unsafe input handling.

## `tests_deps`

Core: `osv-scanner` or `pip-audit` (either one `ran` suffices). Inputs: `deps.vulns`, the Deep test
run (`tests: verified|failed|timeout|not_run|refused|unknown — <command>`), test-to-source layout,
plus judged findings.

- **strong** — the test run verified; no known-vulnerable dependency with a published fix; tests
  sit beside the hot spots.
- **adequate** — tests exist and pass but miss the hot spots, or vulnerable dependencies without a
  fix yet.
- **weak** — the test run failed, no tests for core code, or a known-vulnerable dependency with a
  published fix.
- A declined or failed test run is `unknown` test health — never read as passing.

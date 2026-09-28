# codebase-analysis-skills Reference

## Immutable Facts and Constants

### Repo & baseline
- Repo: `snewhouse/aa-ma-forge` (PUBLIC). Plan authored on `main` at `f3ad912`; precondition PR #3 merged as `80caae7`.
- Version at planning: `0.16.0` (tag `v0.16.0`); this effort releases `v0.17.0` via `scripts/release.sh minor` on `main` only (`scripts/release.sh:35-42`: branch main, clean tree, HEAD == origin/main, non-empty `## Unreleased`).
- Merge mode: `/sole-dev-merge` rebase-merges (`claude-code/commands/sole-dev-merge.md:826`); rollback = `git revert <first>^..<last>`.
- Counts at planning: 13 commands / 21 skills / 12 agents → after M3: 14 / 22 / 12. Pins: `SECURITY.md:11-13` (counts + name lists), `docs/spec/claude-code-foundations.md:73,91`, `tests/test_doc_counts.py`, `tests/commands/test_aa_ma_share_command.py:49-93`, README `### All commands` (~:210) + skills table (~:251), local gitignored `CLAUDE.md:51-53`.
- Forge tracked files at `f3ad912`: 665. Plugin-surface golden: 191 edges, 7 orphans, dangling pin `{"aa-ma-plan","haiku-eval"}` (`tests/codemem/test_plugin_surface.py:68`) → `{"haiku-eval"}` after M4.
- `codebase-deep-dive` mentions under `claude-code/`: 29 on 27 lines in 10 files; `deep-analysis` 3; `Skill(aa-ma-plan)` 1 (`understand-codebase/SKILL.md:345`).

### Names & paths (new)
- Skill `claude-code/skills/assess-codebase/` (SKILL.md ≤ 250 lines; `references/RATING.md`, `references/AGENT-PROMPTS.md`); command `claude-code/commands/assess-codebase.md`.
- Shared contract `claude-code/skills/understand-codebase/references/ANALYSIS-CONTRACT.md`.
- Python leaf package `src/aa_ma/analysis/` (models, stamp, ids, sarif, secrets, cli, measure, run, finalize, report_md, ground, changed); console script `aa-ma-analysis`.
- Report dir `.claude/reports/assess-codebase/<sha12>[-dirty]/` (self-ignoring `.gitignore` = `*`); work dir `.claude/reports/assess-codebase/.work-<sha12>/`; per-run codemem index `<work>/codemem.db`.
- Onboarding machine output `.claude/onboarding/onboarding.json`.
- Tests: `tests/analysis/` (collected by CI catch-all `security.yml:182`), goldens `tests/golden/analysis/{summary,finding,judged_finding,onboarding}.schema.json`, fixtures `tests/fixtures/analysis/`, vendored SARIF schema `tests/fixtures/sarif/sarif-schema-2.1.0.json`.
- Next ADR: `docs/adr/0017-assess-codebase-adaptation.md`; ADR-0006 gets a dated `## Amendment` (precedent `docs/adr/0003-prototype-adoption.md:139`).

### Constants
- Finding ID: `"F-" + sha256("\x1f".join([dimension, rule, path, anchor]))[:12]`; anchor = whitespace-collapsed source line text (never a line number, never secret text).
- Dimensions: architecture, maintainability, security, tests_deps. Ratings: strong/adequate/weak/unknown + confidence high/med/low; no overall grade.
- ToolStatus: ran/absent/unknown/skipped (lowercase). Report-based UNKNOWN rule: `claude-code/commands/sole-dev-merge.md:342-431`.
- Baseline vocabulary: new/persisting/fixed; SARIF map new→new, persisting→unchanged, fixed→absent.
- SARIF: our ID in `result.fingerprints["aaMaFindingId/v1"]`; `security-severity` strings critical "9.5", high "7.0", medium "4.0", low "2.0" — only on security-dimension findings above info (amended 2026-09-28; §5a's "9.0"/"0.0" were off GitHub's spec).
- Dirty = tracked changes only: `git status --porcelain --untracked-files=no`.
- Tool timeout default 300 s; run timeout default 300 s; CommandCheck note = last 40 lines, redacted.
- Offline env: `UV_OFFLINE=1 UV_NO_SYNC=1 UV_PYTHON_DOWNLOADS=never PIP_NO_INDEX=1 npm_config_offline=true YARN_ENABLE_NETWORK=0 COREPACK_ENABLE_NETWORK=0 CARGO_NET_OFFLINE=true GOPROXY=off GOTOOLCHAIN=local GOFLAGS=-mod=readonly`; child env = PATH, HOME, LANG, TMPDIR + these.
- Network-reaching tools (semgrep, osv-scanner, pip-audit) run in Deep only, disclosed at the tier ask.
- gitleaks (8.18 on BATS; no `dir` subcommand): `gitleaks detect --no-git --redact -s <src> -f json -r <tmp> --exit-code 0`; rc≠0 → unknown.
- gitleaks 8.18 column convention (live-probed 2026-09-28): token at 0-based index i, length L → `StartColumn = i+2`, `EndColumn = i+L+1` (span = `line[sc-2:ec-1]`) — but on a file's FIRST line one lower (`i+1`, `i+L`); `secrets._widen` trims edge whitespace then widens to the enclosing non-whitespace token, correct for either offset. Bad `-s` path → rc 1, no report.
- Vendored SARIF schema `tests/fixtures/sarif/sarif-schema-2.1.0.json`: sha256 `c3b4bb2d6093897483348925aaa73af03b3e3f4bd4ca38cef26dcb4212a2682e`, 112768 B.
- Consumer invocation: `AA_MA_ROOT=${AA_MA_ROOT:-$(cd "$(dirname "$(readlink -f ~/.claude/skills/<skill>/SKILL.md)")/../../.." && pwd)}`; `uv run --quiet --project "${AA_MA_ROOT}" aa-ma-analysis …` (live-probed: cwd kept, forge codemem on PATH).
- codemem CLI: `--db` is top-level (before `query`); `build` never fills commits tables → `refresh-commits`; `query` tools 6 → 10 after M2.
- Import contracts: `aa-ma-never-imports-codemem` (`.importlinter:75-81`); `render-is-leaf` explicit list (`.importlinter:53-73`) pinned by `tests/render/test_leaf_contract.py`; new `analysis-is-leaf`.
- Eval repo: `honojs/hono` (485 blobs on main at planning; SHA pinned at 7.1). Private Python repo: 154 tracked files, existing 2026-09-17 deep-dive report — described by shape/count only (L-029), never named.

### aa_ma.analysis (built in M1)
- CLI `aa-ma-analysis` (M1): `stamp --tier T [--repo R]`, `fresh <dir|onboarding.json> [--repo R]`, `validate summary|finding|judged_finding|onboarding <file>`, `scan-secrets <dir> [--redact]`.
- Goldens regenerate with `uv run python -m aa_ma.analysis.models --write-schemas tests/golden/analysis`.
- `Hit.pointer` addresses JSON object members as `/@<position>` (never key text); `.jsonl` prefixes the 1-based line number.
- pydantic 2.12: `Literal[1]` accepts JSON `true` in strict mode → `SchemaVersion` BeforeValidator.
- Secret gate fails closed (exit 1, `GateError`/`UnsupportedFile`) on: duplicate JSON keys; any `.gitignore` except root `.gitignore` == `*\n` (constant `stamp.SELF_IGNORE_*`); unmappable gitleaks entry (a known text with a bad span is blanked whole instead); hard links; symlinks; lone surrogates; nesting past the recursion limit; secret-shaped file/dir names (also with separators removed; never echoed); non-UTF-8; unknown suffix.
- JSON string values are also scanned as `"key": "value"` context texts (offset = prefix length); hits map back to the value, keys stay readable. Identical texts are scanned once and fanned out (5000-finding report 10.84s → 0.92s).
- `Finding.path` rejects absolute, `\\`-rooted, URI-scheme/drive-letter, `..`, `%` and control-character paths; `Stamp.date_utc` must be UTC; counts/baseline `NonNegativeInt`. field_validator rules are NOT in the golden JSON Schemas — non-Python consumers must use `aa-ma-analysis validate`.
- `scan-secrets` exits 0 when the regex set is clean even if gitleaks is `unknown`; callers read the `gitleaks:` stderr line.
- Import contracts: `analysis-is-leaf`, `analysis-is-self-contained` (names prefixed with the id so `lint-imports` prints it).

### Tool facts (M2.1 prototype, live on BATS 2026-09-28 — `prototype/cas-assess-core` SHAPES.md)
- lizard 1.24.0: headerless CSV, 11 cols `NLOC,CCN,token,PARAM,length,location,file,function,long_name,start,end` (`long_name` has commas → csv module); rc 0 even for missing/unparseable input.
- jscpd 5.3.3: `{duplicates[{firstFile{name "path:format", startLoc{line}}, secondFile, format, fragment, lines, tokens}], statistics{total{percentage}}}`; `fragment` is source text (never copied). Findings for code formats only.
- gitleaks 8.18 `--redact`: `Secret` and `Match` both `REDACTED`; `File` relative to `-s`.
- semgrep 1.156: `results[{check_id,path,start{line},extra{severity}}]`, `errors[]` (partial parse ≠ failure); severity map ERROR/CRITICAL/HIGH→high, WARNING/MEDIUM→medium, INFO/LOW→low.
- osv-scanner 2.6.0: rc 0 clean / 1 vulns / 127 error / 128 no packages (empty stdout → ran, zero); `results[{source{path(abs)},packages[{package{name,version,ecosystem},vulnerabilities[{id,affected[{ranges[{events[{fixed?}]}]}]}]}]}]`.
- pip-audit 2.10: `-f json --no-deps --disable-pip -r <req>`; `{dependencies[{name,version,vulns[{id,fix_versions,aliases}]}]}`; rc 1 for vulns and for a missing file → status by report.
- codemem: `dead_code` needs a large `--budget` (default truncates); metric only. `owners` dir paths need a trailing `/`; returns emails (never stored). hot_spots `{files[{path,commits_in_window,function_count,score}]}`, co_changes `{files[{path,count}],target}`, layers `{layers{core,middle,periphery},ascii}`.
- Bare `codemem` on BATS PATH is a broken conda stub; `uv run --project <forge>` puts `.venv/bin/codemem` first.

### aa_ma.analysis engine (M2, as built)
- CLI adds `measure [--repo R] --tier T [--tool-timeout 300]` (prints the work dir), `run [--repo R] [--timeout 300] --cmd C…` (JSON checks; exit 0 only if all verified), `finalize --work DIR [--repo R]` (prints the report dir; exit 1 + "work dir kept: …" on refusal).
- Report dir files: `summary.json`, `findings.jsonl`, `findings.sarif`, `report.md`, `run.log` (`finalize.REPORT_FILES`). run.log: one tab-separated line per call — name, argv, rc, seconds, status (never tool output); `<tool>.version` lines carry the probed version; `tool-config:<path>` lines list target scanner configs.
- Staging: `tempfile.mkdtemp(prefix="aa-ma-stage-")` (never inside the reports root — a `.gitignore` of `*` there hid everything from semgrep/osv/jscpd, found live 2.9). Tool majors pinned in `measure.TOOL_MAJOR`.
- Metrics keys: `size.files|size.bytes|churn.90d|last_touch_days:<topdir>` (last-touch vs HEAD's commit time), `complexity.functions|ccn_max|over_15`, `duplication.pct|clones` (code formats), `secrets.findings`, `sast.findings`, `deps.vulns` (None if any contributing dep tool missed), `layers.core|middle|periphery`, `dead_code.candidates`, `hot_spot:<path>`, `co_change:<a>|<b>`, `owners.authors|top_pct:<dir>/`, `tool_config.overrides`, `suppressions.<tool>`, `findings.unreportable`.
- `run` allowlist: `run.RUNNERS`, `RUNNER_SUBCOMMANDS`, `PY_MODULES`; env = PATH (absolute entries only), HOME, LANG, TMPDIR + OFFLINE_ENV.
- Shared safe I/O in `stamp`: `find_binary` (`<NAME>_BIN` else absolute-only PATH), `safe_env`, `read_regular` (O_NOFOLLOW|O_NONBLOCK, regular only), `contained`, `REPORT_NAME`, `report_name`. Rating policy `models.CORE_INPUTS` / `NETWORK_TOOLS`.
- finalize baseline: newest report dir by stamp that git does not track, read without symlinks, stamp not in the future; a same-commit re-run compares with the report it replaces.
- Live forge Deep (2026-09-28, 2.9): 12.8 s wall-clock; 178 measured findings (66 deps.vuln, 54 duplication, 25 secret — test fixtures, 21 complexity, 12 sast).

### Research files
- `docs/research/codebase-analysis-skills-prior-art.md` — Ticket 1 prior art (Valid-Through per header)
- `docs/research/codebase-analysis-skills-codemem-coverage.md` — Ticket 2 codemem coverage
- `docs/research/codebase-analysis-skills-agent-scope.md` — Ticket 3 whole-repo agent scope
- `docs/research/codebase-analysis-skills-measurement-tools.md` — Ticket 4 optional tools + degradation (Valid-Through: 2026-Q4)
- `docs/research/codebase-analysis-skills-sarif.md` — minimal valid SARIF 2.1.0, fingerprints, baselineState (Phase 3)
- `docs/research/codebase-analysis-skills-offline-command-run.md` — offline env per ecosystem, process-group kill (Phase 3)

### Map tickets (source: `codebase-analysis-skills-map.md`, all RESOLVED 2026-09-27)
- Ticket 1: Prior art — measure/judge/refute + coverage ledger + SHA-stamped, masked output (claude-security, code-modernization); wiki generators for onboarding.
- Ticket 2: codemem coverage — graph/co-change/owners covered; complexity, duplication, coverage, structural search missing; ast-grep binary not codemem replaces `sg`.
- Ticket 3: Agent scope — verify-impl audit agents are diff-only; whole-repo uses built-in agents + prompts (shape C/D).
- Ticket 4: Measurement tools — one optional tool per metric; UNKNOWN never zero (report-based rule).
- Ticket 5: Shape — two independent skills + one shared contract file; understand reads fresh assess output, Deep asks once.
- Ticket 6: Names — `assess-codebase` skill + thin command; 27 mention lines repointed, one flagged legacy rule; local copy retired by Ste after eval.
- Ticket 7: Content — 4 dimensions; tools measure, model judges with file:line; per-dimension rating, no overall grade; High+ refutation; Quick/Standard/Deep.
- Ticket 8: Output — `<sha12>[-dirty]` self-ignoring dir; summary.json + findings.jsonl + SARIF + Markdown; SHA freshness; ANALYSIS-CONTRACT.md.
- Ticket 9: Residuals — R1/R2/R5/R7/R8/N1 in-plan test-first; R4 extractor; `/deep-analysis` dropped; ADR-0017 + ADR-0006 amendment; R6 → eval.
- Ticket 10: Evaluation — forge + private Python repo + pinned public TS/JS repo; 2 blinded judges; pass bar; CI contract tests on a fixture repo.
- Ticket 11: understand v1 — all 8 improvements (grounding, currency check, ledger, 10-claim check, codemem tools, onboarding.json, leaner AGENTS.md, incremental regen).
- Ticket 12: codemem bare-`sg` — fixed outside the plan in PR #3 (`80caae7`).

### Structural context (codemem, fresh build at `f3ad912`: 208 files, 2122 symbols, 5203 edges)
- `packages/codemem-mcp/src/codemem/draw/plugin_surface.py` imports `draw/cut.py` and `draw/surface_allowlist.py`; called by `draw/views.py` (the living doc).
- `packages/codemem-mcp/src/codemem/cli.py` imports `mcp_tools` function-locally (no module-level edges drawn).

Architecture View: see plan.md §13

_Last Updated: 2026-09-28_

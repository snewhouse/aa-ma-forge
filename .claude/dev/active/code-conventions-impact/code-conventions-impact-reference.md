# code-conventions-impact Reference

**Immutable facts and constants for this task.** Source: `code-conventions-impact-plan.md` (approved 2026-10-08), `code-conventions-impact-map.md` (15/15 RESOLVED), `code-conventions-impact-verification.md` (Revision 3, PASS WITH WARNINGS). All facts below are `[valid: 2026-10-08]` unless marked otherwise.

_Last Updated: 2026-10-09_

Test-Command: uv run pytest

Architecture View: see plan.md §13

Prerequisite: see tasks.md "Prerequisite (not a milestone)" (merge `feature/engineering-standards` into `main` via `/sole-dev-merge`, Ste's explicit OK, before M1).

---

## Repository and Branch

| Fact | Value | Marker |
|------|-------|--------|
| Repo path | `~/projects/github_private/aa-ma-forge` | [valid: 2026-10-08] |
| GitHub repo | `snewhouse/aa-ma-forge` — **PUBLIC**; no client-derived code, names or paths may enter it | [valid: 2026-10-08] |
| Plan authored on | branch `feature/engineering-standards` @ `14ae44c` (12 commits ahead of main + Phase 5 artifact commit) | [valid: 2026-10-08] |
| Default branch | `main` | [valid: 2026-10-08] |
| Branch model | one branch + PR per milestone, cut from fresh `main` (L-032: `git status -sb` on main first); merged via `/sole-dev-merge` (rebase-merge) | [valid: 2026-10-08] |
| Worktree per milestone | `.worktrees/<branch>` (D7, L-066); first action `uv sync && uv run codemem build` (`.venv`, `.codemem/index.db` are gitignored, per-checkout) | [valid: 2026-10-08] |
| Live install | `scripts/install.sh` runs ONLY from the main checkout after merge (install.sh derives REPO_ROOT from its own location); in-milestone install proofs use a fake `CLAUDE_HOME` | [valid: 2026-10-08] |
| M14 exception | M14 runs on the main checkout after M13 merges (D7 exception, D11); main pushes need Ste's explicit OK | [valid: 2026-10-08] |
| First branch name | `feat/cci-m1-touched-harness` | [valid: 2026-10-08] |
| Canary branch (M1.4) | `canary/cci-m1-touched` (DRAFT PR, closed + deleted after) | [valid: 2026-10-08] |
| Prototype branches | `prototype/cmd-to-skill` (M3.1), `prototype/impact-hook` (M10.1) | [valid: 2026-10-08] |
| Release target | v0.18.0 (minor), single release in M14 (D11) | [valid: 2026-10-08] |
| Next free ADR number | 0022 (0018 = M1 lint gate, 0019 = M2 skill migration, 0020 = M3 commands → skills, 0021 = M4 writing-for-agents); eight ADRs planned | [valid: 2026-10-09] |
| Session rules | `/rigor` (`~/.claude/skills/rigor/SKILL.md`), ≤5 concurrent sub-agents, `Skill(double-check)` before any COMPLETE | [valid: 2026-10-08] |

## Baseline Numbers (plan §0, 2026-10-08)

| Measure | Value | Marker |
|---------|-------|--------|
| `uv run pytest -q` | 2429 passed, 5 skipped, 7 deselected in 112.5 s | [valid: 2026-10-08] |
| M1 BASELINE (provenance) | pytest 2429/5/7, ruff src+packages 4, Ruff S 34, shellcheck 0 (24 .sh), rules_chars 20249 | [valid: 2026-10-08] |
| Touched-file debt, repo-wide (2026-10-08, /sole-dev-merge C1) | `ruff format --check .` 113 files to reformat (35 src/packages/scripts, 77 tests); `ruff check .` 39 findings; 19 of 31 `.bats` fail shellcheck (excluded from the hook via `exclude_types: [bats]`) | [valid: 2026-10-08] |
| Ruff S findings (`ruff check --isolated --select S src packages scripts`) | 34 | [valid: 2026-10-08] |
| Oversized prompt files (lines) | aa-ma-execution 1295, execute-aa-ma-milestone 1244, aa-ma-plan 1154, sole-dev-merge 1054, execute-aa-ma-full 757, plan-verification 608 | [valid: 2026-10-08] |
| Existing >100-line references without a TOC | 23 (go into `TOC_ALLOWLIST (23 at plan time; 24 after M2 imports logging-and-comments/references/python.md)`) | [valid: 2026-10-08] |
| Test files referencing `commands/` paths | 31 | [valid: 2026-10-08] |
| Touched-file debt | ≤11 strict findings per planned file | [valid: 2026-10-08] |
| `uv audit` (uv 0.12.3) | experimental; exits 1 with 13 vulnerable packages (12 with `--no-dev`: pyjwt, starlette, urllib3, mcp, fastmcp, cryptography…) | [valid: 2026-10-08] |
| gitleaks current hits | 3, all test fixtures (`tests/analysis/test_measure.py`, `tests/hooks/security-static-check.bats`) | [valid: 2026-10-08] |
| Bandit B404 | fires 10× on this repo; Ruff `S404` is preview-only at 0.15.9 | [valid: 2026-10-08] |
| Auto-loaded rule cost (map T1) | ~8.8k tokens (7 files); ~12.2k with project CLAUDE.md + ponytail injection | [valid: 2026-10-08] |
| Counts before plan | skills 22, top-level hooks 8, rules 2, MCP tools 13, commands 14 | [valid: 2026-10-08] |
| Counts after plan | skills 22→27 (M2) → 38 after M3 (+11 new dirs: 2 commands merge into existing skills, grill-me deleted) → −write-a-skill +writing-for-agents (M4) → +1 secops (M8) → +1 language-conventions (M12) = 40 at end; hooks 8→9 (M2) →10 (M10); rules 2→3 (M12); MCP tools 13→14 (M10); commands 14→0 (M3) | [valid: 2026-10-08] |
| codemem index at verification | 239 files after `codemem build` (was 7 files stale) | [valid: 2026-10-08] |

## Tool Versions

| Tool | Version | Source / note | Marker |
|------|---------|---------------|--------|
| ruff | 0.15.9 | uv.lock (PATH ruff is conda 0.15.4 — never used; pre-commit hook runs `uv run ruff`) | [valid: 2026-10-08] |
| uv | 0.12.3 | CI pins via `astral-sh/setup-uv@<sha>` `version: 0.12.3` | [valid: 2026-10-08] |
| gitleaks (local) | 8.18.0 | conda, not in venv; 8.18 has no `git` subcommand (use `detect` / `protect`) | [valid: 2026-10-08] |
| gitleaks (CI + pre-commit) | v8.18.4 | tarball, sha256 verified | [valid: 2026-10-08] |
| shellcheck | 0.11.0 | conda/system; pre-commit `language: system` | [valid: 2026-10-08] |
| pre-commit | 4.6.2 (uv.lock; conda has 4.5.1 — never used) | added to `[dependency-groups] dev` in M1.2 (`pre-commit>=4.5`) | [valid: 2026-10-08] |
| bandit | 1.9.4 | resolves to conda today; pinned `bandit==1.9.4` in dev group in M1.2 | [valid: 2026-10-08] |
| griffe | absent | added (pinned) to dev group in M10.7 | [valid: 2026-10-08] |
| osv-scanner | absent | YAGNI for the forge (P7) | [valid: 2026-10-08] |
| Claude Code | 2.1.294 | no MultiEdit tool; `claude plugin eval` exists | [valid: 2026-10-08] |
| writing-for-agents upstream | mattpocock/skills @ c55ee46 | fetch via `gh api …?ref=<40-hex>` | [valid: 2026-10-08] |

## API Endpoints

| Endpoint | URL / form | Auth | Notes |
|----------|-----------|------|-------|
| GitHub repo | https://github.com/snewhouse/aa-ma-forge | gh CLI | PUBLIC [valid: 2026-10-08] |
| Fork fetch (M4.4) | `gh api repos/mattpocock/skills/contents/…?ref=<40-hex of c55ee46>` | gh CLI | never from the plugin cache (lags upstream); record sha256 [valid: 2026-10-08] |
| Hook docs (A1, M10.1) | code.claude.com hook docs | none | PreToolUse/PostToolUse `hookSpecificOutput.additionalContext` [valid: 2026-10-08] |
| Skills docs (M4.1) | code.claude.com skills docs | none | source of the allowed frontmatter key list; cite in test docstring [valid: 2026-10-08] |
| Release check (M14.2) | `gh release view v0.18.0` | gh CLI | must exit 0 [valid: 2026-10-08] |

## Gate Fields (plan §2a — transcribed to tasks.md)

| Milestone | Gate | Audit-Profile | Critical-Path | Prototype-Required | TDD-Waiver |
|---|---|---|---|---|---|
| M1 | HARD | full | hook-modification | — | — |
| M2 | HARD | full | hook-modification | — | — |
| M3 | HARD | full | hook-modification | YES | — |
| M4 | SOFT | full | version-pipeline | — | — |
| M5 | HARD | code-only | hook-modification | — | refactor |
| M6 | HARD | full | hook-modification | — | — |
| M7 | HARD | full | hook-modification | — | — |
| M8 | HARD | full | hook-modification | — | — |
| M9 | HARD | full | hook-modification | — | — |
| M10 | HARD | full | hook-modification | YES | — |
| M11 | HARD | full | hook-modification | YES | — |
| M12 | HARD | full | hook-modification | — | — |
| M13 | SOFT | docs-only | — | — | docs-only |
| M14 | HARD | code-only | version-pipeline | — | — |

`[valid: 2026-10-08]` — "—" means the field is omitted in tasks.md; never written empty (gate exit 2).

## Canonical Enum Values Used (`src/aa_ma/plan_parsers.py`, `src/aa_ma/enforce.py`)

| Field | Canonical set | Used here | Marker |
|-------|---------------|-----------|--------|
| Audit-Profile | full, code-only, docs-only, infra, custom | full, code-only, docs-only | [valid: 2026-10-08] |
| TDD-Waiver | refactor, docs-only, prototype, hotfix-emergency, tooling-config | refactor (M5), docs-only (M13) | [valid: 2026-10-08] |
| Critical-Path | auth-flow, data-xform, external-api, version-pipeline, doc-count-drift, hook-modification | hook-modification, version-pipeline | [valid: 2026-10-08] |
| Diagram-Waiver (plan-level) | none, docs-only, config-only, single-file | none | [valid: 2026-10-08] |
| Gate | SOFT, HARD | both | [valid: 2026-10-08] |
| Mode | HITL, AFK | both | [valid: 2026-10-08] |
| Prototype-Required | YES, NO | YES (M3, M10, M11) | [valid: 2026-10-08] |
| Milestone Status | PENDING, ACTIVE, IN_PROGRESS, COMPLETE, BLOCKED | PENDING, COMPLETE (M1, M2, M3) | [valid: 2026-10-09] |
| Step Status | PENDING, IN_PROGRESS, COMPLETE, BLOCKED, SKIPPED, DEFERRED | PENDING, COMPLETE | [valid: 2026-10-09] |
| Plan heading grammar (strict writer) | `^## Milestone (\d+): ` / `^### Sub-step (\d+\.\d+): ` (`grammar.CANONICAL_*_RE`) | step `8.4a` renumbered to 8.5 for that reason | [valid: 2026-10-08] |

## CLI Contracts

### `scripts/check_conventions.py` (new, M1; rules in M6)
- Usage: `scripts/check_conventions.py [--from-ref REF --to-ref REF] [FILE...]` [valid: 2026-10-08]
- Exit codes: `0` clean | `1` findings (one line each: `path:line: CODE message`) | `2` usage/git error, including "no diff source" (no refs, nothing staged). [valid: 2026-10-08]
- Precedence: `--from-ref/--to-ref` flags > `PRE_COMMIT_FROM_REF`/`PRE_COMMIT_TO_REF` env > staged mode; three-dot diff `from...to`; `FILE...` filters the diff. [valid: 2026-10-08]
- M1 ships zero checks: prints `check_conventions: 0 checks enabled`. M6 adds `WHY001`, `TODO001` (added/modified lines only). [valid: 2026-10-08]
- `TODO001` reference regex: `#\d+|ADR-\d{4}`. [valid: 2026-10-08]
- As built (M1, d3b6bc4): every diff runs from `git rev-parse --show-toplevel` with `--literal-pathspecs`, `--no-textconv`, `--no-ext-diff`; FILE args are repo-root-relative (normalised with `os.path.normpath`); name-status `-z` walk mirrors `src/aa_ma/analysis/changed.py` (R/C take two paths); summary line goes to stderr, findings to stdout; `CHECKS` is a list of `(path, {line: text}) -> [(path, line, code, message)]`. [valid: 2026-10-08]
- Deferred to M6: escape control characters in printed findings (security I1) and print non-UTF-8 paths safely (`errors="backslashreplace"` on output; /sole-dev-merge C1 LOW); one-call diff if per-file latency shows (code-review I2). [valid: 2026-10-08]
- Format on touch: a `git mv`/`sed`/manual edit bypasses the edit-time ruff-format hook, so format the file in the same change (M3 renames). [valid: 2026-10-08]

### `aa-ma-impact` (new, M11; `[project.scripts] aa-ma-impact = "aa_ma.impact:main"`)
- Usage: `aa-ma-impact <plan.md> <tasks.md> --milestone N --base SHA [--format kv|json] [--ignore-cutover]` [valid: 2026-10-08]
- Exit codes: `0` pass | `1` unexplained / undeclared API break / no Contract Files (post-cutover) / derived Critical-Path without review | `2` usage / unreadable / git error | `3` codemem index unavailable or `refresh-commits` failed (fails closed) | `5` not applicable (grandfathered; prints why). [valid: 2026-10-08]
- kv keys: `changed= predicted= cochange= unexplained= api_breaks= derived_cp=<value:file,…>`; `api_diff=skipped(<reason>)` when griffe cannot run. [valid: 2026-10-08]
- Order: cutover/grandfather check FIRST (exit 5) before `aa_ma_milestone_base`. [valid: 2026-10-08]

### `aa_ma_milestone_base` (bash, `claude-code/hooks/lib/aa-ma-parse.sh`, M11)
- `git merge-base origin/<default> HEAD`; empty or == HEAD → exit 2 "no milestone window"; no origin → exit 2 with a named error. [valid: 2026-10-08]
- `aa_ma_impact` launcher returns 127 when uv is missing (aa_ma_gate pattern). [valid: 2026-10-08]

### `aa-ma-gate` (existing)
- `uv run aa-ma-gate <tasks.md> [--milestone N] [--step N.M] [--format kv]`; exit 0/1/2/3/4; empty field value → exit 2. [valid: 2026-10-08]

### codemem CLI additions (M10)
- `codemem query callees`; `codemem query co_changes <path>... --threshold N --min-ratio R` (JSON; no `--json` flag exists; exit 1 on `error`); `codemem impact <path> --format brief|json`; `codemem refresh-commits`. [valid: 2026-10-08]

### `scripts/run-evals.sh` (new, M4)
- Exit 0 always (advisory); rc in the last line; results → `.claude/evals/<YYYY-MM-DD>.jsonl` (gitignored) + one summary line; `claude plugin eval` always with `--no-publish`, `--runs 1`, no ablation arm. [valid: 2026-10-08]

## Provenance Token Formats

| Token | Exact format | Written by | Marker |
|-------|--------------|-----------|--------|
| BASELINE | `[ts] BASELINE — pytest=<passed>/<skipped>/<deselected> ruff_src_packages=<N> ruff_S=<N> shellcheck=<N> rules_chars=<N>` | M1.1 | [valid: 2026-10-08] |
| TESTS_VERIFIED | `[ts] TESTS_VERIFIED — <milestone heading> — passed=N cmd=<TEST_CMD>` | §6.7 fence 3 (live from M10's gate) | [valid: 2026-10-08] |
| TESTS_VERIFIED (opt-out) | `[ts] TESTS_VERIFIED — <milestone heading> — skipped: <reason>` (needs `Test-Command: none — <reason>` + GATE APPROVAL) | fence 3 | [valid: 2026-10-08] |
| IMPACT_VERIFIED | `[ts] IMPACT_VERIFIED — <milestone heading> — changed=N predicted=P cochange=C unexplained=0` | §6.7 fence 4 (post-cutover plans only) | [valid: 2026-10-08] |
| IMPACT-GATE n/a | `IMPACT-GATE: not applicable (grandfathered)` — printed, never silent | fence 4 | [valid: 2026-10-08] |
| CRITICAL_PATH_REVIEW | `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — <value> — <evidence>` | last sub-step of each Critical-Path milestone | [valid: 2026-10-08] |
| PROTOTYPE | `[ts] PROTOTYPE — <milestone heading> — <verdict> — verdict-changes-plan: YES\|NO` | M3.1, M10.1, M11.1 | [valid: 2026-10-08] |
| DIAGRAM_VERIFIED | `DIAGRAM_VERIFIED — <milestone heading> — edges=N checked=C phantom=0 unknown=K` | existing §6.7 fence 2 | [valid: 2026-10-08] |
| PAYLOAD_CAPTURED | `PAYLOAD_CAPTURED <event>` (one per registered hook event) | M7.5 | [valid: 2026-10-08] |
| COMMANDS | `COMMANDS pre=N post=N-14` | M4.0 | [valid: 2026-10-08] |
| Ruff/Bandit decision (context-log) | `DECISION ruff-only\|fallback (<ids>) — approved by Ste` | M8.1 | [valid: 2026-10-08] |

The §6.7 gate matches `<milestone heading>` with `grep -F` against the tasks.md heading (without `## `, backticks included). [valid: 2026-10-08]

## Constants

| Constant | Value | Context | Marker |
|----------|-------|---------|--------|
| `COCHANGE_MIN_SHARED` | 5 | `src/aa_ma/impact.py`; a pair counts only with ≥5 shared commits (T7) | [valid: 2026-10-08] |
| `COCHANGE_MIN_RATIO` | 0.5 | partner changed in ≥50% of the file's commits (≥ semantics) | [valid: 2026-10-08] |
| Cochange-Threshold override bounds | n ≤ 20, ratio ≤ 0.9 | `Cochange-Threshold: <n> <ratio>` in reference.md merge-base copy; needs GATE APPROVAL | [valid: 2026-10-08] |
| `IMPACT_CUTOVER` | `"9999-12-31"` (sentinel) | set to the v0.18.0 release date in M14.1 | [valid: 2026-10-08 to M14.1] |
| `IMPACT_EXCLUDE` | `(".claude/dev/**", "docs/architecture/**", "tests/golden/**", "uv.lock", "CHANGELOG.md")` | impact.py | [valid: 2026-10-08] |
| Fence 3 timeout | `${AA_MA_TEST_TIMEOUT:-540}` s | Bash tool max is 600 s; baseline suite 112.5 s | [valid: 2026-10-08] |
| Fence 3 pass regex | final non-empty line after `sed -E 's/^=+ //; s/ =+$//'` matches `(^|, )([0-9]+) passed` | earlier "2 snapshots passed." lines ignored | [valid: 2026-10-08] |
| Fence 3 rejected chars | `;` `\|` `&` `$` backtick `<` `>` | TEST_CMD run as shlex argv, no `bash -c` | [valid: 2026-10-08] |
| `coding-standards.md` budget | ≤ 6,000 chars (~1.5k tokens) | `tests/test_autoload_budget.py` | [valid: 2026-10-08] |
| Rules RATCHET | measured after M12; may only fall; ≤ M1 rules-only `rules_chars` baseline | `tests/test_autoload_budget.py` | [valid: 2026-10-08] |
| Prompt body cap | ≤500 lines | `tests/test_prompt_size.py` | [valid: 2026-10-08] |
| TOC threshold | references >100 lines (new/modified only) | `tests/test_prompt_size.py` | [valid: 2026-10-08] |
| assess-codebase SKILL.md cap | ≤250 lines (220 now) | `test_assess_codebase.py:73` | [valid: 2026-10-08] |
| mccabe max-complexity | 10 | Ruff C901 | [valid: 2026-10-08] |
| pylint max-args | 6 | Ruff PLR0913 | [valid: 2026-10-08] |
| Frontmatter limits | name ≤64 `[a-z0-9-]`; description ≤1024, no `<`; description + `when_to_use` ≤1536 | `tests/test_frontmatter_at_top.py` | [valid: 2026-10-08] |
| Eval cases | 24 (3 × 8 skills) | `evals/<skill>/<case>/case.yaml` | [valid: 2026-10-08] |
| Pre-edit hook output cap | ≤5 lines; `sanitize_context_line(text, max_len=200)` | aa-ma-impact-preedit.sh | [valid: 2026-10-08] |
| Pre-edit hook latency budget | p95 ≤1.5 s over 20 runs; 2 s timeout fails open with notice | M10.1 | [valid: 2026-10-08] |
| ruff hook additionalContext cap | ≤10 lines | ruff-format.sh | [valid: 2026-10-08] |
| `session_id` pattern | `^[A-Za-z0-9_-]{1,64}$` | pre-edit hook | [valid: 2026-10-08] |
| Redaction input cap | 8 KB before matching; 100 KB adversarial timing test per pattern | logsetup / aa-ma-log.sh | [valid: 2026-10-08] |
| `callees` defaults | `max_depth=3, budget=8000` | codemem mcp_tools | [valid: 2026-10-08] |
| `file_impact` default budget | 2000 | codemem mcp_tools | [valid: 2026-10-08] |
| gitutil timeout | 10.0 s | `git(args, repo, timeout=10.0)` | [valid: 2026-10-08] |
| Dependabot cooldown | 7 days | `.github/dependabot.yml` | [valid: 2026-10-08] |
| codemem schema | v4 (adds `plugin_edges(src TEXT, dst TEXT, kind TEXT, ref_class TEXT)`) | storage/db.py, M10.3 | [valid: 2026-10-08] |
| Security-static-check Ruff selection | `S602,S604,S307,S608,S301` | D12, M8.6 | [valid: 2026-10-08] |
| Only Ruff S ignore | `tests/**` S101 | tested (§0 v2) | [valid: 2026-10-08] |

## Configuration

### Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `AA_MA_TEST_TIMEOUT` | 540 | no | fence 3 timeout, seconds [valid: 2026-10-08] |
| `HOOK_DEBUG` | unset | no | `=1` enables `log_debug` (also stderr) in hooks [valid: 2026-10-08] |
| `AA_MA_PLAN_MARKER_DEBUG` | unset | no | deprecated alias for one release (prints notice) — removal recorded in TODOS.md [valid: 2026-10-08] |
| `AA_MA_HOOK_LOG` | `~/.claude/logs/hooks.log` | no | hook log path (compaction.log folds in) [valid: 2026-10-08] |
| `LOG_LEVEL` | — | no | Python CLI log level (with `-v`/`-q`) [valid: 2026-10-08] |
| `LOG_FORMAT` | text | no | `json` opt-in for CLIs; required for services [valid: 2026-10-08] |
| `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` | unset | no | read by check_conventions.py (pre-commit cannot template refs into args) [valid: 2026-10-08] |
| `AA_MA_HOOKS_DISABLE` | unset | no | master kill switch (emergency rollback for new fences, stated to Ste) [valid: 2026-10-08] |
| `CLAUDE_HOME` | `~/.claude` | no | fake home for in-milestone install proofs [valid: 2026-10-08] |
| `RUFF_BIN` | `ruff` | no | scanner override; `/nonexistent` exercises the UNKNOWN path [valid: 2026-10-08] |
| `BANDIT_BIN` | `bandit` | no | retired in M8 (Stage C3) [valid: 2026-10-08 to M8] |
| `SHELLCHECK_BIN` | `shellcheck` | no | scanner override (existing) [valid: 2026-10-08] |
| `GH_TOKEN`, `GITHUB_TOKEN`, `SSH_AUTH_SOCK` | — | no | unset inside the eval sandbox (`env -i`) [valid: 2026-10-08] |

### Config Files and keys
- `pyproject.toml` [valid: 2026-10-08]:
  - `[dependency-groups] dev` (`:129`) — gains `pre-commit`, `bandit==1.9.4` (M1), pip-audit (M8), griffe pinned (M10); `tool.uv.dev-dependencies` removed.
  - `:49` "≥90% coverage gate" and `:121` "CI perf job" claims deleted (M9.3, P5); `:68` comment "CI runs `ruff check src/`" updated (M1).
  - `[tool.ruff.lint]` `:81-83` D101–D104 parked list + `TODO(logging-std)` deleted (M6); extend-select += D, RUF100, PGH003, PGH004, C901, PLR0913, S; extend-ignore D107, TD003; convention google.
  - `[project.scripts] aa-ma-impact = "aa_ma.impact:main"` (M11).
- `.pre-commit-config.yaml` hook ids (all `repo: local`): `ruff-check`, `ruff-format`, `shellcheck`, `check-conventions` (+ gitleaks M8). [valid: 2026-10-08]
- `~/.claude/settings.json`: `:561` existing ruff-format.sh command string; `:295 "off"` senior-secops override left alone (L-1210). [valid: 2026-10-08]
- `.importlinter`: `:80-86` forbids `aa_ma` importing `codemem`; leaf contracts `render-is-leaf`, `analysis-is-leaf`, `analysis-is-self-contained` gain `aa_ma.logsetup`, `aa_ma.gitutil`, `aa_ma.impact`, `aa_ma.contract_rows`. [valid: 2026-10-08]

## Dependencies

| Package | Version | Class | Purpose |
|---------|---------|-------|---------|
| pre-commit | (locked in uv.lock) | Dev-only | touched-files harness (P1) [valid: 2026-10-08] |
| bandit | ==1.9.4 | Dev-only | pinned for the M8.1 comparison; fallback gate only [valid: 2026-10-08] |
| ruff | 0.15.9 (uv.lock) | Dev-only | lint, format, Ruff S [valid: 2026-10-08] |
| pip-audit | (locked in dev group) | Dev-only | hashed dependency audit (A6 fallback) [valid: 2026-10-08] |
| griffe | pinned in M10.7 | Dev-only | API diff for `aa_ma` and `codemem` (P6) [valid: 2026-10-08] |
| codemem-mcp | workspace member | Dev-only for `aa_ma` | `pyproject.toml:56`; aa_ma shells out to its CLI, never imports it [valid: 2026-10-08] |
| GitHub Actions | `astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7` (v10.2.0), `actions/checkout@11d5960…` (v4.4.0) | CI | SHA-pinned; `persist-credentials: false` [valid: 2026-10-08] |

## File Paths

### Files to Create
- `.pre-commit-config.yaml`; `scripts/check_conventions.py` (stdlib-only) — M1 [valid: 2026-10-08]
- `tests/scripts/test_check_conventions.py`, `tests/test_precommit_config.py` — M1
- `docs/adr/NNNN-touched-code-lint-gate.md` — M1
- `claude-code/skills/{logging-and-comments,python-quality-gates,llm-output-safety,secrets-management,bash-defensive-patterns}/…`; `claude-code/hooks/ruff-format.sh`; `tests/hooks/ruff-format.bats`; `docs/adr/NNNN-coding-doctrine-skill-migration.md` — M2
- `claude-code/skills/<11 moved commands>/SKILL.md`; `tests/skills/test_no_command_skill_collision.py`, `tests/skills/test_model_invocation_list.py`; `docs/adr/NNNN-commands-become-skills.md` — M3
- `tests/test_prompt_size.py`; `claude-code/skills/writing-for-agents/`; `evals/<skill>/<case>/case.yaml` (24); `scripts/run-evals.sh`; `tests/scripts/test_run_evals_sandbox.bats`; `docs/adr/NNNN-writing-for-agents-fork.md` — M4
- `tests/test_split_preserves_content.py`; `references/` dirs for the 6 split skills — M5
- `claude-code/hooks/lib/aa-ma-log.sh`; `src/aa_ma/logsetup.py`; `tests/hooks/aa-ma-log.bats`; `tests/test_logsetup.py`; `tests/fixtures/hook-payloads/` — M7
- `docs/research/code-conventions-impact-ruff-vs-bandit.md`; `.github/dependabot.yml`; `.gitleaksignore`; `claude-code/skills/secops/SKILL.md`; `tests/security/test_canary.py`; `tests/fixtures/canary/`; `docs/adr/NNNN-secops-baseline.md` — M8
- `tests/hooks/test_tests_verified.bats`; `tests/test_tdd_waiver_doc_sync.py`; `docs/adr/NNNN-tests-verified-gate.md` — M9
- `packages/codemem-mcp/src/codemem/gitutil.py`; `src/aa_ma/gitutil.py`; `claude-code/hooks/aa-ma-impact-preedit.sh`; `tests/codemem/{test_callees,test_file_impact,test_plugin_surface_index,test_critical_path_globs}.py`; `tests/test_gitutil_contract.py`; `tests/hooks/aa-ma-impact-preedit.bats`; `docs/adr/NNNN-impact-preedit-hook-and-callees.md` — M10
- `src/aa_ma/impact.py`; `src/aa_ma/contract_rows.py`; `tests/test_impact.py`; `tests/test_contract_rows.py`; `tests/test_impact_codemem_contract.py`; `tests/hooks/test_impact_verified.bats`; `tests/hooks/aa-ma-milestone-base.bats`; `claude-code/skills/execute-aa-ma-milestone/references/impact-gate.md`; `docs/adr/NNNN-gate-computed-impact-verified.md` — M11
- `claude-code/rules/coding-standards.md`; `claude-code/skills/language-conventions/{SKILL.md,references/{python,bash,markdown,typescript,r,sql}.md}`; `tests/test_autoload_budget.py`; `tests/test_rule_references.py` — M12

### Files to Modify (with plan line citations)
- `pyproject.toml` (:49, :56, :68, :81-83, :121, :129) [valid: 2026-10-08]
- `.github/workflows/security.yml` (:39 Bandit `|| true` = carried defect 3; bats job Bandit :103-107)
- `scripts/install.sh` (REQUIRED_DIRS :80; rules backup list :145-146; pre-compact backup :149; foreign-symlink/stale-link logic; symlink target :257-269; rules symlinks :284-287; AA_MA_HOOKS table :314-323; hooks/lib per-file list :331-346); `scripts/uninstall.sh`
- `claude-code/skills/FORKS.json`; `src/aa_ma/forks.py`; `scripts/fork-drift.sh` (:4, :39 hard-code `repos/mattpocock/skills`)
- `packages/codemem-mcp/src/codemem/draw/surface_allowlist.py`; `packages/codemem-mcp/src/codemem/draw/plugin_surface.py`
- `claude-code/skills/understand-codebase/references/PLAYBOOK-CONTRIBUTE.md:46`; `claude-code/skills/python-quality-gates/SKILL.md:42`
- `claude-code/commands/aa-ma-plan.md:579`, `claude-code/commands/aa-ma-share.md:30` (readlink fix → `/../../..`)
- `claude-code/rules/engineering-standards.md` (:66 hook-modification scope; §2 TDD block; §5 rows; §1 Critical-Path table)
- `docs/spec/aa-ma-specification.md` (:145, :183-188, :911); `docs/spec/claude-code-foundations.md` (:34, :73, :92, :113, :157); `README.md` (:255, "### All commands"); `SECURITY.md` (:11-12)
- `examples/**/aa-ma-team-guide-reference.md:69`; `claude-code/hooks/lib/aa-ma-footer.sh:5`; `claude-code/hooks/lib/aa-ma-chart-guard.sh:18` (comments)
- `tests/test_frontmatter_at_top.py`; `tests/test_doc_counts.py`; `tests/fixtures/draw-node-ids.json`; `tests/skills/test_assess_codebase.py:73`; `tests/test_plugin_surface.py:113-119`; 31 test files referencing `commands/`
- `claude-code/skills/dispatching-parallel-agents/SKILL.md` (:6 `languages:`, :7 `context:`); operational-constraints and system-mapping (`triggers`)
- `docs/adr/0004-write-a-skill-adoption.md` (→ Superseded); `docs/adr/INDEX.md` (every ADR step)
- Bats pinning prompt text (M5): `execute_aa_ma_milestone_phase_6_8.bats` (10 greps), `aa-ma-deps.bats`, `aa-ma-gate-scans.bats:155`, `aa-ma-gate-python.bats:45`, `test_diagram_verified.bats:127`, sole-dev-merge `fixtures/extract_stage.sh`
- `claude-code/hooks/lib/aa-ma-parse.sh` (`aa_ma_debug`, `HOOK_DEBUG` read at :68; `aa_ma_gate` launcher :261); `claude-code/hooks/aa-ma-plan-skip-warn.sh`; `claude-code/hooks/pre-compact-aa-ma.sh`; `tests/hooks/pre-compact.bats:110`; `docs/spec/plan-marker-grammar.md:207`
- `claude-code/hooks/security-static-check.sh`; `claude-code/agents/security-auditor.md:3,7`; verify-impl SKILL.md (:93-96 window, :205/:211); execute-aa-ma-milestone (:604, :605 conditions 3/4; :611-630 CRITICAL_PATH_REVIEW grep; :661-731 DIAGRAM_VERIFIED fence; :793/:857); sole-dev-merge Stage D (:443-531), `test_stage_d_triage.bats`, `test_smoke_e2e.bats:209`
- `claude-code/agents/code-reviewer.md` (:91 style-nit ban kept)
- `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py` (`blast_radius` returns key `downstream` :252; `aa_ma_context` reads `callees` :1287 = carried defect 1); `mcp_tools/sanitizers.py`; `cli.py` (`_cmd_query`; co_changes passed only path+budget :246); `packages/codemem-mcp/src/codemem/analysis/git_mining.py:207-210`; `storage/db.py`; `indexer.py`; `claude-code/codemem/mcp/server.py`
- 14-MCP-tool count sites: `tests/codemem/test_mcp_server.py` (`test_thirteen_exact`), SECURITY.md, `claude-code/codemem/README.md:63`, `claude-code/codemem/commands/codemem.md:57`, `packages/codemem-mcp/README.md`, `packages/codemem-mcp/pyproject.toml`, `docs/codemem/install-zero-config.md`; wording in `skills/impact-analysis/SKILL.md:227-232`, `skills/system-mapping/SKILL.md:140`
- `src/aa_ma/plan_parsers.py`; `src/aa_ma/enforce.py`; `src/aa_ma/render/coverage.py` (`_ROW_RE` :36 Create|Modify only; `contract_paths` :70 drops tests/docs); `src/aa_ma/grammar.py:49` imports plan_parsers (hence new `contract_rows` module)
- `docs/templates/{reference-template,tasks-template,plan-template}.md`; `claude-code/agents/aa-ma-scribe.md`; `claude-code/hooks/aa-ma-commit-drift.sh`; `scripts/regen-generated.sh`; `scripts/release.sh`
- Outside repo (HITL): `~/.claude/skills/<5>` + `~/.claude/hooks/lib/ruff-format.sh` (M2); `~/.claude/skills/senior-secops` (M8); `~/.claude/CLAUDE.md` "Coding & Architecture" :58-69 (M12); `~/.claude/settings.json` via install.sh. Project `CLAUDE.md` (gitignored; :51-52) is a local edit.

### Key Directories
- `.claude/dev/active/code-conventions-impact/` — this task's AA-MA files [valid: 2026-10-08]
- `.worktrees/<branch>` — per-milestone worktrees
- `~/.claude/backups/cci-mN-<ts>.tgz` — outside-repo backups (M2, M8, M12), count-verified (L-1300)
- `~/.claude/runtime/impact-seen-<session_id>/` — pre-edit hook once-per-file markers
- `~/.claude/logs/hooks.log` — single hook log
- `.claude/evals/` — eval results (gitignored)

## M2 As-Built Facts (2026-10-09)

- ADR-0019 `docs/adr/0019-coding-doctrine-skill-migration.md` — Accepted, INDEX row 41. [valid: 2026-10-09]
- Fork pins (`claude-code/skills/FORKS.json`): `secrets-management` = wshobson/agents `plugins/cicd-automation/skills/secrets-management` @ `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, state **derived** (no secret echo; trufflehog `--fail`), local md5 `ea0799c2`, upstream md5 `5273fb73`; `bash-defensive-patterns` = `plugins/shell-scripting/skills/bash-defensive-patterns` @ `5d65aa10638bcc1b390738e11f9bff213f61955a`, derived, upstream md5 `8280da5a`; `references/advanced-patterns.md` is local-only and kept out of `files`. [valid: 2026-10-09]
- LICENSE in every fork dir: wshobson MIT md5 `0e1b4dd9`; mattpocock MIT @ c55ee46 md5 `a1d7928c` (also added to the 5 pre-existing forks). [valid: 2026-10-09]
- `src/aa_ma/forks.py` ForkEntry required fields now include `upstream_repo` and `licence`; `python -m aa_ma.forks files` prints 4 columns (skill, repo, upstream, file); `scripts/fork-drift.sh` pre-flights and fetches each row's own repo; `--sha` applies to every row. [valid: 2026-10-09]
- Outside-repo backup: `~/.claude/backups/cci-m2-20261009T073602Z.tgz`, 11 files, sha256 `dfe5f8f9…4ec4c5` (restore fallback). [valid: 2026-10-09]
- `claude-code/hooks/ruff-format.sh` = Adoption, adapted: honours `AA_MA_HOOKS_DISABLE`, logs to `${CLAUDE_HOOK_LOG:-~/.claude/logs/hooks.log}`, passes `--` before the path. Not cmp-identical to the live `~/.claude/hooks/lib/ruff-format.sh` (until 3.0 relinks it). [valid: 2026-10-09]
- `scripts/install.sh`: row `PostToolUse|Edit|Write|ruff-format.sh|10|`; rows parsed by a regex anchored on `<name>.sh|<timeout>|` (same grammar as codemem `_HOOK_ROW`); settings backups are sibling files `~/.claude/backups/settings-aa-ma-forge-<ts>.json`; `--force` still backs up real dirs. `scripts/uninstall.sh --restore` walks every `aa-ma-forge-*` backup newest-first (newest copy per path wins); deregisters ruff-format only without `--restore`. [valid: 2026-10-09] [Superseded by M3 (2f2de1a, 41d8288): uninstall deregisters every AA_MA_HOOKS row, with or without `--restore`; the table lives in scripts/lib/aa-ma-install-lib.sh.]
- Real PostToolUse(Edit) payload fixture: `tests/hooks/fixtures/ruff-format/posttooluse-edit.json` (captured 2026-10-09, paths rewritten to `/tmp/capture`). [valid: 2026-10-09]
- Counts after M2: skills 27, top-level hooks 9. Orphans pinned in `test_plugin_surface.py` until M12: `llm-output-safety`, `bash-defensive-patterns`. [valid: 2026-10-09]
- Convention (TDD dispute, 2026-10-09): RED tests get their own `test(...)` commit before the GREEN commit. [valid: 2026-10-09]

## M3 As-Built Facts (2026-10-09)
- Slash entry points are skills: `claude-code/commands/` is gone; 13 former commands live at `claude-code/skills/<name>/SKILL.md` (11 git mv + assess-codebase, understand-codebase merged); skills 38, commands 0. [valid: 2026-10-09]
- `disable-model-invocation: true` on exactly `sole-dev-merge`, `aa-ma-share`, `execute-aa-ma-full`, `archive-aa-ma` (`tests/skills/test_model_invocation_list.py`). [valid: 2026-10-09]
- Checkout from an installed skill: `readlink -f ~/.claude/skills/<x>/SKILL.md` then `/../../..` (aa-ma-plan, aa-ma-share). [valid: 2026-10-09]
- The one hook table: `AA_MA_HOOKS` in `scripts/lib/aa-ma-install-lib.sh` (+ `aa_ma_hook_parse`, `aa_ma_hooks_validate`, `points_into_repo`); sourced by install.sh/uninstall.sh; codemem `surface_allowlist.HOOK_TABLE` points at it. [valid: 2026-10-09]
- Foreign-symlink manifest: `~/.claude/backups/aa-ma-forge-<ts>/foreign-symlinks.tsv` (`<link>\t<dest>`), replayed by `uninstall.sh --restore`. [valid: 2026-10-09]
- `/grill-me` is declared external (`surface_allowlist.EXTERNAL["command"]`), the user-level mattpocock skill. [valid: 2026-10-09]
- ADR-0020 Accepted; next ADR is 0021. [valid: 2026-10-09]

## Decisions (one line each; full text in plan §3)

- D1 Two plans: this plan = map groups 1–12, forge only; reuse (T13/T14) → later `reuse-kit` plan; T13's in-repo git-HEAD helper stays (M10). [valid: 2026-10-08]
- D2 `deslop-shared-libs` → declared-external (gstack-owned); migration is 5 skills, not 7.
- D3 `senior-secops` → new forge skill `secops` (thin router); global copy backed up and removed (deletes stub scanner, defect 2); `"off"` override left alone.
- D4 Retire forge `/grill-me`; 13 commands convert.
- D5 Milestone order approved, commands→skills early (M3).
- D6 Prototypes: M3 install path, M10 hook UX, M11 co-change threshold.
- D7 Worktree per milestone (live symlinks point at the main checkout).
- D8 Touched files comply in full (file-level, not line-level).
- D9 (superseded) no `disable-model-invocation`; **D9 revised** (2026-10-08): `disable-model-invocation: true` on `sole-dev-merge` and `aa-ma-share`; **revised again** (2026-10-09, M3 §6.8 security): also `execute-aa-ma-full` and `archive-aa-ma` (commit/tag/push with no per-step gate) — 4 skills.
- D10 `Test-Command: none — <reason>` opt-out for TESTS_VERIFIED.
- D11 One release (v0.18.0) in its own milestone M14; interim releases dropped.
- D12 Commit scan keeps blocking: forge-pinned `ruff check --isolated --select S602,S604,S307,S608,S301` + secret-literal/path-traversal regexes, exit 2 in any repo.
- P1 Touched-files harness = pre-commit (staged locally; `--from-ref/--to-ref` in CI). P2 Expected-Blast-Radius = Contract `Files:` rows. P3 IMPACT_VERIFIED via `aa-ma-impact` CLI shelling out to codemem. P4 TESTS_VERIFIED for every plan; IMPACT_VERIFIED only for plans `Created:` ≥ IMPACT_CUTOVER. P5 delete unbacked pyproject claims. P6 griffe for aa_ma + codemem only. P7 Dependabot = github-actions + uv. P8 split-on-touch is M5. P9 evals advisory via run-evals.sh (release + weekly local).

## Map Tickets (all RESOLVED; source `code-conventions-impact-map.md`)

- Ticket 1: Where is every coding convention stated today, and where is it enforced? — ~8.8k auto-loaded tokens; real standard is global-only; enforcement thin (bandit `|| true`, D1xx ignored); ponytail↔SOLID/TDD and debug-env-var contradictions. [valid: 2026-10-08]
- Ticket 2: How do our Python, Bash and Markdown-skill conventions compare with best practice? — text strong, enforcement weak: 4 silent-pass security checks, no supply-chain layer, 6 oversized skills, no skill evals; 19 prioritised actions. [valid: 2026-10-08]
- Ticket 3: What should the TS/JS, R and SQL convention cards contain? — TS strict + typescript-eslint + pino (stderr); R Air/lintr/roxygen2/logger/renv; SQLFluff + dbt style; conflicts noted (pino stdout, `@param` vs `Args:`, SQL keyword case). [valid: 2026-10-08]
- Ticket 4: What is the state of impact analysis, and which code-writing skills invoke it? — most gaps open; `aa_ma_context` callees/downstream key bug; no general coding skill invokes it; cheapest wins = co_changes, who_calls pre-edit, path tagging. [valid: 2026-10-08]
- Ticket 5: What reusable code exists, and how do others curate and graduate it? — nothing packaged; ~3k untested snippet fences; git-HEAD helper ×6 is the first graduation candidate; copier + uv workspaces viable. [valid: 2026-10-08]
- Ticket 6: Should impact analysis be an explicit step in the coding skills? — global index-gated PreToolUse hook (once/file/session) + forge skills name it; R1/R3/R4/R6; plugin-surface edges into codemem; `callees` rename + alias. [valid: 2026-10-08]
- Ticket 7: Is the impact check HARD-enforced in the gate? — HARD, gate-computed (DIAGRAM_VERIFIED pattern); unpredicted / predicted-unchanged / co-change (≥5 & ≥50%) misses need `Impact-Explained:`; undeclared API breaks block; derived path tags; new plans only. [valid: 2026-10-08]
- Ticket 8: What is the comments and docstrings standard per language? — native doc format for public API; full Ruff D (google, D417) on touched files; `# why:` on justified suppressions, RUF100 removes the rest; `TODO(#N|ADR-NNNN)`; reviewer WARNs on substance. [valid: 2026-10-08]
- Ticket 9: Is `logging-and-comments` adopted as the logging standard? — moves into forge as one revised skill; NullHandler optional; JSON for services; ruff hook feeds findings back; `LOG_LEVEL` + `HOOK_DEBUG`; one hook log + shared log lib. [valid: 2026-10-08]
- Ticket 10: What is the SecOps baseline, and where does each check run? — 4-layer fail-loud baseline (edit/commit/CI/gate); gitleaks, `uv sync --locked` + audit, Dependabot; Ruff S replaces Bandit after a pinned comparison (gap fallback); secops router; redaction helpers. [valid: 2026-10-08]
- Ticket 11: How are design principles stated so they are checkable? — start concrete, earn abstractions by evidence (Ste's policy); knowledge-DRY now, code ~3rd occurrence; C901/PLR0913 + `# why:`; risk-proportionate TDD; gate runs tests (TESTS_VERIFIED). [valid: 2026-10-08]
- Ticket 12: How is the coding doctrine packaged within an auto-load budget? — thin auto-loaded `coding-standards.md` (≤~1.5k tok) + topic skills + `language-conventions`; state-once dedupe incl. global CLAUDE.md (HITL); budget ratchet; global skills migrate; ponytail declared-external. [valid: 2026-10-08]
- Ticket 13: Where does the reusable-code collection live? — private Carmen uv repo + PEP 723 snippets; public-forge router skill; public copier template; confidentiality gate — deferred to the `reuse-kit` plan (D1), except the in-repo git-HEAD helper (M10). [valid: 2026-10-08]
- Ticket 14: When does shared code graduate from snippet to module to library? — evidenced same-contract reuse → `_experimental`; public API after 2 stable minors + 2 repos; griffe at library; SemVer 0.y→1.0 — deferred to `reuse-kit` (D1). [valid: 2026-10-08]
- Ticket 15: What conventions govern Markdown skills and commands as prompt-as-code? — fold writing-for-agents-eval in; 500-line cap + ratchet; strict frontmatter schema test; ≥3 eval cases for gate skills (advisory); commands → skills; why-or-pointer on MUST rules; hook contracts + real-payload bats. [valid: 2026-10-08]

## Research Files

- `docs/research/code-conventions-impact-inventory.md` — T1: where is every coding convention stated, and where is each enforced? [valid: 2026-10-08]
- `docs/research/code-conventions-impact-best-practice.md` — T2: how do our Python, Bash and Markdown-skill conventions compare with current best practice? [valid: 2026-10-08]
- `docs/research/code-conventions-impact-language-cards.md` — T3: what should the TS/JS, R and SQL convention cards contain? [valid: 2026-10-08]
- `docs/research/code-conventions-impact-impact-status.md` — T4: state of impact analysis now, and which code-writing skills invoke it? [valid: 2026-10-08]
- `docs/research/code-conventions-impact-reuse-prior-art.md` — T5: what reusable code exists, and how do others curate and graduate it? [valid: 2026-10-08]
- `docs/research/code-conventions-impact-ruff-vs-bandit.md` — (created in M8.1) does Ruff S at 0.15.9 cover every Bandit 1.9.4 test that fires here; plus §deps triage of the 13 vulnerable packages. [valid: 2026-10-08]
- Prior evidence: `docs/research/impact-analysis-lifecycle-review.md` (2026-09-24; gaps 1–7, R1–R6).

## Folded-in Inputs

- `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md` — 4/4 RESOLVED; executed by M4. [valid: 2026-10-08]
- Imported map: `.claude/dev/active/code-conventions-impact/code-conventions-impact-map.md` (moved from `.claude/dev/charting/code-conventions-impact/`). [valid: 2026-10-08]
- Eng-review test plan: `~/.gstack/projects/snewhouse-aa-ma-forge/sjnewhouse-feature-engineering-standards-eng-review-test-plan-20261008-132258.md`. [valid: 2026-10-08]

## Carried Defects (fixed by this plan)

1. `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:1287` — `aa_ma_context` reads `callees` but `blast_radius` returns `downstream` (:252) → count always 0. Fixed M10.2. [valid: 2026-10-08]
2. `~/.claude/skills/senior-secops/scripts/security_scanner.py` — stub `analyze()` always returns no findings. Removed M8.7 (D3). [valid: 2026-10-08]
3. `.github/workflows/security.yml:39` — Bandit `|| true` can never fail CI. Fixed M8.2. [valid: 2026-10-08]

## Glossary

| Term | Definition |
|------|-----------|
| Touched file | A file in the staged set (local) or the PR diff (CI); must comply in full (D8). Untouched files are never checked against new rules. |
| Fence 3 / fence 4 | New §6.7 gate blocks in execute-aa-ma-milestone: TESTS_VERIFIED (M9) and IMPACT_VERIFIED (M11), each its own bash block after DIAGRAM_VERIFIED. |
| Step N.0 | Post-merge work of milestone N-1 (live install, pre-commit install, live probes), run from the main checkout. |
| Grandfathered | A plan `Created:` before `IMPACT_CUTOVER`; fence 4 prints "not applicable". This plan (Created 2026-10-08) is grandfathered. |
| Expected-Blast-Radius | The milestone's Contract `Files:` rows (Create/Modify/Test/Move/Merge/Delete), via `contract_rows.milestone_contract_rows`. |

## M4 As-Built Facts (2026-10-09)
- Skill frontmatter schema lives in `tests/test_frontmatter_at_top.py` (`SKILL_KEYS`, `skill_schema_errors`, `UNSCOPED_TOOLS_ALLOWLIST` = assess-codebase, retro). Per-skill versions are `metadata.version`. [valid: 2026-10-09]
- Size ratchet `tests/test_prompt_size.py`: whole-file lines, `ALLOWLIST` ceilings aa-ma-execution 1295, execute-aa-ma-milestone 1244, aa-ma-plan 1154, sole-dev-merge 1057, execute-aa-ma-full 758, plan-verification 608; `TOC_ALLOWLIST` 24 references. [valid: 2026-10-09]
- Eval fixtures live in `tests/fixtures/evals/<name>/` (scaffolds `evals/_lib/`); baseline 14/24 (pre-4.7) → 22/24 with skill-fired 24/24 (single run after 4.7 + §6.8 fixes); failing cases vary between n=1 runs. [valid: 2026-10-09]
- Eval mechanism: `claude plugin eval <repo-root> --no-publish --runs 1 --ablation none --trust-plugin --max-cost-usd <cap> --json <f>`; cases `evals/<skill>/<case>/case.yaml` with `plugins: ["../../../claude-code"]`; skills load as `claude-code:<skill>`; every case has a `tool_used: Skill` grader. One haiku case ≈ $0.0034. [valid: 2026-10-09]
- `writing-for-agents` fork: mattpocock/skills @ c55ee46, state derived, upstream md5 SKILL.md 9663b04e / SKILL-MECHANICS.md f3648a8f; ADR-0021 Accepted; next ADR 0022. [valid: 2026-10-09]
- install.sh stale sweep covers `commands/*.md`, `skills/*`, `agents/*.md` links dangling into the repo. [valid: 2026-10-09]

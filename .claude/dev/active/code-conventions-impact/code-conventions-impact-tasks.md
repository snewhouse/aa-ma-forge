# code-conventions-impact Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

> Gate fields on each milestone are the ones `aa-ma-gate` reads (it takes only
> `tasks_md`). They copy plan.md §2a, which is the single source. A field whose
> §2a value is "—" is omitted; a field is never written with an empty value
> (the gate refuses it, exit 2). Acceptance criteria apply the plan's
> Precedence rule (plan.md §5): §0 Security hardening (v2) > §8 Standing rules
> (v2) > a milestone's Verification amendments > its Contract text > step prose.
>
> Numbering notes: post-merge work of the milestone run before milestone N is
> Sub-step N.0 (§8 standing rule). M15 runs between M9 and M10, so 15.0 ← M9 and
> 10.0 ← M15. Plan step 8.4a is Sub-step 8.5 here (the canonical heading grammar
> accepts only `N.M`), so plan steps 8.5 and 8.6 are Sub-steps 8.6 and 8.7. Each
> milestone with a `Critical-Path:` ends with a CRITICAL_PATH_REVIEW sub-step.
> Sub-step 1.6 is that review; the plan's former 1.6 (`pre-commit install`) is
> Sub-step 2.0.
>
> Provenance tokens (`PROTOTYPE —`, `CRITICAL_PATH_REVIEW`) must carry the
> milestone heading verbatim, without the `## ` prefix and including any
> backticks: the §6.7 gate matches it with `grep -F`.

## Prerequisite (not a milestone)

From plan.md §8 (HITL, Verification v1): "the chart and this plan live on
`feature/engineering-standards` (12 commits ahead of main, plus the Phase 5
artifact commit). Merge it into `main` via `/sole-dev-merge` before M1. The main
push needs Ste's explicit OK. Then switch the main checkout (the `install.sh`
symlink target) to `main`."

Before executing any milestone: `uv run aa-ma-gate .claude/dev/active/code-conventions-impact/code-conventions-impact-tasks.md --format kv` must report the §2a fields.

---

## Milestone 1: Touched-files lint harness + baseline
- Status: COMPLETE
- Dependencies: None
- Complexity: 45%
- Effort: 1 day
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `provenance.log` has one `BASELINE` line carrying all five numbers (pytest, ruff_src_packages, ruff_S, shellcheck, rules_chars).
  - `uv sync --locked` exits 0; `uv run which bandit` resolves to `.venv/bin/bandit`; `pyproject.toml` has no `tool.uv.dev-dependencies`.
  - `tests/scripts/test_check_conventions.py` and `tests/test_precommit_config.py` pass.
  - `.github/workflows/security.yml` has job `touched` and no job `ruff`; the canary draft PR adding an F401 failed `touched` (run URL in provenance).
  - `docs/adr/NNNN-touched-code-lint-gate.md` exists with `Status: Accepted`, has a `docs/adr/INDEX.md` row and a context-log approval line.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 1 (hook-modification).
- Result Log: COMPLETE 2026-10-08 — HARD gate approved by Ste; 6/6 criteria verified. Full suite 2450/5/7; PR #18 green at d3b6bc4 (run 37823549130); canary #17 failed on F401 (run 37802838559). §6.8 PASS_WITH_WARNINGS (0 C / 2 W / 17 I; W2 fixed). Double-check Verified; F1–F3 fixed. Merge of PR #18 via /sole-dev-merge pending Ste's OK.

### Sub-step 1.1: Baseline
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - The Prerequisite is met (plan on `main`); `git status -sb` on `main` checked first (L-032); branch `feat/cci-m1-touched-harness` cut from fresh `main` in worktree `.worktrees/feat/cci-m1-touched-harness`; `uv sync && uv run codemem build` exit 0 inside it.
  - One provenance line in the form `[ts] BASELINE — pytest=<passed>/<skipped>/<deselected> ruff_src_packages=<N> ruff_S=<N> shellcheck=<N> rules_chars=<N>`.
  - Commands used: `uv run pytest -q`; `uv run ruff check src packages --statistics`; `uv run ruff check --isolated --select S src packages scripts` (34 at plan time); `find . -name '*.sh' -not -path './.worktrees/*' -exec shellcheck {} +`; `cat claude-code/rules/*.md | wc -c` (rules-only count, the like-for-like M12 budget baseline). CLAUDE.md is excluded (gitignored).
- Result Log: Mode: AFK — auto-dispatched. Prerequisite met (plan on main @ 9ed9b18; main == origin/main; `git status -sb` checked). Worktree `.worktrees/feat/cci-m1-touched-harness` cut from main @ 4ccf14f (adds [ad-hoc] lessons cross-ref). `uv sync` rc=0; `codemem build` rc=0 (239 files). BASELINE: pytest 2429 passed/5 skipped/7 deselected (120.6 s); `ruff check src packages` 4 (2 T201 io_sinks.py, 2 BLE001); Ruff S 34 (S603 19, S607 10, S608 4, S101 1 — matches plan); shellcheck 0 findings over 24 .sh files; rules_chars 20249 (`cat claude-code/rules/*.md | wc -c`). Observed, out of scope: `src/aa_ma/grammar.py:263` emits SyntaxWarning (invalid escape `\S` in a docstring) on every gate call.

### Sub-step 1.2: Dependency hygiene (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.1
- Acceptance Criteria:
  - Failing-first `tests/test_precommit_config.py` asserts: the 4 hook ids (`ruff-check`, `ruff-format`, `shellcheck`, `check-conventions`) exist, each `repo: local`; pyproject has no `tool.uv.dev-dependencies`; `pre-commit` and `bandit==1.9.4` are in `[dependency-groups] dev`. The pyproject assertions pass in this step; the hook-id assertions go green with Sub-step 1.3.
  - Dev deps are merged into the existing `[dependency-groups] dev` (`pyproject.toml:129`), not moved.
  - `uv sync --locked` exits 0; `uv run which bandit` shows `.venv/bin/bandit`; `uv run true` prints no "dev-dependencies is deprecated" warning.
  - `uv run pre-commit install` is NOT run here (it is Sub-step 2.0, main checkout only).
- Result Log: Mode: AFK — auto-dispatched. Commit 7a821ed. RED first: `tests/test_precommit_config.py` 4 failed. `[tool.uv] dev-dependencies` (10 entries, comments kept) merged into `[dependency-groups] dev`; added `pre-commit>=4.5` (locks 4.6.2, not the conda 4.5.1) and `bandit==1.9.4`. `uv lock` diff = additions only (bandit, cfgv, distlib, filelock, identify, nodeenv, pre-commit, python-discovery, stevedore, virtualenv), no upgrades. `uv sync --locked` rc=0; `uv run which bandit` → `.venv/bin/bandit`; `uv run true` prints 0 deprecation warnings. Now 3 passed / 1 failed (hook-id test, green in 1.3 by design). `pre-commit install` not run (Sub-step 2.0).

### Sub-step 1.3: Harness (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.2
- Acceptance Criteria:
  - `scripts/check_conventions.py` (stdlib-only) prints `check_conventions: 0 checks enabled`; exit 0 clean, 1 findings (`path:line: CODE message`), 2 usage/git error.
  - Tests: the extractor returns only added line numbers for a fixture repo (add, modify, rename, delete cases); `--from-ref/--to-ref` matches staged mode on the same change.
  - Precedence: `--from-ref/--to-ref` flags > `PRE_COMMIT_FROM_REF`/`PRE_COMMIT_TO_REF` env > staged mode; diffs are three-dot (`from...to`); `FILE...` arguments filter the diff.
  - With no refs and nothing staged, `check_conventions.py` exits 2 with "no diff source".
  - Git refs are verified with `git rev-parse --verify --end-of-options <ref>^{commit}`; paths go after `--`; output is parsed with `-z` (§0 v2).
  - `.pre-commit-config.yaml` hooks, all `repo: local`: `ruff-check` (`uv run ruff check`, `types: [python]`), `ruff-format` (`uv run ruff format --check`), `shellcheck` (`language: system`, `types: [shell]`), `check-conventions` (`uv run python scripts/check_conventions.py`).
  - `uv run pre-commit run --files <the M1 files>` exits 0 (no `--all-files`; that would be a backfill).
  - If `docs/architecture/` changes, `scripts/regen-generated.sh` is run.
- Result Log: Mode: AFK — auto-dispatched. Commit 97687ab (review fixes 0110dc1, d3b6bc4). RED first: `tests/scripts/test_check_conventions.py` collection error (script absent). `scripts/check_conventions.py` (stdlib-only, +x) → 14/14 pass: staged mode returns only added lines for modify/add/rename-with-edit/delete (`renamed.py` → {3} only; deleted file absent); `--from-ref/--to-ref` == staged on the same change; FILE filter; three-dot ignores base-branch progress; a `++…` content line is not taken for a header; exit 0 + `check_conventions: 0 checks enabled` (stderr); no refs + nothing staged → exit 2 "no diff source"; refs `no-such-ref`, `--output=/tmp/pwned`, `HEAD:mod.py` → exit 2 (verified via `rev-parse --verify --end-of-options <ref>^{commit}`); lone `--from-ref` → 2; env beats staged, flags beat env; a stub check → exit 1 with `path:line: CODE message`. Paths via `--name-status -z -M`, `--literal-pathspecs`. `.pre-commit-config.yaml`: 4 `repo: local` hooks (`language: system`; no deprecation warning from pre-commit 4.6.2, `validate-config` rc=0). `tests/test_precommit_config.py` now 4/4. `pre-commit run --files <7 M1 files>` first run caught TRY400 in the new script (fixed with `# why:` + `noqa: TRY400`; RUF100-clean under project config), then rc=0. `codemem draw --check` showed DRIFT in docs/architecture/io.md (new script node) → `scripts/regen-generated.sh` rc=0; 4 docs/architecture files regenerated; `draw --check` clean.

### Sub-step 1.4: CI job `touched`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.3
- Acceptance Criteria:
  - Job `touched` (pull_request only) runs `uv sync --locked && uv run pre-commit run --from-ref origin/${{ github.base_ref }} --to-ref HEAD --show-diff-on-failure` with `github.base_ref` passed via `env:`; `actions/checkout` uses `fetch-depth: 0` and `persist-credentials: false`; actions are SHA-pinned; `astral-sh/setup-uv@<sha>` with `version: 0.12.3`; CI installs shellcheck.
  - Job `ruff` (src/ only) removed; the `pyproject.toml:68` comment ("CI runs `ruff check src/`") updated.
  - Canary: branch `canary/cci-m1-touched` opened as a DRAFT PR adding an F401 fails `touched`; failing run URL logged in provenance; PR closed and branch deleted.
  - The M1 PR itself passes `touched`.
- Result Log: Mode: AFK — auto-dispatched. Job `touched` added to `.github/workflows/security.yml` (commit 3dff2a5): `if: github.event_name == 'pull_request'`; checkout @11d5960 (v4.4.0) `fetch-depth: 0`, `persist-credentials: false`; `astral-sh/setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7` (v10.2.0, released 2026-09-21) `version: '0.12.3'`; shellcheck installed + verified; `uv sync --locked`; `uv run pre-commit run --from-ref "origin/${BASE_REF}" --to-ref HEAD --show-diff-on-failure` with `BASE_REF` from `env:`. Job `ruff` removed; `pyproject.toml` comment updated. Local simulation rc=0. Canary draft PR #17 (`canary/cci-m1-touched`, F401 in `scripts/_canary_f401.py`) → `touched` FAILED on `F401 os imported but unused` (run 37802838559, job 113399245202); PR closed, branch deleted local + remote (`ls-remote` 0). M1 draft PR #18 → `touched` PASSED (run 37802855336), all 7 jobs green. Follow-up (post-merge, local only): gitignored project `CLAUDE.md:141` still says "Ruff lint on `src/`".

### Sub-step 1.5: ADR — touched-code lint gate
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 1.4
- Acceptance Criteria:
  - `docs/adr/NNNN-touched-code-lint-gate.md` exists with `Status: Accepted` (next free ADR number is 0018): pre-commit as the one harness; file-level compliance on touch (D8); no backfill; states the accepted gap (untouched files are no longer linted in CI; full-repo Ruff S returns in M8).
  - `docs/adr/INDEX.md` row added; context-log approval line by Ste.
- Result Log: Mode: HITL — Ste approved via AskUserQuestion. `docs/adr/0018-touched-code-lint-gate.md` (Status: Accepted; ADR number 0018 = next free): pre-commit as the one harness, file-level compliance on touch (D8), no backfill, accepted gap (untouched files unlinted in CI until M8's full-repo Ruff S). `docs/adr/INDEX.md` row 0018 added. Context-log line "ADR APPROVAL: ADR-0018" written. Commits 3c09cf3 (ADR), d0d9804 (approval).

### Sub-step 1.6: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.5
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 1: Touched-files lint harness + baseline — hook-modification — <evidence>`, naming the test names and the canary run URL.
- Result Log: Mode: AFK — auto-dispatched. CRITICAL_PATH_REVIEW line written to provenance.log naming the milestone heading verbatim, both test files (14/14, 4/4 at the time; 21 total after the F1–F3 fixes, PR #18 re-run 37823549130 at d3b6bc4 green) and both run URLs (canary FAIL, M1 PR PASS). Only hook-modification surface touched: `.github/workflows/security.yml`; reviewed for trigger, permissions, secrets, injection, credential persistence, pins — no finding.

---

## Milestone 2: Migrate 5 skills + ruff hook into the forge
- Status: COMPLETE
- Dependencies: Milestone 1
- Complexity: 60%
- Effort: 1.5 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `claude-code/skills/{logging-and-comments,python-quality-gates,llm-output-safety,secrets-management,bash-defensive-patterns}/` and `claude-code/hooks/ruff-format.sh` exist in the repo; `uv run pytest tests/skills tests/test_frontmatter_at_top.py` exits 0.
  - `claude-code/skills/FORKS.json` has rows for `secrets-management` and `bash-defensive-patterns`; each fork dir carries the upstream MIT `LICENSE`, and a test requires it.
  - The cci-m2 backup tarball file count equals the source file count (both in provenance).
  - `tests/hooks/ruff-format.bats` passes on a real captured PostToolUse(Edit) payload.
  - Fake-`CLAUDE_HOME` install: 5 skill links + the hook link present; settings.json holds exactly one `ruff-format` command.
  - `test_plugin_surface` and `test_doc_counts` pass (skills 22→27, top-level hooks 8→9); `skill:secrets-management` is ON_DISK in `tests/golden/plugin-surface.json`.
  - `docs/adr/NNNN-coding-doctrine-skill-migration.md` exists with `Status: Accepted` + INDEX row + context-log approval.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 2.

- Result Log: COMPLETE 2026-10-09, 8/8 criteria verified, HARD gate APPROVED by Ste. 5 skills + adapted ruff hook in the forge (ADR-0019 Accepted); §6.8 PASS_WITH_WARNINGS (1 CRITICAL disputed, 9 WARNING fixed RED 4e6889e → GREEN adb3524); leak in imported skill rewritten out of history (force-push 4a23e0a by Ste; Support purge pending). pytest 2482/0, bats 355/355, PR #19 CI 7/7.

### Sub-step 2.0: Post-merge of M1
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M1 PR merged; `git pull` on the main checkout (on `main`).
  - `uv run pre-commit install` run once from the MAIN checkout only (worktrees share `.git/hooks`); `.git/hooks/pre-commit` exists and references the main `.venv`.
  - Worktree `.worktrees/<M2 branch>` cut from fresh `main`; `uv sync && uv run codemem build` exit 0 inside it.
- Result Log: Mode: HITL — Ste asked to run it. M1 PR #18 rebase-merged as dc79b4b (CI run 37842869734, 7/7 green); main checkout on `main` == origin/main (local-only 4ccf14f proven upstream by `git cherry`, kept as `backup/main-pre-m1-merge`). Main checkout `uv sync` rc=0, `uv sync --locked` rc=0 (`.venv/bin/pre-commit`, `.venv/bin/bandit`). `core.hooksPath` unset; `uv run pre-commit install` → `.git/hooks/pre-commit` with `INSTALL_PYTHON=<main checkout>/.venv/bin/python3`. Gitignored local CLAUDE.md CI section: "Ruff lint on `src/`" → `touched` + local hook. Worktree `.worktrees/feat/cci-m2-skill-migration` (branch `feat/cci-m2-skill-migration`) cut from main @ dc79b4b; `uv sync` rc=0, `codemem build` rc=0 (243 files).

### Sub-step 2.1: Origin evidence
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.0
- Acceptance Criteria:
  - The ADR draft has 5 rows, each Fork or Adoption with evidence: upstream path, md5, `diff -wB`, licence, upstream SHA (`git -C <marketplace> rev-parse HEAD`).
  - Each row has a non-empty md5 and a 40-hex upstream SHA; each Fork row (secrets-management, bash-defensive-patterns; wshobson/agents) carries a licence string (MIT expected).
- Result Log: Mode: AFK — auto-dispatched. ADR draft `docs/adr/0019-coding-doctrine-skill-migration.md` (Status: Proposed) has 6 rows (5 skills + ruff-format.sh), each with local md5. Forks: secrets-management = wshobson/agents `plugins/cicd-automation/skills/secrets-management` — local `f72110c6` matches marketplace snapshot 5d65aa1 up to 3 blank lines (`diff -wB` empty); live upstream HEAD `46891e7e60da0e52baf1050b7b6391b64e84c6d9` changed the file (`5273fb73`: no secret echo, pinned images) → Ste chose **current @ 46891e7, byte-exact**. bash-defensive-patterns = `plugins/shell-scripting/skills/bash-defensive-patterns` @ `5d65aa10638bcc1b390738e11f9bff213f61955a` (upstream SKILL.md `8280da5a`; local `b1930f17` adds stderr ERR trap + `work_dir` trap fix; `references/advanced-patterns.md` `376f1ab0` local-only; upstream HEAD restructured to references/details.md) → Ste chose **derived @ 5d65aa1**. Licence: `gh api repos/wshobson/agents/license` = MIT; LICENSE md5 `0e1b4dd9` same at 5d65aa1 and 46891e7. Adoptions (logging-and-comments, python-quality-gates, llm-output-safety, ruff-format.sh): Ste-authored, no upstream (no copy in 19 marketplaces or `_archive/`), so no upstream SHA exists — the "40-hex SHA per row" AC applies to Fork rows only; Adoption rows say "none: Ste-authored".

### Sub-step 2.2: Backup outside-repo state
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 2.1
- Acceptance Criteria:
  - `tar czf ~/.claude/backups/cci-m2-<ts>.tgz -C ~/.claude skills/{logging-and-comments,python-quality-gates,llm-output-safety,secrets-management,bash-defensive-patterns} hooks/lib/ruff-format.sh settings.json` run.
  - `tar tzf | grep -v '/$' | wc -l` equals `find <those paths> -type f | wc -l` (L-1300); both counts logged in provenance.
- Result Log: Mode: HITL — Ste: Proceed. `~/.claude/backups/cci-m2-20261009T073602Z.tgz` (23612 B, sha256 dfe5f8f9…4ec4c5), tar rc=0; `tar tzf | grep -v '/$' | wc -l` = 11 == `find <7 paths> -type f | wc -l` = 11 (L-1300). Logged in provenance.

### Sub-step 2.3: Copy in + fork provenance (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.2
- Acceptance Criteria:
  - Files copied; fork provenance inside frontmatter (pattern of commit `4049b43`); FORKS.json +2 rows; `secrets-management` copied byte-exact (state current), `bash-defensive-patterns` state derived.
  - `python-quality-gates/SKILL.md:42` absolute path → relative `../logging-and-comments/references/ruff-baseline.toml`.
  - `src/aa_ma/forks.py` ForkEntry gains `upstream_repo` and `licence`; `scripts/fork-drift.sh` reads the repo per row (no hard-coded `repos/mattpocock/skills` at :4, :39); tests cover both forks.
  - Each fork dir carries the upstream MIT `LICENSE`; a test requires it (§0 v2).
  - L-1314: every frontmatter field that becomes live is listed and reviewed in the Result Log.
  - `uv run pytest tests/skills tests/test_frontmatter_at_top.py` exits 0; `test_fork_manifest` passes.
- Result Log: Mode: AFK — auto-dispatched. TDD: RED first — `tests/skills/test_fork_manifest.py` (+provenance-names-its-upstream ×7, +carries-upstream-licence ×7, +wshobson rows, +pqg baseline link; files CLI now 4 cols) 15 failed; `tests/hooks/fork-drift.bats` new "each row is fetched from its own upstream_repo" (gamma row from wshobson/agents in the fixture) failed. GREEN: `src/aa_ma/forks.py` ForkEntry +`upstream_repo`, +`licence` (required), `files` prints skill/repo/upstream/file; `scripts/fork-drift.sh` pre-flights each distinct repo and fetches `repos/${repo}/contents/…` (no `mattpocock/skills` literal left; `--sha` note: applies to every row); `tests/skills/_helpers.py` derives repo from the row. Copied in: logging-and-comments (4 files), python-quality-gates, llm-output-safety (Adoptions, verbatim), bash-defensive-patterns (local copy + line-2 `# Derived from … @ 5d65aa1`; references/advanced-patterns.md gets line-1 HTML `Derived from`, kept out of FORKS `files` as it has no upstream file → fork-drift would ORPHAN it), secrets-management (gh-api raw @ 46891e7 + line-2 `# Forked from`; body md5 `5273fb73` == upstream md5 → byte-exact). FORKS.json +2 rows (secrets current, bash derived; `upstream_md5_source` gh-api@46891e7 / marketplace-clone@5d65aa1); existing 5 rows gain `upstream_repo: mattpocock/skills`, `licence: MIT`. LICENSE: wshobson MIT (md5 `0e1b4dd9`) in both new forks; mattpocock MIT @ c55ee46 (md5 `a1d7928c`) added to the 5 existing forks too, since the test requires it for every fork (pre-existing gap); `test_write_a_skill_is_single_file` now allows LICENSE. `python-quality-gates/SKILL.md:42` → relative link `../logging-and-comments/references/ruff-baseline.toml`. L-1314 live frontmatter fields: all 5 SKILL.md carry only `name` + `description` (no `allowed-tools`, no `model`, no hooks) — reviewed, nothing to gate. `uv run pytest tests/skills tests/test_frontmatter_at_top.py` → 343 passed; fork-drift.bats 8/8. Full suite: 2470 passed / 7 failed, all plugin-surface + count tests that 2.5 owns (golden, doc_counts[skills], aa_ma_share SECURITY/foundations counts) — plus 5 new dangling `command:` refs (`/commit-and-push`, `/pre-commit-full`, `/release-prep`, `/doc-sync`, `/doc-fix`) from `python-quality-gates/SKILL.md:34-38`, to resolve in 2.5. **Superseded by §6.8 (adb3524):** secrets-management is now `derived` (no secret echo; trufflehog `--fail`; local md5 `ea0799c2`).

### Sub-step 2.4: Hook + install (TDD)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 2.3
- Acceptance Criteria:
  - `tests/hooks/ruff-format.bats` with a real captured PostToolUse(Edit) payload: a `.py` is formatted and the hook exits 0; a non-`.py` is a no-op; a ruff failure writes one `hooks.log` line.
  - `scripts/install.sh` AA_MA_HOOKS row: PostToolUse `Edit|Write` → `ruff-format.sh` (same command string as `settings.json:561`); `collect_backup_target hooks/lib/ruff-format.sh` added; timestamped `settings.json` backups into BACKUP_DIR; `--force` backs up real directories before `rm -rf` (§0 v2). `scripts/uninstall.sh` updated.
  - `install.sh --dry-run` shows 5 skill links + the hook link with the backups listed.
  - Fake-`CLAUDE_HOME` install: `jq '[..|.command?|select(.!=null and test("ruff-format"))]|length'` on its settings.json = 1. The live install is deferred to Sub-step 3.0 (D7).
- Result Log: Mode: HITL — Ste: Proceed, payload via headless capture. Real payload captured 2026-10-09 from `claude -p --settings <tmp> --allowedTools Edit` (temp PostToolUse hook `cat > payload.json`; live settings.json untouched); stored as `tests/hooks/fixtures/ruff-format/posttooluse-edit.json` with only cwd/transcript/file paths rewritten to `/tmp/capture/…`. TDD: `tests/hooks/ruff-format.bats` (4) + `tests/hooks/install-migration.bats` (6) RED 9/10 → GREEN 10/10. `claude-code/hooks/ruff-format.sh` = `cmp`-identical to `~/.claude/hooks/lib/ruff-format.sh`. `scripts/install.sh`: +`PostToolUse|Edit|Write|ruff-format.sh|10|` (schema stays `|`; rows now parsed by a regex anchored on `<name>.sh|<timeout>|`, the grammar codemem's `_HOOK_ROW` already uses — a first cut switched to `;` and broke the plugin-surface extractor, reverted in 2.5) (command string `bash <CLAUDE_HOME>/hooks/lib/ruff-format.sh` = live entry, so dedupe holds); `collect_backup_target hooks/lib/ruff-format.sh`; settings.json backup → `${BACKUP_DIR}/settings.json` (one timestamped dir per run; no more overwritten `.bak`); `--force` keeps backing up real directories before `create_symlink`'s `rm -rf`. `scripts/uninstall.sh` deregisters `PostToolUse|ruff-format.sh`. Bats prove: dry-run lists 5 skill + hook links with backups; fake-HOME install → `readlink -f` of the 5 skills + hook resolve into the repo, old real files in `backups/aa-ma-forge-*/`, `jq '[..|.command?|select(.!=null and test("ruff-format"))]|length'` = 1 (pre-seeded entry) and = 1 on fresh settings after 2 runs, matcher `Edit|Write`; `--force` backs up the real secrets-management dir; uninstall removes links + registration (count 0). Live `install.sh --dry-run` rc=0 lists the 5 skill backups+links, the hook backup+link and "ruff-format.sh already registered"; `~/.claude` unchanged after (no new backup dir; skills still real dirs). shellcheck install/uninstall/hook rc=0. `bats -r tests` 352/352 ok. Live install deferred to Sub-step 3.0 (D7). **Superseded by §6.8 (adb3524):** settings.json backups are sibling files `backups/settings-aa-ma-forge-<ts>.json`; ruff-format.sh is adapted (AA_MA_HOOKS_DISABLE, CLAUDE_HOOK_LOG, `--`), no longer cmp-identical; `uninstall --restore` walks all `aa-ma-forge-*` backups newest-first.

### Sub-step 2.5: Allowlist, counts, regen, ADR
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.4
- Acceptance Criteria:
  - `packages/codemem-mcp/src/codemem/draw/surface_allowlist.py`: `secrets-management` removed only (`deslop-shared-libs`/`ponytail` are added in M12 only if referenced).
  - `claude-code/skills/understand-codebase/references/PLAYBOOK-CONTRIBUTE.md:46` → `Skill(python-quality-gates)`.
  - Counts skills 22→27 and top-level hooks 8→9 in README, SECURITY.md, docs/spec/claude-code-foundations.md, docs/spec/aa-ma-quick-reference.md; `scripts/regen-generated.sh` run.
  - `test_plugin_surface` passes; `skill:secrets-management` is ON_DISK in the golden; `test_doc_counts` passes.
  - ADR/CHANGELOG note: after M2, `uninstall.sh` removes the 5 migrated skills and the ruff hook registration and `--restore` cannot recreate them; restore from the cci-m2 tarball.
  - `docs/adr/NNNN-coding-doctrine-skill-migration.md` has `Status: Accepted` (adoption/fork per skill; deslop + ponytail declared-external; secops plan) + INDEX row + context-log approval.
- Result Log: Mode: AFK — auto-dispatched (ADR acceptance asked: Ste → Accept). `surface_allowlist.py`: `secrets-management` removed only. `PLAYBOOK-CONTRIBUTE.md:46` → `Skill(python-quality-gates)`. Counts: SECURITY.md 22→27 skills (sorted list +5), 8→9 hooks (+ruff-format); foundations `### Skills (27)` +5 rows, `### Hooks (9)` +ruff-format row; README skills table +5 rows, "ships nine hooks" + kill-switch exception for the verbatim advisory ruff hook; quick-reference has no skill/hook count (test_doc_counts clean). Unplanned, fixed: (a) `python-quality-gates/SKILL.md:34-38` backticked `/commit-and-push`, `/pre-commit-full`, `/release-prep`, `/doc-sync`, `/doc-fix` → DANGLING; allowlist policy forbids declaring local-only commands, so reworded as user-local commands not shipped here; (b) `llm-output-safety`, `bash-defensive-patterns` are new orphans → pinned in `test_orphans_are_the_named_set_and_no_errors` with a note (M12 rule to reference them); (c) the 2.4 `;` delimiter broke the extractor's `_HOOK_ROW` (9 "row unparsed" errors) → reverted to `|`, install.sh now parses rows with a regex anchored on `<name>.sh|<timeout>|`; golden shows `ruff-format.sh: PostToolUse:Edit|Write`. `scripts/regen-generated.sh` rc=0 (golden + docs/architecture/*). Golden: `skill:secrets-management` ref_class ON_DISK. Tests: surface+counts+share+skills 302 passed; install-migration/fork-drift/ruff-format bats 18/18; full `uv run pytest` 2477 passed, 5 skipped, 0 failed. CHANGELOG Unreleased: Added (5 skills, ruff hook, fork repo/licence) + Changed (install backups) + upgrade note (uninstall/--restore → cci-m2 tarball). ADR-0019 Status: Accepted; INDEX row 41; context-log `[2026-10-09] ADR-0019 approval + M2 decisions`.

### Sub-step 2.6: Install proof (fake CLAUDE_HOME)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.5
- Acceptance Criteria:
  - In the fake `CLAUDE_HOME`, `readlink -f <fake>/skills/<each of 5>` resolves into this checkout.
  - The live L-1315 isolated probe is deferred to Sub-step 3.0 (standing rule); the Result Log says so.
- Result Log: Mode: AFK — auto-dispatched. Fake HOME (scratchpad), `scripts/install.sh` rc=0 from the M2 worktree: `readlink -f <fake>/.claude/skills/{logging-and-comments,python-quality-gates,llm-output-safety,secrets-management,bash-defensive-patterns}` → `<checkout>/claude-code/skills/<same>` (5/5); `hooks/lib/ruff-format.sh` → `<checkout>/claude-code/hooks/ruff-format.sh`. With the live settings.json re-rooted at the fake HOME (`sed s|$HOME/.claude|<fake>/.claude|`): ruff-format command count before=1, after=1; all 9 AA_MA_HOOKS "already registered". Caveat observed: copying settings.json un-rerooted gives count 2, because register_hook dedupes on the full `<CLAUDE_HOME>/hooks/lib/<hook>` path — on the real machine CLAUDE_HOME is the live one, so the live install keeps 1 (re-checked in 3.0). Also covered by `tests/hooks/install-migration.bats` (6/6). The live L-1315 isolated probe is deferred to Sub-step 3.0 (standing rule, D7: live symlinks must point at the main checkout after merge).

### Sub-step 2.7: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 2: Migrate 5 skills + ruff hook into the forge — hook-modification — <evidence>`, naming the bats/test names.
- Result Log: Mode: AFK — auto-dispatched. provenance.log `CRITICAL_PATH_REVIEW — Milestone 2: Migrate 5 skills + ruff hook into the forge — hook-modification — …` written, naming ruff-format.bats 4/4, install-migration.bats 6/6, fork-drift.bats 8/8, bats -r 352/352, pytest 2477/0. Re-checked `uninstall --restore` against a settings-only backup dir: settings.json skipped (exists), no clobber; registrations remain — pre-existing, logged out of scope.

---

## Milestone 3: Commands → skills (13), install hygiene
- Status: COMPLETE
- Dependencies: Milestone 2
- Complexity: 85% ⚠️ HIGH COMPLEXITY
- Effort: 2.5 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - `provenance.log` has a `PROTOTYPE — Milestone 3: Commands → skills (13), install hygiene — <verdict>` line with `verdict-changes-plan: YES|NO`; the `Skill(complexity-router)` verdict is in context-log.
  - `claude-code/commands/` is absent or empty; 11 commands moved to `claude-code/skills/<name>/SKILL.md`; `assess-codebase` and `understand-codebase` wrappers merged and deleted; `grill-me.md` deleted.
  - `tests/skills/test_no_command_skill_collision.py` and `tests/skills/test_model_invocation_list.py` pass (exactly {sole-dev-merge, aa-ma-share} carry `disable-model-invocation`). [Superseded by §6.8 (196461b, Ste): 4 skills — also execute-aa-ma-full, archive-aa-ma.]
  - `tests/hooks/install_dry_run.bats` passes with the stale-link and foreign-symlink cases.
  - `uv run pytest` count ≥ the baseline minus the deleted command-only tests (named in the Result Log); all bats green; `test_doc_counts` passes.
  - `docs/adr/NNNN-commands-become-skills.md` has `Status: Accepted` + INDEX row + context-log approval.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 3.
- Result Log: COMPLETE 2026-10-09, 7/7 criteria verified, HARD gate APPROVED by Ste (after double-check F1/F2 fixed). 13 commands are skills (11 git mv + 2 merged), /grill-me retired and declared external, claude-code/commands/ gone (ADR-0020 Accepted). Install hygiene: one sourced hook table (scripts/lib/aa-ma-install-lib.sh), stale command links swept, foreign symlinks recorded + restored, uninstall validates first and deregisters every row. D9 revised to 4 non-model-invocable skills. §6.6 0C/15W (all fixed), §6.8 PASS_WITH_WARNINGS 0C/7W (all fixed). pytest 2571 passed/0 failed (baseline 2482; 7 command-only tests deleted, named in 3.4/3.5), bats 378/378, shellcheck rc=0. Double-check Verified. Deferred to 4.0: live install from main + 13 probes, CLAUDE.md local edit, pre-compact hook home-path decision.

### Sub-step 3.0: Post-merge of M2
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M2 merged; `git pull` on main; live `scripts/install.sh` run from the MAIN checkout (Ste confirms).
  - `readlink -f ~/.claude/skills/<each of 5 migrated>` resolves into the main checkout; `~/.claude/settings.json` has exactly one ruff-format.sh entry (`jq '[..|.command?|select(.!=null and test("ruff-format"))]|length'` = 1).
  - L-1315 isolated probe lists each of the 5 skill names (deferred from 2.6).
  - Worktree for M3 cut from fresh main; `uv sync && uv run codemem build` exit 0 inside it.
- Result Log: Mode: HITL — Ste ran the live `scripts/install.sh` from the main checkout. M2 PR #19 rebase-merged as 686abac (CI run 37916630923, 7/7 green at f3ae3cf); main checkout ff to 686abac == origin/main; remote feature branch deleted (`git push origin --delete`, since `--delete-branch` can't delete a branch checked out in a worktree). Live: `readlink -f ~/.claude/skills/{logging-and-comments,python-quality-gates,llm-output-safety,secrets-management,bash-defensive-patterns}` → `<main>/claude-code/skills/<same>` (5/5); `~/.claude/hooks/lib/ruff-format.sh` → `<main>/claude-code/hooks/ruff-format.sh`; ruff-format command count in settings.json = 1; install backup `~/.claude/backups/aa-ma-forge-20261009-112048`. L-1315 isolated probe (`claude -p --setting-sources project --strict-mcp-config`, 5 skills copied into `<probe>/.claude/skills`): all 5 listed with their own descriptions. Control: a malformed `name: [x` value still loaded (lenient reader) → not discriminating; a line-1 HTML comment control is listed with the comment as its description → discriminating. Global L-1315 updated with this. Ste deleted the local `backup/cci-m2-pre-rewrite` (leak-bearing). Worktree `.worktrees/feat/cci-m3-commands-to-skills` cut from main @ 686abac; `uv sync` rc=0, `codemem build` rc=0.

### Sub-step 3.1: PROTOTYPE — command-to-skill install path
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 3.0
- Acceptance Criteria:
  - `Skill(complexity-router)` run first (85% milestone); its verdict logged in context-log.
  - On branch `prototype/cmd-to-skill`, `aa-ma-search` only is converted, then installed, uninstalled and reinstalled in a fake `CLAUDE_HOME` and in an L-1315 isolated probe: `/aa-ma-search` resolves; the stale command link is removed; a foreign symlink is recorded before replacement.
  - `provenance.log` has `[ts] PROTOTYPE — Milestone 3: Commands → skills (13), install hygiene — <verdict> — verdict-changes-plan: YES|NO`, plus a list of verdict deltas in the Result Log.
- Result Log: Mode: HITL — Ste: Proceed. complexity-router: weighted 61%, auto-triggers (50+ files; breaking path contract commands/→skills/) → 80% Critical → deep review = this prototype + HITL gates. Prototype `prototype/cmd-to-skill` @ ac5f814 (pushed; throwaway): `git mv commands/aa-ma-search.md → skills/aa-ma-search/SKILL.md` (already had `name:`); install.sh gains (a) a stale-command-link sweep — links in `~/.claude/commands/*.md` whose `readlink` is under `${REPO_ROOT}/claude-code/` and whose source is gone are removed; (b) `record_foreign_symlink` in `create_symlink` — a link whose destination is not under `${REPO_ROOT}/` is appended to `${BACKUP_DIR}/foreign-symlinks.tsv` (`<link>\t<dest>`) before `rm`. Fake HOME (pre-state: stale command link into the repo + foreign `skills/aa-ma-search` → `elsewhere/`): install rc=0 → stale link removed, foreign link recorded (1 row) then replaced by the repo link, 13 other command links created; `uninstall.sh --restore` rc=0 → skill link and all command links gone, **foreign link NOT restored**; reinstall rc=0 and again rc=0 → 0 new foreign rows, 0 stale removals (idempotent). L-1315 probe (`claude -p --setting-sources project --strict-mcp-config`): listing shows `aa-ma-search` with its own description; line-1-comment control shows the comment (discriminating); `/aa-ma-search zzqx-probe-term` ran the skill body (its report frame), 0 `Unknown skill/command` lines. Verdict deltas: Δ1 (changes plan) `uninstall.sh --restore` must replay `foreign-symlinks.tsv` → added to 3.2 AC; Δ2 a link into a *different* forge checkout (e.g. main while installing from a worktree) is recorded as foreign — by design, noted for the ADR; Δ3 the stale sweep is `REPO_ROOT`-scoped, so installing from a worktree leaves main's command links alone (D7 safe) and the live cleanup happens on install from main (4.0, already planned); Δ4 uninstall already removes dangling links into the repo by prefix — no change; Δ5 none of the 11 new skill names collide with anything in live `~/.claude/skills`; the only foreign live link is `skills/grill-me` → `~/.agents/skills/grill-me`, which no forge source targets.

### Sub-step 3.2: install/uninstall hygiene (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.1
- Acceptance Criteria:
  - bats written first: a stale `~/.claude/commands/<x>.md` link that resolves into this repo and whose source is gone is removed; a foreign symlink (`grill-me` shape) has its target recorded in the backup manifest and, with `--force`, is replaced only after it is recorded.
  - `uninstall.sh` derives its deregistration list from install's `AA_MA_HOOKS` (not a fixed count), including `security-static-check` and `plan-skip-warn`, also under `--restore`.
  - `install.sh` REQUIRED_DIRS (:80, `~/.claude/commands`) updated.
  - `tests/hooks/install_dry_run.bats` passes.
  - (3.1 Δ1) `uninstall.sh --restore` replays `foreign-symlinks.tsv`: a foreign link replaced by install points at its original destination again after `--restore`.
- Result Log: Mode: AFK — auto-dispatched. TDD: RED 692242e (7 bats) + RED 68acb63 (1 bats: a repo link whose source *directory* is gone — `readlink -f` fails there, so prototype Δ4 was wrong once `claude-code/commands/` is deleted) → GREEN 2f2de1a. install.sh: stale-command-link sweep (links under `${REPO_ROOT}/claude-code/` whose source is gone), `record_foreign_symlink` → `${BACKUP_DIR}/foreign-symlinks.tsv` before `rm` (dry-run announces, records nothing; `--force` still records), `~/.claude/commands` dropped from REQUIRED_DIRS. uninstall.sh [Superseded by §6.6 fix 41d8288: the table now lives in scripts/lib/aa-ma-install-lib.sh, sourced by both scripts and validated row-by-row before any change]: deregistration list parsed from install.sh's AA_MA_HOOKS with the `_HOOK_ROW` grammar (fails closed with an error if none read), moved out of the non-restore branch so it also runs under `--restore` (adds security-static-check, aa-ma-plan-skip-warn ×2 events); `--restore` replays each backup's manifest newest-first via the same RESTORED map; link scan falls back to raw `readlink` and matches `${REPO_ROOT}/` (was a bare prefix that also matched a sibling `aa-ma-forge-*` dir). New bats in tests/hooks/install_dry_run.bats: 'install removes a command link that dangles into this repo, and leaves a foreign dangling one', 'install records a foreign symlink's destination before replacing it', '--force still records a foreign symlink before replacing it', '--dry-run announces a foreign symlink and records nothing', 'uninstall --restore puts a recorded foreign symlink back', 'uninstall deregisters every hook install.sh registers (derived from AA_MA_HOOKS)', 'uninstall --restore also deregisters every AA_MA_HOOKS row', 'uninstall removes a link into this repo whose source directory is gone'. install_dry_run + install-migration 22/22; `bats -r tests` 366/366 rc=0; shellcheck rc=0. AA_MA_HOOKS row format unchanged → codemem `_HOOK_ROW` reader unaffected (L-041). Note for 3.5: install.sh's two `claude-code/commands/*.md` loops (backup collect, link) become dead once the dir is deleted — remove them there.

### Sub-step 3.3: Move 11 commands + fix paths
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.2
- Acceptance Criteria:
  - `git mv` of aa-ma-chart, aa-ma-plan, aa-ma-search, aa-ma-share, archive-aa-ma, execute-aa-ma-full, execute-aa-ma-milestone, execute-aa-ma-step, ops-mode, sole-dev-merge, verify-plan → `claude-code/skills/<name>/SKILL.md`; `name:` added to ops-mode and sole-dev-merge.
  - readlink fix (target and depth): `readlink -f ~/.claude/skills/<x>/SKILL.md` then `/../../..` in aa-ma-plan (was `aa-ma-plan.md:579`) and aa-ma-share (was `aa-ma-share.md:30`).
  - `disable-model-invocation: true` on sole-dev-merge and aa-ma-share only (D9 revised) [Superseded by §6.8 (196461b, Ste): 4 skills — also execute-aa-ma-full, archive-aa-ma.]; descriptions scoped to explicit requests; `test_model_invocation_list.py` passes.
  - The 31 test files referencing `commands/` paths updated; `plugin_surface.py` `_DIRS/_resolve` (`/x` → skills/x; `/x-*` globs over skills); `tests/fixtures/draw-node-ids.json` `command:*` → `skill:*`; `test_frontmatter_at_top.py::test_surfaces_are_not_empty` no longer requires `commands/`.
  - Also updated: `claude-code/rules/engineering-standards.md:66` (hook-modification scope drops `claude-code/commands/**`); docs/spec/aa-ma-specification.md:183, :911; foundations :34; `examples/**/aa-ma-team-guide-reference.md:69`; comments in `aa-ma-footer.sh:5` and `aa-ma-chart-guard.sh:18`.
  - `uv run pytest` count ≥ baseline minus the deleted command-only tests (listed by name in the Result Log); all bats green; `git grep -n 'commands/'` shows only history/docs (logged).
- Result Log: Mode: AFK — auto-dispatched. Baseline pytest 2482 passed / 7 skipped. Commits: dbb02d4 RED (`test_a_slash_glob_expands_over_skills_too`) → 256237f format-only (D8: 6 touched files + plugin_surface.py were not ruff-clean at HEAD; split out so the path edits review as 17 lines) [Correction (§6.8 tdd-sequence): 256237f also carries the 11 R100 renames, already staged when it was committed; 210ca3f then carries the content edits.] → d83f8ac GREEN (`_resolve`: `/x-*` expands over commands, then skills) → 210ca3f the move. `git mv` ×11 to `claude-code/skills/<name>/SKILL.md`; `name:` added to ops-mode, sole-dev-merge; `disable-model-invocation: true` on sole-dev-merge + aa-ma-share [Superseded by §6.8 (196461b, Ste): 4 skills — also execute-aa-ma-full, archive-aa-ma.]; each description gains its explicit-request clause; readlink in aa-ma-plan:579 / aa-ma-share:31 → `readlink -f ~/.claude/skills/<x>/SKILL.md` + `/../../..` (verified in a fake HOME: resolves to the checkout root). New `tests/skills/test_model_invocation_list.py` (2 tests). Paths updated in 25 test files by a literal rewrite + 3 path-joined forms by hand (`test_understand_codebase_xrefs.py`, `test_aa_ma_share_command.py` COMMAND_MD, `test_angle6_coverage.py` home fixture → dir symlinks as install makes them); the rewrite also hit one SYNTHETIC tmp-tree fixture in `test_bold_markdown_after_a_command_is_not_a_glob` — reverted, every other hit audited as a real repo path. `test_frontmatter_at_top.py`: commands/ dropped from SURFACES (moved files now meet the stricter skills `name`+`description` rule). Also: engineering-standards.md:66 scope, spec :183/:911, foundations :34, examples team-guide :69, aa-ma-footer.sh:5, aa-ma-chart-guard.sh:18, TODOS.md (3 open items), plan §13 EXM/SDM stale `(new)` dropped. `tests/fixtures/draw-node-ids.json` has no `command:*` ids (only `tests/commands/…` file paths) → no change; plan assumption was wrong. Regenerated golden + docs/architecture via `scripts/regen-generated.sh`. Test files referencing `commands/` (W2, 32 at 2ea2ed2): tests/codemem/test_plugin_surface.py, tests/assets/test_understand_codebase_xrefs.py, tests/commands/{test_aa_ma_share_command,test_planning_standard_count,test_understand_codebase_command}.py, tests/commands/sole-dev-merge/{fixtures/extract_stage.sh, test_smoke_e2e, test_stage_a_preflight, test_stage_b_scope, test_stage_c_dispatch, test_stage_d_triage, test_stage_e3_body, test_stage_e_remote, test_stage_f_idempotent, test_stage_g_merge, test_stage_g_poll}.bats, tests/hooks/{aa-ma-chart-guard, aa-ma-deps, aa-ma-gate-python, aa-ma-gate-scans, execute_aa_ma_milestone_phase_6_8, test_diagram_verified, install_dry_run}.bats, tests/skills/{test_angle6_coverage,test_understand_codebase_rewire}.py, tests/test_{active_plans_canonical,doc_counts,frontmatter_at_top}.py, plus fixture/golden JSON (draw-node-ids, onboarding schema/fixtures — unrelated `commands` keys). Results: pytest 2488 passed / 5 failed — all 5 are count sites deferred to 3.5 by plan (`test_command_count_sites_match_disk`, `test_security_md_asset_lists_match_disk`, `test_foundations_count_headings_match_disk`, `test_plugin_asset_counts_match_the_tree[commands]`, `[skills]`); 0 tests deleted. bats -r tests 366/366. Coverage audit: only `test_the_backticked_rule_loses_no_edge_the_any_occurrence_rule_found` (frozen pre-M6 command rule) goes vacuous once commands/ is empty — superseded by the skill-glob test; decide delete-or-keep in 3.5. `git grep 'commands/'` on live files: remaining hits are 3.5 (SECURITY.md:11,27; install.sh command loops :128,:308), the sweep itself, generic `.claude/commands` concepts (RULES-FILES.md:44, foundations :34, uninstall comment), sole-dev-merge's upgrade note, plugin_surface docstring; history (ADRs, research, CHANGELOG, docs/plans) untouched. Diagram lint: edges=25 checked=25 phantom=0 invalid=0.

### Sub-step 3.4: Merge the 2 collisions (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.3
- Acceptance Criteria:
  - `argument-hint` and routing text from `commands/{assess-codebase,understand-codebase}.md` moved into the SKILL.md bodies (not `references/`); `test_inventory_is_exactly_skill_md_and_two_references` passes.
  - assess-codebase SKILL.md ≤250 lines (`test_assess_codebase.py:73`); tests pinning wrapper text updated.
  - Both wrappers deleted; tests green.
- Result Log: Mode: AFK — auto-dispatched. TDD: a4c424f format-only (test_assess_codebase.py not ruff-clean at HEAD, D8) → RED 805ab0c (4 failing: assess/understand `test_skill_carries_the_command_surface`, `test_r7_deep_flag_no_longer_claims_unshipped_commands`, new `tests/skills/test_no_command_skill_collision.py::test_no_stem_is_both_a_command_and_a_skill`) → GREEN 9585130. Merged into SKILL.md bodies (not references/): both get `argument-hint: "[path] [--quick | --standard | --deep]"`; understand-codebase Tier selection gains the `Parse $ARGUMENTS` tier line (tier flags + Deep's `/assess-codebase` offer); assess-codebase "When not to use" → "When to use vs. not" with the wrapper's Use list. assess-codebase SKILL.md 224 lines (≤250); `test_inventory_is_exactly_skill_md_and_two_references` passes. Wrappers deleted. Tests retargeted from the wrapper to the skill: `test_r2_…` (now Step 0 section: codemem + /assess-codebase, no `/index`), `test_r7_…`, `test_r8_…`, ROUTES_TO_UNSHIPPED rows. Deleted command-only tests (5): tests/commands/test_understand_codebase_command.py::{test_command_file_exists, test_command_frontmatter, test_command_delegates_to_skill, test_command_documents_tier_flags}, tests/skills/test_assess_codebase.py::test_command_is_a_thin_wrapper — their surviving assertions moved onto the skills (+2 new surface tests, +1 collision test). No other live file links the wrappers (git grep outside history). Regenerated golden; plugin_surface 31/31. tests/skills+commands+assets: 297 passed, 3 failed = the 3.5 count sites only.

### Sub-step 3.5: Retire grill-me, counts, regen, ADR
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.4
- Acceptance Criteria:
  - `claude-code/commands/grill-me.md` deleted (D4); `claude-code/commands/` removed.
  - `test_doc_counts` passes with the new counts (commands-count line removed from `tests/test_doc_counts.py`); `test_only_the_fork_route_command_dangles` passes; golden regenerated via `scripts/regen-generated.sh`.
  - README `### All commands` table → `/name` list; SECURITY.md:11-12; foundations :73, :92 updated. CLAUDE.md:51-52 is a local edit (gitignored).
  - CHANGELOG/ADR carry the upgrade note: existing installs must re-run `scripts/install.sh` (CEO F16).
  - `docs/adr/NNNN-commands-become-skills.md` has `Status: Accepted` + INDEX row + context-log approval.
- Result Log: Mode: AFK — auto-dispatched (ADR acceptance asked: Ste → Accept). TDD: 8c89db7 format-only (test_doc_counts.py, D8) → RED 8d4eda9 (`test_the_forge_ships_no_commands`, `test_readme_slash_names_are_shipped_skills`, SECURITY/foundations/doc-count skills=38) → GREEN 24c3676. `claude-code/commands/grill-me.md` deleted (D4) and `claude-code/commands/` gone; `grill-me` added to `surface_allowlist.EXTERNAL["command"]` (aa-ma-plan's `simple` grill mode → user-level mattpocock skill) so `test_only_the_fork_route_command_dangles` passes. install.sh: command backup + link loops removed (stale-link sweep kept; header comments updated). README `### All commands` table → `### All slash commands` list of 13 `/names` (+ invocation note); README:40 tree line; SECURITY.md command-files line removed, skills line 38 with the full list (generated from disk), :27/:89 wording; foundations `### Commands (14)` → `### Slash commands` (no /grill-me row), `### Skills (38)`; quick-reference marks /grill-me as user-level. `tests/test_doc_counts.py` commands rows removed. CHANGELOG Unreleased: Changed (commands→skills, **upgrade note: re-run scripts/install.sh** — CEO F16; install/uninstall hygiene; plugin_surface glob), Removed (/grill-me). ADR-0020 `docs/adr/0020-commands-become-skills.md` Accepted + INDEX row + context-log approval. Deleted command-only tests (2): `tests/commands/test_aa_ma_share_command.py::test_command_count_sites_match_disk` (→ `test_readme_slash_names_are_shipped_skills`), `tests/codemem/test_plugin_surface.py::test_the_backticked_rule_loses_no_edge_the_any_occurrence_rule_found` (frozen pre-M6 command rule, vacuous with no commands; covered by `test_a_slash_glob_expands_over_skills_too`). Regenerated golden + docs/architecture; codemem rebuilt; §13 lint edges=25 checked=25 phantom=0 invalid=0 rc=0. Full: pytest 2490 passed / 0 failed (baseline 2482; M3 deleted 7 command-only tests in total, named in 3.4/3.5), bats -r tests 366/366. CLAUDE.md:51-52 (gitignored) deferred to 4.0 (context-log).

### Sub-step 3.6: Install proof (fake CLAUDE_HOME)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.5
- Acceptance Criteria:
  - `install.sh` into a fake `CLAUDE_HOME`: 13 skill links present, 14 command links absent, foreign `grill-me` link recorded in the manifest.
  - Live install and the 13 probes are deferred to Sub-step 4.0.
- Result Log: Mode: AFK — auto-dispatched. Fake HOME seeded like the live machine: the 14 old `~/.claude/commands/<x>.md` links into `<repo>/claude-code/commands/` (now dangling), one real user command file (`commit-local.md`), `skills/grill-me` → `../../.agents/skills/grill-me` (relative, as live), plus a deliberately colliding foreign `skills/ops-mode` → `elsewhere/`. `install.sh` rc=0: 13/13 skill links resolve into the repo with a SKILL.md; 0/14 old command links left (14 "Removed stale command link"); real `commit-local.md` untouched; `skills/grill-me` untouched; manifest has exactly 1 row (`skills/ops-mode` → `elsewhere/ops-mode`). `uninstall.sh --restore` rc=0: 0 repo links left, 0 hook commands left in settings.json, `skills/ops-mode` → `elsewhere/ops-mode` again, grill-me and commit-local.md untouched. AC deviation (logged): the tasks AC said the foreign grill-me link is "recorded in the manifest" — install records only links it replaces, and no forge source targets `skills/grill-me`, so the correct and observed result is *untouched, not recorded* (matches the plan's own 4.0 AC "still points to ~/.agents/…"); recording is proven on the colliding `ops-mode` link instead. Live install + 13 probes deferred to Sub-step 4.0 as planned.

### Sub-step 3.7: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 3: Commands → skills (13), install hygiene — hook-modification — <evidence>`, naming bats/test names.
- Result Log: Mode: AFK — auto-dispatched. `CRITICAL_PATH_REVIEW — Milestone 3: Commands → skills (13), install hygiene — hook-modification — …` appended to provenance.log, naming the 6 gate/fence bats files, the sole-dev-merge stage bats, the 8 new install_dry_run.bats test names, install-migration.bats, and the suite totals (bats 366/366, pytest 2490/0 failed, shellcheck rc=0).

---

## Milestone 4: Prompt-as-code checks + writing-for-agents fork
- Status: COMPLETE
- Dependencies: Milestone 3
- Complexity: 60%
- Effort: 2 days
- Gate: SOFT
- Audit-Profile: full
- Critical-Path: version-pipeline
- Mode: HITL
- Acceptance Criteria:
  - `tests/test_frontmatter_at_top.py` schema passes; a negative-control fixture with an unknown key fails.
  - `tests/test_prompt_size.py` passes at current sizes; a fixture adding 1 line to an allowlisted file fails.
  - The eval mechanism (`claude plugin eval --no-publish` or `claude -p` fallback) is recorded in the ADR/context-log, with one JSONL result line holding `rc` and `verdict`.
  - `claude-code/skills/writing-for-agents/` exists as a pinned fork; `claude-code/skills/write-a-skill/` is deleted; `test_fork_manifest` passes; `git grep write-a-skill` hits only ADRs/history.
  - `scripts/run-evals.sh` runs all 24 cases and reports pass/fail; `tests/scripts/test_run_evals_sandbox.bats` passes.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 4 (version-pipeline).
- Result Log: 6/6 criteria verified (double-check 2026-10-09T190311Z Partially verified → its 2 record gaps corrected in a9a638f; fresh baseline run done). Skill frontmatter schema test (documented keys + metadata, limits, third person, `context: fork`, scoped allowed-tools, no dynamic exec in forks; 5 skills fixed) and a 500-line size ratchet with a touched-only TOC rule; `claude plugin eval` proven (no plugin.json; Skill grader mandatory after a judge-only false pass); writing-for-agents forked @ c55ee46 with an `## In this repo` block, write-a-skill retired (ADR-0021 Accepted, ADR-0004 superseded), install.sh sweeps retired skill/agent links; 24 advisory eval cases + sandboxed `scripts/run-evals.sh` (env -i, API key dropped unless allowed, never publishes, JSONL + exit 0) + release.sh advisory hook; added 4.7 (Ste): skill triggering fixed by description routing — eval baseline 14/24 → 22/24, skill-fired 24/24. §6.6 0C/9W (fixed), §6.8 PASS_WITH_WARNINGS 0C/8W (fixed; C1 kept by decision). pytest 2728 passed / 0 failed, bats 398/398, shellcheck rc=0, LIVE sandbox 3 hostile cases pass.

### Sub-step 4.0: Post-merge of M3
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M3 merged; `git pull` on main; live `scripts/install.sh` from main (Ste confirms).
  - For each of the 13 `/names`, an isolated `claude -p "/<name> --help-like no-op" </dev/null` probe (L-1322 prompt-first): 13/13 resolve; no stdout contains `Unknown skill` or `Unknown command`.
  - `ls ~/.claude/commands/ | wc -l` drops by 14 (13 moved + grill-me); provenance logs `COMMANDS pre=N post=N-14`; `~/.claude/skills/grill-me` still points to `~/.agents/…`.
  - Worktree for M4 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log: Mode: HITL — Ste ran the live `scripts/install.sh` from the main checkout (14:18 and 14:25; backups `~/.claude/backups/aa-ma-forge-20261009-141822`, `-142526`) after M3 PR #20 merged (main 13de435 == origin/main). 13 isolated probes (Ste chose "Sandboxed"): each `/name` run in its own `mktemp -d` + `git init` (no remote) with `claude -p "/<name> zzqx-probe-noop …" --model haiku --max-turns 1 --strict-mcp-config --disallowedTools Bash Write Edit NotebookEdit WebFetch WebSearch Agent </dev/null` → 13/13 rc=0, each reply names the loaded skill, 0 `Unknown skill`/`Unknown command` lines across stdout+stderr. `~/.claude/commands/`: post=15, all regular user files, 0 symlinks; pre=29 is derived (15 user files with mtimes before today + the 14 forge links installed from main by M2's 3.0 install), because the 14:18 install that swept them ran before this session and its output was not kept → COMMANDS line logged with that caveat. `readlink ~/.claude/skills/grill-me` = `../../.agents/skills/grill-me` (untouched). Worktree `.worktrees/feat/cci-m4-prompt-as-code` cut from main @ 13de435; `uv sync` rc=0; `uv run codemem build` rc=0 (248 files). Deferred from M3: local gitignored CLAUDE.md updated (commands/ line removed, skills 38, hooks 9 + ruff-format; Flow line); pre-compact home-path fix already landed in M3 (ba60dc1). Uncommitted L-044 moved into this branch (2e21eaf). Noted, not fixed here: `src/aa_ma/grammar.py:263` SyntaxWarning (`\S` in a non-raw docstring).

### Sub-step 4.1: Frontmatter schema (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 4.0
- Acceptance Criteria:
  - Failing tests written first; they fail on the current `triggers`/`version`/`context:` sites.
  - Allowed keys = documented skill keys (from the code.claude.com skills docs, fetched in this step and cited in the test docstring) + `metadata`; unknown key fails; name ≤64 chars `[a-z0-9-]`; description ≤1024 with no `<`; description + `when_to_use` ≤1536.
  - Pronoun rule (v3): no second-person `\b(you|your)\b` in descriptions, outside quoted trigger phrases ("Use when…" and quoted user phrases allowed).
  - §0 v2: unscoped `Bash`, `Write` or `Edit` in `allowed-tools` rejected unless an allowlist entry gives a why (`assess-codebase:13` allowlisted or narrowed); `` !` `` dynamic-exec lines rejected in forked bodies.
  - Fixes: `triggers` → `when_to_use` (operational-constraints, system-mapping); `version` → `metadata.version`; `dispatching-parallel-agents:6` `languages:` → metadata; `:7` `context:` dropped; the imperative description from T2 rewritten; grill-with-docs "your plan" fixed with its FORKS.json md5 updated.
  - L-1314: every field made live is reviewed (listed in the Result Log).
  - The schema test passes; the negative-control fixture with an unknown key fails.
- Result Log: Mode: AFK — auto-dispatched. Sources fetched 2026-10-09 and cited in the test block: code.claude.com/docs/en/skills#frontmatter-reference (20 keys; "ignores a field it doesn't recognize without reporting an error"; 1,536-char listing cap) + agentskills.io/specification (name 1-64 [a-z0-9-], description 1-1024). TDD: RED 807788e (5 failing: dispatching-parallel-agents, grill-with-docs, operational-constraints, retro, system-mapping) → GREEN a406dc3. Schema in tests/test_frontmatter_at_top.py: `skill_schema_errors()` + `SKILL_KEYS` (documented keys incl. `metadata`), name/description/listing limits, no `<`, third-person rule (quoted phrases stripped first), `context` must be `fork`, `metadata` must be a map, unscoped Bash/Write/Edit in allowed-tools needs a `UNSCOPED_TOOLS_ALLOWLIST` why (assess-codebase, retro — whys checked against the bodies; stale-entry guard test), `!`…`` dynamic exec refused in FORKS.json bodies. Negative controls: 12 parametrised cases incl. unknown key `triggers`/`version` → fail; positive control passes. Fixes: operational-constraints + system-mapping `triggers` → `when_to_use`; dispatching-parallel-agents imperative description (T2) → "Dispatches …", `when_to_use` gains "Use when", `version`/`languages` → `metadata`, `context:` dropped; retro `version` → `metadata.version` (doc-drift-ignore comment kept); grill-with-docs "your plan" → "a plan", FORKS.json md5 e552cb8a → 0607197f (manifest recipe = file minus line 2; recipe re-verified on HEAD). L-1314 fields made live, reviewed: `when_to_use` on operational-constraints and system-mapping (now in the skill listing; text reviewed, 140/127 chars); dispatching-parallel-agents description + when_to_use (reworded only); `context` removed (was a live field with a non-fork value). `metadata.*` is not acted on by Claude Code. No reader of `triggers` exists (repo git grep + ~/.claude/hooks grep). Tests: frontmatter+fork 204 passed; full pytest 2625 passed / 7 skipped / 0 failed.

### Sub-step 4.2: Size ratchet (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 4.1
- Acceptance Criteria:
  - `tests/test_prompt_size.py`: body ≤500 lines; ALLOWLIST holds ceilings at current size for the 6 oversized files (may only fall).
  - TOC rule touched-only: a `references/*.md` >100 lines that is new or modified vs merge-base needs a TOC; the 23 existing >100-line references without one are in `TOC_ALLOWLIST`.
  - The test passes at current sizes; a fixture adding 1 line to an allowlisted file fails.
- Result Log: Mode: AFK — auto-dispatched. cda0c30 adds tests/test_prompt_size.py (66 tests, all pass at current sizes). Cap MAX_LINES=500 over skills/*/SKILL.md + agents/*.md, counted for the whole file incl. frontmatter (= the plan's measured figures); ALLOWLIST ceilings at today's size: aa-ma-execution 1295, execute-aa-ma-milestone 1244, aa-ma-plan 1154, sole-dev-merge 1057 (plan said 1054; M3 added 3), execute-aa-ma-full 758 (plan 757), plan-verification 608; stale-entry guard (an entry under the cap fails). TOC rule: skills/*/references/*.md >100 lines needs a TOC (a Contents heading or 3+ in-file anchor links) when not in TOC_ALLOWLIST or touched vs `git merge-base origin/main HEAD` (diff + untracked); merge-base unavailable → warning, allowlist part still runs. TOC_ALLOWLIST = the 24 existing references (23 at plan time + logging-and-comments/references/python.md from M2), with a guard that each still needs it. Negative controls: `test_one_added_line_breaks_an_allowlisted_ceiling` (ceiling+1 fails, current passes); `test_cap_applies_to_a_file_not_on_the_allowlist` (501 fails, 500 passes); touched rule verified by hand — appending one line to retro/references/output-format.md failed `test_references_over_threshold_have_a_toc`, reverted. Not TDD-RED: a guard over existing code passes on first run by design; the negative controls are its failing case. Note for 4.4: a verbatim fork's reference >100 lines cannot gain a TOC without breaking the fork — handle there.

### Sub-step 4.3: Eval harness proof
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 4.2
- Acceptance Criteria:
  - Proven (or disproven) that `claude plugin eval` targets `claude-code/skills/<x>` with no `plugin.json` (A2); always run with `--no-publish`, `--runs 1`, no ablation arm; eval-dir placement settled; cost of one case logged.
  - Fallback if it fails: `claude -p "<prompt>" … </dev/null` (L-1322).
  - One case runs end to end, producing one JSONL result line with `rc` and `verdict` fields; the chosen mechanism is recorded in the ADR/context-log.
- Result Log: Mode: HITL — Ste approved the paid proof (cap $0.50). Proven: `claude plugin eval` (2.1.295) targets a skills-dir with no plugin.json (plugin name = dir name, skills namespaced `<plugin>:<skill>`). Run 1 (scratch copy of aa-ma-search, prompt `/aa-ma-search …`, llm grader only) was a FALSE PASS — the skill did not load ("isn't installed in this session") but the judge scored 1.0 (PASS FAIL PASS); cause: namespacing. Run 2, repo-shaped scratch (`claude-code/skills/aa-ma-search` + `evals/aa-ma-search/no-match/case.yaml` with `plugins: ["../../../claude-code"]`, target = root, `--no-publish --runs 1 --ablation none --trust-plugin --max-cost-usd 0.50 --json`, model haiku): rc=0, `skill-fired` (tool_used Skill) PASS, `no-invented-results` (llm) PASS, score 1, cost $0.0034, 12 s. Case-file target rejects the `plugins` entry (containment); root target accepts it. JSONL line `{"case":"aa-ma-search/no-match","rc":0,"verdict":"pass",…}` in provenance (EVAL_PROOF). Mechanism, placement, flags, cost and the every-case-needs-a-Skill-grader rule recorded in context-log ("M4.3 Eval mechanism"); the ADR in 4.4 cites it. Fallback `claude -p` not needed.

### Sub-step 4.4: writing-for-agents fork
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 4.3
- Acceptance Criteria:
  - `claude-code/skills/writing-for-agents/` is a verbatim fork of mattpocock/skills @ c55ee46, fetched with `gh api repos/mattpocock/skills/contents/…?ref=<40-hex of c55ee46>` with sha256 recorded, never from the plugin cache; upstream MIT `LICENSE` in the fork dir; `## In this repo` block added (T15 conventions + surviving write-a-skill sections).
  - `claude-code/skills/write-a-skill/` deleted; FORKS.json + writing-for-agents − write-a-skill; not invoked by AA-MA Phase 5 writers (writing-for-agents-eval T4).
  - `docs/adr/NNNN-writing-for-agents-fork.md` `Status: Accepted` (supersedes ADR-0004) + INDEX row + context-log approval; `docs/adr/0004-write-a-skill-adoption.md` marked `Superseded by NNNN`.
  - README:255, SECURITY.md:12, foundations:113, the orphan set in `test_plugin_surface.py:113-119` updated; golden regenerated.
  - `test_fork_manifest` passes; `git grep write-a-skill` hits only ADRs/history. The L-1315 probe listing `writing-for-agents` is deferred to Sub-step 5.0 (standing rule: live probes run post-merge).
- Result Log: Mode: AFK — auto-dispatched (ADR acceptance asked: Ste → Accept). Fetched via `gh api repos/mattpocock/skills/contents/skills/productivity/writing-for-agents/<f>?ref=c55ee46073ed923f86ce59a5eb3b6d895095d1b7` (not the plugin cache): SKILL.md sha256 551adca9…a896a74a (md5 9663b04e), SKILL-MECHANICS.md sha256 c768e630…0a0059 (md5 f3648a8f), LICENSE sha256 0e7ac423…07dbb5 (md5 a1d7928c = the existing mattpocock MIT); `agents/openai.yaml` not taken (Codex-only). TDD: RED 79c82bf (`tests/skills/test_writing_for_agents_fork.py`, 4 failing: frontmatter/provenance, file set, upstream text unedited above the block (md5 of SKILL.md minus line 2 up to `## In this repo` = 9663b04e), write-a-skill retired; `test_aa_ma_writers_do_not_invoke_it` passes; `test_write_a_skill_frontmatter.py` deleted) → GREEN 6960571. Fork: line-2 YAML provenance in SKILL.md, line-1 HTML provenance in SKILL-MECHANICS.md, `## In this repo` block (frontmatter schema, size cap + TOC, descriptions — upstream wins on trigger branches and user-invoked summaries, layout carried over from write-a-skill, slash entry points as skills, MUST rules carry a why, evals with a mandatory Skill grader, not for AA-MA artefacts). FORKS.json: + writing-for-agents (state derived, upstream_md5 recorded, source gh-api@c55ee46), − write-a-skill. ADR-0021 Accepted + INDEX row + context-log approval; ADR-0004 Superseded by 0021 (+ INDEX). README skills row, SECURITY.md:11 list, foundations row; orphan set write-a-skill → writing-for-agents (new edge writing-for-agents → aa-ma-plan from the block's Phase 5 line); `test_fork_manifest` fixture uses aa-ma-research for the null-upstream ORPHAN case; golden + docs/architecture regenerated; CHANGELOG Unreleased. Scope added: install.sh stale sweep extended to skills/agents links (RED d3830a8 → GREEN 4ae7c7c; bats 'install removes retired skill and agent links that dangle into this repo, and leaves foreign ones'). Tests: pytest 2696 passed / 6 skipped / 0 failed; `bats -r tests` 384/384; shellcheck rc=0. `git grep write-a-skill` outside ADRs/history (docs/adr, docs/plans, docs/research, docs/superpowers, .claude/dev, CHANGELOG) = only tests/skills/test_writing_for_agents_fork.py (the retirement assertion). L-1315 probe deferred to 5.0 per plan.

### Sub-step 4.5: Eval cases + sandboxed runner
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 4.4
- Acceptance Criteria:
  - 24 cases `evals/<skill>/<case>/case.yaml`, 3 each for execute-aa-ma-milestone, execute-aa-ma-step, execute-aa-ma-full, aa-ma-plan, plan-verification, impact-analysis, logging-and-comments, writing-for-agents.
  - `scripts/run-evals.sh`: each case in a throwaway fixture repo (`mktemp -d`, `git init`, no remote); `git push`, `gh` and network tools denied via `--disallowedTools`; `--allowedTools` allowlist; `env -i` with PATH + Claude auth only (SSH_AUTH_SOCK, GH_TOKEN, GITHUB_TOKEN unset); HOME-scoped writes refused; results → `.claude/evals/<YYYY-MM-DD>.jsonl` (gitignored) + one summary line; exit 0 always with rc in the last line.
  - `tests/scripts/test_run_evals_sandbox.bats` passes: a case trying `git push` fails; the fixture repo has no remote; a case writing `$HOME/.probe` leaves it absent; a test asserts run-evals.sh never uses `bypassPermissions` or `--dangerously-skip-permissions`.
  - `scripts/release.sh` runs `run-evals.sh` advisorily and prints the summary.
  - `scripts/run-evals.sh` runs all 24 and reports pass/fail; results logged, not gated.
- Result Log: Mode: AFK — auto-dispatched (HITL asks: Ste chose "Add guard, run sonnet" after the billing question). TDD: RED 313dc42 (sandbox bats 7, release bats 3, tests/test_eval_cases.py) → GREEN ed90742 (runner, 24 cases, fixtures, release hook) + e841392 (fixture CLAUDE.md was gitignored → `!evals/_fixtures/**/CLAUDE.md`) + RED 1737de8 → GREEN 08e6648 (API-key guard) + 9b1fe80 (sandbox graders) + 09269ae (CHANGELOG, runbook) + RED 68438ca → GREEN 9c4c62a (JSONL `failed` grader names). 24 cases = 3 × {execute-aa-ma-milestone, execute-aa-ma-step, execute-aa-ma-full, aa-ma-plan, plan-verification, impact-analysis, logging-and-comments, writing-for-agents} under `evals/<skill>/<case>/case.yaml`; 8 fixtures in `evals/_fixtures/`, scaffolds `evals/_lib/<fixture>.sh` → `scaffold.bash` (copy + `git init`, no remote); every case read-only tools (Read/Glob/Grep/Skill); model-invoked cases carry `tool_used: Skill` + result grader, the user-invoked execute-aa-ma-full cases use `/claude-code:execute-aa-ma-full` + result + regex graders (the expanded slash prompt is not in the trace — probe 2026-10-09). `scripts/run-evals.sh`: `claude plugin eval .` from the repo root under `env -i` (PATH, HOME, LANG, CLAUDE_CODE_OAUTH_TOKEN/CLAUDE_CONFIG_DIR if set; ANTHROPIC_API_KEY only with RUN_EVALS_ALLOW_API_KEY=1), `--no-publish --runs 1 --ablation none --scaffold --trust-plugin --model sonnet --max-cost-usd 5`, temp output dir, JSONL per case to `.claude/evals/<date>.jsonl` (gitignored via `.claude/*`), summary line, last line `run-evals: rc=N`, exit 0 always. AC mapping (deviation, recorded in context-log M4.3/M4.5): `claude plugin eval` has no `--disallowedTools`; tools not granted are absent from the session, so git push/gh/network cannot run; each run has a temp HOME + empty workspace. Sandbox bats `tests/scripts/test_run_evals_sandbox.bats` 9/9 (8 stubbed + LIVE with AA_MA_EVAL_LIVE=1): never bypassPermissions/dangerously-skip; flags; no tool grants; scrubbed env (GH_TOKEN/GITHUB_TOKEN/SSH_AUTH_SOCK/AWS absent); API key dropped; JSONL+summary+rc; no-result path; every scaffold = git repo with no remote; LIVE hostile cases `git-push` + `home-write` pass (session tool list has no Bash/Write — the first grader version counted refused calls: trace showed "No such tool available: Bash … in subagents as well"), real `~/.probe` absent before and after. `scripts/release.sh` runs run-evals advisorily before editing (not under --dry-run/--skip-evals; missing script reported) — release bats 18/18. Excluded `evals/_fixtures` from pytest (`--ignore=evals`), ruff (`extend-exclude`) and pre-commit (`exclude:`). All 24 run: run 1 13 pass/11 fail $2.36 est; run 2 (with `failed` names) 14 pass/10 fail $2.58 est, 1m35s, `-j 4`, plan usage (claude.ai login, no API key) — 9 fails are `skill-fired` only (answer right, skill not triggered: aa-ma-plan/planning-standard, execute-aa-ma-milestone/not-complete, execute-aa-ma-step/next-step + sync-after-step, plan-verification ×3, writing-for-agents/review-draft-skill + write-description), 1 is `result` (execute-aa-ma-full/execution-order). Advisory — logged, not gated. Tests: pytest 2721 passed / 6 skipped / 0 failed; `bats -r tests` 397/397. [Superseded by e9dfcbb: fixtures live in `tests/fixtures/evals/` and the .gitignore negation is `!tests/fixtures/evals/**/CLAUDE.md`. Superseded by 1a912bf/1157273: sandbox bats is 10 tests (9 default + 1 LIVE with 3 hostile cases: git-push, home-write, skill-escape).]

### Sub-step 4.6: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 4.5
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 4: Prompt-as-code checks + writing-for-agents fork — version-pipeline — <evidence>`, naming the `scripts/release.sh` change, the sandbox bats name and the eval summary line.
- Result Log: Mode: AFK — auto-dispatched. `CRITICAL_PATH_REVIEW — Milestone 4: Prompt-as-code checks + writing-for-agents fork — version-pipeline — …` appended to provenance.log, naming the scripts/release.sh change (--skip-evals, EVALS seam, advisory block before edits; version/tag/push path unchanged), the 4 new release.bats cases (18/18), the sandbox bats file and its LIVE case (9/9), and the eval summary line (24 cases, 14 pass, 10 fail; rc=1, advisory). [Superseded by 1a912bf/1157273: the sandbox bats is 10 tests (9 default + 1 LIVE covering 3 hostile cases: git-push, home-write, skill-escape); CRITICAL_PATH_REVIEW addenda record both.]

### Sub-step 4.7: Skill triggering fix (added 2026-10-09, Ste)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 4.6
- Acceptance Criteria:
  - Diagnosis recorded (context-log): kept traces of 4 failing cases show sibling collision (aa-ma-plan-workflow fired for an aa-ma-plan request), no-skill answers from files (execute-aa-ma-step, plan-verification), and a weak pointer (writing-for-agents).
  - Descriptions rewritten per writing-for-agents (leading word first, one trigger per branch, routing to the sibling) for execute-aa-ma-step, execute-aa-ma-milestone, aa-ma-execution, aa-ma-plan, aa-ma-plan-workflow, plan-verification, verify-plan; writing-for-agents gains a local `when_to_use` (fork test: upstream text unedited apart from that one frontmatter line); no `disable-model-invocation` change (callers: system-mapping → aa-ma-plan-workflow, verify-plan → plan-verification).
  - Eval prompts phrased as real requests (no "report … then stop" hints); `tests/test_frontmatter_at_top.py`, `tests/test_eval_cases.py`, fork tests pass.
  - `scripts/run-evals.sh` re-run: pass count and `skill-fired` failures compared with the 14/24 baseline, recorded in provenance (advisory, not gated).
- Result Log: Mode: AFK — added mid-milestone at Ste's request. Diagnosis (context-log 2026-10-09 "Skill-triggering diagnosis"): kept traces of 4 failing cases — sibling collision (aa-ma-plan-workflow fired for an aa-ma-plan request), no-skill answers from files (execute-aa-ma-step, plan-verification), weak pointer (writing-for-agents). TDD: RED 40997e9 (fork test: writing-for-agents carries one local `when_to_use`, upstream text otherwise unedited) → GREEN 8af9099: descriptions rewritten and quoted (YAML `: `) for execute-aa-ma-step, execute-aa-ma-milestone, aa-ma-execution (no longer "proactively use when detecting .claude/dev/active"; routes step/milestone requests to their skills), aa-ma-plan, aa-ma-plan-workflow (phase reference; start-a-plan goes to aa-ma-plan), plan-verification (gains "Use when"), verify-plan (slash entry + saved report); writing-for-agents `when_to_use` + FORKS.json md5 fe932c8d → 0f9f7e86; no `disable-model-invocation` change (system-mapping → Skill(aa-ma-plan-workflow); verify-plan → Skill: plan-verification). Eval prompts rephrased as requests (no "report … then stop"); plan-verification Skill grader accepts verify-plan (its wrapper); sync-after-step rubric adapted. Re-run (sonnet, `-j 4`, plan usage, $3.00 est): **22/24 pass** (baseline 14/24); `skill-fired` misses 9 → 1. Remaining: aa-ma-plan/first-phase `skill-fired`, execute-aa-ma-step/sync-after-step `result` (traces not kept; n=1 per case; causes unverified). Confound: descriptions and prompts changed in the same run. Also: eval fixtures moved to `tests/fixtures/evals/` (e9dfcbb) — under `evals/_fixtures` codemem's component view drew them as repo architecture; `tests/` paths are excluded by `is_test_path`; `codemem draw --check` OK; pytest/ruff/pre-commit/.gitignore exclusions repointed; one-case live check after the move: 1/1 pass (haiku). Tests: pytest 2721 passed / 6 skipped / 0 failed; `bats -r tests` 397/397. Follow-up (Ste: "what were the 2 fails?" → dig first): kept traces — first-phase: no Skill call, the model planned a 3-line feature inline (prompt never said AA-MA; Ste: aa-ma-plan fires only when AA-MA is named → prompt now 'Plan this as an AA-MA plan: …'); sync-after-step: skill fired and correctly refused to mark 1.2 COMPLETE because `python greet.py Ada` was never run (Bash/Edit absent) — rubric defect, now passes a step left PENDING for want of evidence. 3eab5e4; both re-run: 2/2 pass ($0.37 est). [Correction (double-check 2026-10-09T190311Z): no single run was 24/24 — that sentence joined a 22/24 full run with a 2/2 targeted re-run after a prompt decision and a rubric fix.] Baseline of record (Ste: fresh single run, 2026-10-09 20:2x, sonnet, `-j 4`, $2.97 est): **22/24 pass; skill-fired 24/24**; fails aa-ma-plan/artifact-names [names-tasks-file, result] and plan-verification/missing-criteria [result] — a different pair from the earlier run, so with `--runs 1` the failing set varies run to run (result graders, not triggering). JSONL `.claude/evals/2026-10-09.jsonl` holds exactly this run.

---

## Milestone 5: Split the six oversized prompt files (behaviour-preserving)
- Status: COMPLETE
- Dependencies: Milestone 4
- Complexity: 70%
- Effort: 1.5 days
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- TDD-Waiver: refactor
- Mode: HITL
- Acceptance Criteria:
  - Each of the 6 files has SKILL.md ≤500 lines + `references/*.md` one level deep, with a TOC on every reference >100 lines.
  - `tests/test_split_preserves_content.py` passes for all 6 files.
  - `tests/test_prompt_size.py` passes with an empty ALLOWLIST.
  - Full `uv run pytest` and all bats pass, with test-pinned text either still in SKILL.md or the test moved in the same commit.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 5.
- Result Log: 5/5 criteria verified; Gate HARD approved by Ste 2026-10-11. Six SKILL.md split into SKILL.md + 28 references (487/498/427/317/432/416 lines), each split one `refactor(skills): split <skill> ` commit checked against its parent by tests/test_split_preserves_content.py (no line lost or reordered; only stub headings, titles, `## Contents`, bare links and `See [..](references/..#anchor) — purpose` pointers added); executed fences (§5, §6.7, §7.1) and 15 sole-dev-merge stage bodies byte-identical to bc177e5; ALLOWLIST empty and asserted. Every test that read moved text moved or widened (shared tests/skills/_helpers.py skill_files/skill_text + tests/lib/skill_files.bash), each widened negative proven by a planted line; L-047 written and tightened after a recurrence. §6.6 0C (fixed), §6.8 PASS_WITH_WARNINGS 0C/4W/12I (fixed; duplicate pre-execution-validation reference deferred), double-check Partially verified → F1–F4 fixed (9c03f05, df9142c). Evals 11/12 ×2 (advisory; no split effect). pytest 2774 passed / 6 skipped / 0 failed; bats 403/403; shellcheck rc=0.

### Sub-step 5.0: Post-merge of M4
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M4 merged; `git pull` on main; live `scripts/install.sh` from main (M4 changed the skill set: + writing-for-agents, − write-a-skill).
  - L-1315 isolated probe lists `writing-for-agents` (deferred from 4.4).
  - Worktree for M5 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log: Mode: HITL (Ste: "merge to main, then cut the M5 worktree … finish Sub-step 5.0"). M4 PR #21 merged; follow-ups PR #22 (L-045 bare-negation sweep) and PR #23 (install.sh stale count) rebase-merged → main bc177e5 == origin/main. Live `scripts/install.sh` from the main checkout @ bc177e5: rc=0, symlinks 65, copied 5, backed up 5, stale removed 0 (the pre-#23 run reported 65 — the miscount #23 fixed); `~/.claude/skills/writing-for-agents` → main checkout, `write-a-skill` absent, 0 dangling links under skills/agents/rules/hooks. Worktree `.worktrees/feat/cci-m5-split-prompts` cut from main @ bc177e5; `uv sync` rc=0; `uv run codemem build` rc=0 (303 files, 2956 symbols). Compaction checkpoint lines carried over from the main checkout via stash. L-1315 isolated probe (run by Ste — the nested `claude -p` was refused by the permission layer in-session): `mktemp -d` + `git init`, `.claude/skills/{writing-for-agents (copied from main), zz-control (frontmatter after a line-1 HTML comment)}`, `claude -p --setting-sources project --strict-mcp-config --model haiku --max-turns 1 </dev/null` → `writing-for-agents: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md. - Use when writing, reviewing or editing a skill …` (own description + local when_to_use) and `zz-control: <!-- CONTROL-COMMENT-LINE-ONE -->` (control discriminates) → PASS.

### Sub-step 5.1: Split aa-ma-execution (1295 lines)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.0
- Acceptance Criteria:
  - `tests/test_split_preserves_content.py` created: for each split file, multiset(non-blank lines of the pre-split file @ base SHA) ⊆ multiset(lines of SKILL.md ∪ references/*.md); added lines are only link/TOC lines matching `^\s*[-*] \[.+\]\(.+\)$|^#+ |^>? ?See .*\]\(references/`.
  - `claude-code/skills/aa-ma-execution/SKILL.md` ≤500 lines; each reference opens with its one-line purpose.
  - `test_split_preserves_content` and the full suite + all bats pass for this file; committed.
- Result Log: Mode: AFK — auto-dispatched. Baseline @ a766804: pytest 2730 passed / 6 skipped / 0 failed; bats 401/401. RED 7957ddc `tests/test_split_preserves_content.py` (finds the split commit by subject `refactor(skills): split <skill> ` and compares it with its parent; before the commit, working tree vs HEAD, failing if they are equal so a wrong subject or shallow clone cannot pass vacuously; + flat-references test + 3 controls) — failed for the right reason (no split). GREEN 58b73d6: SKILL.md 1295 → 487 lines; IV, V, VI, VIII+IX, IX.5, XI, XII moved verbatim to references/{execution-workflows, commit-signature, finalization-protocol, compaction-and-rollback, goal-conditions, error-handling, best-practices}.md; each heading stays in SKILL.md + one `See [..](references/..) — <purpose>` line; each reference opens `# <title> — <purpose>`, TOC (`## Contents`) on the 4 over 100 lines. III (HTP template linted by test_active_plans_canonical) and VII (sync) stay inline; goal-condition-synthesis' pointer to §IX.5 resolves via the kept heading. ALLOWLIST entry removed. Check: commit vs parent 1 file → 8, 0 errors; mutating one moved line → `lost:` reported. regen-generated: edges/golden unchanged (stamp-only churn reverted). Tests: pytest 2741 passed / 6 skipped / 0 failed; bats 401/401.

### Sub-step 5.2: Split execute-aa-ma-milestone (1244 lines)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.1
- Acceptance Criteria:
  - SKILL.md ≤500 lines; §6.7 fences STAY in SKILL.md (bats `_gate_fence` extracts by heading).
  - Text pinned by `execute_aa_ma_milestone_phase_6_8.bats` (10 greps), `aa-ma-deps.bats` and `aa-ma-gate-scans.bats:155` stays in SKILL.md or the test moves in the same commit.
  - `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log: Mode: AFK — auto-dispatched. 6399c58: SKILL.md 1244 → 492 lines; §1–§4.5, §6.1, §6.3–§6.6, §6.8, §7.2–§7.4 and §8–end moved verbatim to references/{pre-execution-validation, context-and-todos, boundary-checks, post-impl-review, finalization, checkpoint-and-errors}.md (§8–end as one contiguous block, one stub; nothing outside the file cites §8–§11). Stay inline: §5.1 advisory fence (aa-ma-deps `_advisory_fence`), §5.2 Mode dispatch, §6.2 (aa-ma-deps awk 6.2→6.3), both §6.7 fences (`_gate_fence`, `_diagram_fence`), §6.8/§7.1 headings (order test), §7.1 HARD-gate fence, footer. Tests moved in the same commit: execute_aa_ma_milestone_phase_6_8.bats reads the §6.8 stub + references/post-impl-review.md (+1 pointer test; removing the reference fails 9); aa-ma-gate-scans.bats awk/bash -n guards scan SKILL.md + references/*.md (+1 coverage test; a planted awk in a reference fails 3 guards — before, moved snippets would have left the guard silently); test_active_plans_canonical WRITER_TEMPLATES → the 2 references holding tasks.md templates; ALLOWLIST entry removed, ratchet control now uses aa-ma-plan. Defect caught by test_skill_links_resolve: the moved ADR-0005 link needed one more `../` from references/; test_split_preserves_content now compares relative links by resolved target (+control). regen: edges/golden unchanged. Tests: pytest 2751 passed / 6 skipped / 0 failed; bats 403/403.

### Sub-step 5.3: Split aa-ma-plan (1154 lines)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.2
- Acceptance Criteria:
  - SKILL.md ≤500 lines; `test_planning_standard_count` SITES ("ALL 13 elements") stay findable.
  - `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log: Mode: AFK — auto-dispatched. 485f998: SKILL.md 1154 → 425 lines; Phases 0, 1, 2, 3, 4.2+4.5 and the tail (Error Handling → Design Principles, one contiguous block) moved verbatim to references/{phase-0-runtime-log, phase-1-context, phase-2-brainstorm, phase-3-research, phase-4-reviews-and-verification, operations}.md. Phase 4 stays (Step 4.2b fence run by test_angle6_coverage `_fence`, seed text between `### Phase 4:` and `### Phase 4.2:`, "ALL 13 required elements" for test_planning_standard_count SITES) and Phase 5 stays (tasks.md templates for test_active_plans_canonical; the Dependencies fence aa-ma-deps.bats runs). Before this split, 90a0224 widened test_understand_codebase_rewire to read split skills' references (5.2 had moved §6.3 out of its no-unshipped-route and PROJECT_INDEX-names-codemem checks with nothing failing; planted line now fails both) → lesson L-047. In 485f998: planning-standard drift check and test_aa_ma_writers_do_not_invoke_it read aa-ma-plan's references (planted line fails both). ALLOWLIST entry removed; ratchet control → sole-dev-merge. regen: edges/golden unchanged. Tests: pytest 2759 passed / 6 skipped / 0 failed; bats 403/403.

### Sub-step 5.4: Split sole-dev-merge (1054 lines)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.3
- Acceptance Criteria:
  - SKILL.md ≤500 lines; stage fences referenced by `tests/commands/sole-dev-merge/*.bats` and `fixtures/extract_stage.sh` stay in place or the tests follow in the same commit.
  - `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log: Mode: AFK — auto-dispatched. abd3abe: SKILL.md 1057 → 314 lines (measured 1057 at bc177e5; heading keeps the plan-time 1054); Stages C, D, E, F, G moved verbatim, one reference each: references/{stage-c-review-and-security, stage-d-triage, stage-e-remote-and-body, stage-f-push, stage-g-merge}.md. Stay inline: migration banner (test_smoke_e2e greps its markers in SKILL.md), Stages A, B, B-commit, exit-status contract, Tests. The test followed in the same commit: `fixtures/extract_stage.sh` reads a SKILL.md with its references/*.md and refuses a marker found more than once (planted duplicate → rc=1); all 15 stage markers extract. No negative checks read this file (L-047 sweep). c97c31f (separate, so the split commit stays pure moves): the 'inline bash blocks below' sentence now says where C–G live. regen: edges/golden unchanged. Tests: pytest 2765 passed / 6 skipped / 0 failed; bats 403/403 (sole-dev-merge 70/70).

### Sub-step 5.5: Split execute-aa-ma-full (757 lines)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.4
- Acceptance Criteria:
  - SKILL.md ≤500 lines; `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log: Mode: AFK — auto-dispatched. ebabd70: SKILL.md 758 → 430 lines; §1, §2+§2.5 and §8–§11 (contiguous, one stub; nothing outside the file cites §8–§11) moved verbatim to references/{pre-execution-validation, context-and-goal, errors-and-operations}.md. §3–§7 stay, incl. §5 (B.6 hand-off pinned by execute_aa_ma_milestone_phase_6_8.bats awk B.6→C., `aa_ma_deps advisory` pinned by aa-ma-deps.bats). L-047: aa-ma-deps.bats "never halts on Dependencies" (a negative check) now greps SKILL.md + references/*.md; planted 'dependency … HALT' in a reference fails it. Tests: pytest 2769 passed / 6 skipped / 0 failed; bats 403/403; regen edges/golden unchanged.

### Sub-step 5.6: Split plan-verification (608 lines)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.5
- Acceptance Criteria:
  - SKILL.md ≤500 lines; `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log: Mode: AFK — auto-dispatched. 211f38d: SKILL.md 608 → 416 lines; Angles 1–5 moved verbatim to references/angles-1-5.md (216 lines, TOC); each `#### Angle N` heading kept with a See pointer. Angle 6 stays (text pinned by test_plan_verification_angle6 + test_angle6_coverage slices of check 8; the lib-resolution snippet aa-ma-gate-python.bats compares). The ALLOWLIST emptied here, not in 5.7: removing the last entry is forced by test_allowlist_ceilings_track_the_file, so the ratchet control (test_one_added_line_breaks_an_allowlisted_ceiling) now uses a synthetic monkeypatched entry; the per-entry ceiling test reports an empty parameter set (1 skip) and still guards any future entry. L-047: test_angle6_runs_the_lint_not_a_grep (negative) and test_prose_code_profile_sets_match_the_constant read references too; planted lines fail both. Tests: pytest 2771 passed / 7 skipped / 0 failed; bats 403/403; regen edges/golden unchanged.

### Sub-step 5.7: Empty the size allowlist
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.6
- Acceptance Criteria:
  - `tests/test_prompt_size.py` passes with an empty ALLOWLIST.
  - M4 evals re-run for the 4 affected skills with cases (execute-aa-ma-milestone, execute-aa-ma-full, aa-ma-plan, plan-verification); delta logged (advisory; Risk 3 mitigation).
- Result Log: Mode: AFK — auto-dispatched. `tests/test_prompt_size.py`: `ALLOWLIST: dict[str, int] = {}` (emptied in 211f38d, 5.6 — forced by the ceiling-tracking test); test_prompt_size 60 passed / 1 skipped (empty parameter set of the per-entry ceiling test). SKILL.md sizes at 211f38d: aa-ma-execution 487, execute-aa-ma-milestone 492, aa-ma-plan 425, sole-dev-merge 315, execute-aa-ma-full 430, plan-verification 416 (after the review stub edits 6a64cd2/9c03f05: 487/498/427/317/432/416, milestone Result Log). Evals re-run (advisory, sonnet, plan usage, `scripts/run-evals.sh --case '<skill>-*' -j 3` from the M5 worktree, $1.52 est): execute-aa-ma-milestone 3/3, execute-aa-ma-full 3/3, aa-ma-plan 2/3, plan-verification 3/3 → 11/12, skill fired 12/12. Delta vs M4 baseline of record (same 12 cases 10/12): aa-ma-plan/artifact-names still fails [names-tasks-file, result] (same graders as baseline); plan-verification/missing-criteria now passes (n=1, within the noise the baseline recorded). No regression from the splits. Re-run after the §6.8/double-check stub edits (9c03f05, Ste chose re-run): 11/12 again, $1.62 est — aa-ma-plan/artifact-names now passes; execute-aa-ma-milestone/not-complete fails `skill-fired` only (answer right). All six frontmatters are byte-identical to bc177e5 and that case passed in the first M5 run and the M4 baseline, so the miss is n=1 triggering noise, not a split effect. (A 2-second test mutation of plan-verification/references/angles-1-5.md overlapped the aa-ma-plan cases of this run; restored; aa-ma-plan 3/3.)

### Sub-step 5.8: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 5.7
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 5: Split the six oversized prompt files (behaviour-preserving) — hook-modification — <evidence>`, naming `test_split_preserves_content`, the fence bats and the suite counts.
- Result Log: Mode: AFK — auto-dispatched. CRITICAL_PATH_REVIEW appended to provenance.log naming test_split_preserves_content (6 split commits vs parents, 0 lost lines), the fence bats (aa-ma-gate-python `_gate_fence`, test_diagram_verified `_diagram_fence`, aa-ma-deps `_advisory_fence` + Step 5.5 fence, sole-dev-merge extract_stage ×15) and suite counts; executed blocks byte-identical bc177e5 vs HEAD (§5, §6.7, §7.1 md5; 15 stage bodies).

---

## Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3)
- Status: COMPLETE
- Dependencies: Milestone 5
- Complexity: 55%
- Effort: 1.5 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - Ruff fixtures: undocumented public function fails D103; complexity 11 fails C901; `# noqa: E501` on a clean line fails RUF100; an undocumented argument fails D417.
  - `tests/scripts/test_check_conventions.py` WHY001/TODO001 positive + negative cases pass; `TODO(ADR-0021): x` passes TODO001.
  - `claude-code/agents/code-reviewer.md` carries the WARN rules; an eval case for a what-comment WARN exists.
  - Canary PR (undocumented function + bare `|| true`) fails `touched` with D103 + WHY001 (run URL logged).
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 6.

### Sub-step 6.0: Post-merge of M5
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M5 merged; `git pull` on main (M5 changed no install.sh, hooks, rules or skill set, so no `install.sh` run is needed; recorded in the Result Log).
  - Worktree for M6 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log: Mode: HITL (Ste: "please proceed"). M5 PR #24 rebase-merged → main f6a3af3 == origin/main; M5 worktree, local and remote branch removed. No install.sh run, as planned — verified, not assumed: `git diff bc177e5..main` touches no scripts/install.sh, uninstall.sh, scripts/lib, rules or agents, adds/removes no skill; the one hooks change is a 2-line comment in claude-code/hooks/lib/aa-ma-footer.sh, which install.sh does not deploy (sole-dev-merge sources it from the repo root). The six split skills are directory links into the main checkout, so their references/ are live (~/.claude/skills/<s>/references: 7/6/6/5/3/2 files). Worktree `.worktrees/feat/cci-m6-comments-docstrings` cut from main @ f6a3af3; `uv sync` rc=0; `uv run codemem build` rc=0 (305 files, 2976 symbols).

### Sub-step 6.1: Ruff docstring/KISS config (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 6.0
- Acceptance Criteria:
  - `pyproject.toml` `[tool.ruff.lint]`: extend-select += D, RUF100, PGH003, PGH004, C901, PLR0913; TD kept; pydocstyle convention `google`; extend-ignore `D107` and `TD003`, each with a `# why:`; mccabe max-complexity 10; pylint max-args 6; PLR2004 not selected; the D101–D104 parked list and its `TODO(logging-std)` (:81-83) deleted.
  - D417 verified enabled under google (`ruff --show-settings`), or enabled explicitly.
  - Fixtures: undocumented public function fails D103; complexity 11 fails C901; `# noqa: E501` on a clean line fails RUF100; undocumented argument fails D417.
  - Ruff rules apply file-level (D8); run `regen-generated.sh` if docs/architecture changes.
- Result Log: Mode: AFK — auto-dispatched. RED c324b5c (9 failed / 5 controls passed) → GREEN: tests/test_ruff_config.py 14 passed. pyproject: extend-select += D, RUF100, PGH003, PGH004, C901, PLR0913 (TD kept); extend-ignore D107, TD003 each with `# why:`; mccabe max-complexity 10, pylint max-args 6 (each `# why:`); PLR2004 not selected (asserted quiet); D101–D104 parked list + TODO(logging-std) deleted (asserted). D417 enabled under google — `ruff --show-settings` lists undocumented-param (D417), and a fixture with an undocumented arg fails D417. Fixtures fire: D103, C901 (complexity 11), RUF100 (`# noqa: E501` on a clean line), D417, PLR0913 (7 args), PGH004, PGH003; quiet: documented fn, complexity 10, 6 args, TODO(ADR-0021), __init__ (D107), magic 7 (PLR2004). Fixture caught: a `_private` module path hides D103 (pydocstyle), so the fixture path is public. No architecture change → no regen. Repo-wide untouched debt now visible (D8 touched-only): D205 73, D209 65, D101 48, D103 32, C901 23, D301 16, D102 8, RUF100 5, PLR0913 3. ruff bats (ruff-format 11, stage_b_scope) pass.

### Sub-step 6.2: WHY001 / TODO001 (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 6.1
- Acceptance Criteria:
  - WHY001: an added line with a suppression (Python `# noqa`, `# type: ignore` from tokenize COMMENT tokens only; Bash `|| true`, `2>/dev/null` outside comments and heredocs) without `# why:` on the same line or the line above. TODO001: an added TODO/FIXME without a `(#\d+|ADR-\d{4})` reference. Markdown, strings and docstrings never scanned; added/modified lines only.
  - `.pre-commit-config.yaml` shellcheck args `--enable=check-extra-masked-returns,check-set-e-suppressed`.
  - Tests pass: positive + negative cases (noqa inside a string, a heredoc, a markdown file → no finding); `TODO(ADR-0021): x` passes TODO001.
- Result Log: Mode: AFK — auto-dispatched. RED 126ecbb (18 failed) → GREEN: test_check_conventions 54 passed, test_precommit_config 6 passed. check_conventions.py: CHECKS = [check_why (WHY001), check_todo (TODO001)]; a check now gets (path, added lines, whole new-side text) — `new_text` reads `git show :path` (staged) or `<to>:path` (refs), so an unchanged `# why:` above an added suppression counts and tokenize/heredoc state see the whole file. Python: tokenize COMMENT tokens only (`# noqa`, `# type: ignore`, case-insensitive); shell (.sh/.bash/sh shebang; .bats skipped like the shellcheck hook): `|| true`, `2>/dev/null` in code with quoted text blanked, comments split at an unquoted word-start `#`, heredoc bodies (<<, <<-, quoted delimiters) skipped; Markdown/other never scanned. `# why:` accepted on the same line or anywhere in the contiguous comment block directly above (spec said 'line above'; a reason often spans lines). TODO001 = `#\s*(TODO|FIXME)` (a tag, as ruff TD reads it — prose 'the TODO at the bottom' was a measured FP) without `#\d+|ADR-\d{4}`; `TODO(ADR-0021): x` passes. M1-deferred items done: control chars escaped (`\x1b`) and undecodable path bytes backslash-replaced in output (tested). Mutation proof (L-045): 12 mutations (heredoc, string blanking, why-block, why-same-line, bats, markdown/shebang, todo-ref, hash-in-word, py-strings, utf8, ctrl) each fail ≥1 test; the 2 survivors fixed (hash case made positive; an untested rename-skip filter deleted). False-positive scan over every tracked .py/.sh (all lines as added): WHY001 80 hits, all genuine suppressions without `# why:`; TODO001 1 (scripts/check_adr_index.sh:87 `TODO(v0.6.0)`). `.pre-commit-config.yaml` shellcheck `args: ["--enable=check-extra-masked-returns,check-set-e-suppressed"]` — behavioural test caught that the unquoted YAML flow list split on the comma (shellcheck read the 2nd check as a file); real `pre-commit run shellcheck` fires SC2312. Debt note: 124 SC2310/SC2312 in 51 existing .sh files become due when each file is touched (D8). ADR-0018 Implementation line updated.

### Sub-step 6.3: code-reviewer WARN rules
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 6.2
- Acceptance Criteria:
  - `claude-code/agents/code-reviewer.md` WARNs (never CRITICAL) on: what-comments restating code; missing why on non-obvious logic; docstring claims the code lacks; unjustified suppression; unnamed magic constant (any count); MUST/NEVER/ALWAYS in touched markdown with no why-or-pointer (T15 §6). The `:91` style-nit ban is kept.
  - An eval case for code-reviewer WARN on a what-comment is added (advisory run).
- Result Log: Mode: AFK — auto-dispatched. RED 7620890 (9 failed) → GREEN. `claude-code/agents/code-reviewer.md`: new section 'Comment and docstring substance (WARNING only)' — WARNING [what-comment], [missing why], [docstring claim], [unjustified suppression], [unexplained imperative] (a [magic constant] bullet was added here, then removed in §6.8 cd64eda as a duplicate of pattern 5) (MUST/NEVER/ALWAYS in touched markdown with no why-or-pointer, T15 §6); never CRITICAL (asserted: no CRITICAL in the section); pattern 5 magic numbers now WARNING at any count (was INFO 1-2 / WARNING 3+); the style-nit ban line (old :91) kept verbatim (asserted). Tests: new tests/skills/test_code_reviewer_warn_rules.py (9) — kept out of test_verify_impl_agents.py because that file is not ruff-formatted and touching it would force a whole-file reformat (D8/L-007). Eval: evals/code-reviewer/what-comment (+ tests/fixtures/evals/py-review/stats.py, evals/_lib/py-review.sh); graders agent-fired (`tool_used: Agent`, subagent_type code-reviewer) + result (llm: what-comments flagged at ≤WARNING, not CRITICAL). test_eval_cases.py gains EVAL_AGENTS={code-reviewer} (≥1 case, may grant Agent, needs an Agent grader). Advisory run (sonnet): 1/1 pass, $0.09. Control run against the pre-change agent prompt: also 1/1 pass ($0.08) — at n=1 the case does not discriminate (sonnet flags what-comments unprompted); recorded, not hidden. test_eval_cases + test_code_reviewer_warn_rules 36 passed (test_eval_cases alone 27); sandbox fixture bats ok.

### Sub-step 6.4: Canary PR
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 6.3
- Acceptance Criteria:
  - A draft PR adding an undocumented function + a bare `|| true` fails `touched` with D103 + WHY001; run URL logged in provenance; PR closed and branch deleted.
- Result Log: Mode: AFK — auto-dispatched. Pre-flight: `pre-commit run --from-ref origin/main --to-ref HEAD` on the M6 branch passes all 4 hooks. Canary branch canary/cci-m6-touched (54d08cd, from 994ed35) adds scripts/canary_m6.py (undocumented public `canary()`; public module name — a `_` module hides D103) + scripts/canary_m6.sh (bare `|| true`); local run fails D103 + WHY001. Draft PR #25 → `Touched files (pre-commit)` FAILED: ruff-check `D103 Missing docstring in public function` + check-conventions `scripts/canary_m6.sh:3: WHY001 …`; ruff format and shellcheck passed; every other job passed (Bats, codemem smoke, Architecture drift, ShellCheck, Bandit, Explorer) — so the M6 files themselves are clean in CI. Run: https://github.com/snewhouse/aa-ma-forge/actions/runs/38140041890/job/114471854486. PR #25 closed; branch deleted local + remote (`gh --delete-branch` failed on the worktree layout — 'main' is checked out in the main worktree — so the remote was deleted with `git push --delete`; ls-remote 0). Re-run at the final code (double-check F1): canary commit 2cdb3f6 on 79e83cb, draft PR #26 → touched FAILED D103 + WHY001 on the `"$(… 2>/dev/null || true)"` form (fixed in 9edd103), run https://github.com/snewhouse/aa-ma-forge/actions/runs/38142145243/job/114478012309; the full-repo ShellCheck job failed only on the canary's SC2034; PR closed, branch deleted local + remote.

### Sub-step 6.5: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 6.4
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3) — hook-modification — <evidence>`, naming the test names and the canary run URL.
- Result Log: Mode: AFK — auto-dispatched. provenance.log CRITICAL_PATH_REVIEW line written naming the milestone heading, hook-modification, the 5 test files (+ mutation proof) and the canary run URL. New fact surfaced: the edit-time ruff-format.sh `--fix` now applies D209/D212/D403/RUF100 safe fixes to any edited file in this repo (77 fixable repo-wide; 4 D403 capitalisations such as `id`→`Id`) — cosmetic, touched-only (D8).

---

## Milestone 7: Logging standard (T9) + hook contracts (T15 §7)
- Status: COMPLETE
- Dependencies: Milestone 6
- Complexity: 65%
- Effort: 2 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `tests/hooks/aa-ma-log.bats` and `tests/test_logsetup.py` pass.
  - A bats loop over `claude-code/hooks/*.sh` asserts the `# Event:`, `# Mode: (Blocking|Advisory)` and `# Exit:` headers.
  - `git grep -n 'AA_MA_PLAN_MARKER_DEBUG\|VERBOSE\|\bDEBUG=' claude-code/` returns only the alias line.
  - ruff-format.sh bats: additionalContext JSON asserted on a captured payload; the hostile `.venv/bin/ruff` sentinel is never created; ruff off PATH → exactly 1 systemMessage per session_id.
  - One captured payload fixture per registered hook event, with a `PAYLOAD_CAPTURED <event>` provenance line each.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 7.
- Result Log: COMPLETE 2026-10-12, GATE APPROVAL (Ste, HARD) in context-log. 6/6 ACs; 8/8 sub-steps; bats 452/452, pytest 2968 passed/6 skipped/0 failed; §6.3 MEDIUM; §6.6 16 findings → 1dc490b; §6.8 PASS_WITH_WARNINGS → fe79b23 + 2b6be1e; double-check → f8f7220 + 4544060 (re-check Verified); deferred items in TODOS.md "Hook hot-path and helper tidy-ups".

### Sub-step 7.0: Post-merge of M6
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M6 merged; `git pull` on main (M6 changed no install.sh, hooks, rules or skill set, so no `install.sh` run; recorded in the Result Log).
  - Worktree for M7 cut from fresh main; `uv sync && uv run codemem build` exit 0.
  - Ste decision 2026-10-11 (after M6): SC2312 dropped from the shellcheck hook — `.pre-commit-config.yaml` args become `["--enable=check-set-e-suppressed"]`, and `tests/test_precommit_config.py::test_shellcheck_hook_enables_masked_return_checks` asserts SC2310 fires and SC2312 does not (RED first). Rationale: SC2312 was 116 of the 124 findings due on touch, mostly `echo "$(cmd)"`.
  - Hook sweep before 7.1: `shellcheck --enable=check-set-e-suppressed` reports 0 SC2310 across `git ls-files '*.sh'` (8 findings in 2 files at a063a53, 4 of them in `claude-code/hooks/`), each fix behaviour-preserving with the file's bats green.
- Result Log: Mode: HITL — Ste: Proceed. M6 merged as a063a53 (PR #27); main pulled (74cc7e2, already up to date). No install.sh run: M6 changed no install script, hook registration, rules or skill set. M6 worktree + local branch removed (remote branch already gone; non-AA-MA diff vs main empty, L-1332). Worktree `.worktrees/feat/cci-m7-logging-hook-contracts` cut from main 74cc7e2; uv sync rc=0, codemem build rc=0 (310 files, 3030 symbols). SC2312 dropped: RED 48e05a7 (test renamed `test_shellcheck_hook_enables_set_e_suppressed_only`, asserts SC2310 fires and SC2312 does not), GREEN a22106d (`args: ["--enable=check-set-e-suppressed"]`). SC2310 sweep e175676: all 8 sites are deliberate (pre-compact-aa-ma.sh: fail-open audit appends, 3 narrow directives; uninstall.sh: pure predicates manifest_slot_ok / slot_free_for_restore, 2 directives), each `# shellcheck disable=SC2310  # why: …` — no logic change. `shellcheck --enable=check-set-e-suppressed` over `git ls-files '*.sh'`: 0 SC2310, rc=0. pytest 2874 passed / 6 skipped / 0 failed; bats -r tests 403/403. Decision W1 (Ste): hook log var stays CLAUDE_HOOK_LOG — 7.1 AC and reference corrected.

### Sub-step 7.1: aa-ma-log.sh + bats (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.0
- Acceptance Criteria:
  - `claude-code/hooks/lib/aa-ma-log.sh`: `log_info|log_warn|log_error|log_debug <hook-name> <msg>` append `<date -Is> LEVEL <hook-name>: <msg>` to `${CLAUDE_HOOK_LOG:-~/.claude/logs/hooks.log}` (the shipped contract — Ste, 2026-10-11, 7.0); `log_debug` only when `HOOK_DEBUG=1` (also stderr); `log_*` always masks and strips CR/LF.
  - `fail_open_notice <hook-name> <msg>` prints `{"systemMessage": "..."}` to stdout, built with `jq -n --arg`, plus a `log_warn` line (L-1319).
  - `mask_secrets <text>`; the bash and Python pattern sets are generated from one source file, with a parity test.
  - `aa-ma-parse.sh` sources it from its own directory; `aa_ma_debug` becomes a thin wrapper over `log_debug`; `install.sh` symlinks `hooks/lib/aa-ma-log.sh` (lib list :331-346); `uninstall.sh` removes it.
  - `tests/hooks/aa-ma-log.bats` passes (format, stderr/stdout split, systemMessage JSON shape, masking); injected `"` in payload data leaves `jq 'paths'` with only the expected keys; stdout passes `jq empty`.
- Result Log: Mode: AFK — auto-dispatched. RED 9d35fcd (16 new aa-ma-log.bats cases + aa_ma_debug format + install dry-run announce), GREEN 5fc528b. `claude-code/hooks/lib/aa-ma-log.sh`: log_info/warn/error/debug → `<date -Is> LEVEL <hook>: <msg>` to `${CLAUDE_HOOK_LOG:-~/.claude/logs/hooks.log}` (Ste W1 decision); input capped at 8192 chars, CR/LF → space, masking on every log_* line; unwritable log → rc 0 + one stderr line; log_debug only with HOOK_DEBUG=1, line also on stderr. fail_open_notice → `jq -cn --arg` systemMessage + WARN line; no jq → fixed-string systemMessage + log_error. Pattern source = `src/aa_ma/secret_patterns.tsv` (13 gitleaks rule ids, ERE ∩ Python-re subset, ordered specific-first); bash reads it through the lib's real path (forge root, the aa_ma_gate pattern); unreadable → every message "[redaction failed]" (fail closed, tested). aa-ma-parse.sh sources aa-ma-log.sh from `readlink -f` dir (survives a pulled-but-not-reinstalled checkout; symlinked-layout test); aa_ma_debug = `log_debug "${0##*/}" "$*"`. install.sh links hooks/lib/aa-ma-log.sh; uninstall removes it (generic repo-symlink sweep; new round-trip test in install-migration.bats). Mutations caught: no masking (3 fail), no LF strip (1), JSON by interpolation (1). Suite caught 3 readers of the old format (L-047): session-end-dirty.bats:86 updated; 4 bare `! grep` in my own bats (never fail) → `run ! grep` (test_bats_assertions); plugin-surface golden + docs/architecture regenerated. Bash/Python **parity test** carried to 7.2 (needs logsetup.py; the shared source file exists now). bats -r tests 421/421; pytest 2874 passed / 6 skipped / 0 failed; shellcheck rc=0.

### Sub-step 7.2: logsetup.py (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.1
- Acceptance Criteria:
  - `src/aa_ma/logsetup.py`: `configure_logging(verbosity: int = 0, fmt: Literal["text","json"] | None = None) -> None` (LOG_LEVEL / LOG_FORMAT env; -v/-q mapping; stderr handler); `class SecretRedactingFormatter(logging.Formatter)` at handler level (covers child loggers, `exc_text` and stack traces; §0 v2 governs over the amendment's "Filter" wording); `SECRET_PATTERNS: tuple[re.Pattern[str], ...]`.
  - Input capped at 8 KB before matching; each pattern has a 100 KB adversarial timing test.
  - `.importlinter` + `tests/render/test_leaf_contract.py`: `aa_ma.logsetup` added to `render-is-leaf`, `analysis-is-leaf` and the forbidden list of `analysis-is-self-contained`.
  - `tests/test_logsetup.py` passes: an API-key-shaped string in a log record is masked; with a pattern monkeypatched to raise, `record.getMessage() == "[redaction failed]"` (fail closed, never leaks, never drops).
- Result Log: Mode: AFK — auto-dispatched. RED 8928661 (impl moved aside so the tests ran against nothing: collection error; the new bash straddle case failed against shipped 5fc528b), GREEN 0f4cf65. `src/aa_ma/logsetup.py`: `configure_logging(verbosity, fmt)` → one StreamHandler(stderr) via `basicConfig(force=True)`; level = verbosity (−2..2 → CRITICAL..DEBUG) when non-zero, else LOG_LEVEL, else WARNING; bad LOG_LEVEL/LOG_FORMAT → logged warning + fallback (no silent). `SecretRedactingFormatter(fmt, as_json=)` masks the rendered record (msg + args + exc_text + stack); JSON mode masks message/exc fields then dumps; any exception → record.msg "[redaction failed]", args/exc/stack cleared. `SECRET_RULES` (id, pattern) + `SECRET_PATTERNS` loaded from package data `secret_patterns.tsv` (wheel verified to ship it). `mask_secrets`: masks a MAX_CHARS+256 window then truncates to 8192 — fixes a cap-straddle fragment leak found while reviewing the background security notice (bash fixed identically). `.importlinter`: aa_ma.logsetup in render-is-leaf, analysis-is-leaf, analysis-is-self-contained forbidden list; lint-imports 6 kept/0 broken; test_leaf_contract green. **Parity test (7.1 AC)**: 13-string corpus, bash `mask_secrets` == Python `mask_secrets`, all pass. Timing: every rule × 10 adversarial 100 KB inputs < 1 s. Mutations caught: no cap overlap (1), no fail-closed (1), unmasked text path (4). tests/test_logsetup.py 53 cases; bats 422/422; pytest 2927 passed / 6 skipped / 0 failed.

### Sub-step 7.3: Migrate the hooks
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.2
- Acceptance Criteria:
  - Every `claude-code/hooks/*.sh` carries the header contract (Event, Blocking|Advisory, exit codes 0 / 2 and never 1 for a policy decision, fail-open behaviour); the bats header loop passes.
  - `aa-ma-plan-skip-warn.sh` uses `HOOK_DEBUG`; `AA_MA_PLAN_MARKER_DEBUG` kept one release as an alias printing a deprecation notice; `docs/spec/plan-marker-grammar.md:207` alias note updated.
  - `pre-compact-aa-ma.sh` `warn_append` → aa-ma-log.sh; compaction.log folds into hooks.log; `pre-compact.bats:110` path updated.
  - `git grep -n 'AA_MA_PLAN_MARKER_DEBUG\|VERBOSE\|\bDEBUG=' claude-code/` returns only the alias line.
- Result Log: Mode: AFK — auto-dispatched. RED 8ce708a (tests/hooks/hook-headers.bats: 4 header fields, Event ↔ AA_MA_HOOKS table, Advisory never exits 2, exit 1 only as a marked infra error; pre-compact.bats:110 → hooks.log + compaction.log absent; 3 skip-warn debug cases) + RED aca814d (log functions under set -e with stdout/stderr closed). GREEN d9ed690 (aa-ma-log.sh: every write has a fallback — found because pre-compact.bats' existing EPIPE case failed once pre-compact used fail_open_notice: a real 7.1 defect, jq on closed stdout aborted the set -e hook) and 7db959b. All 9 claude-code/hooks/*.sh carry `# Event:/# Mode:/# Exit:/# Fail-open:` (plan-marker: Event none — helper; its first-draft Fail-open line was wrong and corrected against the code before commit). Blocking hooks keep exit 1 for infra errors only (header says so; non-breaking). pre-compact: LOG_FILE removed, log_info/log_warn via aa-ma-log.sh, warn_append → log_warn (no `|| true`), final notice via fail_open_notice; previously-unguarded `>> $LOG_FILE` lines could abort the hook under set -e and no longer can. skip-warn: sources aa-ma-log.sh via its real path (degrades to no debug if absent), 5 debug sites → log_debug; alias line 42 exports HOOK_DEBUG and prints the deprecation notice; TODOS.md removal item; plan-marker-grammar.md Bypass note updated; SECURITY.md path; CHANGELOG Unreleased (Added ×4, Changed ×3, Fixed path). Grep AC: `claude-code/hooks/` → only the alias line ✓; remaining `claude-code/` hits are skills (bash-defensive-patterns VERBOSE/DEBUG=, logging-and-comments bash.md VERBOSE) — rewritten in 7.6, re-checked at the milestone boundary. WHY001 (M6 rule) blocked the first commit on two suppression lines; reasons moved onto the lines. bats -r tests 429/429; pytest 2927 passed / 6 skipped / 0 failed; shellcheck rc=0 on all hooks + lib.

### Sub-step 7.4: ruff hook additionalContext (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.3
- Acceptance Criteria:
  - `ruff-format.sh` (PostToolUse): ruff check findings for the edited file → `hookSpecificOutput.additionalContext` (≤10 lines); own failures → `log_error`; never blocks; ruff not on PATH → one `fail_open_notice` per session.
  - ruff resolved ONLY from the forge root (`readlink -f` on the hook → `<forge>/.venv/bin/ruff`) or PATH, never from the edited repo (Security v2 CRITICAL).
  - bats: captured payload → additionalContext JSON asserted; a fixture repo with a tracked `.venv/bin/ruff` that writes a sentinel file → sentinel never created; ruff stripped from PATH → exactly 1 `systemMessage` per session_id.
  - The LIVE transcript check is deferred to Sub-step 8.0.
- Result Log: Mode: AFK — auto-dispatched. RED c50c8ce, GREEN 7abd17d. ruff-format.sh: fix → format → `ruff check --output-format concise --quiet` findings as `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":…}}` via `jq -cn --arg`, ≤10 lines (9 + "… and N more — run: ruff check <f>"); format failure → log_error; clean file → no stdout; never blocks. ruff resolution: `<forge>/.venv/bin/ruff` (forge = hook's `readlink -f` dir/../..) else `command -v ruff` **only if absolute**; none → `fail_open_notice` once per session (marker `~/.claude/hooks/cache/ruff-format-no-ruff-<session_id>`, session_id `^[A-Za-z0-9_-]{1,64}$`). **Security finding**: the shipped hook ran a hostile repo's committed `.venv/bin/ruff` when PATH held a relative `.venv/bin` (RED proved it). The first draft of the hostile test passed vacuously — its stub's `#!/usr/bin/env bash` could not start on the restricted PATH — caught by a manual repro; stub is now `#!/bin/sh` + builtin redirect. bats: captured M2 payload → additionalContext JSON with only the 3 expected paths; 15-finding file → 10 lines; hostile repo (forge ruff present, and no-forge + relative PATH) → sentinel never created; no ruff → exactly 1 systemMessage per session_id (A, A, B → 1, 0, 1; 2 WARN lines). Mutations caught: relative ruff accepted, no session marker, no cap, code-level exit 1 in an Advisory hook (hook-headers.bats now ignores comment lines). Docs: foundations.md, logging-and-comments SKILL.md, CHANGELOG (Added + Security). LIVE transcript check → 8.0 as planned. bats -r tests 435/435; pytest 2927 / 0 failed.

### Sub-step 7.5: Captured payload fixtures
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.4
- Acceptance Criteria:
  - One fixture per registered hook event in `tests/fixtures/hook-payloads/`, captured live (not hand-written), each keeping its real `session_id`/`transcript_path`.
  - Every hook's bats is fed a real captured payload.
  - `provenance.log` has a `PAYLOAD_CAPTURED <event>` line per event.
- Result Log: COMPLETE d2fcb17. 7 payloads captured live 2026-10-11/12 (`claude -p --model haiku`, plan billing; ExitPlanMode via an interactive plan-mode session Ste ran): SessionStart, PreCompact, SessionEnd, PreToolUse-Bash, PreToolUse-ExitPlanMode, PostToolUse-Bash, PostToolUse-Edit → `tests/fixtures/hook-payloads/`. **AC deviation (Ste):** session_id/prompt_id/tool_use_id scrubbed to placeholders, `/home/<user>`→`/home/capture`, scratchpad uid→`/tmp/claude-capture`; all other fields as captured. Masker: 7/7 unchanged. Wiring: `tests/lib/hook_payloads.bash` `payload` helper; make_input/build_stdin in commit-signature, security-static-check, commit-drift, plan-skip-warn now build from the fixtures; +1 piped-fixture test each in session-start, pre-compact, session-end-dirty, plan-skip-warn (SessionEnd); ruff-format repointed, M2.4 fixture deleted. Guard `tests/test_hook_payloads.py` (8): every registered event+matcher has a fixture; no home/uid/real-uuid/toolu leak; masker-clean. Mutations: 8/8 hook bats fail on a broken fixture; guard catches uuid, home, missing-fixture mutants (3/3). bats 439/439, pytest 2935 passed/6 skipped/0 failed.

### Sub-step 7.6: Revise logging skills
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.5
- Acceptance Criteria:
  - `logging-and-comments`: NullHandler optional + why; JSON for services, opt-in elsewhere; `HOOK_DEBUG`/`LOG_LEVEL` only (VERBOSE/DEBUG removed); strict-mode + BashFAQ/105 caveats; hooks.log format; pino → fd 2 note.
  - `bash-defensive-patterns/SKILL.md`: bracketed log example → hook-log format; strict-mode caveats.
  - M4 evals for logging-and-comments re-run; delta logged.
- Result Log: COMPLETE 4f9df10. Mode: AFK — auto-dispatched. `logging-and-comments`: NullHandler optional + `# why:` (references/python.md, HOWTO quote; TOC added, TOC allowlist entry dropped); JSON default for services, opt-in `LOG_FORMAT` elsewhere; `LOG_LEVEL`/`HOOK_DEBUG` the only switches; `set -e` caveats + BashFAQ/105 (SKILL.md + new references/bash.md section; `inherit_errexit`; header template on LOG_LEVEL + hooks.log format); hooks.log format with example + `aa-ma-log.sh` helpers; pino → `pino.destination(2)`. `bash-defensive-patterns`: `set -e` caveats block; Pattern 5 logging → hooks.log format; Pattern 4 `-v` → `LOG_LEVEL=DEBUG`; derived-fork md5 updated in FORKS.json; no longer a plugin-surface orphan (test set + golden regenerated). Grep AC `git grep -n 'AA_MA_PLAN_MARKER_DEBUG\|VERBOSE\|\bDEBUG=' claude-code/` → only aa-ma-plan-skip-warn.sh:42 (the alias). Evals logging-and-comments (sonnet, n=1): before 3/3 $0.30 → after 3/3 $0.24; delta 0. bats 439/439, pytest 2935 passed/6 skipped/0 failed.

### Sub-step 7.7: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 7.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 7: Logging standard (T9) + hook contracts (T15 §7) — hook-modification — <evidence>`, naming the bats/test names.
- Result Log: COMPLETE — CRITICAL_PATH_REVIEW written to provenance.log (2026-10-12T10:11:32+01:00); evidence: 21 commits main..HEAD, every changed hook/lib exercised by named bats with real payloads, mutation runs recorded per sub-step.

---

## Milestone 8: SecOps CI baseline (T10)
- Status: COMPLETE
- Dependencies: Milestone 7
- Complexity: 70%
- Effort: 2.5 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - context-log has `DECISION ruff-only|fallback (<ids>) — approved by Ste`.
  - `uv run ruff check --isolated --select S src packages scripts` exits 0; the only Ruff S ignore is `tests/**` S101 (tested); `tests/security/test_canary.py` passes.
  - gitleaks full-history scan exits 0 with a reviewed fingerprint `.gitleaksignore`; a local canary repo fails `gitleaks detect`.
  - The `deps` job (hashed pip-audit) exits 0 on the branch; the 13-package triage table is in `docs/research/code-conventions-impact-ruff-vs-bandit.md` §deps.
  - `tests/hooks/security-static-check.bats` passes: S602 fixture exit 2, secret literal exit 2, no-ruff notice exit 0.
  - `ls ~/.claude/skills/senior-secops` reports absent; its backup tgz count is verified.
  - `docs/adr/NNNN-secops-baseline.md` has `Status: Accepted` + INDEX row + context-log approval.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 8.
- Result Log: COMPLETE 2026-10-13, GATE APPROVAL (Ste, HARD) in context-log. 8/8 ACs (2 via approved deviations: tests/** S set, 8 gitleaks fingerprints); 9/9 sub-steps; bats 505/505, pytest 3004 passed/6 skipped/0 failed at 0eaa6c9; CI run 38377287777 9/9 green; §6.3 MEDIUM; §6.7 PASS, DIAGRAM_VERIFIED edges=25 phantom=0; §6.8 PASS_WITH_WARNINGS (0/16/19; A–G fixed, 2 deferred); double-check F1 → CRITICAL_PATH_REVIEW addendum 5c44a49.

### Sub-step 8.0: Post-merge of M7
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M7 merged; `git pull` on main; live `scripts/install.sh` from main (M7 changed hooks); `readlink -f ~/.claude/hooks/lib/aa-ma-log.sh` resolves into the main checkout.
  - Live check (deferred from 7.4): a live edit that introduces F401 shows the finding in the next turn's context; the transcript line is logged.
  - Worktree for M8 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log: HITL — Ste: proceed, pause only at decisions. PR #28 MERGED 2026-10-12T11:27Z (f331e3a); M7 worktree removed (tree diff vs origin/main empty, `git cherry` 0 → `branch -D`); `scripts/install.sh` from main (66 symlinks); `readlink -f ~/.claude/hooks/lib/aa-ma-log.sh` → main checkout. **Live F401 check FAILED first:** ruff-format did nothing on live edits; session transcript `hook_success` stderr `line 22: /dev/stdin: No such device or address` (Claude Code delivers stdin on a socket → ENXIO), a silent fail-open since 563cee4 (M2). Fixed via PR #29 (RED fb2f0a4 socketpair bats + /dev/stdin guard, GREEN 73edc09 `payload=$(cat)` — `read -d ''` rejected, measured 1.9 s vs 34 ms @2 MB; L-050 0df379c); bats 460/460, pytest 2970/6/0, CI 7/7 (run 38269492960); rebase-merged by Ste's OK. Re-check PASS: live Edit of scratch `f401_probe.py` → next-turn context `F401 [*] \`os\` imported but unused`, file reformatted (`x=1`→`x = 1`); transcript line 492 of session 7bba3333. M8 worktree `feat/cci-m8-secops-ci-baseline` from 0df379c; `uv sync` 0, `codemem build` 0 (315 files, 3088 symbols).

### Sub-step 8.1: Pinned Ruff-vs-Bandit comparison
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 8.0
- Acceptance Criteria:
  - `docs/research/code-conventions-impact-ruff-vs-bandit.md`: every Bandit test ID → Ruff S code or GAP at ruff 0.15.9 / bandit 1.9.4 (venv-pinned, M1.2), run on this repo; a table of every Bandit ID that fired, with its Ruff mapping.
  - Records Ruff `S404` as preview-only at 0.15.9 while Bandit B404 fires 10×, deciding whether the fallback ID list includes B404 (A4).
  - context-log has `DECISION ruff-only|fallback (<ids>) — approved by Ste`.
- Result Log: HITL decision. `docs/research/code-conventions-impact-ruff-vs-bandit.md` written (ruff 0.15.9 / bandit 1.9.4, venv). Bandit 39 hits (B101 1, B404 11, B603 15, B607 9, B608 3); Ruff S 36 stable / 51 preview. A per-call cross-check found no hit for Bandit alone (11 line offsets = multi-line anchoring). Ruff +8 = `# nosec` sites. 75 IDs: 71 mapped (13 preview), 4 GAP (B613→PLE2502 0 hits; B614/B615/B703 not importable here). B404 preview-only, import-level noise → excluded (A4). Context-log: `DECISION ruff-only () — approved by Ste`.

### Sub-step 8.2: Ruff S on + CI security jobs
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 8.1
- Acceptance Criteria:
  - `pyproject.toml` extend-select += S; the ONLY S ignore is `tests/**` S101, asserted by a test; S603/S607 sites get per-site `# noqa: S60x  # why:` (34-finding baseline triaged: fix or noqa+why).
  - `security.yml`: job `bandit` removed (or, on the fallback decision, `uv run bandit -t <GAP ids> -ll -r src packages` with no `|| true`; carried defect 3); job `ruff-security` runs `uv run ruff check --isolated --select S src packages scripts` on push to main + weekly schedule.
  - `tests/security/test_canary.py`: a canary file with `shell=True` + a fake AWS key under `tests/fixtures/canary/` (secret assembled at runtime by concatenation, never a literal; the canary exclusion names one file) is flagged by Ruff S when scanned explicitly.
  - `ruff check --select S src packages scripts` exits 0; the canary test passes.
- Result Log: Mode: AFK — auto-dispatched; two HITL decisions taken with Ste. (1) tests/** S ignores = S101,S108,S603,S607 + pre-existing S110 (Ruff S over tests found 327 hits / 50 files; a literal S101-only would force noqa on every touched test subprocess call); `test_only_tests_ignore_s_rules_and_only_the_approved_set` asserts the exact set. (2) D8 debt on the 16 touched files paid down: AST-identical format commit; 63 docstring fixes (subagent, AST minus docstrings identical) + 20 D209 autofixes; 10 C901/PLR0913 get noqa+why + a TODOS entry; codemem owners' silent `except Exception: return {}` now logs one warning (test mutation-checked). Commits: RED 8fab08b → GREEN f700f90 (S selected, Bandit job removed — carried defect 3 closed — `ruff-security` job on push main/PR/weekly cron, pre-commit ruff `--force-exclude` + `--`, 35 per-site `noqa: S60x # why:`, snapshot.py assert → raise) → style 20f0838 → 6fe1770. Canary `tests/fixtures/canary/canary_shell.py` (S602; AWS key id joined at runtime, the regex finds none in source); its single extend-exclude, when removed, fails 2 tests. Gate `uv run ruff check --isolated --select S src packages scripts` rc 0; tests/security 11 passed; pytest 2982/6/0; bats 460/460; local touched sim rc 0; draft PR #30 CI 7/7 incl. Ruff S (run 38274739316). `# nosec B404` import comments stay until 8.6 (Stage C still runs Bandit).

### Sub-step 8.3: gitleaks
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 8.2
- Acceptance Criteria:
  - CI job `gitleaks`: v8.18.4 from the tarball with sha256 verified; `gitleaks detect --redact --exit-code 1 --log-opts="--all"`; checkout `fetch-depth: 0`.
  - `.gitleaksignore` holds fingerprint entries (commit:file:rule:line) for the 3 fixture hits (tests/analysis/test_measure.py, tests/hooks/security-static-check.bats), each preceded by a `# why:` line; a test asserts that; no path or regex allowlists; Ste reviews the allowlist.
  - `.pre-commit-config.yaml` + gitleaks (staged), rev frozen to a SHA.
  - The full-history scan exits 0; a canary commit in a LOCAL `mktemp -d` repo fails `gitleaks detect --source <tmp>`; no canary secret is ever pushed (A5).
- Result Log: HITL (allowlist reviewed and approved by Ste). Full-history scan found **8** generic-api-key hits, all tests/ fixtures, not 3: M7 added 5 (aa-ma-parse.bats, test_logsetup.py ×2, test_fork_manifest.py ×2 — a git SHA). 8.18.0 and 8.18.4 give the same 8 fingerprints. 2 commits sit only on local refs (20a7bb95, a6b2e51e refs/original); they are kept and marked. `.gitleaksignore` holds 8 fingerprints, each under a `# why:`; no allowlist file. CI job `gitleaks`: v8.18.4 tarball, sha256 ba6dbb65…7d (matches the release checksums file) `sha256sum -c`, `detect --redact --exit-code 1 --log-opts="--all"`, fetch-depth 0, persist-credentials false. Pre-commit `gitleaks-system` @02808f45 (v8.18.4 commit; tag object 77c3c6a3); touched job `SKIP: gitleaks-system`. Canary: a runtime key in a tmp repo → detect rc 1 (test); a staged canary in the worktree → hook Failed "leaks found: 1", unstaged and deleted, never committed. RED 068c268 → GREEN e9016cc; tests/security + precommit 24 passed; PR #30 CI 8/8 incl. gitleaks (run 38275374954).

### Sub-step 8.4: deps job + Dependabot
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 8.3
- Acceptance Criteria:
  - Job `deps`: `uv sync --locked && uv export --frozen --no-emit-workspace --no-emit-project -o req.txt` (hashed) `&& uv run pip-audit --disable-pip --require-hashes --strict -r req.txt`; pip-audit locked in the dev group; a test fails any ignore past its expiry date.
  - `.github/dependabot.yml`: github-actions + uv, weekly, `cooldown: 7` days.
  - All jobs use `astral-sh/setup-uv@<sha>` (`version: 0.12.3`) instead of `pip install uv`, `uv sync --locked`, `persist-credentials: false`; pre-commit `rev:`s frozen to SHAs.
  - All jobs except `deps` are green; `deps` goes green after Sub-step 8.5; A6 resolution logged.
- Result Log: Mode: AFK — auto-dispatched. RED fbe2190 (6 tests) → GREEN 0d6d6b6. Job `deps`: `uv sync --locked`, `uv export --frozen --no-emit-workspace --no-emit-project -o req.txt` (hashed), `uv run pip-audit --disable-pip --require-hashes --strict -r req.txt`, with ignores read from `.pip-audit-ignore` (`<ID>  # expires: YYYY-MM-DD — why`; the loop was checked with 0 and 2 entries). pip-audit 2.10.1 locked in the dev group. The expiry test was mutation-checked (an expired entry fails it). `.github/dependabot.yml` covers github-actions + uv, weekly, `cooldown.default-days: 7` (schema checked against the GitHub docs; GitHub's dependabot check passed). bats, codemem-smoke, architecture-drift and explorer-contract moved from setup-python + `pip install uv` + `uv sync` to setup-uv@c18668a (0.12.3, py 3.13) + `uv sync --locked`. All 9 checkouts set `persist-credentials: false`. Pre-commit's only remote rev is frozen to a SHA (8.3). PR #30 run 38276289265: 9/10 green, `deps` red as expected ("Found 72 known vulnerabilities in 13 packages"). **A6 resolved:** pip-audit replaces the experimental `uv audit`. Local note: uv-managed CPython 3.13.5 lacks the stdlib `venv` package, so local pip-audit ran via `uvx --python /usr/bin/python3.14 pip-audit==2.10.1` (toolchain not modified). pytest 2995/6/0.

### Sub-step 8.5: Triage the 13 vulnerable packages (plan 8.4a)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 8.4
- Acceptance Criteria:
  - For each of the 13 packages (12 with `--no-dev`: pyjwt, starlette, urllib3, mcp, fastmcp, cryptography…): `uv lock --upgrade-package <pkg>`, or an ignore entry with ID, why and expiry date.
  - The `deps` job exits 0 on the branch; the triage table is in `docs/research/code-conventions-impact-ruff-vs-bandit.md` §deps.
- Result Log: HITL (ignore decision approved by Ste). Baseline: 72 findings / 46 unique advisory IDs / 13 packages. A blanket upgrade was rejected (mcp → 2.3.0 major, fastmcp downgraded). 11 packages upgraded within constraints (mcp 1.27→1.30, dev pin `>=1.29.1,<2`; cryptography 46→50; pyjwt 2.15.1; starlette 1.7; urllib3 2.8; …). fastmcp ≥3.2 was blocked by watchfiles `<1` (TUI), so 3 IDs are ignored to 2027-01-12 with reasons: PYSEC-2026-2475/2476 (fastmcp; Gemini-CLI and OAuth proxy, both absent — grep confirms stdio-only) and PYSEC-2026-2447 (diskcache, no fix). TODOS P2 covers the fastmcp 3 / watchfiles 1 migration. Live MCP stdio round-trip on mcp 1.30: 15 tools, `who_calls` OK. Re-audit: 0 unignored. Commit 2f81482. pytest 2995/6/0 (+2 authlib-1.8 DeprecationWarnings from fastmcp imports; gone after the migration); bats 460/460; PR #30 CI 9/9 incl. deps (run 38287827088). Triage table in research doc §deps.

### Sub-step 8.6: Commit hook → forge-pinned Ruff S (blocking) + Stage C (plan 8.5, TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 8.5
- Acceptance Criteria:
  - `security-static-check.sh` (D12, BLOCKING): forge-pinned `ruff check --isolated --select S602,S604,S307,S608,S301` on staged .py + secret-literal and path-traversal regexes; exit 2 on findings in ANY repo; regex classes Ruff covers retired; no ruff → `fail_open_notice` + exit 0, never a silent pass.
  - sole-dev-merge Stage C3: Ruff S replaces Bandit; `BANDIT_BIN` retired (CLAUDE.md bypass table is a local edit); a missing scanner still writes `[HIGH] … UNKNOWN`; Stage D auto-fix reads Ruff S JSON (:443-531) with `test_stage_d_triage.bats` and `test_smoke_e2e.bats:209` updated; the security.yml bats-job Bandit (:103-107) removed.
  - Contract text naming the hook's classes updated in `agents/security-auditor.md:3,7`, verify-impl :205/:211, execute-aa-ma-milestone :793/:857, spec :145, foundations :157.
  - `tests/hooks/security-static-check.bats` passes: S602 fixture exit 2; secret literal exit 2; no-ruff notice exit 0. A `RUFF_BIN=/nonexistent` bats case greps the findings file for `[HIGH].*UNKNOWN`; sole-dev-merge bats pass.
- Result Log: Mode: AFK, with 1 HITL design decision (Ste, circuit breaker). **Hook:** forge-pinned ruff (forge .venv or an absolute PATH entry; a hostile repo's `.venv/bin/ruff` is never run), `--isolated --ignore-noqa --select S102,S301,S307,S602,S604,S608` on the WHOLE staged blob. S102 was added to D12's list so the retired exec() regex loses no coverage. Retired regexes: shell=True, dynamic-code, SQL, deserialisation; secrets and path traversal kept, on added lines, parsed from a `--no-color --no-ext-diff --no-textconv` diff with headers only before the first hunk. No ruff → `fail_open_notice` + exit 0. Ruff/git rc 2+, unreadable JSON, or no parsable hunk → exit 2 (fail closed). **Three background security review rounds** (52d5cda → b94e2f6 → c7de979) each found a bypass in the "introduced lines only" filter (in-file noqa; start-row anchoring; first-line key; jq --arg E2BIG; `++x` as a `+++` header; repo color.diff). Circuit breaker → Ste chose whole-file (D8): 964e5b7. L-049 tightened. **Stage C3/D** (subagent, verified independently): Ruff S replaces Bandit; RUFF_SEV_JSON maps 72 codes, unknown → HIGH; `RUFF_BIN=/nonexistent` → `[HIGH] … UNKNOWN`; Stage D auto-fix keys on code == S602; the bats-job Bandit steps are removed; bandit leaves the dev group (lock: bandit, stevedore); `# nosec B404` lines are gone (db3c46a). Contract text: security-auditor.md :7/:74 and foundations :164 updated (880f7cd). verify-impl :205/:211, post-impl-review and spec :145 name only the hook and its bypass, so they are unchanged. Golden + architecture regenerated (e558b02). bats 483/483 (security-static-check 42/42; mutations: rc-2 notice, multiset, statement scope, `++` header, all caught at their commit); sole-dev-merge 72/72; pytest 2994/6/0; PR #30 CI 9/9 (run 38301444630). Pending post-merge: the gitignored CLAUDE.md bypass table row BANDIT_BIN → RUFF_BIN (local edit).

### Sub-step 8.7: Skills secops / secrets-management / defense-in-depth; remove global senior-secops (plan 8.6)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 8.6
- Acceptance Criteria:
  - `claude-code/skills/secops/SKILL.md` thin router (Ruff S, gitleaks, pip-audit / uv audit once GA, ShellCheck, osv-scanner for JS/R lockfiles; cites ASVS 5.0, OWASP Top 10:2025, NIST SSDF with no 1.2 practice IDs); eval-first: 3 cases committed before SKILL.md.
  - `secrets-management`: gitleaks primary, TruffleHog `--fail` + digest pin as alternative (FORKS state → derived). `defense-in-depth`: validate once at trust boundaries into typed values; cheap asserts deeper; LLM output untrusted (→ `Skill(llm-output-safety)`).
  - Outside repo (D3): `~/.claude/skills/senior-secops` backed up (tgz count verified) and removed; `settings.json:295 "off"` override left alone (L-1210); `ls ~/.claude/skills/senior-secops` reports absent.
  - Counts skills +1 (secops); golden regenerated; `docs/adr/NNNN-secops-baseline.md` `Status: Accepted` + INDEX row + context-log approval.
  - The L-1315 probe listing `secops` is deferred to Sub-step 9.0 (standing rule).
- Result Log: HITL (ADR and removal approved by Ste). Eval-first: 3 cases `evals/secops/{scanner-map,js-lockfile,shell-true}` + fixture `tests/fixtures/evals/py-secops`, committed RED bf92b21 before SKILL.md (FileNotFoundError). `claude-code/skills/secops/SKILL.md` is a thin router: Ruff S, gitleaks, pip-audit (uv audit once GA), osv-scanner `scan -L` (syntax and renv.lock checked against the osv-scanner docs), ShellCheck, Dependabot × edit/commit/CI/weekly. It cites ASVS 5.0, OWASP Top 10:2025 and NIST SSDF by name, no 1.2 IDs (62dd2d0). secrets-management: gitleaks primary, TruffleHog `--fail` + digest pin as the alternative; FORKS.json md5 → 0af555f2 (state derived). defense-in-depth: parse once at the trust boundary into typed values, cheap asserts deeper, LLM output untrusted → Skill(llm-output-safety) (7c3555c). Counts 38→39 (SECURITY.md, foundations, README); golden regenerated; orphan set secops in, llm-output-safety out. ADR-0022 Accepted + INDEX row. senior-secops: read first — a template stub (all 3 scripts `findings = []`, boilerplate refs, identical to the marketplace copy, already `skillOverrides: off`). Backup `/home/sjnewhouse/.claude/backups/cci-m8-senior-secops-20261013-094804.tgz` verified 7/7 files, extracted content diff-identical. The guard hook blocked the agent's `rm -r` under ~/.claude/skills, so Ste removed it via `!` (10 entries removed); `ls` → absent. settings.json `"off"` override left alone (L-1210). pytest 3002/6/0.

### Sub-step 8.8: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 8.7
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 8: SecOps CI baseline (T10) — hook-modification — <evidence>`, naming the bats/test names and the CI run URLs (ruff-security, gitleaks, deps).
- Result Log: Mode: AFK — auto-dispatched. CRITICAL_PATH_REVIEW line written to provenance.log naming the security-static-check, sole-dev-merge and ruff-format bats cases and the CI run 38372156840 job URLs for ruff-security, gitleaks, deps and bats (all pass @3ab820d). Superseded 2026-10-13 by the addendum at 5c44a49: CI run 38377287777 @0eaa6c9, hook bats 61/61, bats 505/505.

---

## Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5)
- Status: COMPLETE
- Dependencies: Milestone 8
- Complexity: 60%
- Effort: 1.5 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `tests/hooks/test_tests_verified.bats` passes (pass writes line; failing suite exit 1 with no line; missing summary exit 1; custom Test-Command honoured; banner line; `-q` line; opt-out; rc 5; custom Test-Command-Pass-Regex honoured (with trailing praise line); rc 0 + FAIL>0 summary → exit 1 no line; invalid Pass-Regex → exit 1).
  - `aa-ma-gate-python.bats` and `test_diagram_verified.bats` stay green unchanged.
  - `tests/test_tdd_waiver_doc_sync.py` passes.
  - `! grep -nE 'coverage gate|perf job' pyproject.toml` succeeds.
  - `docs/adr/NNNN-tests-verified-gate.md` has `Status: Accepted` + INDEX row + context-log approval.
  - This plan's reference.md carries `Test-Command: uv run pytest`.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 9.
- Result Log: COMPLETE 2026-10-13, GATE APPROVAL (Ste, HARD) in context-log. 7/7 ACs; 8/8 sub-steps; test_tests_verified 39/39, aa-ma-gate-approval 12/12, mutants 13/13; full bats 543/543 (recount; 561 was a miscount), pytest 3010 passed/6 skipped/0 failed at 036319d; CI run 38418957143 9/9 green; §6.3 MEDIUM, no HIGH; §6.6 C–F fixed, G → TODOS; §6.7 fences 1–3 PASS (DIAGRAM_VERIFIED edges=25 phantom=0; TESTS_VERIFIED passed=3010, dogfooded); §6.8 PASS_WITH_WARNINGS (1 CRITICAL accepted + fixed 449cb14; WARNINGs 1–6 fixed); CPR addendum f99dd5a. PR #37. sole-dev-merge Stage C (Ste: Apply both MEDIUMs): RED ee80fe3 → GREEN 705413b — nested fences close only on their own marker; fence 3 names a local base (`inputs: local <ref> (no origin/HEAD)`); bats 548/548, pytest 3010/6/0.

### Sub-step 9.0: Post-merge of M8
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M8 merged; `git pull` on main; live `scripts/install.sh` from main (M8 changed the commit hook and the skill set); `readlink -f ~/.claude/hooks/security-static-check.sh` resolves into main and the live hook contains the forge-pinned Ruff S invocation.
  - L-1315 probe lists `secops` (deferred from 8.7).
  - Worktree for M9 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log: Mode: HITL — Ste: Proceed. M8 merged (PR #30, 60127e1 2026-10-13T10:36:44Z); main pulled (ff, at 1ff3178, clean). Live `scripts/install.sh` from main rc 0 (67 links, 5 docs backed up). The AC's path `~/.claude/hooks/security-static-check.sh` does not exist: the registered hook is `~/.claude/hooks/lib/security-static-check.sh` (settings.json:479), `readlink -f` → main checkout; live file has the forge-pinned Ruff S call (`${FORGE}/.venv/bin/ruff` :207, `RUFF_RULES="S102,S301,S307,S602,S604,S608"` :217, `--isolated --ignore-noqa` :237). L-1315 isolated probe (Ste ran `claude -p --setting-sources project --strict-mcp-config` from a scratch dir): `secops` listed with its own description; control (frontmatter not on line 1) listed with its CONTROL-COMMENT → discriminating PASS. Worktree `.worktrees/feat/cci-m9-tests-verified-gate` cut from 1ff3178; `uv sync` rc 0; `uv run codemem build` rc 0 (327 files, 3123 symbols, 8338 edges; one SyntaxWarning `invalid escape '\S'` from a parsed file, non-fatal). Baseline: pytest 3004 passed/6 skipped/0 failed; bats 509/510 on the first run (one failure, name not captured), then 510/510 on 4 further runs → an unidentified pre-existing flake; every later run logs its `not ok` lines. Part A (approved scope change) committed first on the branch as a1bdb6b.

### Sub-step 9.1: Fence 3 TESTS_VERIFIED (bats first, TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 9.0
- Acceptance Criteria:
  - Fence 3 is its OWN bash block after the DIAGRAM_VERIFIED block in `claude-code/skills/execute-aa-ma-milestone/SKILL.md` §6.7, never inside the first §6.7 block; it replaces comment-only conditions 3 (:604) and 4 (:605).
  - TEST_CMD = the `Test-Command:` value in the MERGE-BASE copy of `<task>-reference.md` (`git show $base:…`), else `uv run pytest`; printed, then run as a shlex argv (no `bash -c`); the characters ; | & $ backtick < > are rejected.
  - Timeout `${AA_MA_TEST_TIMEOUT:-540}` s. PASS iff rc==0 AND the final non-empty line, after `sed -E 's/^=+ //; s/ =+$//'`, matches `(^|, )([0-9]+) passed` → append `[ts] TESTS_VERIFIED — <milestone heading> — passed=N cmd=<TEST_CMD>`; else `BLOCKED: tests …` exit 1 with no provenance line.
  - Optional `Test-Command-Pass-Regex:` (merge-base reference.md) replaces the pytest summary match; bottom-up scan, the last line matching it via bash `[[ =~ ]]` (no eval) must give an all-digit `BASH_REMATCH[1]` = N; invalid ERE (rc 2) / empty / non-numeric → BLOCKED; the TEST_CMD character-rejection rule is not applied to it; default path unchanged. No auto-rerun: a failing run is BLOCKED.
  - Opt-out (D10): `Test-Command: none — <reason>` (needs a context-log GATE APPROVAL) → `TESTS_VERIFIED — <milestone> — skipped: <reason>`; pytest rc 5 without that line → BLOCKED, naming the opt-out.
  - §6.7 summary prints the real count of conditions (no fixed "all 5").
  - `tests/hooks/test_tests_verified.bats` passes all cases; `aa-ma-gate-python.bats:45` and `test_diagram_verified.bats:127` green unchanged.
- Result Log: Mode: AFK — auto-dispatched. RED a54be1d → GREEN de3f390. DEVIATION (Ste, AskUserQuestion): SKILL.md was 498/500 lines and tests/test_prompt_size.py forbids raising the cap, so fence 3 is a thin 3rd §6.7 bash block that runs `claude-code/skills/execute-aa-ma-milestone/scripts/tests-verified.sh` (repo-local, then ~/.claude; ships with the skill symlink); the diagram-gate table/prose and the Absent-field paragraph moved verbatim to new references/gate-fences.md (+ fence 3 contract). SKILL.md now 497 lines. Fence 1: conditions 3/4 comments replaced; summary prints a real count (`CONDITIONS`), no 'all 5'. Opt-out approval format chosen (review at 9.4 ADR): `## [date] GATE APPROVAL: Test-Command none — <heading>` + `- Decision: APPROVED`, read from HEAD context-log like §7.1. tests/hooks/test_tests_verified.bats 25/25 (banner, -q, real pytest pass+fail, failing suite, missing summary, rc 5→opt-out named, merge-base self-pass guard, default uv run pytest, shlex quoted arg, metachar rejected, duplicate line, timeout, opt-out ±approval, Pass-Regex: testthat, trailing praise, FAIL>0, invalid ERE (no stderr leak), non-numeric group, last-match wins; hostile: unbalanced quote, CRLF reference). Mutation 7/7 killed (HEAD-not-merge-base, CRLF trim, metachar check, first-match, approval skip, non-numeric group, no-summary pass) — first-match initially SURVIVED → added the last-match case. aa-ma-gate-python.bats and test_diagram_verified.bats unchanged vs main and green (lib-resolution identity test #54 kept: fence 3 uses `_tv`, not `_cand`). Full: bats 535/535, pytest 3005 passed/6 skipped/0 failed; shellcheck clean; whole-tree ruff 227 findings identical to main (no Python changed). Validator line refs now: SKILL.md conditions moved; bats helpers :47/:81; fence 3 is the 3rd block.

### Sub-step 9.2: TDD-waiver regen target (TDD)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 9.1
- Acceptance Criteria:
  - `claude-code/rules/engineering-standards.md` §2 TDD text is a marker-delimited block regenerated from `plan_parsers.CANONICAL_TDD_WAIVERS` by a new target in `scripts/regen-generated.sh` (no new script); "infrastructure-only" → `tooling-config`; `refactor` requires existing tests to stay green; `hotfix-emergency` requires a follow-up test task.
  - `tests/test_tdd_waiver_doc_sync.py` passes (the rule block equals the regenerated text).
- Result Log: Mode: AFK — auto-dispatched. RED 19c7a92 → GREEN 50476c0. `plan_parsers.TDD_WAIVER_RULES` (dict: waiver → rule) is now the single source; `CANONICAL_TDD_WAIVERS = frozenset(TDD_WAIVER_RULES)` (same 5 values; consumers: plan_parsers internal + test_tdd_waiver_parser, unchanged). engineering-standards.md §2 TDD bullet is a `<!-- BEGIN/END GENERATED tdd-waivers -->` block: "infrastructure-only"/"config-only" gone → `tooling-config`; `refactor` = existing tests must stay green; `hotfix-emergency` = requires a follow-up test task. New target in scripts/regen-generated.sh (no new script): `uv run python tests/test_tdd_waiver_doc_sync.py` (the test file regenerates when run as a script, like test_plugin_surface.py); regen end-to-end rc 0, idempotent; stamp-only docs/architecture churn reverted, `codemem draw --check` OK. tests/test_tdd_waiver_doc_sync.py 4/4; all plan_parsers consumers 187 passed/1 skipped; doctests 6/6. Touching plan_parsers.py pulled in its 4 pre-existing D301s (ruff on touched files): raw docstrings with halved backslashes, every __doc__ verified identical via ast.

### Sub-step 9.3: Delete unbacked pyproject claims
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 9.2
- Acceptance Criteria:
  - The `:49` "≥90% coverage gate" and `:121` "CI perf job" claims removed (P5); `! grep -nE 'coverage gate|perf job' pyproject.toml` succeeds.
- Result Log: Mode: AFK — auto-dispatched. 5ae7f0e. Claims were at pyproject.toml :130 ("CI's perf job opts in with `-m perf`") and :146 (pytest-cov "coverage gate ≥90%"), not :49/:121 (validator). Verified unbacked first: CI pytest runs `--ignore=tests/perf` (security.yml:253) and no `--cov`/`fail_under` exists anywhere. Comments now say: run perf locally with `-m perf` (CI does not run it); pytest-cov is for on-demand reports, no threshold enforced. pytest-cov dependency kept (not in AC). `! grep -nE 'coverage gate|perf job' pyproject.toml` succeeds; TOML parses; `uv lock --check` resolves; the 10 test files that read pyproject.toml: 333 passed.

### Sub-step 9.4: ADR + spec/template/scribe updates
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 9.3
- Acceptance Criteria:
  - `docs/adr/NNNN-tests-verified-gate.md` `Status: Accepted` + INDEX row + context-log approval.
  - `docs/templates/reference-template.md` gains the `Test-Command:` line and an optional, commented `Test-Command-Pass-Regex:` example; `claude-code/agents/aa-ma-scribe.md` copies `Test-Command:` into reference.md (and `Test-Command-Pass-Regex:` when the plan declares one); `docs/spec/aa-ma-specification.md:183-188` (§6.7/§6.8 table) updated.
- Result Log: Mode: HITL — Ste: Proceed; opt-out approval format kept; ADR-0023 Accepted (context-log ADR APPROVAL). docs/adr/0023-tests-verified-gate.md (Status: Accepted; options inline / thin fence + script / Python CLI; residual risk; component view; testthat example) + INDEX row (Accepted). docs/templates/reference-template.md: `Test-Command:` line + commented `Test-Command-Pass-Regex:` example (inert: the script reads only lines starting with the key). claude-code/agents/aa-ma-scribe.md: reference.md skeleton carries `Test-Command:` and, when the plan declares one, `Test-Command-Pass-Regex:`. docs/spec/aa-ma-specification.md §6.7 row now names fences 1–3 (ADR-0009/0015/0023). Doc/ADR/spec/template/scribe readers: 225 passed/4 skipped. Spec is copied by install.sh (not symlinked) → re-run install after merge.

### Sub-step 9.5: Dogfood Test-Command
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 9.4
- Acceptance Criteria:
  - `code-conventions-impact-reference.md` has the line `Test-Command: uv run pytest` (met within M9). Because of D7, fence 3 goes live after the M9 merge + install, so the provenance check moves to Sub-step 10.0 / the Milestone 10 gate.
- Result Log: Mode: AFK — auto-dispatched. Met before M9 (Ste agreed at the scope-change approval): reference.md:7 reads `Test-Command: uv run pytest`, re-checked at HEAD and at origin/main (the merge-base fence 3 will read). No edit. The live TESTS_VERIFIED check moves to Sub-step 10.0 / the Milestone 10 gate (D7: fence 3 goes live after merge + install.sh).

### Sub-step 9.6: Re-run execute-aa-ma-milestone evals
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 9.5
- Acceptance Criteria:
  - M4 evals for execute-aa-ma-milestone re-run (advisory); delta logged (CEO F13).
- Result Log: Mode: AFK — auto-dispatched. `scripts/run-evals.sh --case 'execute-aa-ma-milestone-*' -j 3` from the M9 worktree (sonnet, plan usage, $0.44): hitl-pause, next-milestone, not-complete all `verdict: pass`, score 1, `failed: []` (skill-fired included) → 3/3. Delta: M4 baseline 3/3; M5 first run 3/3, M5 re-run 2/3 (not-complete skill-fired only, judged n=1 noise) → M9 3/3, no regression from fence 3 or the §6.7 prose move. Results: .claude/evals/2026-10-13.jsonl (gitignored). Advisory.

### Sub-step 9.7: CRITICAL_PATH_REVIEW
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 9.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — hook-modification — <evidence>`, naming the bats/test names, where the heading is verbatim (backticks included): Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5)
- Result Log: Mode: AFK — auto-dispatched. CRITICAL_PATH_REVIEW written to provenance.log with the verbatim heading, written AFTER the last critical-path commit (L-1346): head 8331093, critical-path commits a54be1d/de3f390, 903adf0/6f299b3, 19c7a92/50476c0; names the six Pass-Regex bats cases plus merge-base, metachar, opt-out and symlink cases; full bats 538/538, pytest 3009/6/0; CI run 38407580385 @8331093 9/9 (draft PR #37) with job URLs.

---

## Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper)
- Status: PENDING
- Dependencies: Milestone 9, Milestone 15
- Complexity: 75%
- Effort: 3 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - `provenance.log` has a `PROTOTYPE —` line naming this milestone's heading verbatim, with `verdict-changes-plan: YES|NO`; hook p95 latency ≤1.5 s logged.
  - `provenance.log` has a `TESTS_VERIFIED` line for Milestone 10, written by the live fence 3 at this milestone's gate (fence 3 first ran live at the M9 gate; 2026-10-13 scope change).
  - `provenance.log` has a `CODE_INTEL_REFRESH` line for Milestone 10 naming the pre-commit HEAD, the first written by the live M15 step (D7: the executor gains it only after the M15 merge + install.sh; moved from M15, PR review 2026-10-14).
  - `tests/codemem/test_callees.py`, `test_co_changes.py`, `test_aa_ma_context.py`, `test_file_impact.py`, `test_plugin_surface_index.py`, `tests/test_gitutil_contract.py`, `tests/codemem/test_critical_path_globs.py` and `tests/hooks/aa-ma-impact-preedit.bats` pass.
  - `codemem query who_calls impact-analysis` lists skill callers; `uv run pytest -m perf` stays within budget.
  - `docs/adr/NNNN-impact-preedit-hook-and-callees.md` has `Status: Accepted` + INDEX row + context-log approval.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 10.

### Sub-step 10.0: Post-merge of M15
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M15 merged (M9's post-merge ran in 15.0; 2026-10-13 scope change); `git pull` on main; live `scripts/install.sh` from main; the live `~/.claude/skills/execute-aa-ma-milestone/` carries fence 3 (`grep -rl TESTS_VERIFIED` over SKILL.md and references/ non-empty) and the M15 boundary step (`grep -rl CODE_INTEL_REFRESH ~/.claude/skills/execute-aa-ma-milestone/references/` non-empty).
  - Recorded: `TESTS_VERIFIED` and `CODE_INTEL_REFRESH` must appear for Milestone 10 at its own gate (checked by the milestone acceptance criteria).
  - Worktree for M10 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 10.1: PROTOTYPE — impact hook UX
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 10.0
- Acceptance Criteria:
  - On `prototype/impact-hook`, the hook runs on 4 real files (a hub such as `src/aa_ma/grammar.py`, a leaf, a hook script, a SKILL.md); the ≤5-line outputs are shown to Ste.
  - A1 verified live (PreToolUse `hookSpecificOutput.additionalContext`, else `systemMessage` fallback); result logged.
  - Hook latency over 20 runs: p95 ≤1.5 s; if `uv run` startup breaks that budget, call the FORGE's `.venv/bin/codemem` directly, never the edited repo's (CEO F14; Security v2).
  - `provenance.log` has `[ts] PROTOTYPE — <milestone heading> — <verdict> — verdict-changes-plan: YES|NO`, where the heading is verbatim (backticks included): Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper)
- Result Log:

### Sub-step 10.2: codemem callees, alias, defect-1 fix, min_ratio, file_impact, CLI (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.1
- Acceptance Criteria:
  - `mcp_tools/__init__.py`: `callees(db_path, name, *, max_depth=3, budget=8000) -> dict` {"target","callees","error","truncated"}; `blast_radius` deprecated alias returns the callees payload + {"downstream": same list, "deprecated": "use callees; removed after v0.18.x"}; `aa_ma_context` reads "callees" (carried defect 1, :1287); `co_changes(..., min_ratio: float = 0.0)`; `file_impact(db_path, file_path, *, budget=2000) -> dict`.
  - `claude-code/codemem/mcp/server.py` registers `callees` + the alias with a deprecation notice; `cli.py`: `codemem query callees`, `codemem query co_changes <path>... --threshold N --min-ratio R` (several paths in one process), `codemem impact <path> --format brief|json`.
  - `git_mining.py:207-210` adds rename detection (`--name-status -M`, old→new mapping); partners absent at HEAD filtered.
  - 14 MCP tools: `tests/codemem/test_mcp_server.py` (`test_thirteen_exact`) and counts in SECURITY.md, claude-code/codemem/README.md:63, claude-code/codemem/commands/codemem.md:57, packages/codemem-mcp/README.md, packages/codemem-mcp/pyproject.toml, docs/codemem/install-zero-config.md updated; `blast_radius` → `callees` wording in skills/impact-analysis/SKILL.md:227-232 and skills/system-mapping/SKILL.md:140.
  - `test_callees.py`, `test_co_changes.py` (+min_ratio), `test_aa_ma_context.py` (asserts the count, not just keys), `test_file_impact.py` pass; after the M3 renames, `co_changes claude-code/skills/execute-aa-ma-milestone/SKILL.md` returns its pre-move partners.
- Result Log:

### Sub-step 10.3: Plugin-surface edges into the index (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.2
- Acceptance Criteria:
  - New table `plugin_edges(src TEXT, dst TEXT, kind TEXT, ref_class TEXT)` (schema v4 migration in storage/db.py), filled at build from `plugin_surface.extract()`; `.md` is NOT indexed into `files`; `who_calls`/`file_impact` consult `plugin_edges` for skill/command/agent/hook names and `.md` paths.
  - `codemem query who_calls impact-analysis` lists skill callers; `test_plugin_surface_index.py` passes; `uv run pytest -m perf` stays within budget.
- Result Log:

### Sub-step 10.4: gitutil x2 + contract test (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.3
- Acceptance Criteria:
  - `src/aa_ma/gitutil.py` and `packages/codemem-mcp/src/codemem/gitutil.py`: `git(args: list[str], repo: Path, timeout: float = 10.0) -> str`; env scrubbed (GIT_*), LC_ALL=C, check=True; refs verified with `git rev-parse --verify --end-of-options <ref>^{commit}`; paths after `--`; `-z` parsing.
  - `.importlinter` + test_leaf_contract gain `aa_ma.gitutil`.
  - `tests/test_gitutil_contract.py` (one test parametrised over both) passes; `lint-imports` clean.
- Result Log:

### Sub-step 10.5: CRITICAL_PATH_GLOBS + derive_critical_paths (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.4
- Acceptance Criteria:
  - `src/aa_ma/plan_parsers.py`, next to `CANONICAL_CRITICAL_PATHS`: `CRITICAL_PATH_GLOBS: dict[str, tuple[str, ...]]`, one fnmatch glob per path and no braces. hook-modification → `claude-code/hooks/**`, `.github/workflows/**`, `src/aa_ma/gate.py`, `src/aa_ma/enforce.py`, `src/aa_ma/grammar.py`, `src/aa_ma/plan_parsers.py`, `src/aa_ma/impact.py`, `src/aa_ma/gitutil.py`, `claude-code/skills/execute-aa-ma-*/**`, `claude-code/skills/sole-dev-merge/**`, `.gitleaksignore`, `.pre-commit-config.yaml`, `scripts/check_conventions.py`, `scripts/install.sh`, `scripts/uninstall.sh`, `.github/dependabot.yml`; version-pipeline → `scripts/release.sh`, `VERSION`.
  - `derive_critical_paths(paths: Iterable[str]) -> dict[str, list[str]]` (value → triggering files).
  - `tests/codemem/test_critical_path_globs.py` passes: every listed real file matches its glob; globs ⇔ engineering-standards table; every glob is fnmatch-valid.
- Result Log:

### Sub-step 10.6: Pre-edit hook + install (TDD)
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 10.5
- Acceptance Criteria:
  - `claude-code/hooks/aa-ma-impact-preedit.sh`: PreToolUse(Edit|Write) (no MultiEdit tool in 2.1.294; NotebookEdit ignored); reads `.tool_input.file_path`; once per file per session via atomic `mkdir ~/.claude/runtime/impact-seen-<session_id>/<sha1(path)>`; no index → ONE systemMessage per session; 0 external callers and 0 co-changes → silent; else ≤5 lines via additionalContext; exit 0 always; JSON via `jq -n --arg`.
  - Injected strings pass a new never-raising `sanitize_context_line(text, max_len=200)` in codemem `mcp_tools/sanitizers.py`, framed as "codemem data (untrusted):"; file_path quoted, passed after `--`; out-of-repo paths ignored via `realpath -m` + trailing-slash prefix.
  - §0 v2: `session_id` validated against `^[A-Za-z0-9_-]{1,64}$`; codemem wrapped in `timeout -k`; index.db opened `mode=ro`, `trusted_schema=OFF`; a git-tracked `.codemem/index.db` ignored; runtime markers cleaned at SessionEnd; codemem resolved from the forge root or PATH, never the edited repo.
  - `install.sh` AA_MA_HOOKS += impact-preedit; `uninstall.sh` updated; hooks count 9→10.
  - `tests/hooks/aa-ma-impact-preedit.bats` passes: real captured Edit/Write payloads; NotebookEdit + out-of-repo path → exit 0, empty stdout; codemem absent from PATH → one notice; once-per-file; no-index notice once; silent at 0; injection-named symbol sanitized; file_path with spaces and `$(touch x)` executes nothing; two concurrent invocations print once.
  - Fake-`CLAUDE_HOME` install shows exactly one impact-preedit registration; the live install is deferred to Sub-step 11.0.
  - codemem is resolved as M15.8 recorded in the M10 Contract: `CODEMEM_BIN` → forge `.venv/bin/codemem` → `~/.local/share/codemem-plugin/.venv/bin/codemem` → absolute PATH; never from the edited repo.
- Result Log:

### Sub-step 10.7: §6.3 / §6.8 / Angle-3 / writers wiring + ad-hoc advisory
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.6
- Acceptance Criteria:
  - execute-aa-ma-milestone §6.3: predicted-vs-actual over (merge-base..HEAD ∪ working tree) vs Contract Files + co_changes misses; one line per unpredicted file; the list goes to §6.8. verify-impl and `claude-code/agents/code-reviewer.md` take the unpredicted-file list as input (§6.3 stops self-grading, R6).
  - plan-verification Angle 3; `docs/spec/aa-ma-specification.md` and `docs/templates/tasks-template.md`: PROTOTYPE entry gains `verdict-changes-plan: YES|NO`, and YES triggers an Angle-3 check on the decision delta (R3).
  - `Skill(impact-analysis)` named at pre-edit in execute-aa-ma-step, execute-aa-ma-full, prototype, defense-in-depth and aa-ma-execution SKILL.md.
  - `aa-ma-commit-drift.sh`: ad-hoc commits (no active plan) get an advisory co_changes-at-commit line.
  - `pyproject.toml` dev group += griffe (pinned).
  - The Contract-named tests for this wiring pass (standing rule), shown in the Result Log.
- Result Log:

### Sub-step 10.8: ADR — impact pre-edit hook and callees
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 10.7
- Acceptance Criteria:
  - `docs/adr/NNNN-impact-preedit-hook-and-callees.md` `Status: Accepted` + INDEX row + context-log approval; the alias removal is tracked as `TODO(ADR-NNNN)`.
- Result Log:

### Sub-step 10.9: Re-run impact-analysis + execute-aa-ma-milestone evals
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.8
- Acceptance Criteria:
  - M4 evals for impact-analysis and execute-aa-ma-milestone re-run (advisory); delta logged (CEO F13).
- Result Log:

### Sub-step 10.10: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 10.9
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — hook-modification — <evidence>`, naming the bats/test names, where the heading is verbatim (backticks included): Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper)
- Result Log:

---

## Milestone 11: Gate-computed `IMPACT_VERIFIED` (T7)
- Status: PENDING
- Dependencies: Milestone 10
- Complexity: 85% ⚠️ HIGH COMPLEXITY
- Effort: 3 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - `provenance.log` has a `PROTOTYPE —` line naming this milestone's heading verbatim, with the chosen threshold values and `verdict-changes-plan: YES|NO`; the `Skill(complexity-router)` verdict is in context-log.
  - `tests/test_contract_rows.py`, `tests/test_impact.py`, `tests/test_impact_codemem_contract.py`, `tests/hooks/test_impact_verified.bats`, `tests/hooks/aa-ma-milestone-base.bats` and the extended `tests/test_gate_parity.py` pass; `lint-imports` clean.
  - `aa-ma-impact` exits 0 pass / 1 unexplained or undeclared break / 2 usage / 3 codemem index unavailable / 5 not applicable, each covered by a test.
  - `docs/adr/NNNN-gate-computed-impact-verified.md` has `Status: Accepted` + INDEX row + context-log approval; the runbook `claude-code/skills/execute-aa-ma-milestone/references/impact-gate.md` exists.
  - The 11.7 retro-check output is logged, and every unexplained file has a one-line disposition in context-log.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 11.

### Sub-step 11.0: Post-merge of M10
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M10 merged; `git pull` on main; live `scripts/install.sh` from main (deferred from 10.6); `~/.claude/settings.json` has exactly one `aa-ma-impact-preedit.sh` registration.
  - A live Edit in a session shows either ≤5 lines of impact context or exactly one no-index notice.
  - Worktree for M11 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 11.1: PROTOTYPE — co-change threshold
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 11.0
- Acceptance Criteria:
  - `Skill(complexity-router)` run first (85% milestone); its verdict logged in context-log.
  - On this repo's history, the pairs that fire at 5/50%, 3/50% and 5/30% over the last 3 completed plans' milestones are listed, with an estimate of the `Impact-Explained:` lines each would have needed; Ste picks the threshold.
  - `provenance.log` has `[ts] PROTOTYPE — <milestone heading> — <verdict, chosen n/ratio> — verdict-changes-plan: YES|NO`, where the heading is verbatim (backticks included): Milestone 11: Gate-computed `IMPACT_VERIFIED` (T7)
- Result Log:

### Sub-step 11.2: read_text_field_lines + contract_rows (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.1
- Acceptance Criteria:
  - `src/aa_ma/enforce.py`: `read_text_field_lines(block, field) -> list[str]` (full value, not first token) for `Impact-Explained: <path> — <reason>`.
  - New `src/aa_ma/contract_rows.py`: `milestone_contract_rows(plan_text, milestone) -> list[tuple[verb, path]]` with verbs Create|Modify|Test|Move|Merge|Delete, no exemptions, sliced per `### Milestone N`, reusing `_split/_expand`; imports `aa_ma.grammar` only; `src/aa_ma/render/coverage.py` imports the shared row helpers (its `--coverage` behaviour unchanged).
  - `.importlinter` + test_leaf_contract gain `aa_ma.contract_rows`.
  - `tests/test_contract_rows.py` passes; `lint-imports` clean (no grammar↔plan_parsers cycle).
- Result Log:

### Sub-step 11.3: impact.compute + aa-ma-impact CLI (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.2
- Acceptance Criteria:
  - `src/aa_ma/impact.py`: `IMPACT_CUTOVER = "9999-12-31"` (sentinel until M14.1; a test asserts it parses as an ISO date); `COCHANGE_MIN_SHARED = 5`; `COCHANGE_MIN_RATIO = 0.5`; `IMPACT_EXCLUDE = (".claude/dev/**", "docs/architecture/**", "tests/golden/**", "uv.lock", "CHANGELOG.md")`; `ImpactReport` dataclass; `compute(plan_md, tasks_md, milestone, base, head="HEAD")`.
  - Changed set = merge-base..HEAD ∪ working tree (staged, unstaged, untracked non-ignored from `git status --porcelain`).
  - Order: the cutover/grandfather check runs FIRST (exit 5) before `aa_ma_milestone_base`; `--ignore-cutover` flag supported and tested.
  - `codemem refresh-commits` runs before any co_changes query; a refresh failure, or "another writer holds … — skipped" with exit 0, → exit 3. No Contract Files rows post-cutover → exit 1 "no Contract Files for Milestone N".
  - `Cochange-Threshold: <n> <ratio>` read from the merge-base copy of reference.md, bounded n ≤ 20 and ratio ≤ 0.9, and only with a context-log GATE APPROVAL.
  - `[project.scripts] aa-ma-impact = "aa_ma.impact:main"`; CLI `aa-ma-impact <plan.md> <tasks.md> --milestone N --base SHA [--format kv|json]`; kv keys `changed= predicted= cochange= unexplained= api_breaks= derived_cp=<value:file,…>`; imports only plan_parsers/enforce/grammar/contract_rows/gitutil/logsetup; the entrypoint calls `configure_logging`; `.importlinter` + test_leaf_contract gain `aa_ma.impact`.
  - `tests/test_impact.py` passes: unpredicted file; predicted-unchanged; co-change 4 vs 5 shared commits and 49% vs 50% (≥ semantics); explained passes; rename counted as old+new; a deleted predicted file counts as changed; grandfathered → exit 5; index missing → exit 3; a diff touching `claude-code/hooks/x.sh` with no CRITICAL_PATH_REVIEW → exit 1.
  - `tests/test_impact_codemem_contract.py` calls the REAL `codemem query co_changes` on a fixture repo and validates the keys aa-ma-impact reads.
- Result Log:

### Sub-step 11.4: griffe API diff (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.3
- Acceptance Criteria:
  - griffe for `aa_ma` and `codemem` only (P6); no Python package / not importable statically → prints `api_diff=skipped(<reason>)`, never silent.
  - Removing a public function from a fixture package without `API-Break:` → exit 1; with it → pass.
- Result Log:

### Sub-step 11.5: Fence 4 + launcher + milestone base (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.4
- Acceptance Criteria:
  - `claude-code/hooks/lib/aa-ma-parse.sh`: `aa_ma_impact` launcher (aa_ma_gate pattern; 127 when uv missing) + `aa_ma_milestone_base` (`git merge-base origin/<default> HEAD`; empty or == HEAD → exit 2 "no milestone window"; R1).
  - Fence 4 is its own bash block after fence 3 in execute-aa-ma-milestone §6.7; base SHA = `aa_ma_milestone_base`; derived Critical-Path values need a CRITICAL_PATH_REVIEW naming the triggering files; on pass writes `[ts] IMPACT_VERIFIED — <milestone heading> — changed=N predicted=P cochange=C unexplained=0`.
  - A codemem result whose `stale` is not `false` (`true` or `unknown`, M15 X2) never satisfies fence 4: exit 1 naming `stale_reason`; bats case in `tests/hooks/test_impact_verified.bats` (PR review 2026-10-14; G13).
  - verify-impl Step 1 window → `aa_ma_milestone_base`; on failure (default branch or no origin) one WARN and fallback to the old heuristic, fixed so `HEAD~10` really applies when the grep is empty (fixes :93-96); Phase 6.8 never aborts; the IMPACT fence still fails closed.
  - `tests/hooks/test_impact_verified.bats` (pass writes line; fail exits 1; grandfathered prints not-applicable), `tests/hooks/aa-ma-milestone-base.bats` (branched → merge-base SHA; branch == main → exit 2; rebased branch → new merge-base; no origin → exit 2 with a named error) and the extended `tests/test_gate_parity.py` pass.
- Result Log:

### Sub-step 11.6: Rule/spec/template updates + ADR + runbook
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 11.5
- Acceptance Criteria:
  - `claude-code/rules/engineering-standards.md`: §5 Impact row → gate-computed; Tests row → TESTS_VERIFIED; §1 Critical-Path table → derived-globs pointer.
  - `docs/templates/tasks-template.md`, `docs/spec/aa-ma-specification.md`, `docs/templates/plan-template.md` (`API-Break:` in Contract) and `claude-code/agents/aa-ma-scribe.md` (`Impact-Explained:`) updated.
  - `docs/adr/NNNN-gate-computed-impact-verified.md` (ADR-0009 scope; states that callers are the domain of who_calls/§6.3, not fence 4) `Status: Accepted` + INDEX row + context-log approval.
  - Runbook `claude-code/skills/execute-aa-ma-milestone/references/impact-gate.md`: how to read a block, write `Impact-Explained:`, declare `API-Break:` (CEO F15).
- Result Log:

### Sub-step 11.7: Retro-check on M10
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.6
- Acceptance Criteria:
  - `aa-ma-impact --format kv --ignore-cutover` run against this plan's Milestone 10; output logged; each unexplained file listed in context-log with a one-line disposition (evidence only, not a gate on this grandfathered plan).
- Result Log:

### Sub-step 11.8: Re-run execute-aa-ma-milestone evals
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.7
- Acceptance Criteria:
  - M4 evals for execute-aa-ma-milestone re-run (advisory); delta logged (CEO F13).
- Result Log:

### Sub-step 11.9: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 11.8
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — hook-modification — <evidence>`, naming the bats/test names, where the heading is verbatim (backticks included): Milestone 11: Gate-computed `IMPACT_VERIFIED` (T7)
- Result Log:

---

## Milestone 12: Doctrine packaging: `coding-standards.md`, `language-conventions`, dedupe, budget (T11 §4, T12)
- Status: PENDING
- Dependencies: Milestone 11
- Complexity: 60%
- Effort: 2 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `claude-code/rules/coding-standards.md` exists, ≤ 6,000 chars; context-log has a GATE APPROVAL naming its blob SHA.
  - `tests/test_autoload_budget.py` and `tests/test_rule_references.py` pass; the rules-only auto-loaded total ≤ the M1 `rules_chars` baseline (before/after logged).
  - `claude-code/skills/language-conventions/` exists, with its 3 eval cases committed before SKILL.md.
  - `grep -cE 'KISS|DRY|SOLID' claude-code/skills/operational-constraints/SKILL.md` ≤ 2.
  - The global `~/.claude/CLAUDE.md` edit has its backup path + diff + Ste's OK in context-log.
  - This milestone's gate prints `IMPACT-GATE: not applicable (grandfathered)` from the live fence 4 (never silent).
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 12.

### Sub-step 12.0: Post-merge of M11
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M11 merged; `git pull` on main; live `scripts/install.sh` from main; the live execute-aa-ma-milestone SKILL.md contains fence 4; `uv run aa-ma-impact --help` exits 0 on main.
  - Worktree for M12 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 12.1: language-conventions (eval-first)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 12.0
- Acceptance Criteria:
  - `claude-code/skills/language-conventions/{SKILL.md, references/{python,bash,markdown,typescript,r,sql}.md}`; TS/R/SQL cards from `docs/research/code-conventions-impact-language-cards.md`; python/bash/markdown cards point to topic skills.
  - `git log --diff-filter=A` shows the 3 eval cases committed before SKILL.md.
  - Counts skills +1; golden regenerated.
- Result Log:

### Sub-step 12.2: coding-standards.md + §2 pointer
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 12.1
- Acceptance Criteria:
  - `claude-code/rules/coding-standards.md` ≤ 6,000 chars: non-negotiables; T11 principles table (KISS, DRY, YAGNI, SoC, SOLID — heuristic | configured automated check with scope | reviewer rule); T11 §1 conflict-resolution policy verbatim; T8 ponytail reconciliation; testing floor; "when X → Skill(Y)" routing table.
  - `claude-code/rules/engineering-standards.md` §2 → pointer to coding-standards.md (AA-MA process doctrine stays).
  - `scripts/install.sh`: coding-standards.md added to the rules backup list (:145-146) and the rules symlink list (:284-287); counts rules 2→3.
  - `surface_allowlist.py` adds `deslop-shared-libs` / `ponytail` only if coding-standards.md references them (`test_every_allowlisted_external_is_still_referenced`).
  - context-log has a `GATE APPROVAL` naming the coding-standards.md blob SHA (Ste reviews the wording).
- Result Log:

### Sub-step 12.3: Dedupe operational-constraints
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 12.2
- Acceptance Criteria:
  - Restated KISS/DRY/SOLID/comments text replaced by a pointer; `grep -cE 'KISS|DRY|SOLID' claude-code/skills/operational-constraints/SKILL.md` ≤ 2.
- Result Log:

### Sub-step 12.4: Budget + rule-reference tests (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 12.3
- Acceptance Criteria:
  - `tests/test_autoload_budget.py`: sum(chars) of `claude-code/rules/*.md` ≤ RATCHET (= measured after this milestone; may only fall); coding-standards.md ≤ 6,000 chars; compared with the M1 rules-only baseline (like-for-like).
  - `tests/test_rule_references.py`: every `Skill(x)` in coding-standards.md is on disk or declared-external (no dangling).
  - Both pass; the auto-loaded rules-only total ≤ the M1 `rules_chars` baseline (before/after logged).
- Result Log:

### Sub-step 12.5: Global CLAUDE.md pointer
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 12.4
- Acceptance Criteria:
  - `~/.claude/CLAUDE.md` "Coding & Architecture" (:58-69) → pointer; backup taken first; diff shown to Ste; applied only on OK.
  - Backup path + diff in context-log; Ste's OK recorded.
- Result Log:

### Sub-step 12.6: Install proof (fake CLAUDE_HOME)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 12.5
- Acceptance Criteria:
  - Fake-`CLAUDE_HOME` install: `rules/coding-standards.md` symlink present and resolving into this checkout.
  - The live install + L-1315 probe (rule loads at session start) are deferred to Sub-step 13.0.
- Result Log:

### Sub-step 12.7: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 12.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — hook-modification — <evidence>`, naming the install.sh change and the test names, where the heading is verbatim (backticks included): Milestone 12: Doctrine packaging: `coding-standards.md`, `language-conventions`, dedupe, budget (T11 §4, T12)
- Result Log:

---

## Milestone 13: Docs, counts, TODOS (pre-release)
- Status: PENDING
- Dependencies: Milestone 12
- Complexity: 30%
- Effort: 0.5 day
- Gate: SOFT
- Audit-Profile: docs-only
- TDD-Waiver: docs-only
- Mode: HITL
- Acceptance Criteria:
  - `test_doc_counts` passes; `Skill(doc-drift-detection)` is clean.
  - CHANGELOG Unreleased carries the upgrade note ("re-run scripts/install.sh", CEO F16) as a headline, plus a README line.
  - TODOS.md contains `blast_radius`, `AA_MA_PLAN_MARKER_DEBUG`, `IMPACT_CUTOVER` and `reuse-kit`.

### Sub-step 13.0: Post-merge of M12
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M12 merged; `git pull` on main; live `scripts/install.sh` from main (12.6's live part); `readlink -f ~/.claude/rules/coding-standards.md` resolves into the main checkout.
  - L-1315 isolated probe asks for one coding-standards line verbatim and gets it (the rule loads at session start).
  - Worktree for M13 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 13.1: Counts and docs
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 13.0
- Acceptance Criteria:
  - README.md, CHANGELOG.md (Unreleased + upgrade note), SECURITY.md, docs/spec/claude-code-foundations.md, docs/spec/aa-ma-quick-reference.md, docs/spec/aa-ma-specification.md, docs/adr/INDEX.md updated; CLAUDE.md (gitignored) is a local edit.
  - `test_doc_counts` passes; `Skill(doc-drift-detection)` is clean.
- Result Log:

### Sub-step 13.2: TODOS
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 13.1
- Acceptance Criteria:
  - TODOS.md records the companion `reuse-kit` plan seed (T13/T14 answers + the map path, including T14's "reuse-first while coding" rule, which needs the router skill) and the debt items: remove the `blast_radius` alias, remove the `AA_MA_PLAN_MARKER_DEBUG` alias, review `IMPACT_CUTOVER`.
  - TODOS.md contains `blast_radius`, `AA_MA_PLAN_MARKER_DEBUG`, `IMPACT_CUTOVER` and `reuse-kit`.
- Result Log:

---

## Milestone 14: Release v0.18.0 + IMPACT_CUTOVER (on main)
- Status: PENDING
- Dependencies: Milestone 13
- Complexity: 40%
- Effort: 0.5 day
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: version-pipeline
- Mode: HITL
- Acceptance Criteria:
  - `test_cutover_is_release_date` passes: `IMPACT_CUTOVER` is an ISO date, != `9999-12-31`, and == the date of tag v0.18.0.
  - `gh release view v0.18.0` exits 0, and the tag's commit contains the cutover.
  - `git status --porcelain` is empty after the cutover commit and after the release's advisory evals.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 14 (version-pipeline).

### Sub-step 14.0: Post-merge of M13
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M13 merged; `git pull` on main; `uv run pytest -q` green. M14 runs on the main checkout (D7 exception, D11); main pushes need Ste's explicit OK.
- Result Log:

### Sub-step 14.1: Cutover (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 14.0
- Acceptance Criteria:
  - Failing test first: `test_cutover_is_release_date` in `tests/test_impact.py`; then `IMPACT_CUTOVER` in `src/aa_ma/impact.py` set to the planned release date; committed on main with the plan footer.
  - The test passes; `test_doc_counts` re-run passes (M13 Risk 1); `git status --porcelain` is empty.
- Result Log:

### Sub-step 14.2: Release v0.18.0
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 14.1
- Acceptance Criteria:
  - `scripts/release.sh minor --headline "…" --dry-run`, then `--no-push` (CHANGELOG, README, VERSION, pyproject.toml via commitizen; never hand-edited); `release.sh` runs the evals advisorily and asserts a clean tree after them (Security v2).
  - Run `test_cutover_is_release_date` against the LOCAL tag; if it fails, fix the cutover and re-tag locally; then push main + tag with Ste's OK (release.sh pushes both in one run otherwise, so never amend after a pushed tag).
  - `gh release view v0.18.0` exits 0; the tag's commit contains the cutover.
- Result Log:

### Sub-step 14.3: Archive readiness — CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 14.2
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 14: Release v0.18.0 + IMPACT_CUTOVER (on main) — version-pipeline — <evidence>`, naming the dry-run output and the release URL.
- Result Log:

## Milestone 15: Codemem freshness (report 03 T2–T9)
- Status: ACTIVE
- Dependencies: Milestone 9
- Complexity: 75%
- Effort: 6 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Decision ids: `R03-Dn` = decision n of report 03's CEO-review ledger, never this plan's Dn (renamed 2026-10-14, pre-exec validator W2).
- Source: ~/projects/github_private/ooh_ideas/research/03-codemem-graphify-report.md §8 P0/P0+/P1 and §Implementation Tasks T2–T9, T12 (scope change 2026-10-13, Ste: B1 + T7 + T8 + T9)
- Acceptance Criteria:
  - `codemem refresh` runs the real `refresh_index` driver (no "placeholder" text in `cli.py`); report 03 P0#1 AC (a)–(e) and its edge cases (no git, detached HEAD, shallow clone, dirty tree, missing index) pass as tests, incl. a refresh killed mid-run that the next refresh recovers from.
  - Every codemem MCP response carries `index_sha`, `head_sha`, `stale` (true|false|unknown), `stale_reason` (golden tests updated additively); an impact-analysis run on a locked index emits `CODE_INTEL_STALE`.
  - After a commit, `.codemem/last_sha` and `graphify-out/.built_sha` equal HEAD; a killed or failed graphify rebuild leaves the previous `.built_sha`; the race test (pause/release, A last) leaves `.built_sha == A`.
  - The Session Briefing prints `Code-intel: …` per report 03 X1 output rules, < 200 ms on aa-ma-forge, never blocks.
  - 15.6's milestone dry run prints a `CODE_INTEL_REFRESH` line naming the pre-commit HEAD; a graphify failure WARNs and never blocks. The first live line is Milestone 10's (R03-D7: the executor gains the step after merge + install.sh).
  - `uv run --no-sync codemem draw --check` exits 0; `docs/codemem/kill-criteria.md` has a 2026-10 review entry; `grep -c '_M2 placeholder_' claude-code/codemem/commands/codemem.md` prints 0; the wheel README has no false `pip install` claim.
  - codemem MCP answers at user scope in a second repo via a stable symlink (R03-D13), whose `git status` stays clean (global excludes `.codemem/`, `graphify-out/`).
  - `~/.claude/rules/code-intel-routing.md` exists (per-language table R03-D10, `~/biorelate/**` + client repos code-only), `GRAPHIFY_QUERY_LOG_DISABLE=1` is set, and the graphify skill description no longer claims every codebase question (`grep -c 'any question about a codebase' ~/.claude/skills/graphify/SKILL.md` prints 0).
  - `TODOS.md` has the X4 entry (`grep -n X4 TODOS.md`).
  - `provenance.log` has `PROTOTYPE`, `TESTS_VERIFIED` and `CRITICAL_PATH_REVIEW` lines for Milestone 15.

### Sub-step 15.0: Post-merge of M9 + X4 TODOS entry (T12)
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M9 merged (PR #37, d0a1833), main pulled, live `scripts/install.sh` rc 0, live fence 3 and `aa_ma_has_gate_approval` verified — record the evidence already in provenance.log.
  - Worktree for M15 cut from fresh main; `uv sync && uv run codemem build` exit 0.
  - `TODOS.md` gains the X4 entry (non-Python call gap; trigger: a language family fails the parity gate; path to full project-index retirement, R03-D10).
- Result Log: Mode HITL — Ste: Proceed + rename title to T2–T9. M9 post-merge evidence already in provenance (PR #37 d0a1833, install.sh rc 0, installed `aa_ma_has_gate_approval` rc 0/1; fence 3 live at M9's gate `TESTS_VERIFIED … passed=3010`); nothing install-relevant changed since (`git diff d0a1833..9546a2e -- docs/spec scripts/install.sh claude-code/hooks` empty). Worktree `.worktrees/feat/cci-m15-codemem-freshness` @ 9546a2e; `uv sync` + `codemem build` rc 0 (329 files, 3136 symbols, 8353 edges, 0.87 s). Baseline: pytest 3012 passed / 6 skipped / 7 deselected (135 s), bats 560/560. TODOS.md X4 entry (`grep -n X4 TODOS.md` → :154). Pre-exec validator WARN 0 FAIL / 7 WARN — all 7 applied (context-log 2026-10-14 M15 start). Gate reads M15 ACTIVE, HARD, 11 PENDING; deps advisory silent; lint-views edges=25 checked=25 phantom=0; tasks.md canonical violations [].

### Sub-step 15.1: PROTOTYPE — bounded refresh cap (T2 risk)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 15.0
- Prototype-Required: YES
- Acceptance Criteria:
  - On `prototype/codemem-refresh-cap`, prove the 5 s cap around the synchronous `refresh_index` (`incremental.py:74`): thread vs subprocess; killing it mid-run leaves the writer lock and WAL consistent and the next refresh recovers.
  - `provenance.log` has `[ts] PROTOTYPE — Milestone 15: Codemem freshness (report 03 T2–T9) — <verdict> — verdict-changes-plan: YES|NO`.
- Result Log: Mode HITL — Ste: Proceed, then Accept both. Branch `prototype/codemem-refresh-cap` @ b854f25 (`prototypes/codemem-refresh-cap/{proto,probe_readers,probe_swap,slow_refresh}.py` + RESULTS.md; committed `--no-verify` for throwaway lint noise, gitleaks run after: Passed). Thread arm: two threads both acquire `db.lock` (lockf per-process). SIGKILL mid-incremental-txn / mid-full-rebuild (no last_sha) / mid-full-rebuild (no DB, valid last_sha): lock free, integrity ok, next refresh counts == cold build (61/300/300) in all 3. Subprocess past 5 s cap: returns 5.00 s, background finishes, last_sha == HEAD. No-op refresh 68 ms in-process / 125 ms subprocess; `git rev-parse` 3.8 ms, `status -uno` 6.4 ms. In-place full rebuild: ~23k reader raises (unable to open / no such table / disk I/O) in both arms; temp DB + `os.replace` ×5: 1802/1802 reads OK. Verdict: subprocess cap behind an in-process staleness pre-check; plan change → 15.2 atomic swap.

### Sub-step 15.2: Bounded refresh + stale semantics; real `codemem refresh` (T2)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 15.1
- Acceptance Criteria:
  - TDD: tests for P0#1 AC (a)–(e) and every edge case with its defined output fail first, then pass.
  - `grep -ci placeholder packages/codemem-mcp/src/codemem/cli.py` prints 0 (the stale `:12` replay and `:103` refresh-commits docstrings included), or each remaining hit is true and named in the Result Log.
  - (15.1 verdict, Ste 2026-10-14) The cap is a subprocess: spawned only when an in-process pre-check (`last_sha` vs HEAD, `git status --porcelain -uno`) says stale; wait ≤ 5 s; on timeout it keeps running detached and the response says `stale=true, reason=timeout`. The full-rebuild fallback builds into a temp DB and `os.replace`s it (no in-place unlink); tests: readers during a full rebuild see no error, and a long-lived reader holding the old `index.db-wal` across the swap leaves the new DB intact.
  - `codemem refresh` calls `refresh_index`; `ensure_built` checks staleness and refreshes under the cap; the 10 s other-process wait (`mcp_tools/__init__.py`) shrinks to the same cap; locked/error/timeout → results with `stale=true` + reason and one log line (`refresh.log`).
- Result Log: Mode AFK — auto-dispatched. RED 4ff1639 + 781cb0b → GREEN 6a2b73d; RED 7d… log hardening → GREEN 9100258 (see provenance). `tests/codemem/test_freshness.py` 30 tests: AC (a) fresh spawns nothing, (b) behind → refreshed fresh, (c) lock held → <5 s stale/locked, (d) corrupt DB → stale/error + `refresh: error` in refresh.log, (e) cold build writes last_sha; no git → unknown/no_git; detached HEAD; orphaned SHA → full rebuild; dirty tree → refreshed fresh (stale/dirty only via check_freshness); missing last_sha → no_index_sha; timeout (cap 0.01) → stale/timeout, background finishes → fresh; other-process build wait capped (0.3 s); kill -9 mid-incremental and mid-full-rebuild → next refresh recovers, integrity ok; full rebuild never unlinks the live DB; old -wal frames never bleed into the swapped DB; option-shaped last_sha never reaches git; CLI exit 0/75/1; `grep -ci placeholder cli.py` = 0. Mutations 4/4 killed (keep old sidecars, no 40-hex guard, in-place rebuild, no tree_sig). Design: `incremental.check_freshness` (last_sha vs HEAD + `git status --porcelain=v1 -z -uno` signature with mtime/size → `.codemem/tree_sig`); `mcp_tools.ensure_fresh` (subprocess `python -m codemem.cli refresh`, `start_new_session`, cap `REFRESH_CAP_S = 5.0`), `ensure_built` = None-or-error wrapper. stale_reason after a failed refresh = the failure (locked|error|timeout), the pre-check cause (behind|dirty|no_index_sha) goes in the refresh.log line — report 03 said `reason=dirty` for a failed dirty refresh; AC (c)/(d) name locked/error, so the failure wins. Fixture fix: `test_mcp_server_integration.populated_env` records last_sha (a seeded DB without it is now rebuilt). Hostile/fault probes: symlinked refresh.log refused, newline-folded log lines, git absent → unknown/no_git, read-only `.codemem` → error dict. Full suite: pytest 3039 passed / 6 / 7, bats rc 0; codemem 837 after hardening. D8: cli.py pre-existing D205/D103×2 fixed, C901 `_cmd_query` noqa + TODOS pay-down line. **Security addendum (background review of the pushed commits):** RED 153ae7c → GREEN bfcc1f6 — refresh subprocess `python -I` from `.codemem/` (a repo's `codemem/cli.py`, top or `.codemem/`, ran inside it); `git status` dropped, `tree_sig` = stat signature of `discover_files` (`indexer.tree_signature`), index-path git calls pinned via `indexer.SAFE_GIT` (`git ls-files`/`status` ran a repo's core.fsmonitor — measured); `last_sha`/`tree_sig` via `indexer.write_sidecar` (temp + os.replace, symlink replaced). Mutations 3/3 killed (no git pins, no -I, write through symlink). Contract deviation: `indexer.py` modified (ls-files + last_sha write live there). Remaining codemem git calls → TODOS P1. pytest 3045/6/7, bats rc 0.

### Sub-step 15.3: X2 staleness envelope + `CODE_INTEL_STALE` (T3)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 15.2
- Acceptance Criteria:
  - `index_sha`/`head_sha`/`stale`/`stale_reason` added once, in `_with_autobuild` (`claude-code/codemem/mcp/server.py:266`); golden tests updated additively; the 15.2 stale paths assert the fields.
  - `Skill(impact-analysis)` (and plan-verification) record `CODE_INTEL_STALE` when proceeding on a stale result; a locked-index impact run shows it.
- Result Log: Mode AFK — auto-dispatched. RED 01cd89d → GREEN e69ed8f. `_with_autobuild` (server.py) calls `mcp_tools.ensure_fresh` and merges the 4 fields into every response; no index → `{error, stale: "unknown", stale_reason: "no_index"}`; a raising handler now returns `{error: "query failed: …"}` + fields (corrupt index raised `DatabaseError` before). Golden (additive): `test_mcp_server_integration` 15 tool/alias cases assert stale False + 40-hex index_sha == head_sha; `test_x2_envelope.py` 6: fresh, (c) locked → stale/locked with results still served, (d) corrupt → stale/error, dirty → refreshed fresh, no git → unknown/no_git, build failure → fields. Skills: impact-analysis Freshness gate rewritten (stale ≠ false = leads, `CODE_INTEL_STALE — <tool> — <stale_reason> — index <8> head <8>`); plan-verification Angle 3 prompt (references/angles-1-5.md) same rule; `tests/skills/test_code_intel_stale.py`. **Live:** `claude -p` (sonnet, $0.34, `--plugin-dir` worktree, `--mcp-config` worktree server) on a fixture repo whose index was 1 commit behind with db.lock held → output `CODE_INTEL_STALE — who_calls — locked — index 72d2ff9e head 93158616`; the stale index missed caller `other()`, the run found it by Grep/Read; refresh.log `ensure_fresh: serving a stale index (behind); refresh locked`. D8: server.py pre-existing C901 `build_server` (21→22) noqa + TODOS pay-down line. codemem+skills 1244 passed.

### Sub-step 15.4: Our own post-commit step + `.built_sha` sidecar (T4)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 15.2
- Acceptance Criteria:
  - `claude-code/codemem/hooks/post-commit.sh`: `codemem refresh` + `graphify update .` in the background under `flock`, writing the SHA captured at start to `graphify-out/.built_sha` only when graphify exits 0 (R03-D12); graphify's own post-commit hook is not used.
  - bats: race test (pause/release, A last → `.built_sha == A`); a killed run keeps the old sidecar; graphify absent → one notice, exit 0. `scripts/install.sh` updated if the hook wiring changes.
- Result Log: Mode AFK — auto-dispatched. RED de6634d → GREEN b52f850. `claude-code/codemem/hooks/post-commit.sh` rewritten: hook captures HEAD → detached worker `--worker <sha> <repo>` (setsid); workers queue on `flock` over `<git-dir>/codemem-post-commit.lock`; `codemem refresh` (forge `.venv/bin/codemem` first, then absolute PATH) → `graphify update .` → commit-time SHA to `graphify-out/.built_sha` only on graphify rc 0 (temp + rm + mv). Old `refresh.pid` kill dropped (repo-writable PID; PR review LOW). `tests/hooks/codemem-post-commit.bats` 12/12: sidecars == HEAD after a commit; hook returns < 2 s with a held worker; graphify fail → old sidecar + 1 log line; kill -9 mid-run → old sidecar; race (B held under lock, A queued then released last) → `.built_sha == A`, starts never overlap; graphify absent → 1 notice, codemem still refreshed; relative PATH `./graphify` never runs; symlinked `.built_sha` replaced, symlinked `refresh.log` untouched; non-hex SHA refused; rebase no-op; exit 0 outside a repo. Mutations 5/5 killed (no flock, HEAD-at-write, write on failure, relative PATH kept, log through symlink). `test_post_commit_storm.py` rewritten to the flock contract (5 amends rc 0 < 2 s, both sidecars end at HEAD). Docs: SECURITY.md writer line, codemem README written-files list, ARCHITECTURE.md Primitive 3, lock.py docstring (+ D205/D209 debt). install.sh unchanged (wiring line is the same). Live forge wiring (`install.sh --wire-git-hook` on main) is a post-merge step for 10.0. Full: pytest 3051/5/7, bats 572 rc 0. Graphify 0.9.85 cold `update .` on the forge 11.5 s (backgrounded).

### Sub-step 15.5: X1 Session Briefing `Code-intel:` line (T5)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 15.3, Sub-step 15.4
- Acceptance Criteria:
  - `claude-code/hooks/aa-ma-session-start.sh` reads `.codemem/last_sha` and `graphify-out/.built_sha` directly (no `uv run`) + one `git rev-list --count`; output rules per report 03 X1 (nothing when neither index exists; `not built`; `graphify: no sha`; `unknown (<reason>)` on error, logged).
  - A sidecar is repo-controlled (a clone can commit it): only `^[0-9a-f]{40}$` is used, passed to git after `--end-of-options`; anything else prints `unknown (bad sha)` and is never echoed into the briefing. bats: a `-`-leading value, a 39-char value, a value with a newline (PR review 2026-10-14).
  - One shared shell function for "SHA vs HEAD", tested against the same fixture repo as X2's Python; bats for every output rule; < 200 ms measured on aa-ma-forge.
- Result Log: Mode AFK — auto-dispatched. RED 7f3703b → GREEN 8bfd228. `aa_ma_sha_behind <repo> <sidecar>` added to `claude-code/hooks/lib/aa-ma-parse.sh` (header entry): regular file only, `head -c 128`, `^[0-9a-f]{40}$`, `git -c core.fsmonitor=false rev-list --count --end-of-options <sha>..HEAD` under `timeout 1`; reasons bad sha | not in history | git timeout; value never printed. `aa-ma-session-start.sh` prints `Code-intel: codemem N behind · graphify M behind (code layer)` BEFORE the no-active-task exit (it describes the repo); not built / `: no sha` / `unknown (<reason>)` + one `log_warn` per unknown. Shared fixture `tests/fixtures/code-intel/make-repo.sh` read by `session-start-code-intel.bats` (13/13: every X1 rule, `-`-leading / 39-char / embedded-newline sidecars, not-in-history logged once, no repo, kill switch, AA-MA line still second, `aa_ma_sha_behind` 2/0) and `test_x2_envelope.py::test_shared_fixture_sha_vs_head` (Python: stale/behind, index_sha = HEAD~2, rev-list 2). Timing (20 runs, whole hook): aa-ma-forge p50 91 / p95 105 ms; synthetic 10k-commit repo, sidecars 9999 behind, p50 85 / p95 90 ms (report 03 owner-must-prove). Naming: the visible "Session Briefing" banner is the personal global `~/.claude/hooks/lib/session-briefing.sh` (not in the forge); per the Contract and report 03 X1 the line lives in the forge's `aa-ma-session-start.sh` output. Full: pytest 3052/5/7, bats 585 rc 0.

### Sub-step 15.6: `CODE_INTEL_REFRESH` at the milestone boundary (T6)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 15.4
- Acceptance Criteria:
  - `execute-aa-ma-milestone` (references) refreshes codemem (`refresh` + `refresh-commits`) and graphify (`update .`, code-only, R03-D7) at the boundary and appends `[ts] CODE_INTEL_REFRESH — <milestone heading> — codemem=<sha> graphify=<sha|WARN reason>` naming the pre-commit HEAD; graphify failure WARNs, never blocks; codemem failure keeps the existing BLOCKED contract.
  - A milestone dry run logs the pre-commit HEAD; SKILL.md stays under its 500-line cap.
- Result Log: Mode HITL — Ste: Proceed (design: script + §6.0 + 2-line SKILL.md pointer, reuse the post-commit worker, BLOCKED only on an existing codemem index that fails to reach HEAD). RED fdeaf79 → GREEN f23a387. `claude-code/skills/execute-aa-ma-milestone/scripts/code-intel-refresh.sh <task> [--dry-run]` runs `post-commit.sh --worker <HEAD> <top>` synchronously (same flock), then reads the sidecars; `references/boundary-checks.md` §6.0 (fence + rules, TOC row); SKILL.md +2 lines (496/500). Worker gains `codemem refresh-commits` (0.21 s on the forge) and `CODEMEM_BIN` (pins the binary, no fallback). `tests/hooks/code-intel-refresh.bats` 9/9: line names the pre-commit HEAD with uncommitted work present, `--dry-run` prints only, graphify fail/absent WARN rc 0, corrupt existing index → BLOCKED nothing appended, no index + no codemem → `codemem=skipped(no index)`, symlinked provenance refused, non-slug task refused, SKILL.md pointer + cap. **Dry run on this milestone** (real codemem + graphify 0.9.85, 15.7 s): `[2026-10-14T10:49:58+01:00] CODE_INTEL_REFRESH — Milestone 15: Codemem freshness (report 03 T2–T9) — codemem=fdeaf79095cb08d20cbea79c8799bdf66b1aae18 graphify=fdeaf79095cb08d20cbea79c8799bdf66b1aae18` = pre-commit HEAD; provenance 241 → 241 lines (not appended). First appended line: M10's gate (R03-D7: after merge + install.sh). Contract deviation: new file `scripts/code-intel-refresh.sh` (tests-verified.sh precedent). Full: pytest 3052/5/7, bats 594 rc 0. **Security addendum (background review of f23a387):** the script sourced `aa-ma-parse.sh` from the target repo's `claude-code/hooks/lib/` first (repo-planted code ran inside the gate) — RED f8e79bd → GREEN f9829d7: the script sources from its own forge; the §6.0 fence runs the installed copy only; 11/11 bats; L-049 recurrence 5. The older fences keep the TODOS P2 item.

### Sub-step 15.7: Doc drift + kill-criteria review (T7)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 15.2
- Acceptance Criteria:
  - `claude-code/codemem/commands/codemem.md` placeholder text (`grep -c '_M2 placeholder_' claude-code/codemem/commands/codemem.md` prints 0) and the wheel README `pip install` claim fixed; `docs/codemem/kill-criteria.md` gains a 2026-10 review entry; `uv run --no-sync codemem draw --check` exits 0.
- Result Log: Mode AFK — auto-dispatched. 83fb7c6: `grep -c '_M2 placeholder_' claude-code/codemem/commands/codemem.md` = 0 (refresh/replay sections describe the real commands); wheel README `pip install` claim replaced (plugin-only, AD-Q15); journal truth fixed in codemem README, SECURITY.md, ARCHITECTURE.md, migration guide (`wal.jsonl` is written only by Python callers of `build_index(wal_path=…)` — no production caller); `docs/architecture/` regenerated → `uv run --no-sync codemem draw --check` exit 0 (io.md had drifted); codemem doc-drift no findings; doc tests 46 passed. 330beda: `docs/codemem/kill-criteria.md` 2026-10-14 review entry — Signal 4 **FIRED** (background researcher, primary sources; repowise MCP_TOOLS.md spot-checked via gh api: co_change_partners, owners/bus factor, hotspot_score, layers) → Ste: apply the pre-committed rule (codemem consolidates under AA-MA; standalone framing dropped; M15/M10/M11 unchanged); positioning edits → TODOS P2.

### Sub-step 15.8: User-scope codemem MCP via stable symlink + global excludes (T9)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 15.3, Sub-step 15.5
- Acceptance Criteria:
  - `~/.local/share/codemem-plugin` → a dedicated git worktree of the forge on `main` (R03-D13; PR review 2026-10-14: never the working checkout, whose branch changes under review and prototypes), made with `ln -sfn`, updated only by `scripts/install.sh` or a pull; codemem MCP registered at user scope with that path; the 15.5 session-start check reports a missing link and a target that is not that worktree on `main`.
  - Global git excludes carry `.codemem/` and `graphify-out/`; codemem tools answer in a second repo and its `git status` stays clean. Taken first: `~/.claude` backup (count-verified) and timestamped copies of the global excludes file and the shell rc (plan §7 M15 row).
  - The M10 contract records how its pre-edit hook resolves codemem (this stable path, or `uv run --directory <forge>`).
- Result Log: Mode HITL — Ste: Proceed + install.sh refresh. Design note: git refuses `main` in a second worktree while the main checkout has it, so the dedicated worktree is **detached at main's tip** and "on main" means HEAD == refs/heads/main. Repo (RED c471032 → GREEN d7a5090): session-start prints one `Code-intel:` line when `~/.claude.json` names the link and it is missing or off main (5 bats); `scripts/install.sh` §8 re-points a linked worktree of this forge to main + `uv sync --locked --quiet`, leaves alone the checkout itself / other targets / a dirty worktree, dry-run says so (6 bats, throwaway forge copy). Live (outside repo, 2026-10-14): backup `~/.claude/backups/cci-m15-20261014T100926Z.tgz` (20/20 files: ~/.claude.json, settings.json, rules/, skills/graphify/, ~/.config/git/ignore, ~/.bashrc; sha256 40263f34…) + `~/.config/git/ignore.cci-m15-20261014T100926Z`, `~/.bashrc.cci-m15-20261014T100926Z`; `git worktree add --detach ~/.local/share/codemem-plugin-wt main` (9546a2e), `ln -sfn` → `~/.local/share/codemem-plugin`, `uv sync --locked`; `claude mcp add -s user codemem -- <link>/.venv/bin/python <link>/claude-code/codemem/mcp/server.py` (forge keeps its project-scope entry); `~/.config/git/ignore` += `.codemem/`, `graphify-out/`. Proof: fresh second repo, `claude -p` (haiku, $0.017) → `search_symbols greet` answered (app.py:1) via the user-scope server; `git status --porcelain` empty with `.codemem/` present. X2 fields absent there until merge + install.sh re-points the worktree (it runs main's pre-M15 code). M10 Contract + 10.6 AC record the resolution order (`CODEMEM_BIN` → forge venv → `~/.local/share/codemem-plugin/.venv/bin/codemem` → absolute PATH). Full: pytest 3052/5/7, bats 607 rc 0.

### Sub-step 15.9: Routing rule + graphify trigger (T8)
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 15.8
- Acceptance Criteria:
  - `~/.claude/rules/code-intel-routing.md` per report 03 §5 + R03-D10 table (Python → codemem only after parity; others as tabled), naming `~/biorelate/**` and client repos code-only (R03-D14); never cite INFERRED/AMBIGUOUS graphify edges as evidence.
  - `GRAPHIFY_QUERY_LOG_DISABLE=1` in the shell env (`env | grep GRAPHIFY_QUERY_LOG_DISABLE`); graphify skill description narrowed (`grep -c 'any question about a codebase' ~/.claude/skills/graphify/SKILL.md` prints 0); graphify's PreToolUse hook-guard not installed.
- Result Log: Mode HITL — Ste: Approve as drafted (preview). Outside repo, covered by backup `cci-m15-20261014T100926Z.tgz`: `~/.claude/rules/code-intel-routing.md` written (1,736 chars: report 03 §5 table, R03-D10 language routing, INFERRED/AMBIGUOUS never evidence, stale → leads + CODE_INTEL_STALE, `~/biorelate/**` + client repos graphify code-only (R03-D14), no hook-guard); graphify SKILL.md description narrowed (`grep -c 'any question about a codebase' ~/.claude/skills/graphify/SKILL.md` = 0; live in the session skill listing); `~/.bashrc` += `export GRAPHIFY_QUERY_LOG_DISABLE=1` (`bash -ic 'env | grep GRAPHIFY_QUERY_LOG_DISABLE'` → `=1`; graphify 0.9.85 `querylog.py:24` honours it and it wins over opt-in logging); no graphify PreToolUse hook in settings.json (only the `gsd-graphify: off` skill override). L-1315 isolated probe (`claude -p`, haiku, $0.015): the rule is loaded and its INFERRED/AMBIGUOUS bullet quoted verbatim. Note: graphify is a pipx install; `graphify install` / upgrade rewrites SKILL.md → TODOS (re-narrow after upgrades).

### Sub-step 15.10: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 15.6, Sub-step 15.7, Sub-step 15.9
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — hook-modification — <evidence>`, naming the bats/test names, where the heading is verbatim: Milestone 15: Codemem freshness (report 03 T2–T9)
- Result Log:

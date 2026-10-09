# code-conventions-impact Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

> Gate fields on each milestone are the ones `aa-ma-gate` reads (it takes only
> `tasks_md`). They copy plan.md §2a, which is the single source. A field whose
> §2a value is "—" is omitted; a field is never written with an empty value
> (the gate refuses it, exit 2). Acceptance criteria apply the plan's
> Precedence rule (plan.md §5): §0 Security hardening (v2) > §8 Standing rules
> (v2) > a milestone's Verification amendments > its Contract text > step prose.
>
> Numbering notes: post-merge work of milestone N-1 is Sub-step N.0 (§8 standing
> rule). Plan step 8.4a is Sub-step 8.5 here (the canonical heading grammar
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
  - `tests/skills/test_no_command_skill_collision.py` and `tests/skills/test_model_invocation_list.py` pass (exactly {sole-dev-merge, aa-ma-share} carry `disable-model-invocation`).
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
  - `disable-model-invocation: true` on sole-dev-merge and aa-ma-share only (D9 revised); descriptions scoped to explicit requests; `test_model_invocation_list.py` passes.
  - The 31 test files referencing `commands/` paths updated; `plugin_surface.py` `_DIRS/_resolve` (`/x` → skills/x; `/x-*` globs over skills); `tests/fixtures/draw-node-ids.json` `command:*` → `skill:*`; `test_frontmatter_at_top.py::test_surfaces_are_not_empty` no longer requires `commands/`.
  - Also updated: `claude-code/rules/engineering-standards.md:66` (hook-modification scope drops `claude-code/commands/**`); docs/spec/aa-ma-specification.md:183, :911; foundations :34; `examples/**/aa-ma-team-guide-reference.md:69`; comments in `aa-ma-footer.sh:5` and `aa-ma-chart-guard.sh:18`.
  - `uv run pytest` count ≥ baseline minus the deleted command-only tests (listed by name in the Result Log); all bats green; `git grep -n 'commands/'` shows only history/docs (logged).
- Result Log: Mode: AFK — auto-dispatched. Baseline pytest 2482 passed / 7 skipped. Commits: dbb02d4 RED (`test_a_slash_glob_expands_over_skills_too`) → 256237f format-only (D8: 6 touched files + plugin_surface.py were not ruff-clean at HEAD; split out so the path edits review as 17 lines) → d83f8ac GREEN (`_resolve`: `/x-*` expands over commands, then skills) → 210ca3f the move. `git mv` ×11 to `claude-code/skills/<name>/SKILL.md`; `name:` added to ops-mode, sole-dev-merge; `disable-model-invocation: true` on sole-dev-merge + aa-ma-share; each description gains its explicit-request clause; readlink in aa-ma-plan:579 / aa-ma-share:31 → `readlink -f ~/.claude/skills/<x>/SKILL.md` + `/../../..` (verified in a fake HOME: resolves to the checkout root). New `tests/skills/test_model_invocation_list.py` (2 tests). Paths updated in 25 test files by a literal rewrite + 3 path-joined forms by hand (`test_understand_codebase_xrefs.py`, `test_aa_ma_share_command.py` COMMAND_MD, `test_angle6_coverage.py` home fixture → dir symlinks as install makes them); the rewrite also hit one SYNTHETIC tmp-tree fixture in `test_bold_markdown_after_a_command_is_not_a_glob` — reverted, every other hit audited as a real repo path. `test_frontmatter_at_top.py`: commands/ dropped from SURFACES (moved files now meet the stricter skills `name`+`description` rule). Also: engineering-standards.md:66 scope, spec :183/:911, foundations :34, examples team-guide :69, aa-ma-footer.sh:5, aa-ma-chart-guard.sh:18, TODOS.md (3 open items), plan §13 EXM/SDM stale `(new)` dropped. `tests/fixtures/draw-node-ids.json` has no `command:*` ids (only `tests/commands/…` file paths) → no change; plan assumption was wrong. Regenerated golden + docs/architecture via `scripts/regen-generated.sh`. Test files referencing `commands/` (W2, 32 at 2ea2ed2): tests/codemem/test_plugin_surface.py, tests/assets/test_understand_codebase_xrefs.py, tests/commands/{test_aa_ma_share_command,test_planning_standard_count,test_understand_codebase_command}.py, tests/commands/sole-dev-merge/{fixtures/extract_stage.sh, test_smoke_e2e, test_stage_a_preflight, test_stage_b_scope, test_stage_c_dispatch, test_stage_d_triage, test_stage_e3_body, test_stage_e_remote, test_stage_f_idempotent, test_stage_g_merge, test_stage_g_poll}.bats, tests/hooks/{aa-ma-chart-guard, aa-ma-deps, aa-ma-gate-python, aa-ma-gate-scans, execute_aa_ma_milestone_phase_6_8, test_diagram_verified, install_dry_run}.bats, tests/skills/{test_angle6_coverage,test_understand_codebase_rewire}.py, tests/test_{active_plans_canonical,doc_counts,frontmatter_at_top}.py, plus fixture/golden JSON (draw-node-ids, onboarding schema/fixtures — unrelated `commands` keys). Results: pytest 2488 passed / 5 failed — all 5 are count sites deferred to 3.5 by plan (`test_command_count_sites_match_disk`, `test_security_md_asset_lists_match_disk`, `test_foundations_count_headings_match_disk`, `test_plugin_asset_counts_match_the_tree[commands]`, `[skills]`); 0 tests deleted. bats -r tests 366/366. Coverage audit: only `test_the_backticked_rule_loses_no_edge_the_any_occurrence_rule_found` (frozen pre-M6 command rule) goes vacuous once commands/ is empty — superseded by the skill-glob test; decide delete-or-keep in 3.5. `git grep 'commands/'` on live files: remaining hits are 3.5 (SECURITY.md:11,27; install.sh command loops :128,:308), the sweep itself, generic `.claude/commands` concepts (RULES-FILES.md:44, foundations :34, uninstall comment), sole-dev-merge's upgrade note, plugin_surface docstring; history (ADRs, research, CHANGELOG, docs/plans) untouched. Diagram lint: edges=25 checked=25 phantom=0 invalid=0.

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
- Status: PENDING
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

### Sub-step 4.0: Post-merge of M3
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M3 merged; `git pull` on main; live `scripts/install.sh` from main (Ste confirms).
  - For each of the 13 `/names`, an isolated `claude -p "/<name> --help-like no-op" </dev/null` probe (L-1322 prompt-first): 13/13 resolve; no stdout contains `Unknown skill` or `Unknown command`.
  - `ls ~/.claude/commands/ | wc -l` drops by 14 (13 moved + grill-me); provenance logs `COMMANDS pre=N post=N-14`; `~/.claude/skills/grill-me` still points to `~/.agents/…`.
  - Worktree for M4 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 4.1: Frontmatter schema (TDD)
- Status: PENDING
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
- Result Log:

### Sub-step 4.2: Size ratchet (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 4.1
- Acceptance Criteria:
  - `tests/test_prompt_size.py`: body ≤500 lines; ALLOWLIST holds ceilings at current size for the 6 oversized files (may only fall).
  - TOC rule touched-only: a `references/*.md` >100 lines that is new or modified vs merge-base needs a TOC; the 23 existing >100-line references without one are in `TOC_ALLOWLIST`.
  - The test passes at current sizes; a fixture adding 1 line to an allowlisted file fails.
- Result Log:

### Sub-step 4.3: Eval harness proof
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 4.2
- Acceptance Criteria:
  - Proven (or disproven) that `claude plugin eval` targets `claude-code/skills/<x>` with no `plugin.json` (A2); always run with `--no-publish`, `--runs 1`, no ablation arm; eval-dir placement settled; cost of one case logged.
  - Fallback if it fails: `claude -p "<prompt>" … </dev/null` (L-1322).
  - One case runs end to end, producing one JSONL result line with `rc` and `verdict` fields; the chosen mechanism is recorded in the ADR/context-log.
- Result Log:

### Sub-step 4.4: writing-for-agents fork
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 4.3
- Acceptance Criteria:
  - `claude-code/skills/writing-for-agents/` is a verbatim fork of mattpocock/skills @ c55ee46, fetched with `gh api repos/mattpocock/skills/contents/…?ref=<40-hex of c55ee46>` with sha256 recorded, never from the plugin cache; upstream MIT `LICENSE` in the fork dir; `## In this repo` block added (T15 conventions + surviving write-a-skill sections).
  - `claude-code/skills/write-a-skill/` deleted; FORKS.json + writing-for-agents − write-a-skill; not invoked by AA-MA Phase 5 writers (writing-for-agents-eval T4).
  - `docs/adr/NNNN-writing-for-agents-fork.md` `Status: Accepted` (supersedes ADR-0004) + INDEX row + context-log approval; `docs/adr/0004-write-a-skill-adoption.md` marked `Superseded by NNNN`.
  - README:255, SECURITY.md:12, foundations:113, the orphan set in `test_plugin_surface.py:113-119` updated; golden regenerated.
  - `test_fork_manifest` passes; `git grep write-a-skill` hits only ADRs/history. The L-1315 probe listing `writing-for-agents` is deferred to Sub-step 5.0 (standing rule: live probes run post-merge).
- Result Log:

### Sub-step 4.5: Eval cases + sandboxed runner
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 4.4
- Acceptance Criteria:
  - 24 cases `evals/<skill>/<case>/case.yaml`, 3 each for execute-aa-ma-milestone, execute-aa-ma-step, execute-aa-ma-full, aa-ma-plan, plan-verification, impact-analysis, logging-and-comments, writing-for-agents.
  - `scripts/run-evals.sh`: each case in a throwaway fixture repo (`mktemp -d`, `git init`, no remote); `git push`, `gh` and network tools denied via `--disallowedTools`; `--allowedTools` allowlist; `env -i` with PATH + Claude auth only (SSH_AUTH_SOCK, GH_TOKEN, GITHUB_TOKEN unset); HOME-scoped writes refused; results → `.claude/evals/<YYYY-MM-DD>.jsonl` (gitignored) + one summary line; exit 0 always with rc in the last line.
  - `tests/scripts/test_run_evals_sandbox.bats` passes: a case trying `git push` fails; the fixture repo has no remote; a case writing `$HOME/.probe` leaves it absent; a test asserts run-evals.sh never uses `bypassPermissions` or `--dangerously-skip-permissions`.
  - `scripts/release.sh` runs `run-evals.sh` advisorily and prints the summary.
  - `scripts/run-evals.sh` runs all 24 and reports pass/fail; results logged, not gated.
- Result Log:

### Sub-step 4.6: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 4.5
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 4: Prompt-as-code checks + writing-for-agents fork — version-pipeline — <evidence>`, naming the `scripts/release.sh` change, the sandbox bats name and the eval summary line.
- Result Log:

---

## Milestone 5: Split the six oversized prompt files (behaviour-preserving)
- Status: PENDING
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

### Sub-step 5.0: Post-merge of M4
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M4 merged; `git pull` on main; live `scripts/install.sh` from main (M4 changed the skill set: + writing-for-agents, − write-a-skill).
  - L-1315 isolated probe lists `writing-for-agents` (deferred from 4.4).
  - Worktree for M5 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 5.1: Split aa-ma-execution (1295 lines)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.0
- Acceptance Criteria:
  - `tests/test_split_preserves_content.py` created: for each split file, multiset(non-blank lines of the pre-split file @ base SHA) ⊆ multiset(lines of SKILL.md ∪ references/*.md); added lines are only link/TOC lines matching `^\s*[-*] \[.+\]\(.+\)$|^#+ |^>? ?See .*\]\(references/`.
  - `claude-code/skills/aa-ma-execution/SKILL.md` ≤500 lines; each reference opens with its one-line purpose.
  - `test_split_preserves_content` and the full suite + all bats pass for this file; committed.
- Result Log:

### Sub-step 5.2: Split execute-aa-ma-milestone (1244 lines)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.1
- Acceptance Criteria:
  - SKILL.md ≤500 lines; §6.7 fences STAY in SKILL.md (bats `_gate_fence` extracts by heading).
  - Text pinned by `execute_aa_ma_milestone_phase_6_8.bats` (10 greps), `aa-ma-deps.bats` and `aa-ma-gate-scans.bats:155` stays in SKILL.md or the test moves in the same commit.
  - `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log:

### Sub-step 5.3: Split aa-ma-plan (1154 lines)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.2
- Acceptance Criteria:
  - SKILL.md ≤500 lines; `test_planning_standard_count` SITES ("ALL 13 elements") stay findable.
  - `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log:

### Sub-step 5.4: Split sole-dev-merge (1054 lines)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.3
- Acceptance Criteria:
  - SKILL.md ≤500 lines; stage fences referenced by `tests/commands/sole-dev-merge/*.bats` and `fixtures/extract_stage.sh` stay in place or the tests follow in the same commit.
  - `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log:

### Sub-step 5.5: Split execute-aa-ma-full (757 lines)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.4
- Acceptance Criteria:
  - SKILL.md ≤500 lines; `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log:

### Sub-step 5.6: Split plan-verification (608 lines)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.5
- Acceptance Criteria:
  - SKILL.md ≤500 lines; `test_split_preserves_content` and the full suite + all bats pass; committed.
- Result Log:

### Sub-step 5.7: Empty the size allowlist
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.6
- Acceptance Criteria:
  - `tests/test_prompt_size.py` passes with an empty ALLOWLIST.
  - M4 evals re-run for the 4 affected skills with cases (execute-aa-ma-milestone, execute-aa-ma-full, aa-ma-plan, plan-verification); delta logged (advisory; Risk 3 mitigation).
- Result Log:

### Sub-step 5.8: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.7
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 5: Split the six oversized prompt files (behaviour-preserving) — hook-modification — <evidence>`, naming `test_split_preserves_content`, the fence bats and the suite counts.
- Result Log:

---

## Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3)
- Status: PENDING
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
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M5 merged; `git pull` on main (M5 changed no install.sh, hooks, rules or skill set, so no `install.sh` run is needed; recorded in the Result Log).
  - Worktree for M6 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 6.1: Ruff docstring/KISS config (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 6.0
- Acceptance Criteria:
  - `pyproject.toml` `[tool.ruff.lint]`: extend-select += D, RUF100, PGH003, PGH004, C901, PLR0913; TD kept; pydocstyle convention `google`; extend-ignore `D107` and `TD003`, each with a `# why:`; mccabe max-complexity 10; pylint max-args 6; PLR2004 not selected; the D101–D104 parked list and its `TODO(logging-std)` (:81-83) deleted.
  - D417 verified enabled under google (`ruff --show-settings`), or enabled explicitly.
  - Fixtures: undocumented public function fails D103; complexity 11 fails C901; `# noqa: E501` on a clean line fails RUF100; undocumented argument fails D417.
  - Ruff rules apply file-level (D8); run `regen-generated.sh` if docs/architecture changes.
- Result Log:

### Sub-step 6.2: WHY001 / TODO001 (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 6.1
- Acceptance Criteria:
  - WHY001: an added line with a suppression (Python `# noqa`, `# type: ignore` from tokenize COMMENT tokens only; Bash `|| true`, `2>/dev/null` outside comments and heredocs) without `# why:` on the same line or the line above. TODO001: an added TODO/FIXME without a `(#\d+|ADR-\d{4})` reference. Markdown, strings and docstrings never scanned; added/modified lines only.
  - `.pre-commit-config.yaml` shellcheck args `--enable=check-extra-masked-returns,check-set-e-suppressed`.
  - Tests pass: positive + negative cases (noqa inside a string, a heredoc, a markdown file → no finding); `TODO(ADR-0021): x` passes TODO001.
- Result Log:

### Sub-step 6.3: code-reviewer WARN rules
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 6.2
- Acceptance Criteria:
  - `claude-code/agents/code-reviewer.md` WARNs (never CRITICAL) on: what-comments restating code; missing why on non-obvious logic; docstring claims the code lacks; unjustified suppression; unnamed magic constant (any count); MUST/NEVER/ALWAYS in touched markdown with no why-or-pointer (T15 §6). The `:91` style-nit ban is kept.
  - An eval case for code-reviewer WARN on a what-comment is added (advisory run).
- Result Log:

### Sub-step 6.4: Canary PR
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 6.3
- Acceptance Criteria:
  - A draft PR adding an undocumented function + a bare `|| true` fails `touched` with D103 + WHY001; run URL logged in provenance; PR closed and branch deleted.
- Result Log:

### Sub-step 6.5: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 6.4
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3) — hook-modification — <evidence>`, naming the test names and the canary run URL.
- Result Log:

---

## Milestone 7: Logging standard (T9) + hook contracts (T15 §7)
- Status: PENDING
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

### Sub-step 7.0: Post-merge of M6
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M6 merged; `git pull` on main (M6 changed no install.sh, hooks, rules or skill set, so no `install.sh` run; recorded in the Result Log).
  - Worktree for M7 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 7.1: aa-ma-log.sh + bats (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.0
- Acceptance Criteria:
  - `claude-code/hooks/lib/aa-ma-log.sh`: `log_info|log_warn|log_error|log_debug <hook-name> <msg>` append `<date -Is> LEVEL <hook-name>: <msg>` to `${AA_MA_HOOK_LOG:-~/.claude/logs/hooks.log}`; `log_debug` only when `HOOK_DEBUG=1` (also stderr); `log_*` always masks and strips CR/LF.
  - `fail_open_notice <hook-name> <msg>` prints `{"systemMessage": "..."}` to stdout, built with `jq -n --arg`, plus a `log_warn` line (L-1319).
  - `mask_secrets <text>`; the bash and Python pattern sets are generated from one source file, with a parity test.
  - `aa-ma-parse.sh` sources it from its own directory; `aa_ma_debug` becomes a thin wrapper over `log_debug`; `install.sh` symlinks `hooks/lib/aa-ma-log.sh` (lib list :331-346); `uninstall.sh` removes it.
  - `tests/hooks/aa-ma-log.bats` passes (format, stderr/stdout split, systemMessage JSON shape, masking); injected `"` in payload data leaves `jq 'paths'` with only the expected keys; stdout passes `jq empty`.
- Result Log:

### Sub-step 7.2: logsetup.py (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.1
- Acceptance Criteria:
  - `src/aa_ma/logsetup.py`: `configure_logging(verbosity: int = 0, fmt: Literal["text","json"] | None = None) -> None` (LOG_LEVEL / LOG_FORMAT env; -v/-q mapping; stderr handler); `class SecretRedactingFormatter(logging.Formatter)` at handler level (covers child loggers, `exc_text` and stack traces; §0 v2 governs over the amendment's "Filter" wording); `SECRET_PATTERNS: tuple[re.Pattern[str], ...]`.
  - Input capped at 8 KB before matching; each pattern has a 100 KB adversarial timing test.
  - `.importlinter` + `tests/render/test_leaf_contract.py`: `aa_ma.logsetup` added to `render-is-leaf`, `analysis-is-leaf` and the forbidden list of `analysis-is-self-contained`.
  - `tests/test_logsetup.py` passes: an API-key-shaped string in a log record is masked; with a pattern monkeypatched to raise, `record.getMessage() == "[redaction failed]"` (fail closed, never leaks, never drops).
- Result Log:

### Sub-step 7.3: Migrate the hooks
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.2
- Acceptance Criteria:
  - Every `claude-code/hooks/*.sh` carries the header contract (Event, Blocking|Advisory, exit codes 0 / 2 and never 1 for a policy decision, fail-open behaviour); the bats header loop passes.
  - `aa-ma-plan-skip-warn.sh` uses `HOOK_DEBUG`; `AA_MA_PLAN_MARKER_DEBUG` kept one release as an alias printing a deprecation notice; `docs/spec/plan-marker-grammar.md:207` alias note updated.
  - `pre-compact-aa-ma.sh` `warn_append` → aa-ma-log.sh; compaction.log folds into hooks.log; `pre-compact.bats:110` path updated.
  - `git grep -n 'AA_MA_PLAN_MARKER_DEBUG\|VERBOSE\|\bDEBUG=' claude-code/` returns only the alias line.
- Result Log:

### Sub-step 7.4: ruff hook additionalContext (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.3
- Acceptance Criteria:
  - `ruff-format.sh` (PostToolUse): ruff check findings for the edited file → `hookSpecificOutput.additionalContext` (≤10 lines); own failures → `log_error`; never blocks; ruff not on PATH → one `fail_open_notice` per session.
  - ruff resolved ONLY from the forge root (`readlink -f` on the hook → `<forge>/.venv/bin/ruff`) or PATH, never from the edited repo (Security v2 CRITICAL).
  - bats: captured payload → additionalContext JSON asserted; a fixture repo with a tracked `.venv/bin/ruff` that writes a sentinel file → sentinel never created; ruff stripped from PATH → exactly 1 `systemMessage` per session_id.
  - The LIVE transcript check is deferred to Sub-step 8.0.
- Result Log:

### Sub-step 7.5: Captured payload fixtures
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.4
- Acceptance Criteria:
  - One fixture per registered hook event in `tests/fixtures/hook-payloads/`, captured live (not hand-written), each keeping its real `session_id`/`transcript_path`.
  - Every hook's bats is fed a real captured payload.
  - `provenance.log` has a `PAYLOAD_CAPTURED <event>` line per event.
- Result Log:

### Sub-step 7.6: Revise logging skills
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.5
- Acceptance Criteria:
  - `logging-and-comments`: NullHandler optional + why; JSON for services, opt-in elsewhere; `HOOK_DEBUG`/`LOG_LEVEL` only (VERBOSE/DEBUG removed); strict-mode + BashFAQ/105 caveats; hooks.log format; pino → fd 2 note.
  - `bash-defensive-patterns/SKILL.md`: bracketed log example → hook-log format; strict-mode caveats.
  - M4 evals for logging-and-comments re-run; delta logged.
- Result Log:

### Sub-step 7.7: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 7.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 7: Logging standard (T9) + hook contracts (T15 §7) — hook-modification — <evidence>`, naming the bats/test names.
- Result Log:

---

## Milestone 8: SecOps CI baseline (T10)
- Status: PENDING
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

### Sub-step 8.0: Post-merge of M7
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M7 merged; `git pull` on main; live `scripts/install.sh` from main (M7 changed hooks); `readlink -f ~/.claude/hooks/lib/aa-ma-log.sh` resolves into the main checkout.
  - Live check (deferred from 7.4): a live edit that introduces F401 shows the finding in the next turn's context; the transcript line is logged.
  - Worktree for M8 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 8.1: Pinned Ruff-vs-Bandit comparison
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 8.0
- Acceptance Criteria:
  - `docs/research/code-conventions-impact-ruff-vs-bandit.md`: every Bandit test ID → Ruff S code or GAP at ruff 0.15.9 / bandit 1.9.4 (venv-pinned, M1.2), run on this repo; a table of every Bandit ID that fired, with its Ruff mapping.
  - Records Ruff `S404` as preview-only at 0.15.9 while Bandit B404 fires 10×, deciding whether the fallback ID list includes B404 (A4).
  - context-log has `DECISION ruff-only|fallback (<ids>) — approved by Ste`.
- Result Log:

### Sub-step 8.2: Ruff S on + CI security jobs
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 8.1
- Acceptance Criteria:
  - `pyproject.toml` extend-select += S; the ONLY S ignore is `tests/**` S101, asserted by a test; S603/S607 sites get per-site `# noqa: S60x  # why:` (34-finding baseline triaged: fix or noqa+why).
  - `security.yml`: job `bandit` removed (or, on the fallback decision, `uv run bandit -t <GAP ids> -ll -r src packages` with no `|| true`; carried defect 3); job `ruff-security` runs `uv run ruff check --isolated --select S src packages scripts` on push to main + weekly schedule.
  - `tests/security/test_canary.py`: a canary file with `shell=True` + a fake AWS key under `tests/fixtures/canary/` (secret assembled at runtime by concatenation, never a literal; the canary exclusion names one file) is flagged by Ruff S when scanned explicitly.
  - `ruff check --select S src packages scripts` exits 0; the canary test passes.
- Result Log:

### Sub-step 8.3: gitleaks
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 8.2
- Acceptance Criteria:
  - CI job `gitleaks`: v8.18.4 from the tarball with sha256 verified; `gitleaks detect --redact --exit-code 1 --log-opts="--all"`; checkout `fetch-depth: 0`.
  - `.gitleaksignore` holds fingerprint entries (commit:file:rule:line) for the 3 fixture hits (tests/analysis/test_measure.py, tests/hooks/security-static-check.bats), each preceded by a `# why:` line; a test asserts that; no path or regex allowlists; Ste reviews the allowlist.
  - `.pre-commit-config.yaml` + gitleaks (staged), rev frozen to a SHA.
  - The full-history scan exits 0; a canary commit in a LOCAL `mktemp -d` repo fails `gitleaks detect --source <tmp>`; no canary secret is ever pushed (A5).
- Result Log:

### Sub-step 8.4: deps job + Dependabot
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 8.3
- Acceptance Criteria:
  - Job `deps`: `uv sync --locked && uv export --frozen --no-emit-workspace --no-emit-project -o req.txt` (hashed) `&& uv run pip-audit --disable-pip --require-hashes --strict -r req.txt`; pip-audit locked in the dev group; a test fails any ignore past its expiry date.
  - `.github/dependabot.yml`: github-actions + uv, weekly, `cooldown: 7` days.
  - All jobs use `astral-sh/setup-uv@<sha>` (`version: 0.12.3`) instead of `pip install uv`, `uv sync --locked`, `persist-credentials: false`; pre-commit `rev:`s frozen to SHAs.
  - All jobs except `deps` are green; `deps` goes green after Sub-step 8.5; A6 resolution logged.
- Result Log:

### Sub-step 8.5: Triage the 13 vulnerable packages (plan 8.4a)
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 8.4
- Acceptance Criteria:
  - For each of the 13 packages (12 with `--no-dev`: pyjwt, starlette, urllib3, mcp, fastmcp, cryptography…): `uv lock --upgrade-package <pkg>`, or an ignore entry with ID, why and expiry date.
  - The `deps` job exits 0 on the branch; the triage table is in `docs/research/code-conventions-impact-ruff-vs-bandit.md` §deps.
- Result Log:

### Sub-step 8.6: Commit hook → forge-pinned Ruff S (blocking) + Stage C (plan 8.5, TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 8.5
- Acceptance Criteria:
  - `security-static-check.sh` (D12, BLOCKING): forge-pinned `ruff check --isolated --select S602,S604,S307,S608,S301` on staged .py + secret-literal and path-traversal regexes; exit 2 on findings in ANY repo; regex classes Ruff covers retired; no ruff → `fail_open_notice` + exit 0, never a silent pass.
  - sole-dev-merge Stage C3: Ruff S replaces Bandit; `BANDIT_BIN` retired (CLAUDE.md bypass table is a local edit); a missing scanner still writes `[HIGH] … UNKNOWN`; Stage D auto-fix reads Ruff S JSON (:443-531) with `test_stage_d_triage.bats` and `test_smoke_e2e.bats:209` updated; the security.yml bats-job Bandit (:103-107) removed.
  - Contract text naming the hook's classes updated in `agents/security-auditor.md:3,7`, verify-impl :205/:211, execute-aa-ma-milestone :793/:857, spec :145, foundations :157.
  - `tests/hooks/security-static-check.bats` passes: S602 fixture exit 2; secret literal exit 2; no-ruff notice exit 0. A `RUFF_BIN=/nonexistent` bats case greps the findings file for `[HIGH].*UNKNOWN`; sole-dev-merge bats pass.
- Result Log:

### Sub-step 8.7: Skills secops / secrets-management / defense-in-depth; remove global senior-secops (plan 8.6)
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 8.6
- Acceptance Criteria:
  - `claude-code/skills/secops/SKILL.md` thin router (Ruff S, gitleaks, pip-audit / uv audit once GA, ShellCheck, osv-scanner for JS/R lockfiles; cites ASVS 5.0, OWASP Top 10:2025, NIST SSDF with no 1.2 practice IDs); eval-first: 3 cases committed before SKILL.md.
  - `secrets-management`: gitleaks primary, TruffleHog `--fail` + digest pin as alternative (FORKS state → derived). `defense-in-depth`: validate once at trust boundaries into typed values; cheap asserts deeper; LLM output untrusted (→ `Skill(llm-output-safety)`).
  - Outside repo (D3): `~/.claude/skills/senior-secops` backed up (tgz count verified) and removed; `settings.json:295 "off"` override left alone (L-1210); `ls ~/.claude/skills/senior-secops` reports absent.
  - Counts skills +1 (secops); golden regenerated; `docs/adr/NNNN-secops-baseline.md` `Status: Accepted` + INDEX row + context-log approval.
  - The L-1315 probe listing `secops` is deferred to Sub-step 9.0 (standing rule).
- Result Log:

### Sub-step 8.8: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 8.7
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — Milestone 8: SecOps CI baseline (T10) — hook-modification — <evidence>`, naming the bats/test names and the CI run URLs (ruff-security, gitleaks, deps).
- Result Log:

---

## Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5)
- Status: PENDING
- Dependencies: Milestone 8
- Complexity: 60%
- Effort: 1.5 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `tests/hooks/test_tests_verified.bats` passes (pass writes line; failing suite exit 1 with no line; missing summary exit 1; custom Test-Command honoured; banner line; `-q` line; opt-out; rc 5).
  - `aa-ma-gate-python.bats` and `test_diagram_verified.bats` stay green unchanged.
  - `tests/test_tdd_waiver_doc_sync.py` passes.
  - `! grep -nE 'coverage gate|perf job' pyproject.toml` succeeds.
  - `docs/adr/NNNN-tests-verified-gate.md` has `Status: Accepted` + INDEX row + context-log approval.
  - This plan's reference.md carries `Test-Command: uv run pytest`.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 9.

### Sub-step 9.0: Post-merge of M8
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M8 merged; `git pull` on main; live `scripts/install.sh` from main (M8 changed the commit hook and the skill set); `readlink -f ~/.claude/hooks/security-static-check.sh` resolves into main and the live hook contains the forge-pinned Ruff S invocation.
  - L-1315 probe lists `secops` (deferred from 8.7).
  - Worktree for M9 cut from fresh main; `uv sync && uv run codemem build` exit 0.
- Result Log:

### Sub-step 9.1: Fence 3 TESTS_VERIFIED (bats first, TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 9.0
- Acceptance Criteria:
  - Fence 3 is its OWN bash block after the DIAGRAM_VERIFIED block in `claude-code/skills/execute-aa-ma-milestone/SKILL.md` §6.7, never inside the first §6.7 block; it replaces comment-only conditions 3 (:604) and 4 (:605).
  - TEST_CMD = the `Test-Command:` value in the MERGE-BASE copy of `<task>-reference.md` (`git show $base:…`), else `uv run pytest`; printed, then run as a shlex argv (no `bash -c`); the characters ; | & $ backtick < > are rejected.
  - Timeout `${AA_MA_TEST_TIMEOUT:-540}` s. PASS iff rc==0 AND the final non-empty line, after `sed -E 's/^=+ //; s/ =+$//'`, matches `(^|, )([0-9]+) passed` → append `[ts] TESTS_VERIFIED — <milestone heading> — passed=N cmd=<TEST_CMD>`; else `BLOCKED: tests …` exit 1 with no provenance line.
  - Opt-out (D10): `Test-Command: none — <reason>` (needs a context-log GATE APPROVAL) → `TESTS_VERIFIED — <milestone> — skipped: <reason>`; pytest rc 5 without that line → BLOCKED, naming the opt-out.
  - §6.7 summary prints the real count of conditions (no fixed "all 5").
  - `tests/hooks/test_tests_verified.bats` passes all cases; `aa-ma-gate-python.bats:45` and `test_diagram_verified.bats:127` green unchanged.
- Result Log:

### Sub-step 9.2: TDD-waiver regen target (TDD)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 9.1
- Acceptance Criteria:
  - `claude-code/rules/engineering-standards.md` §2 TDD text is a marker-delimited block regenerated from `plan_parsers.CANONICAL_TDD_WAIVERS` by a new target in `scripts/regen-generated.sh` (no new script); "infrastructure-only" → `tooling-config`; `refactor` requires existing tests to stay green; `hotfix-emergency` requires a follow-up test task.
  - `tests/test_tdd_waiver_doc_sync.py` passes (the rule block equals the regenerated text).
- Result Log:

### Sub-step 9.3: Delete unbacked pyproject claims
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 9.2
- Acceptance Criteria:
  - The `:49` "≥90% coverage gate" and `:121` "CI perf job" claims removed (P5); `! grep -nE 'coverage gate|perf job' pyproject.toml` succeeds.
- Result Log:

### Sub-step 9.4: ADR + spec/template/scribe updates
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 9.3
- Acceptance Criteria:
  - `docs/adr/NNNN-tests-verified-gate.md` `Status: Accepted` + INDEX row + context-log approval.
  - `docs/templates/reference-template.md` gains the `Test-Command:` line; `claude-code/agents/aa-ma-scribe.md` copies `Test-Command:` into reference.md; `docs/spec/aa-ma-specification.md:183-188` (§6.7/§6.8 table) updated.
- Result Log:

### Sub-step 9.5: Dogfood Test-Command
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 9.4
- Acceptance Criteria:
  - `code-conventions-impact-reference.md` has the line `Test-Command: uv run pytest` (met within M9). Because of D7, fence 3 goes live after the M9 merge + install, so the provenance check moves to Sub-step 10.0 / the Milestone 10 gate.
- Result Log:

### Sub-step 9.6: Re-run execute-aa-ma-milestone evals
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 9.5
- Acceptance Criteria:
  - M4 evals for execute-aa-ma-milestone re-run (advisory); delta logged (CEO F13).
- Result Log:

### Sub-step 9.7: CRITICAL_PATH_REVIEW
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 9.6
- Acceptance Criteria:
  - `provenance.log` has `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — hook-modification — <evidence>`, naming the bats/test names, where the heading is verbatim (backticks included): Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5)
- Result Log:

---

## Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper)
- Status: PENDING
- Dependencies: Milestone 9
- Complexity: 75%
- Effort: 3 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - `provenance.log` has a `PROTOTYPE —` line naming this milestone's heading verbatim, with `verdict-changes-plan: YES|NO`; hook p95 latency ≤1.5 s logged.
  - `provenance.log` has a `TESTS_VERIFIED` line for Milestone 10, written by the live fence 3 at this milestone's gate (first live run).
  - `tests/codemem/test_callees.py`, `test_co_changes.py`, `test_aa_ma_context.py`, `test_file_impact.py`, `test_plugin_surface_index.py`, `tests/test_gitutil_contract.py`, `tests/codemem/test_critical_path_globs.py` and `tests/hooks/aa-ma-impact-preedit.bats` pass.
  - `codemem query who_calls impact-analysis` lists skill callers; `uv run pytest -m perf` stays within budget.
  - `docs/adr/NNNN-impact-preedit-hook-and-callees.md` has `Status: Accepted` + INDEX row + context-log approval.
  - `provenance.log` has a `CRITICAL_PATH_REVIEW` line for Milestone 10.

### Sub-step 10.0: Post-merge of M9
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - M9 merged; `git pull` on main; live `scripts/install.sh` from main; the live `~/.claude/skills/execute-aa-ma-milestone/SKILL.md` contains fence 3 (TESTS_VERIFIED).
  - Recorded: `TESTS_VERIFIED` must appear for Milestone 10 at its own gate (checked by the milestone acceptance criteria).
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

# codebase-analysis-skills Context Log

## [2026-09-27] Initial Context

**Feature Request:** `/aa-ma-plan --from-map codebase-analysis-skills` — ship a clean-room whole-repo assessment skill (`assess-codebase`, successor to Ste's local `/codebase-deep-dive`) and an improved `understand-codebase`, per the cleared charting map (12/12 tickets RESOLVED, imported as `codebase-analysis-skills-map.md`).

**Key Decisions (grill, with Ste, 2026-09-27 — on top of the map's 12 tickets):**
- Git: plan artifacts on `main`; one branch + PR per milestone via `/sole-dev-merge`.
- Prototype-Required: M1 (analysis schemas), M2 (assess core), M5 (incremental regeneration).
- Rating: rubric + numeric anchors in `references/RATING.md`; a dimension whose core measured input is UNKNOWN can never be Strong.
- Models: sonnet judge agents; refuter inherits the session model.
- Code home: new leaf package `src/aa_ma/analysis/` + `aa-ma-analysis` CLI (pydantic models are the schemas); both skills call it via `AA_MA_ROOT`.
- R4 extractor: backticked unresolved `/x` → DECLARED_EXTERNAL or DANGLING; local-only user commands are DANGLING and fixed.
- Eval public repo: `honojs/hono`, SHA-pinned.
- Running repo commands: approve list + refuse installers + offline env + timeout (best-effort, stated).
- Engineering standards: all six themes apply.

**Key Decisions (brainstorm/design, Ste approved):** 8 milestones — M1 core+contract → M2 engine → M3 skill → M4 understand rewire → M5 understand v1 → M6 extractor → M7 evaluation → M8 ADRs/release. Deviation from map order: counts move into M3 (tests go red when the skill dir appears); `run` safety lands in M2.

**Key Decisions (reviews + verification):**
- CEO review (HOLD SCOPE, approach A confirmed): +4 ACs — CLI-absent degrade, non-git stamp, untrusted judged input, tool timeouts + run.log.
- Eng review: tracked-only dirty (E1), `.work-<sha12>/` hand-off (E2), one baseline vocabulary (E3), codemem `--db` seam (E4).
- Phase 4.5 V1: accept `/sole-dev-merge` rebase-merge (supersedes the grill's "merge commit").
- Phase 4.5 V2: `run` never uses a shell; `&&` split into approved parts; pipes/`;`/redirects/`$(` → not_run.
- Phase 4.5 V3: extractor keeps today's any-occurrence match for names that resolve (no ON_DISK edge lost); backtick-only applies to unresolved names.
- Phase 4.5 V4: network-reaching tools (semgrep, osv-scanner, pip-audit) run in Deep only, disclosed; Quick/Standard mark them `skipped`.
- Design choice (no question needed): `aa_ma.analysis` reaches codemem by subprocess (import forbidden by `.importlinter`), adding `hot_spots/co_changes/owners/layers` to `codemem query`; each run builds a fresh codemem index under the work dir (target `.codemem/` never read or written — Angle 6).

**Research Findings:**
- `docs/research/codebase-analysis-skills-sarif.md` — minimal valid SARIF 2.1.0 (validated with Draft4Validator), `fingerprints` vs `partialFingerprints`, `baselineState` values.
- `docs/research/codebase-analysis-skills-offline-command-run.md` — offline env per ecosystem, `npx` non-TTY `--yes`, process-group kill, `unshare -rn` caveat.
- Charting research (Tickets 1–4): prior-art, codemem-coverage, agent-scope, measurement-tools files in `docs/research/`.

**Lessons applied:** L-022 (tests under `tests/`), L-024 (fresh index before measuring; UNKNOWN-forever is a defect), L-025 (push only green), L-026 (`git add` before regen), L-027 (no hook bypass), L-028 (RED commit tests-only), L-029 (private repo by shape/count only), L-003/L-006/L-008 (CHANGELOG via Unreleased + release.sh).

**Remaining Questions:**
- None blocking. Residual verification WARNINGs are listed in `codebase-analysis-skills-verification.md` for the milestone that owns each.

_This log will be updated via context compaction as the task progresses._

## [2026-09-28] PLAN APPROVAL — treated as approved (Ste)
- Gate: planning (post-/double-check)
- Approved by: Ste — decision 2026-09-28: the design, grill, CEO/Eng and V1–V4 approvals suffice; plan at `bed5a2b` (+ this sync's corrections) is the approved baseline.
- Context: the plan was committed before Ste read the final text (double-check finding; lesson L-030).

## [2026-09-28] Decisions closing the /double-check (Ste)
- "Use at most 5 agents" means **at most 5 subagents running at once** (not a total). Planning complied (peak 4). Rule written into plan §0 for execution; M7 judges run in waves.
- CONTEXT.md *Codebase analysis* glossary (8 terms, my wording) stays; Ste approves the wording at M8.1 (M14 precedent).
- A fresh read-only consistency pass over plan v5 was run before this sync; its findings are fixed in the same commit.

## [2026-09-28] M1.1 Prototype verdict + §5a refinements (Ste) — recorded before the RED commit
- Prototype: `prototype/cas-analysis-schemas` @ `9cbd29d` (`src/aa_ma/analysis/PROTOTYPE-analysis-schemas.html`); JS `findingId` == Python hashlib (`F-8eee32c533b2` for `security/security.secret/src/db.py/aws-access-token`).
- Verdict: **PASS as specced** — §5a field set (Summary, Finding, JudgedFinding, SARIF shape) accepted unchanged.
- Refinement R-1 (redact before hashing): a judged finding's anchor = whitespace-collapsed source line **after** the regex secret set has replaced each span with `[REDACTED:<rule>]`. `ids.anchor_for(line) -> str` does both; the stored and hashed anchor are the same redacted text, so IDs stay stable and no secret reaches `findings.jsonl`. `ids.py` may import `secrets.py` (intra-package).
- Refinement R-2 (accepted edge): identical twins get `#k` by order of appearance (k ≥ 2 appends `#k` to the anchor before hashing); an inserted twin above the original takes the original's ID. Counts stay correct; the contract states it.
- Refinement R-3 (accepted edge): path is part of the ID, so a file rename reads as fixed + new. Git rename detection deferred (TODOS in M8.2).
- Validator WARN #3 folded into 1.3: negative fixture `schema_version: true` (strict mode must reject it).

## [2026-09-28] M1 review outcomes (§6.8 + §6.6)
- §6.8: 3 CRITICALs accepted by Ste and fixed (dup JSON keys, stray `.gitignore`, gitleaks unmappable entry fail-open); all WARNINGs fixed (Ste: "fix all now"); re-run 0 CRITICAL. Detail: `codebase-analysis-skills-impl-review.md`.
- §6.6: a CRITICAL in the new key-context scan (value offset searched, not known) fixed test-first; distinct-text scanning gives ~12× on a 5000-finding report.
- Decisions for M2 (logged, not done): batch gitleaks into one file per source (touches fail-closed mapping — needs its own tests); decide whether `--redact` keeps the full rescan; key SARIF maps by enums; golden JSON Schemas do not express field_validator rules (path, UTC) — non-Python consumers must use `aa-ma-analysis validate`.

## [2026-09-28] GATE APPROVAL: Milestone 1: Analysis contract + `aa_ma.analysis` core
- Gate: HARD
- Approved by: Ste (AskUserQuestion, 2026-09-28: "Approve + PR + merge")
- Criteria verified: 11/11
- Decision: APPROVED
- Evidence: 1843 passed / 2 pre-existing skips; codemem 791 passed; lint-imports 6/6 KEPT; §6.8 re-run 0 CRITICAL; §6.6 CRITICAL fixed; TDD PASS; PROTOTYPE + CRITICAL_PATH_REVIEW in provenance.

## [2026-09-28] Milestone Completion: Milestone 1 — Analysis contract + `aa_ma.analysis` core
- Status: COMPLETE
- Key outcome: a tested leaf package (`aa_ma.analysis`, CLI `aa-ma-analysis stamp|fresh|validate|scan-secrets`) defines every M1 output schema, the SHA stamp, stable finding IDs, SARIF 2.1.0 and a fail-closed secret gate; `ANALYSIS-CONTRACT.md` is the one contract both skills obey.
- Artifacts: src/aa_ma/analysis/*.py; tests/analysis/* (+ fixtures, goldens, vendored SARIF schema); references/ANALYSIS-CONTRACT.md; SKILL.md + 4 onboarding agents; .importlinter; pyproject.toml; CHANGELOG Unreleased; docs/architecture regenerated.
- Tests: 1843 passed / 2 pre-existing skips; codemem 791 passed; lint-imports 6/6 KEPT; §6.7 ENG-STANDARDS + DIAGRAM gates PASS.
- Next: Milestone 2 — Dependencies: Milestone 1.

## [2026-09-28] §5a amendment — SARIF security-severity (Ste, /sole-dev-merge Stage D)
- Finding (C1 code-reviewer, MEDIUM): §5a pinned critical "9.0" (GitHub buckets > 9.0 as critical, so it showed as high) and info "0.0" (outside GitHub's (0.0, 10.0]); and tagged every dimension, turning maintainability/architecture findings into GitHub security alerts. Our own research (sarif.md:78) already said so.
- Decision: critical "9.5"; property only on `dimension == security` and severity above info. Fixed test-first (bdfa490 → GREEN). Plan §5a + reference.md amended.
- Same pass (LOW, fixed): JSONL framing, list-item key context, baseline 'fixed' refused for current findings, orphan comment, nosec annotations. Disputed as false positives: Bandit B108 on a test literal safe_dir must refuse; 199 × B101 test asserts.

## [2026-09-28T16:07:43Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 2.1: [prototype] run every tool row of §5a on the forge on `prototype/cas-assess-core`
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/codebase-analysis-skills-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-28] M2.1 PROTOTYPE verdict — §5a tool rows on the forge
- Branch `prototype/cas-assess-core` @ `efb0574` (pushed): `prototype/cas-assess-core/{probe.py,SHAPES.md,shapes.forge.json}`; all rows ran on the forge (730 tracked files) in ≈ 20 s. Absent tools run ephemerally (Ste): `uvx lizard` 1.24.0, `npx --yes jscpd` 5.3.3, osv-scanner 2.6.0 release binary (sha256 verified).
- Verdict (Ste): **PASS as corrected**. §5a table amended in plan.md.
- Ste decisions: `maint.dead_code` → metric only (37/37 `src/` candidates were false positives: dispatch dicts, decorators, `Annotated` validators, Textual callbacks); jscpd findings for code formats only (263 clones: 125 markdown, 53 json, 23 text, 48 python); osv-scanner rc 128 (no packages, empty stdout) → `ran`, zero findings.
- Mechanical corrections (no decision needed): pip-audit `--no-deps --disable-pip` (otherwise it pip-installs the target's requirements — runs repo code) and status by report (rc 1 = vulns AND missing file); semgrep severities include the new CRITICAL/HIGH/MEDIUM/LOW scale; codemem owners needs a trailing `/` on dirs (`src` → 0 authors silently) and returns emails (never stored); dead_code default budget truncates (167/1500); jscpd scans tracked files, drops `fragment` (source text), strips `:<format>` from names; osv paths absolute → relativise.
- Environment: bare `codemem` on BATS PATH is a broken conda stub; under `uv run --project <forge>` `.venv/bin/codemem` resolves first (consumer invocation) — `measure` uses `CODEMEM_BIN` else PATH.
- Built-in regex over repo source needs a text-scan entry: `secrets.scan` is report-dir only and fails closed on unknown suffixes.

## [2026-09-28] M2 §6.8 re-run + §6.6 triage — decisions (Ste)
- **run gate becomes an allowlist** (amends §5a / M2 Contract "refuse-list"): only known test-runner argv forms execute; anything else is `not_run — run by hand`; the refuse list stays for explicit `refused` reasons. Why: three review rounds each found new denylist bypasses; a denylist over shells/interpreters/runners cannot be completed.
- **Staging dir** (orchestrator design): tracked regular files hard-linked into `<work>/stage/` minus target scanner configs; scanners run there. Replaces per-file argv (E2BIG, `-`-prefixed names), stops gitleaks walking untracked trees (11 s → tracked only), and scanner configs are recorded but not obeyed.
- In M2 by Ste's choice: inline suppression counts, parallel tool runs, parallel owners blame (codemem), huge-repo argv handling (subsumed by staging).

## [2026-09-29T05:55:01Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 2.7: [verify] live measure + finalize on forge; regen; CRITICAL_PATH_REVIEW; PR
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/codebase-analysis-skills-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-29] M2 §6.8 round 4 — git config allowlist (Ste)
- **Target git config: denylist → allowlist.** Four review rounds each found a new config route to code execution (fsmonitor, filter in config.worktree, gpg.program via log.showSignature, submodule config). Unknown keys in local/worktree/submodule scope now refuse the target (exit 2); our calls also pin `log.showSignature=false` and skip submodules. Trade-off: repos with unusual but harmless local keys are refused and must be analysed from a clean clone — fail closed over fail open.
- **run gate:** `uv run` only for test runners (they execute repo code by design); lint modules via `python -P -m` (no cwd on sys.path); cargo forms refused when the target ships `.cargo/config*`.
- **Staging:** each file's (st_dev, st_ino) at listing is compared with the staged link; a mismatch (parent swapped for a symlink mid-run) is skipped and counted.
- Round-4 INFOs not changed (orchestrator, with reasons): `python -m ruff|black` stay off `PY_MODULES` (ruff/black are binaries; the bare forms are allowed); `-k`/`-run` values with `^ $ |` stay `not_run` (fail-safe; a regex in a test selector is rare and can be run by hand); the staged package.json rewrite shifts line numbers only for findings inside package.json itself (jscpd ignores JSON as prose). Disputed: staged `.codemem/` — codemem always runs with `--db <work>/codemem.db`, cwd = target.

## [2026-09-29] M2 §6.8 round 5 — threat model fixed (Ste)
- **Threat model: hostile content at rest.** The tool defends against anything a target repo can contain (files, names, symlinks, git config, `.git` files, tool configs). A hostile process running concurrently on the machine is out of scope: it already executes as the user and could read the files it would trick us into reading. The (st_dev, st_ino) checks remain as defence in depth. Why: round 5's R5-2 needs a live swapper; closing it needs an openat walk for every read with no gain against an attacker who already runs code.
- **Correction (6c37fd2 claim):** `PYTHONSAFEPATH`/`-P` stops a planted module *named like* the linter; linters still load plugins from their own config (mypy `plugins`, flake8 local-plugins, pylint init-hook) — linters are repo-code runners like test runners.
- Review loop closes after one regression pass (Ste): new out-of-scope items go to an M2 follow-up backlog.

## M2 follow-up backlog (out of the M2 review loop, per Ste's round-5 close-out)
- `safe.directory`: with ISOLATED_CONFIG a repo owned by another uid (WSL /mnt drives, docker volumes) reports "not a git repo with ≥1 commit"; give a specific "dubious ownership — assess as the owner or from a clone" message. Fails closed today.
- (pre-PR, Ste) Planted *untracked* baseline report in a directory handed over rather than cloned: keep an index of report dirs this tool wrote, outside the target, and ignore others.
- (pre-PR, Ste) `run`: a passing command whose detached grandchild keeps the output pipe open is reported as `timeout`.

## [2026-09-29] GATE APPROVAL: Milestone 2: Assess engine (CLI)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 12/12
- Evidence: suite 2125 passed / 2 skipped; lint-imports 6/6; bandit 0 ≥Medium; §6.3 impact LOW; §6.8 final regression pass 0 CRITICAL / 0 WARNING (13/13 earlier findings hold); PROTOTYPE, CRITICAL_PATH_REVIEW (data-xform, live Deep run at final HEAD), DIAGRAM_VERIFIED edges=5 checked=5
- Decision: APPROVED
- Next: PR via /sole-dev-merge; rebase SHA map recorded in provenance

## [2026-09-29] Milestone Completion: Milestone 2 — Assess engine (CLI)
- Status: COMPLETE
- Key outcome: `aa-ma-analysis measure|run|finalize` turn a target repo plus judged findings into the versioned report set (summary.json, findings.jsonl, findings.sarif, report.md, run.log) — measured parts deterministic; scanners run concurrently on a hard-linked stage of tracked files; the target's git config, scanner configs and symlinks are checked, never obeyed; `run` executes only a strict test/build/lint grammar.
- Threat model: hostile content at rest (Ste, round 5); stated in report.md `## Scope`.
- Tests: 2125 passed / 2 pre-existing skips; lint-imports 6/6; bandit 0 ≥Medium; §6.7 PROTOTYPE, CRITICAL_PATH_REVIEW, DIAGRAM_VERIFIED; §6.8 five rounds → final regression 0/0.
- Next: Milestone 3 — `assess-codebase` skill + thin command (Dependencies: Milestone 2).

## [2026-09-29] M3 3.2 — health slice: own prompt, no agent reuse (Ste)
- **Deviation from plan §5 M3 Step 4** ("reuse codebase-onboarding-health for the health slice"): that agent's hard constraint writes only `.claude/onboarding/09-repo-health-and-verdict.md` — outside the report dir, so the output secret gate never scans it, and in prose, not `judged.jsonl`. measure already yields churn / hot spots / owners / deps deterministically. Ste chose: a general-purpose judge with its own `tests_deps` prompt in AGENT-PROMPTS.md, writing judged.jsonl into the work dir like every other judge. Pinned by `test_judges_and_refuter_are_named`.
- Executable skill blocks: the preflight and claude-security guard are fenced bash blocks tagged `# assess:<name>` and the tests run them, so AC6's "one live check" is in CI, not only a one-off.

## [2026-09-29] M3 3.6 — live Standard run observations
- finalize's "HEAD moved since measure" refusal fired live when a fix was committed mid-run. Carried judged/ratings/ledger to a fresh measure because the diff touched only the skill's prompts and a test (no cited path). The skill text leaves a re-run to the user; running assess on a moving branch is a user error, not a tool gap.
- tests_deps judge proposed `unknown`; rated `adequate/low` because RATING.md reserves `unknown` for "neither core input nor judged evidence" and 7 judged lines exist. Security/tests_deps adequate outside Deep as designed.
- lizard/jscpd absent on BATS (M2 used uvx/npx ephemerals): maintainability rests on judged reading; the prompt fix makes judges say so.

## [2026-09-29] M3 §6.8 — remediation decisions (Ste)
- First pass 0 CRITICAL / 14 WARNING → "fix all now" incl. SEC-W2 schema change (sub-step 3.7). New read-only agent `codebase-assessor` (Read, Grep, Glob) replaces general-purpose for judges + refuter; agent count 12 → 13. Judges return lines in replies; the main thread writes `judged/<dim>.jsonl`, gates, validates. Refuter verdicts via `verdicts.jsonl`; refuted findings kept with `refutation_reason` (Finding schema, optional, default null — unreleased, no downstream).
- Not done from SEC-W3's suggestions: a fresh temp HOME for `run` children — it would cut test runners off their offline caches (uv/npm/cargo under HOME) and fail offline runs; disclosure + container advice instead.
- Live re-verification after 3.7 by replay (Ste): real judged lines through the new pipeline, no agents — the agent type is not installed mid-session.
- Regression pass: 4 W + cheap INFO fixed; loop closed after one regression pass (M2 precedent).

## M3 follow-up backlog
- Refuted twins take part in `assign_ids`: a refuted twin listed first pushes a live finding to `#2`, flipping its baseline state. Assign live IDs first.
- `refutation_reason` near 2000 chars can exceed `EVIDENCE_MAX` after redaction → finalize refuses the report (fails closed). Cap below the limit or truncate after redaction.
- No validator pairs `refutation_reason` with `refutation ∈ {survived, refuted}`.
- **M4 carry-over:** when understand-codebase reads assess's `findings.jsonl`, it must drop `refutation == refuted` (they are in the file now) — add a test in 4.2.

## [2026-09-29] GATE APPROVAL: Milestone 3: `assess-codebase` skill + thin command
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6
- Evidence: suite 2197 passed / 2 skipped; bats install_dry_run 5/5; lint-imports 6/6; golden errors []; clean-room 0 shingles; live Standard report 7ff33a0cfb29 + post-3.7 replay a205eeb677c8 validate, 0 leaks; §6.3 LOW (re-run); §6.7 PASS, CRITICAL_PATH_REVIEW doc-count-drift (+ addendum), DIAGRAM_VERIFIED 5/5; §6.8 0 CRITICAL, regression closed
- Decision: APPROVED
- Next: PR via /sole-dev-merge

## [2026-09-29] Milestone Completion: Milestone 3 — `assess-codebase` skill + thin command
- Status: COMPLETE
- Key outcome: `/assess-codebase` + `Skill(assess-codebase)` run Quick / Standard / Deep end to end over the aa-ma-analysis CLI: preflight, stamp/fresh, measure, ledger, Deep extras, read-only `codebase-assessor` judges (gated + validated), refuter via verdicts.jsonl, finalize; refuted findings kept with reasons. Counts 14 / 22 / 13 agree everywhere.
- Artifacts: claude-code/skills/assess-codebase/{SKILL.md,references/RATING.md,references/AGENT-PROMPTS.md}, claude-code/commands/assess-codebase.md, claude-code/agents/codebase-assessor.md, src/aa_ma/analysis/{finalize,models,report_md}.py, tests/skills/test_assess_codebase.py, tests/analysis/test_rating_keys.py, test_finalize.py, goldens, docs counts.
- Tests: 2197 passed / 2 skipped.
- Next: Milestone 4 — understand-codebase repoint + residuals (Dependencies: Milestone 3); carry-over: filter refuted findings; orphan pin for /assess-codebase goes.

## [2026-09-29] M3 merged
- PR #6 rebase-merged via /sole-dev-merge, CI 7/7 green; main at 14384d1 (milestone commit 3d4b856). Rebased SHA map in provenance. Merge review: 1 MEDIUM + 1 LOW fixed (judge rules moved into the JudgedFinding model so `validate` enforces them), Bandit B613 (literal bidi in a test) fixed, Stage B test reformat reverted per L-031.
- To use the skill: run `scripts/install.sh` (symlinks assess-codebase command/skill and the codebase-assessor agent), then restart Claude Code.

## [2026-09-30] M4 4.1 — plan corrections (Ste)
- **AC4 narrowed.** Plan named DIMENSIONS.md:217 and the health agent's `git log -1 --format=%cd` as report-freshness rules; at f3ad912 and HEAD both are dimension-13 "is the repo alive?" checks. They stay (asserted). SHA freshness via `aa-ma-analysis fresh` replaces the date rule for assess and legacy reports: REUSE-MAP.md:8-10 and the SKILL.md Step 0 rows. The gsd `.planning/codebase` row keeps its date rule.
- **AC1: two allowed sites** for `codebase-deep-dive` under claude-code/: the one flagged legacy-absorb rule in SKILL.md Step 0 and ANALYSIS-CONTRACT.md's freshness definition (shared with assess). Every other mention points at the Step 0 rule.
- **M3 carry-over folded in:** the assess-absorb rule drops findings with `refutation == refuted`.

## [2026-09-30T08:41:44Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 4.4: [verify] regen; tests; fresh assess at M4 HEAD; live Quick run absorbing it; PR
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/codebase-analysis-skills-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-30] M4 §6.8 decisions (Ste)
- First pass (0 C / 11 W / 13 INFO): **fix all 11 + cheap INFO** → 4.5.
- Regression 1 (0 C / 4 W): **fix + another regression pass**.
- Regression 2 (`lnk/..` alias; unnormalised `--repo`): fixed `01ec2e6`; loop closed per M2/M3 precedent; residual INFO → backlog (impl-review M4).
- Live AC6 re-run at final HEAD `9a6f441` because `fresh` and Step 0 changed after the `31dedf1` run.

## [2026-09-30] GATE APPROVAL: Milestone 4: understand-codebase repoint + residuals
- Gate: HARD
- Approved by: Ste
- Criteria verified: 7/7 (AC7 CI architecture-drift confirmed on the PR)
- Decision: APPROVED — Approve + PR + merge

## [2026-09-30] M5 5.1 prototype verdict (Ste)
- Section map source: **citations + globs** (not agent-declared). Each section → every backticked repo path it cites; a cited directory (`dir/`) matches as a prefix at **any depth** (Ste chose never-stale over fewer regenerations; exact-only missed architecture on abf5b20).
- Fixed globs per section for truth nobody cites line-by-line (stack → manifests/lockfiles; tests-ci → `.github/workflows/*`, `tests/*`).
- Any Add/Delete/Rename → structure section; stamp sha not a commit (rebased away) → every section.
- Prototype: `prototype/cas-incremental-regen` b10b467 — throwaway; main keeps only this decision.

## [2026-09-30] M5 interface decisions (5.2)
- `changed_since(repo, sha12) -> list[Change(status, path)] | None` — the plan's `list[str]` cannot carry the A/D/R status the 5.1 rule needs; None = sha not a commit (→ every section). A rename yields both paths (status R). sha12 must be 12 lowercase hex (ValueError otherwise; CLI exit 2).
- `cited_paths(md, repo)` lives in ground.py beside the citation parser (DRY); CLI `ground <md> --cited` prints the section's map entry (files + `dir/` prefixes). Fixed per-section globs live in changed.py (SECTION_GLOBS), not in onboarding.json.
- CLI `changed-since <sha12> [--repo R] [--onboarding F]` prints JSON {known, changed, regenerate}; exit 0 (unknown sha is an answer, not an error), 2 on a bad sha or non-repo.
- ground claim unit: one list item / table row line, or one sentence of prose; fenced code skipped; a citation is a backticked path to a regular file inside the repo (`path` or `path:line`); a cited path that is missing or escapes the repo is itself ungrounded (token = path). Numbers standing alone (not inside words like v0.16.0, not list markers) are checked.
- Section keys are deep-dive **file names** (`03-structure.md`), matching M1's onboarding fixture (`04-build-run-debug.md`).

## [2026-09-30] M5 §6.8 remediation decisions (5.6)
- Pack trust moved from skill prose (`git ls-files .claude/onboarding`, defeated by a committed `.claude` symlink) into `changed-since`: `_located` (fresh's one-place + realpath check) + git-tracked refusal → exit 2 → full run. `SectionName` pattern `^\d{2}-[a-z0-9-]+\.md$` in the model (golden schema regenerated).
- Dirty tree → `changed_since` returns None (every section) rather than diffing the working tree: consistent with stamp's tracked-only dirty and simpler than filtering our own untracked outputs.
- Skill order: currency check before any write (Standard step 5; Deep before the synthesizer); grounding / sampled claims / ledger / onboarding.json last.
- The orchestrator builds the codemem index once (build + refresh-commits); workers only query it and get `AA_MA_ROOT` in their prompt.
- CR-W5: `codebase-onboarding-synthesizer.md` was outside the M5 Contract `Files:` list; it changed as a required follow-on of the AGENTS-MD-TEMPLATE size change (now "within that template's size limit" — one source).

## [2026-09-30] GATE APPROVAL: Milestone 5: understand-codebase v1 upgrades
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6
- Decision: APPROVED — Approve + PR + merge

## [2026-09-30T18:00:50Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 6.1: [measure] impact analysis; re-measure on a fresh scratch index; pin both sets
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/codebase-analysis-skills-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-30] M6 6.1 — pinned sets (measured on `git archive` of 3819eb0)
- Pre-M6 golden: 201 edges, 62 ON_DISK command edges (the "no ON_DISK edge lost" base).
- Command DANGLING set pinned at 6.1: {commit-and-push, compress, git-status-smart, healthz, index, pre-commit-*, readyz, release-prep, settings}.
- Set to fix in 6.4: all nine (local-only user commands and `/compress` reworded; `/healthz`, `/readyz`, `/settings` are HTTP routes → `GET /…` form, which AC1 says draws no edge). Expected post-6.4 command DANGLING set: ∅.
- EXTERNAL["command"] (only referenced names; AC3 forbids unreferenced entries): {browse, goal, init, qa, qa-only, superpowers:brainstorming}. Plan examples `help`, `clear`, `claude-security` are not referenced as backticked `/x` today, so not listed.
- Skill DANGLING pin unchanged: {haiku-eval}.
- Decision: the skills/x/ lookup applies to every resolvable occurrence (same rule as commands); a stem that is both a command and a skill resolves to the command. The `{` guard applies to backtick spans only; on the any-occurrence path it was mutation-dead (a `/x-{…}` template never names a real command) and was dropped.

## [2026-09-30] M6 6.4 — `/settings` kept (Ste decision)
- `/settings` is an HTTP route inside `claude-code/skills/prototype/UI.md`, a verbatim fork (FORKS.json `state: current`, md5-pinned to upstream c55ee46). Rewording trips fork-drift.
- Options: keep verbatim (chosen) / edit + mark derived / exempt current forks in the extractor.
- Fixed in 6.4: {commit-and-push, compress, git-status-smart, healthz, index, pre-commit-*, readyz, release-prep}. Post-6.4 command DANGLING = pin − fixed = {settings} (AC2), shown under Dangling in docs/architecture/plugin-surface.md.

## [2026-09-30] M6 §6.8 — scope note (accepted CRITICAL)
- 6.4 also modified `claude-code/agents/codebase-onboarding-runbook.md` (`/healthz`/`/readyz` → `GET /…`), needed for AC2. The M6 Contract `Files:` omits `claude-code/agents/`; this note records it as in scope. plan.md stays frozen (historical record).

## [2026-10-01] GATE APPROVAL: Milestone 6: Plugin-surface extractor learns slash commands (R4)
- Gate: HARD
- Approved by: Ste
- Criteria verified: 5/5 (AC4 CI architecture-drift confirmed on the PR)
- Decision: APPROVED — Approve + PR + merge

## [2026-10-01] Milestone Completion: Milestone 6: Plugin-surface extractor learns slash commands (R4)
- Status: COMPLETE
- Key outcome: backticked unresolved `/x` now classifies DECLARED_EXTERNAL or DANGLING; 8 dangling mentions fixed; only the fork route `/settings` remains (Ste decision); no ON_DISK edge lost.
- Artifacts: draw/plugin_surface.py, draw/surface_allowlist.py, tests/codemem/test_plugin_surface.py, golden + docs/architecture, 7 shipped .md files, CHANGELOG.
- Tests: 2333 passed; PR #9 CI 7/7 green.

## [2026-10-01T09:03:50Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 7.3: [run] new side on all 3 repos (R6 absorb in Provenance)
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/codebase-analysis-skills-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-10-01] M7 CIRCUIT BREAKER — pass bar not met in round 1; fix and re-run (Ste)
- **Evidence (7.4):**
  - AC3 fails on all 3 repos: 60 of 60 checked new Critical/High findings fail the claim check.
  - Every one is a measured `security.secret` finding hard-coded to `Severity.HIGH` (`src/aa_ma/analysis/measure.py:401-405`). The refuter only sees judged critical/high findings, so these never get checked.
  - AC1 fails in 2 of 12 comparisons: hono J1 accuracy and private J2 density.
- **Decision (Ste, AskUserQuestion):** fix and re-run, rather than writing a FAIL verdict now or accepting with exceptions.
- **Secret severity (Ste):** measured hits become MEDIUM, worded "possible secret (unverified)". The security judge escalates a live-looking hit as a judged high, which the refuter then checks.
  - Rejected: collapsing hits to one finding per file (more churn).
  - Rejected: refuting every hit (2565 refutations on one repo).
  - Kept: the target's `.gitleaks.toml` stays unobeyed, so a target cannot hide its own secrets.
- **AC1 policy (Ste):** re-judge with 6 fresh judges on a new seed and report both rounds side by side. Understand packs are not hand-edited.
- **Scope change:** M7 gains sub-steps 7.4a–7.4d. Audit-Profile changes docs-only → code-only and the TDD-Waiver is removed, because 7.4a/b change `src/`. Related HIGH-severity sources (semgrep ERROR, lizard CCN, fixable vulns) are out of scope: none was produced in Standard runs; noted for M8 TODOS.

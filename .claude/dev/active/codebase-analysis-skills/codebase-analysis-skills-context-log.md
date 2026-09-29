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

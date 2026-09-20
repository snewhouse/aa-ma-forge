# Verification Report: mattpocock-trio-adoption
Generated: 2026-09-20T21:05:00Z | Mode: automated | Revision: 2

## Summary
- CRITICAL: 9 findings (9 resolved — revisions 1 and 2)
- WARNING: ~40 findings (all folded into the plan; 0 open)
- INFO: 16
- Overall: **PASS WITH WARNINGS** (0 unresolved CRITICAL after 2 revision loops)

Agents: wave 1 = 4 parallel (ground-truth, assumptions, impact, criteria); wave 2 = fresh-agent + standards/bash specialist + targeted re-check of revised claims (≤5 concurrent throughout).

## Angle 1: Ground-Truth Audit
### Findings
- [CRITICAL→resolved] Plan said the chart guard would be "symlinked by install.sh like `aa-ma-parse.sh`" via a `hooks/lib/*` loop. Reality: `scripts/install.sh:333-344` links helpers by explicit per-file blocks; `lib/aa-ma-footer.sh` exists in the repo and is *not* installed. → M5 gains an explicit `create_symlink` block + `install_dry_run.bats` case; Global Constraint added.
- [CRITICAL→resolved] M1-AC3 expected `DRIFT` for `grill-with-docs`; at `c55ee46` its `CONTEXT-FORMAT.md`/`ADR-FORMAT.md` 404 (moved to `domain-modeling/`), so the classifier's ORPHAN-first precedence yields `ORPHAN`. → criterion pins `ORPHAN / DRIFT / ORPHAN` at `--sha c55ee46`.
- [WARNING→resolved] `tasks-template.md` has a second blank `- **Prototype-Required:**` at milestone level (`:78`), already exit 2 today. → M3-AC7 covers all four blank slots (`:72,:78,:109,:113`).
- [WARNING→resolved] Pre-M1 list missed `foundations.md:52` and `aa-ma-quick-reference.md:86-91` "+2 optional" sites. → added.
- [WARNING→noted] `pyyaml` transitive only; two dev-dep tables in `pyproject.toml`. → `[dependency-groups] dev` named.
- [WARNING→resolved] Research-file header: `Sources` field did not exist in any file. → added to `docs/research/mattpocock-trio-2026-09.md`; Global Constraint defines the 5-field header.
- 61 claims OK (all path/anchor claims at `c87135b`; all five upstream md5s at `c55ee46` verified via `gh api`; 19/11/12 counts on disk match SECURITY.md).

## Angle 2: Assumption Extraction & Challenge
### Assumptions Identified
1. [CRITICAL→resolved] `install.sh` auto-discovers `hooks/lib/*` — contradicted (see Angle 1).
2. [CRITICAL→resolved] `CLAUDE.md` is a committed count site — contradicted by `.gitignore:2`; `test_aa_ma_share_command.py:53-59` already skips it. → removed from every criterion; count test extension limited to foundations headings.
3. [CRITICAL→resolved] ADR-0002 recorded fork-time md5s — it records none (prose only). → `grill-with-docs.upstream_md5` derived from the byte-faithful local fork, flagged `upstream_md5_source: derived-from-local-fork`.
4. [WARNING→resolved] New skills are Skill-callable in the same session as `install.sh` — false; the listing is fixed at session start. → "Session restart rule" Global Constraint; live criteria run in a fresh session and record the resolved path.
5. [WARNING→resolved] `release.sh` can run twice without prep — it refuses without exactly one `## Unreleased` and never re-creates it (`docs/runbooks/release.md:53`); also requires HEAD == origin/main, clean tree, `gh auth`. → Step 5.1 re-adds `## Unreleased`; Step 5.5 requires charting artefacts committed+pushed.
6. [WARNING→resolved] bats can target `~/.claude/hooks/lib/…` — CI has no install; convention is repo path + fake `CLAUDE_HOME`. → Global Constraint + M5 criteria rewritten.
7. [WARNING→resolved] Contract named `MilestoneBlock` — type is `Block` (`grammar.py:52`). → fixed.
8. [WARNING→resolved] No test asserts `Agent ∉ tools` for the researcher. → `test_aa_ma_researcher_agent.py` asserts it plus "never run `claude`".
9. [VERIFIED ×12] nested Skill calls are upstream's own mechanism and already used in-repo (`aa-ma-execution/SKILL.md:147,396`); `gh` authenticated, md5s match; `python -m aa_ma.forks` viable (hatchling; `aa_ma.gate` precedent); additive marker keys accepted by all three parsers; `git mv` of a map inert to TUI/hooks/canonical test; `docs/research/` naming collision-free; pre-M1 drift claims real; line anchors at `c87135b` spot-checked.

## Angle 3: Impact Analysis on Proposed Changes
### Files Affected
- [CRITICAL→resolved] `scripts/install.sh` — missing from M5 artefacts (see Angle 1).
- [CRITICAL→resolved] `src/aa_ma/gate.py` `_read_steps` × this plan's own tasks.md — the scribe copies `tasks-template.md` blank slots → M3's gate refuses M3. → Next Action instructs the scribe to emit `Prototype-Required`/`Critical-Path` only where set; M3 removes all four blank slots.
- [WARNING→resolved] `docs/spec/claude-code-foundations.md:105` + `README.md:247` say "terminal TUI" for prototype. → M3 artefacts + grep criterion cover both.
- [WARNING→resolved] Taxonomy sites disagree today (5+2 / 5+3, impl-review row missing in spec table + templates README). → pre-M1 commit normalises to 5+3; M5 rollback text corrected.
- [WARNING→resolved] `Skill("grilling")` name collision with the plugin skill. → M2 risk 4 + live criterion records resolved path; rename fallback defined.
- [WARNING→resolved] `fork-drift.bats` "PATH stripped" would break `uv`. → `GH` env seam (release.sh precedent) + `--manifest` fixture.
- [WARNING→resolved] Charting commits during the active plan hit the commit-signature hook. → `[ad-hoc]` rule in Global Constraints and in `aa-ma-chart.md`.
- [WARNING→resolved] `_phase_1_3` fingerprint unevidenced under `--from-map`. → TODOS entry (with `_phase_3`).
- [WARNING→resolved] `map-template.md` must not join `WRITER_TEMPLATES` (`test_writer_check_is_not_vacuous` needs milestone headings). → stated in M5.
- [OK ×9] `FORKS.json` file inside `skills/` (dir globs unaffected); `_helpers` "Forked" literal not asserted; `grill-mode-resolver.sh` ignores `--from-map`; `gate.py` external callers are tests only; Critical-Path table scrape (`test_critical_path_parser.py`) — table untouched; `.claude/dev/charting/` scanned by nothing; shellcheck CI reaches `scripts/` + `hooks/lib/`.

## Angle 4: Acceptance Criteria Falsifiability
### Criteria Audit
- 62 criteria audited (35 milestone ACs + 27 step lines): 53 falsifiable as written; 9 rewritten with concrete assertions (M1-AC5, S1.3, M2-AC3 live grilling → `LIVE_CHECK` provenance line + fixed idea + transcript proof; S3.2/S3.3 → greps; M4-AC3 → 5-field header count + citation regex + agent transcript path + fixed PROTOTYPE grammar; M4-AC4 → greps; M5-AC1 → fixed verdict grammar + `Template-amendments:` line; M5-AC5 → bats case (e) for the `MAP_IMPORTED`/import leg).
- Banned terms: "visibly" ×1 (removed), "clean" ×9 (defined once in Global Constraints as `exit 0, no findings`).
- Factual traps fixed: `CRITICAL_PATH_REVIEW` now the 4-field form matching `execute-aa-ma-milestone.md:601`; milestone-level blank slot included; ORPHAN vs DRIFT; grilling frontmatter has no `disable-model-invocation` (verified), so md5 + "absent" agree.
### Score: 62/62 falsifiable after revision (100%)

## Angle 5: Fresh-Agent Simulation
### Implementation Barriers
- [CRITICAL] none — M1 startable from the plan alone; tooling and every path exist.
- [WARNING ×9→resolved] manifest `upstream_md5` per-file-null vs whole-null (per-file always); `ForkEntry` type (stdlib dataclass, extra keys ignored); per-file vs per-skill verdict rows (both printed; roll-up row last); 404 detection (`HTTP 404` on stderr only); `--manifest` flag for bats; `_helpers` change scoped to the upstream-path derivation (name==dir untouched); ADR-0003 anchor text; count-test overlap (foundations headings only); test count four→five; ADR-0004 status line verbatim.
- [INFO ×8→folded] `python -m aa_ma.forks` stdout contract; `uv lock` before `--check`; red-state is an ImportError at collection; ADR filenames; grilling category confirmed at `c55ee46`; glossary-sentence anchor; Theme 1 replacement sentence given verbatim; agent description `Skill(aa-ma-research)`; transcript path; `task`-ticket resolver defined.

## Angle 6: Specialist Domain Audit
### Specialists Dispatched: Engineering Standards Auditor (always) + Bash/CI defensive-scripting auditor
- [CRITICAL→resolved] `fork-drift.sh` pipeline: `gh api` prints a JSON error body on 404 (stdout 127 B) and exits 1; piped into `base64 -d | md5sum` it yields a bogus md5 → false DRIFT, and aborts under `set -euo pipefail`. → Contract captures with `if body=$(…)`, maps **only** `HTTP 404` to `null`/ORPHAN, everything else exit 1; refuses empty content (>1 MB); `cut -d' ' -f1`; `uv run --quiet --project`.
- [CRITICAL→resolved] `guard import` via bare `git mv` → exit 128 when target dir missing, map untracked, or cwd not a repo. → `cd toplevel || exit 1; mkdir -p; git ls-files --error-unmatch ? git mv : mv && git add`; every git failure → exit 1; bats (e) covers tracked, untracked and non-repo.
- [CRITICAL→resolved] literal `~/.claude/hooks/lib/…` guard path unreachable under fake `CLAUDE_HOME`. → the shipped `_cand` resolution pattern (repo toplevel → `${CLAUDE_HOME:-$HOME/.claude}`) required in `aa-ma-chart.md` and `aa-ma-plan.md`; criteria grep for it.
- [WARNING→resolved] M4/M5 bundle tests with implementation; `tdd-sequence-auditor` is vacuous for `hooks/lib`. → 4.1/4.2 "test committed first"; 5.2 commit order pinned (bats red → helper green) and recorded.
- [WARNING→resolved] M3 Contract 3-field `CRITICAL_PATH_REVIEW` vs 4-field elsewhere. → unified.
- [WARNING→resolved] guard should source `aa-ma-parse.sh` and honour `AA_MA_HOOKS_DISABLE=1`. → Contract.
- [WARNING→resolved] release #2 preconditions (HEAD == origin/main; pushed artefacts; `gh auth`). → Step 5.5.
- [WARNING→resolved] agent description `Skill(research)` → `Skill(aa-ma-research)`.
- Structural checks: #1 Element 12 PASS · #2 Critical-Path canonical PASS (`doc-count-drift`, `hook-modification` ∈ `CANONICAL_CRITICAL_PATHS`) · #3 TDD ordering WARN→PASS after revision 2 · #4 Audit-Profile per milestone PASS (code-only ×4, full ×1) · #5 TDD-Waiver PASS (none) · #6 Architecture View: `aa-ma-lint-views` exit 0, `render: UNKNOWN` (INFO, no mmdc — L-012), Component + Flow views present · #7 Contract block per code milestone PASS (M1–M5) · #8 field placements PASS · #9 `aa-ma-gate` on tasks.md **SKIP** (Phase 5 not yet run — re-run `/verify-plan` after artifacts exist).

## Cross-model note
Outside voice (Phase 4.2) and the wave-1 impact angle independently found the install.sh gap (as "never linked" vs "no loop") — treated as one CRITICAL. Outside-voice bullet 2 (fingerprint deferral breaks skip-warn) was rejected on evidence (`aa-ma-plan-skip-warn.sh:19-21` marker-only) and stays rejected; Angle 2 confirmed.

## Revision History
- v1: 2026-09-20 — wave 1: 5 CRITICAL (install.sh loop, CLAUDE.md gitignored, ADR-0002 md5s, ORPHAN precedence, scribe blank slots), ~22 WARNING, 9 criteria rewrites → revised.
- v2: 2026-09-20 — wave 2 + re-check: 3 CRITICAL (fork-drift 404/pipefail, git mv states, literal guard path) + 1 (research header `Sources`), 15 WARNING → revised; re-check 11/12 OK, last item fixed in the docs. Result: **PASS WITH WARNINGS**.

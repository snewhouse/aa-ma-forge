# sole-dev-merge-pr-workflow Context Log

## [2026-05-18] Initial Context

**Feature Request (verbatim from user):**
> we need to update and improve the sole-dev-merge command,skill,workflow to now include pre commit make ci runs (lint,mypy etc and fixes as needed), making an PR and or MR depending on if pushing to gitub or gitlab; proper review and then fixes as need of the code following standard practices; please AskUserQuestion and brainstorm with me; web search as needed; use sub agents as needed

**Key Decisions captured via 5 rounds of AskUserQuestion:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope relative to existing /sole-dev-merge | **Replace entirely** (single command, always PR/MR) | Cleanest mental model; old fast-merge path retired |
| Location | **aa-ma-forge plugin** at `claude-code/commands/` | Versioned, install.sh-managed, CI-covered |
| Code review approach | **Local AI review BEFORE pushing PR + extra security pass** | Fast feedback, no GitHub API spend |
| Auto-fix aggression | **CRITICAL auto-apply; ask on HIGH/MEDIUM** | Safe default, tight loop |
| Remote detection | **Dual-remote aware; AskUserQuestion when both; default GitLab** | Matches Biorelate convention (gitlab=primary) |
| Pre-PR CI checks | **All 4: format+lint+fix, typecheck, pytest fast, pre-commit** | Catch all classes locally |
| Post-PR-open behaviour | **Poll CI green (30s × 15min) then auto-merge** | End-to-end, sole-dev spirit |
| Merge strategy | **Rebase + ff (linear history)** | Closest to existing /sole-dev-merge ff-only flavour |
| Shape | **Command + thin skill wrapper** (later REVISED → command-only) | Originally requested skill wrapper; verification revealed no precedent for skill/lib pattern; user re-chose command-only |
| PR body | **AI-generated from diff** | Better narrative than commit-bullet dump |
| AA-MA handling | **Preserve [AA-MA Plan] footers + link plan dir in PR body** | Continuity with existing AA-MA workflow |
| CI poll | **30s × 15min, then clean exit** | Background-friendly |
| Security pass (post-revision) | **All three: security-auditor agent + Bandit + ShellCheck** | Belt-and-braces |

**Lessons Scan Findings:**
- **L-007 (CRITICAL relevance):** `/sole-dev-merge` quality-check format pass may modify out-of-scope files. Full lesson read inline at planning time. **The new workflow's M1.3 scope-filter is the structural fix for L-007** — `git diff --name-only main...HEAD` constrains the scope of format/lint to only files the branch actually touched.
- **L-008 (low relevance):** cz bump --files-only chain broken with manual CHANGELOG promote — relates to release-prep, not to merge workflow.
- **L-005 (medium relevance):** CI-scope check — for every new test/check artifact, verify CI actually runs it. Drives M5.6 (append bats step to CI workflow).

**Research:**
- Verified `gh` v2.92.0 + `glab` v1.80.4 CLI surfaces via `--help` inline (no Context7 needed — CLIs aren't libraries)
- Checked existing `glab-gitlab-cli` skill for canonical patterns
- Verified `feature-dev:code-reviewer` and `code-reviewer` agents both exist
- Verified `security-auditor` agent exists; `superpowers:security-review` does NOT exist (caught in verification)
- Verified `Skill(doc-drift-detection)` exists for M5.9

**Adversarial Verification (Phase 4.5):**
- Ran `Skill(plan-verification)` mode=automated
- Wave 1 (4 angles): Ground-truth, Assumptions, Impact, Falsifiability
- Wave 2 (2 angles): Fresh-agent simulation, Specialist domain audit (API + Engineering Standards)
- **v1 Result: FAIL** — 17 CRITICAL + 23 WARNING findings
- 17 CRITICALs categorized into:
  - Factual errors (non-existent skills, fabricated CLI flags) — 6 findings
  - Design gaps (skill/lib pattern undefined, severity scheme mismatch) — 3 findings
  - Standards compliance gaps (Audit-Profile missing, non-canonical Critical-Path) — 3 findings
  - Impact omissions (SECURITY.md drift, phantom install.sh edit) — 2 findings
  - Plan-text gaps (Step 1.1 frontmatter undefined, rollback path broken) — 3 findings

**Revision Decision:**
User selected via AskUserQuestion:
- Pattern: **Command markdown only — helpers as inline bash blocks** (drops skill/lib entirely)
- Security: **All three (security-auditor agent + Bandit + ShellCheck)**

**v2 Plan Generated:** All 17 CRITICALs addressed via spot-check verification. Result: PASS WITH WARNINGS.

**Research Findings (consolidated):**

1. **install.sh auto-discovery:** Lines 257-269 of `scripts/install.sh` already loop over `claude-code/commands/*.md` and `claude-code/skills/*/` — new files picked up automatically. v1 plan's claim that install.sh needs editing was a phantom requirement.

2. **Pre-existing repo drift:** SECURITY.md says "19 skills" but CLAUDE.md says "18 reusable procedures" — actual count via `ls claude-code/skills/` is 19. The plan resolves this discrepancy in M5.4 (atomic doc-drift commit).

3. **CLI contract gotchas captured in reference.md:**
   - `glab mr create --description-file` is fabricated (use `-d "$(cat $BODY)"`)
   - `--remove-source-branch=false` syntactically invalid (boolean flag)
   - `glab ci status` is not script-safe (use `glab api` instead)
   - `gh pr checks --watch` + `timeout 900s` → RC=124 on timeout (must translate)

4. **Severity scheme mismatch handled:** code-reviewer agents emit 2-tier or 3-tier schemes, NOT the plan's 4-tier. Workflow handles by passing explicit prompt contract AND falling back to "all HIGH" classification on parse failure (no silent auto-fix without confirmation).

**Remaining Questions / Open Items:**
- WARNING findings W3, W4, W6 deferred to execution-time refinement
- Bats CI step (M5.6) — will need to ensure `bats-core` is available in the GitHub Actions runner image
- Concurrent invocation (multiple `/sole-dev-merge` runs in parallel) explicitly out of scope; document assumption in command markdown frontmatter

**Marker Log (Phase 0–4.5 traces):**
- Phase 0 INIT — written to `~/.claude/runtime/aa-ma-plan-sole-dev-merge-ci-pr-20260518105415.log`
- Phase 1 DONE (context gathering complete)
- Phase 1.3 SKIPPED (user_passed — explicit AskUserQuestion rounds substituted for grill protocol)
- Phase 1.5 DONE (lessons_loaded=3, git_grep_hits=10)
- Phase 2 DONE (brainstorm via 5 AskUserQuestion rounds, 12+ alternatives weighed)
- Phase 3 DONE (context7_calls=0, web_fetches=0 — local CLI docs sufficient)
- Phase 4 DONE (complexity_score=53%, plan_elements=12/12)
- Phase 4.2 SKIPPED (user_passed on CEO/Eng/Design review)
- Phase 4.5 DONE (verdict=RED initially → revision → PASS WITH WARNINGS)
- Phase 5 — pending (proceeding now)

**Next Action:** Phase 5 artifact creation complete with this file. Phase 5 marker to be written after all 5 AA-MA files exist.

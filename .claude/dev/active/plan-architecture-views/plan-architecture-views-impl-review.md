# Impl Review Report: plan-architecture-views / Milestone 3
Generated: 2026-09-12T12:15:43Z | Audit-Profile: docs-only | Budget: normal

## Summary
- CRITICAL: 0
- WARNING: 1 (fixed)
- INFO: 3 (2 fixed, 1 accepted)
- Overall: PASS

Window: e212ab1..47ae344. Slate: future-proofing-auditor (check #1 only).

## Future-Proofing (future-proofing-auditor agent) — 0 CRITICAL, 1 WARNING, 3 INFO
- [WARNING] guard-reachability: `test_command_count_sites_match_disk` read CLAUDE.md, which is gitignored (local-only) → FileNotFoundError on a fresh clone; and CI ran only tests/codemem + test_goal_synthesis, so neither tests/commands nor tests/render executed in CI. → **Fixed**: CLAUDE.md site skipped when absent (mutation: file removed → 4 passed); `.github/workflows/security.yml` gains a `uv run pytest tests/commands tests/render` step (79 tests).
- [INFO] SECURITY.md 12-name list unguarded → **Fixed**: `test_security_md_asset_lists_match_disk` pins command/skill/agent names and counts (mutation: name dropped → 1 failed).
- [INFO] CHANGELOG "11 bats cases" / "11 → 12" → **Accepted** (release note, historical).
- [INFO] CLAUDE.md skills/agents/hooks counts unguarded (pre-existing, local-only file) → **Accepted**; SECURITY.md's equivalents are now pinned.

---

# Impl Review Report: plan-architecture-views / Milestone 2
Generated: 2026-09-12T11:42:48Z | Audit-Profile: code-only | Budget: normal

(Milestone 1 report — docs-only, 0C/2W/5I — is in git history at b7c750c.)

## Summary
- CRITICAL: 4 findings (4 fixed — 0 accepted, 0 disputed, 0 deferred)
- WARNING: 8 findings (8 fixed)
- INFO: 16 findings (5 fixed, 11 accepted with reason)
- Overall: PASS (after remediation commits 0bd8987 + 167a57f; re-verified 1046 passed, real plan rc=0)

Window: 7e82554..2cd25f0 (initial), remediation 0bd8987, 167a57f. Slate: all 5 agents (code-only).

---

## Code Review (code-reviewer agent) — 1 CRITICAL, 5 WARNING, 5 INFO

- [CRITICAL] UNKNOWN_TYPE false positive: `%%{init}%%` / `---` front-matter read as the type word → **Fixed** (`_DIRECTIVE_RE` + `_FRONT_MATTER_RE` skipped; fixtures plan_init_directive.md, plan_yaml_frontmatter.md).
- [WARNING] `(new)` exemption lost on shape labels `[("x (new)")]` → **Fixed** (`_NEW_RE = \(new\)\W*$`; fixture plan_shape_new.md).
- [WARNING] unterminated fence silently degrades → **Fixed** (UNTERMINATED_FENCE + render UNKNOWN; fixture plan_unterminated.md; uses the lint's own `scan_fences` — see context-log 2026-09-12 for why not `has_unterminated_fence`).
- [WARNING] private heading grammars (`^## `, `split("\n## ")`, H3 promotion) → **Fixed** (`grammar.H2_RE` public alias, one additive line; H3 promotion defers to `MILESTONE_RE`; fixture plan_milestone_m_form.md).
- [WARNING] L-007 scope: ADR template/0010 edits → **Fixed** (decision recorded in context-log: ADRs are in the lint's remit).
- [WARNING] leading-slash label resolves from fs root → **Fixed** (`lstrip("/")` + repo-bounded check; fixture plan_parallelogram.md).
- [INFO] duplicate `### Component view` last-wins → **Accepted** (malformed input; first view unlinted is visible in output).
- [INFO] duplicate AUDIT_PROFILE_INVALID with tasks.md → **Fixed** (`dict.fromkeys`).
- [INFO] timeout_s per source → **Fixed** (docstring).
- [INFO] "3 kept" literal; CRLF → **Accepted** (self-correcting; consistent with grammar).

## Security (security-auditor agent) — 2 CRITICAL, 2 WARNING, 3 INFO
Mechanical pre-check (security-static-check.sh): PASS

- [CRITICAL] A04 ReDoS: `_LABEL_RE`/`_PATH_RE` quadratic on a 200 KB line (measured >20 s) → **Fixed** (str.find label scanner; `_PATH_RE` only on tokens ≤256; `test_bracket_flood_is_linear`, `test_slash_flood_is_linear` — 0.02–0.04 s).
- [CRITICAL] A04 ReDoS: `_FENCE_RE` lazy `.*?` × unclosed openers (14.5 s) → **Fixed** (line-based `_mermaid_fences`; `test_fence_flood_is_linear`, `test_unclosed_opener_flood_is_linear`).
- [WARNING] A01 existence oracle via absolute/`..` label paths → **Fixed** (`_inside`: resolve + is_relative_to; `test_paths_outside_repo_root_are_never_probed_as_present`).
- [WARNING] A03 terminal escape in UNKNOWN_TYPE message → **Fixed** (`{first_word!r}`; `test_unknown_type_message_never_carries_raw_control_chars`).
- [INFO] `# nosec` B404/B603 justified; SKILL.md bash quoting; test fakes confined → **Accepted**.

## TDD Sequence (tdd-sequence-auditor agent) — PASS, 2 INFO
- First tests/ commit d5f56ac (12:12:52) precedes first src/ commit cfdb6c6 (12:13:38); second pair 542789b → d353220 also ordered. All three src↔test pairs paired.
- [INFO] 53ed877 bundles RED+GREEN (cli.py); RED evidence in tasks.md 2.6 Result Log → **Accepted**.
- [INFO] 2.7 touches no src/ → **Accepted**.
- Remediation commits 0bd8987/167a57f: tests written and run RED before each fix (Result Log 2.8).

## External Library Evidence (context7-evidence-auditor agent) — PASS, 0 findings
Only a `[project.scripts]` entry in pyproject.toml; uv.lock untouched.

## Future-Proofing (future-proofing-auditor agent) — 1 CRITICAL, 1 WARNING, 6 INFO
- [CRITICAL] render-is-leaf listed 6 of 10 aa_ma modules; new modules silently exempt → **Fixed** (list completed; `tests/render/test_leaf_contract.py` pins it to `pkgutil.iter_modules`; mutation in `schemas/` → BROKEN. `source_modules = aa_ma` was tried and refused by import-linter: "Modules have shared descendants").
- [WARNING] CODE_AUDIT_PROFILES unbound to CANONICAL_AUDIT_PROFILES → **Fixed** (`test_every_canonical_audit_profile_is_classified_for_element_13`).
- [INFO] KNOWN_TYPES allowlist lacks a policy comment → **Fixed**.
- [INFO] "3 kept" literal, `seen >= 5` floor, `_PATH_RE` extension under-coverage, `timeout_s=90.0`, PARSE_ERROR_SIGNATURES coupling → **Accepted** (self-correcting / fail-safe direction / single use).

---

## User Override Decisions

None required: all 4 CRITICALs were fixed with tests before §7.3, so no accept/dispute/defer panel was raised.

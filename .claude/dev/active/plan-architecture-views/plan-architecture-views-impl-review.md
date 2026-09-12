# Impl Review Report: plan-architecture-views / Milestone 4
Generated: 2026-09-12T13:05:46Z | Audit-Profile: code-only | Budget: normal

## Summary
- CRITICAL: 2 findings (2 accepted → fixed in-window before approval; 0 disputed, 0 deferred)
- WARNING: 5 findings (5 fixed)
- INFO: 12 findings (5 applied, 7 accepted)
- Overall: PASS (re-run clean after remediation commit)

Window: de96c12..887a571 (+ remediation commit). Slate: code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor (all 5, parallel). §6.6 (3 agents) ran first and its 1 CRITICAL / 3 WARNING were fixed in 887a571 — see provenance.

## Code Review (code-reviewer agent) — 1 CRITICAL, 3 WARNING, 3 INFO
- [CRITICAL] scope discipline (L-007): tests/render/test_cli.py:21-23,31-33, tests/render/test_hostile_input.py:58-60 — `ruff format` re-wrapped three pre-existing lines unrelated to M4 → **Fixed**: hunks reverted; base-vs-HEAD now removes only the intended import line.
- [WARNING] error-path contract: src/aa_ma/render/cli.py — write-side OSError (`--out` is a file, unwritable dir) escaped as a traceback, exit 1 → **Fixed**: one `try` covers read + mkdir + write, exit 2 with stderr message; `test_render_out_is_a_file_exit_2` (RED reproduced FileExistsError first).
- [WARNING] root-sensitive test: chmod-0 case passes as uid 0 → **Fixed**: `skipif(os.geteuid() == 0)`.
- [WARNING] reference drift: reference.md M4 facts described pre-§6.6 `_raw_html` and test counts → **Fixed** (also the future-proofing CRITICAL below).
- [INFO] magic offsets `j + 4`/`k + 3` → **Applied**: `_OPEN, _CLOSE` + `len()`. [INFO] function-local import in test_hostile_input.py → **Applied**: hoisted. [INFO] `return 2` ×3 matches lint_main convention → **Accepted**.

## Security (security-auditor agent) — 0 CRITICAL, 1 WARNING, 4 INFO
### Mechanical pre-check (security-static-check.sh): PASS (no `[security-bypass:` markers in the window)
- [WARNING] A08 integrity: src/aa_ma/render/html.py — mermaid ESM loaded from cdn.jsdelivr.net with no integrity check and no CSP; SRI on the ESM entry would not cover its lazily imported chunks → **Fixed**: single-file UMD `dist/mermaid.min.js` with `integrity="<MERMAID_SRI>" crossorigin="anonymous"` (constant beside MERMAID_VERSION, bump command in the comment) + `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src https://cdn.jsdelivr.net 'sha256-<init-hash>'; style-src 'unsafe-inline'; img-src data: https:; font-src data:">`; `test_cdn_script_is_integrity_pinned_and_csp_locked`. Live: one CDN request (3 572 661 B), 2 svg / 1 table / 0 console errors under CSP; negative control with a tampered hash → browser refuses the script (0 svg, "Failed to find a valid digest"). Deviation from the plan Contract's ESM import recorded in context-log.
- [INFO] A03 XSS surface verified clean (javascript:/data: URLs, autolinks off, attribute breakout, `</pre>` in fence, title) → **Accepted**. [INFO] mermaid `securityLevel: strict` cannot be downgraded by an in-diagram init directive (inspected bundle) → **Accepted**. [INFO] `--out` honoured verbatim / follows symlinks — same trust model as `cp` → **Accepted**. [INFO] hostile-input budgets all linear; `[` flood ~1.8 s at 200 KB sits near BUDGET_S — do not add that shape to the hostile tests → **Accepted** (noted in reference).

## TDD Sequence (tdd-sequence-auditor agent)
### Verdict: PASS
- Milestone window: de96c12 .. 887a571 — first `tests/` commit ae66cb2 (2026-09-12T13:38:44+01:00) precedes first `src/` commit 67ddac3 (13:39:42+01:00) by 58 s. TDD-Waiver: (none).
- Per-file pairing: html.py → test_html.py + test_hostile_input.py ✅; cli.py → test_cli.py ✅. Informational: 6804324 and 887a571 land src + tests together (RED runs recorded in Result Logs, not as separate commits).

## External Library Evidence (context7-evidence-auditor agent) — 0 CRITICAL, 1 WARNING, 0 INFO
- [WARNING] markdown-it-py@4.0.0 (`>=4,<5`, promoted from transitive) — API measured in .venv and prototyped, but no canonical-doc citation; Context7 timed out at planning and was not retried → **Fixed**: Context7 retried 2026-09-12 (/executablebooks/markdown-it-py, docs/using.md "Renderers" + "Adding a custom render rule") — confirms the rule signature and `.enable('table')`; CONTEXT7 line in provenance.
- Major version bumps: none.

## Future-Proofing (future-proofing-auditor agent) — 1 CRITICAL, 0 WARNING, 5 INFO
- [CRITICAL] hardcoded count drift at write: reference.md M4 facts said test_html.py (7) / tests/render 60 in the commit that made them 9 / 65 → **Fixed**: counts updated (now 9+1 / 67 after the security fix), and the line now names files first.
- [INFO] MERMAID_VERSION 11.x guard → **Applied**: `assert MERMAID_VERSION.startswith("11.")`. [INFO] ADR-0010:92 still said "optional … droppable" → **Applied**: "(shipped 2026-09-12)". [INFO] magic offsets → **Applied** (above). [INFO] golden size "1674 B" quoted in 2 sites → **Accepted** (historical Result Log; reference updated to 1972 B). [INFO] no test guards README "Sharing and rendering plans" / `[project.scripts]` — no shipped CLI count exists → **Accepted**.

## User Override Decisions

| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | ruff format re-wrapped 3 non-M4 test lines (L-007) | accept → fixed | reverted before the gate; no dispute |
| CRITICAL | reference.md test counts stale at write | accept → fixed | corrected before the gate; no dispute |

## Revision History
- v1: 2026-09-12 — Initial impl review: 2 CRITICAL, 5 WARNING → both CRITICAL and all WARNING fixed in the remediation commit → PASS

---

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

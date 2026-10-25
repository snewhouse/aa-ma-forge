# PROTOTYPE — impact pre-edit hook UX (code-conventions-impact 10.1) — throwaway

Question: do ≤5 lines of codemem impact data read usefully before an Edit/Write; does PreToolUse
`additionalContext` reach the model (A1); is p95 ≤ 1.5 s?

Branch shape: neither LOGIC nor UI fits a bash hook; the artifact is the throwaway hook
(`claude-code/hooks/aa-ma-impact-preedit.PROTOTYPE.sh`) plus these captured outputs.

## Outputs (main f0bfbd8b index, ~/.cache/codemem/…)
- src/aa_ma/grammar.py (hub): 6 caller files + 6 test files; top deps.py(10), gate.py(8). Useful.
- src/aa_ma/render/mermaid_lint.py (leaf): 2 callers + 7 tests; co-changed (of 4 commits): git_mining.py(3), views.py(3), incremental.py(3) — noise from 60-file M16 commits.
- claude-code/hooks/aa-ma-session-start.sh: no callers (hooks are called by settings.json); co-changed aa-ma-parse.sh(2).
- claude-code/skills/impact-analysis/SKILL.md: no callers (no plugin edges until 10.3); co-changed SECURITY.md, TODOS.md, codemem.md — noise.

## Latency (20 runs each, derived Edit payload, forge .venv python direct)
p50 67–69 ms, p95 72–77 ms, max 78 ms. ≤5 lines in all four.

## A1 (live, 2026-10-25)
Registered in .claude/settings.local.json mid-session; a real Edit on grammar.py delivered the
4-line `hookSpecificOutput.additionalContext` to the model. Real payload captured (scrubbed):
`PreToolUse-Edit.captured.json` — keys file_path, old_string, new_string, replace_all.

## Verdict (Ste, 2026-10-25) — verdict-changes-plan: YES
UX works; callers carry the signal. Plan delta: co_changes gains a large-commit filter
(ignore commits touching > N files, N=20) used by the hook/file_impact; 10.3 plugin edges
confirmed necessary; 10.6 adds real Edit/Write payload fixtures (none existed).

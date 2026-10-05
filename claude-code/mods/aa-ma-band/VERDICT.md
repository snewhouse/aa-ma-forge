# PROTOTYPE — aa-ma-band — PASS (Ste, 2026-10-05)

Throwaway branch `prototype/aa-ma-band`. Main keeps only the decision.

**Question:** can a Claude Code mod (v2.1.289, function hooks) keep AA-MA position, gate state, repo
hygiene and context % visible above the prompt, as a thin view over `aa-ma-gate`?

**Answer:** yes. It loaded via session hot reload from `~/.claude/dev-mods/<session>/aa-ma-band/`.

| Scenario | Result |
|---|---|
| `claude plugin validate` | passed: 6 hooks, calls limited to process.run, fs, session, clock and ui; one warning (no author) |
| A — active plan (fixture: M8 ACTIVE, 2 PENDING, HARD, CP) | band shown; `/band-variant detailed`, `compact`, `off` all switch (Ste: "looks good for 1st version") |
| B — two ACTIVE milestones (gate rc 3) | red `ambiguous milestone`, refreshed after the Edit by the `tool.call` hook |
| C — no plan | dim `AA-MA: no active plan · ctx 41%/70` |
| not verified | `main ↑N`; off-terminal `classic.UserPromptSubmit` context note (VS Code panel); `claude plugin test`; `tsc` |

**Learned**
- A question panel or permission prompt covers the band. An urgent state change (gate rc 2/3, ctx ≥ 70%)
  should also send one `$.ui.toast`, on the transition only.
- `prompt.context` is wrong for a changing note: it fires once per conversation and re-sending it spends
  the cache. `prompt.attachment` only rewrites the engine's own injections. Use
  `classic.UserPromptSubmit` → `additionalContext` instead.
- `aa-ma-gate` costs 0.06 s from `.venv/bin` and 0.26 s via `uv run`, so refreshing per turn is cheap.
- The forge path is hard-coded (`FORGE`). Production should read `AA_MA_ROOT`, set by `install.sh`.

**Security fix (background commit review, 2026-10-05):** two findings, both fixed in the second commit.
- **Code execution from an untrusted workspace.** The band ran the repo's own `.venv/bin/aa-ma-gate`, and its plain `git status` could run commands configured by the repo (core.fsmonitor, filter.*.clean). Now:
  - git and the gate run only for repos under `TRUSTED_ROOTS`; anywhere else the band says `repo outside trusted roots: band idle`
  - git runs with the global and system config dropped, plus core.fsmonitor=false and core.hooksPath=/dev/null (as `stamp.GIT_OVERRIDES` does)
  - the gate runs only from the forge's own venv
- **Terminal escape injection.** Every string that comes from the repo now passes through `clean()`, which strips C0/C1 and bidi control characters and caps the length, before it reaches the terminal or the model.
- Production: the allowlist moves to `userConfig`. Each mod's security review is an acceptance criterion.

**Next:** `/aa-ma-plan` a mods effort covering:
- `claude-code/mods/` home plus an `install.sh` entry for `CLAUDE_CODE_PLUGIN_DIRS`
- an ADR on the mods home and trust policy (build our own; unsandboxed)
- `claude plugin test` in CI
- the toast-on-transition change
- shortlist mods 2–6: context-70 guard, commit-coach, CI/PR pane, lessons badge, /aa-ma portfolio pane

Critical-Path: hook-modification.

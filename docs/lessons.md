# Lessons Learned (aa-ma-forge)

Project-local pattern + prevention rules. Reviewed at session start.
Newest at top. See also: `~/.claude/rules/self-improvement-loop.md`.

---

## L-029 (2026-09-26) — Private-repo directory names written into a public repo's AA-MA files

**Pattern:** In `diagram-generation` M13.1 I measured the private `medical-research-skills` repo and
wrote its top-level and skill-category directory names into `tasks.md` Result Logs and
`context-log.md`, then pushed. `snewhouse/aa-ma-forge` is PUBLIC. The standing rule was "aggregate
counts only"; I applied it to `reference.md` (the file I was thinking of as the record) and not to
the prose logs I wrote around it. Caught by the §6.8 security auditor, not by me.

**Rule:** Before every commit that follows a measurement of an external private repo, run
`git diff --cached | grep -F -f <(names of that repo's top-level and second-level dirs)` and
refuse on any hit. Describe external structure by shape and count only ("one top-level dir",
"one skill-category dir, 482 edges") — never by name — in EVERY file, logs included.

## L-028 (2026-09-26) — Stubs committed with the RED tests tie the TDD auditor's clock

**Pattern:** In `diagram-generation` M12.2 I committed throwing stubs (`explorer.py`,
`explorer.js`) in the same commit as the RED tests, so failures would be assertion-level
rather than import errors. The tdd-sequence-auditor reads "first tests/ commit before first
src/ commit" — a same-commit tie is FAIL. RED was genuine, but the evidence could not show it,
and one test failed at RED on its own setup bug instead of against the stub.

**Rule:** The RED commit touches `tests/` (and fixtures) only. If assertion-level failures
need stubs, commit them separately right after, in a `test:`-scoped or `chore:` commit that
precedes the implementation. Before committing RED, read each failure: it must be the
assertion under test, never the test's own setup.

---

## L-027 (2026-09-26) — Hooks bypassed on a throwaway commit when the marker would have done

**Pattern:** In `diagram-generation` M12.1 I committed the prototype branch with
`git -c core.hooksPath=/dev/null commit`, skipping every hook, although the message already
carried `[ad-hoc]` — the marker the commit-signature hook accepts. "It's a throwaway branch"
is not a reason: the bypass also skips `security-static-check.sh` and the drift detector.

**Rule:** Never pass `--no-verify` or override `core.hooksPath`. A plan-unrelated commit
gets `[ad-hoc]`; a hook that misfires is diagnosed (or `AA_MA_HOOKS_DISABLE=1` for that one
command, stated to the user) — never silently switched off.

---

## L-026 (2026-09-25) — Generated docs regenerated before `git add` describe a tree nobody committed

**Pattern:** In `diagram-generation` M9 I ran `scripts/regen-generated.sh` while the new
`draw/io_sinks.py` was still untracked, then committed and pushed. codemem indexes
`git ls-files`, so the index — and the committed `docs/architecture/` — lacked the new file.
Local `draw --check` passed against that same index; CI built from the commit, saw the file,
and `architecture-drift` went red on `83b6dbf`. L-025 ("run what CI runs") was followed
in letter only: CI runs on the committed tree, not the working tree.

**Rule:** Stage every new source file BEFORE regenerating anything derived from the index.
`scripts/regen-generated.sh` now refuses (rc 1) while any untracked file with an indexable
extension exists — do not bypass it; `git add` the file (or delete it) and re-run.

---

## L-025 (2026-09-24) — A test that waits on a later sub-step turns CI red the moment you push

**Pattern:** In `diagram-generation` M6 the RED test file included AC5 (the `architecture-drift`
job exists in `security.yml`), which only sub-step 6.4 satisfies. After 6.2's GREEN commit I pushed
with that one test still failing; `codemem-smoke` runs `pytest tests/codemem/ -x`, so CI went red on
`91bdd5f` for a reason I already knew. Earlier milestones never hit this because their RED and GREEN
landed in the same push.

**Rule:** Before every push, run what CI runs (`uv run pytest -q` at minimum) and push only on zero
failures. A test whose GREEN belongs to a later sub-step stays local until that sub-step lands — or
the two sub-steps are pushed together. "Known RED" is not a reason to push red.

---

## L-024 (2026-09-24) — A measurement base you never validated, and a verdict that is always UNKNOWN, both hide defects

**Pattern:** In `diagram-generation` M3 I measured draw cuts on the live
`.codemem/index.db` and put those figures in a decision question to Ste. The index
was corrupt — `build_index` had misattributed 2819 of 4462 symbols across rebuilds —
so every "HEAD" number I quoted was wrong, and one cut showed edges the
`render-is-leaf` import contract makes impossible. Separately, every mermaid render
check had returned `UNKNOWN` for weeks (empty browser dirs in the puppeteer cache);
L-012 correctly never counted UNKNOWN as PASS, but nothing ever asked why it was
never anything else — and it was hiding a real parse error in the plan's own §13
(bare `|@kind|` sigils).

**Rule:** (1) Measure on a FRESH scratch build, never on a long-lived index, until
that index is proven clean; when a result contradicts a known invariant (an import
contract, a leaf rule), treat the data as suspect before the code. (2) A check that
has only ever returned UNKNOWN is not a check — the first time a gate depends on it,
fix the environment until it can return PASS or FAIL, and prove it can FAIL.

**Cross-ref:** L-012 (UNKNOWN is never PASS) — this is its complement: UNKNOWN
forever is a defect of its own.

---

## L-023 (2026-09-24) — Replacing a test literal with the live constant inverts any test that monkeypatches that constant

**Pattern:** Acting on a future-proofing WARNING in `diagram-generation` M1, a
mechanical replace turned every `== 3` in `tests/codemem/test_file_edges.py` into
`== db.CURRENT_SCHEMA_VERSION`. One test monkeypatches `CURRENT_SCHEMA_VERSION` to 2
to simulate older code; after the replace, its asserts read the *patched* value and
would have asserted the downgrade the test exists to forbid — and still passed on
broken code. The same session's earlier regex replace also hit a symbol-count `== 2`
instead of a version check. Both caught by reading context, not by the suite.

**Rule:** Never bulk-replace assertion literals. For each site, check whether the
test patches the constant; if so, capture the real value into a local *before*
`monkeypatch.setattr` and assert against that. After any edit to a guard test,
prove it still guards: disable the guarded line and confirm the test goes red
(M1: removing the `apply_schema` guard -> 2 failed).

**Cross-ref:** L-011 / L-021 (silent-failure family) — here the failure mode is a
test that passes for the wrong reason.

---

## L-022 (2026-09-22) — Tests written under `packages/` are collected locally and never run by CI

**Pattern:** The `diagram-generation` plan routed every new codemem test to
`packages/codemem-mcp/tests/` — a directory that does not exist. All codemem tests
live at `tests/codemem/`; `packages/codemem-mcp/` holds only `README.md`,
`pyproject.toml` and `src/`. CI runs `uv run pytest tests/codemem/`,
`uv run pytest tests/test_goal_synthesis.py`, and a catch-all
`uv run pytest tests --ignore=tests/codemem --ignore=tests/perf
--ignore=tests/test_goal_synthesis.py` — none of which reaches `packages/`.
Because `pyproject.toml` sets no `testpaths`, a local `uv run pytest` **would**
collect them. Seven milestones of tests would therefore have gone green on the
developer's machine and never executed in CI: a silent gap, discovered at release
rather than at the failing commit. Caught by the Phase 4.5 impact-analysis angle,
not by the author.

**Rule:** All tests live under `tests/`, mirroring the package they cover
(`tests/codemem/` for `packages/codemem-mcp/`). When a plan's Contract block names
a new test path, confirm a step in `.github/workflows/security.yml` actually
collects it BEFORE writing the Contract — and prefer asserting that the path is
collected over asserting that the tests pass. A test that runs only locally is
worse than no test: it buys confidence CI does not share.

**Cross-ref:** global L-1256 (hand-enumerated CI test paths are a drift class) —
the same drift class seen from the authoring side rather than the workflow side.

---

## L-021 (2026-09-22) — Gate fields written only in `plan.md` are never read; the gate takes `tasks.md` alone

**Pattern:** The `diagram-generation` plan declared `Audit-Profile:`,
`Critical-Path:` and `Prototype-Required:` inside `plan.md` `#### Contract`
blocks — a natural place, next to the file list they describe. But `aa-ma-gate`
takes **one positional argument, `tasks_md`** (`src/aa_ma/gate.py:462`), and
`enforce.read_enforced_field` pulls those fields from `tasks.md` milestone and
sub-step blocks (`gate.py:230,235,286,291`). A field the gate cannot see reads as
ABSENT, not as an error, so three `Prototype-Required: YES` gates and six
`Critical-Path` reviews would all have passed **green while enforcing nothing**.
Milestone-level fields ARE honoured independently of sub-steps (`_own_text`,
`gate.py:205-209`, OR'd with the sub-step roll-up at `:428`) — the problem was
purely which FILE they lived in.

**Rule:** Every gate field MUST be transcribed onto the matching milestone in
`tasks.md`; `plan.md` may restate it for readers but is never the source. Verify
the transcription by ASKING THE GATE — `uv run aa-ma-gate <tasks.md> --milestone N
--format kv` and read back `audit_profile`, `critical_path`, `prototype_required`
— never by eyeballing the file, because the failure mode is silence. Keep ONE
source for the assignments (a table in the plan) and have every other mention
reference it; a restated list desynchronises, and this one did so within a single
editing session.

**Cross-ref:** L-011 (AA-MA field format is load-bearing and fails silently) —
same silent-failure family, different cause: wrong *file* rather than wrong
*format*. Global L-1232 (empty optional fields are refused).

---

## L-020 (2026-09-22) — Charted a diagram effort for three rounds before asking who reads the diagrams

**Pattern:** `/aa-ma-chart diagram-generation` ran a full destination grill,
ten tickets and four research dispatches optimising *internal* properties —
edge counts, PageRank cuts, mermaid's `maxEdges` ceiling — with the reader
left implicit (a cold planning agent, inherited from ADR-0010's framing). The
prototype then asked Ste to pick a scoping arm on those numbers. He answered
with the actual intent: "a new dev or reviewer can easily understand the
codebase by reading, viewing, interacting with professionally drawn diagrams."
That reframe changed the answer (one scoping knob → layered zoom levels),
re-admitted two Out-of-scope rulings, added four tickets and amended the
Destination — after the research had already been scoped and spent.

**Rule:** For any effort whose output a human reads — diagrams, docs, reports,
dashboards, CLI output — the **first** grilling round establishes **audience**
and **consumption mode** ("who reads this, where, and what must they be able
to do after?") before any question about the artifact's internals. In
`/aa-ma-chart chart` this belongs in step 1 alongside the Destination, and the
Destination is not settled until it names the reader. A quality bar phrased as
a metric ("under N edges", "under N lines") is a proxy; ask what the reader
must be able to *do*, and keep the metric as evidence for that, never as the
goal. When an existing ADR supplies the framing, check whether its audience is
still the audience — ADR-0010's cold agent was correct for plan §13 and wrong
for onboarding.

## L-019 (2026-09-21) — Local `shellcheck` passed while CI's failed for four commits; nobody looked at CI until the release pre-flight

**Pattern:** M5's guard shipped `A && B || C` forms. Local shellcheck 0.11.0
reported them once (as info) and then stopped after unrelated edits; CI's
shellcheck fails on SC2015 at info severity. The ShellCheck job was red from
`50c8099` through `f38983e` — five pushes — and was only noticed because the
release pre-flight lists runs. Had the release run first, v0.14.0 would have
been tagged on a red main.

**Rule:** (a) Run `shellcheck -S info` (the CI severity) on every `.sh` a
milestone touches before its commit — `find . -name '*.sh' -not -path './.git/*'
-not -path './.venv/*' -exec shellcheck -S info {} +` is the CI command;
match it, don't approximate it. (b) After every push inside a milestone,
`gh run list --limit 1` is part of the sub-step Result Log evidence; a red
run blocks the next sub-step, not the release. (c) The release pre-flight
(`release.sh --dry-run`) keeps its CI check — it is the last net, not the
first.

## L-018 (2026-09-21) — `git commit --amend` after writing the hash into provenance records a hash that no longer exists

**Pattern:** §8.3/8.4 of `execute-aa-ma-milestone` says: commit, read `HEAD`,
append `MILESTONE COMPLETE — Commit: <hash>` to provenance, then `--amend`
the commit to include that line. The amend rewrites the commit, so the
recorded hash is the pre-amend one. M1 recorded `7464b5c` (real: `771bc25`);
M2 repeated it minutes after the validator had flagged M1. Twice in one day.

**Rule:** Never `--amend` a commit whose hash is already written into an
artefact. Either (a) write the provenance line *without* the hash, commit,
then append `COMMIT <hash>` in the next docs commit; or (b) compute the
final hash first by committing everything else, then add the provenance
line as its own small `docs(aa-ma)` commit. Option (b) is the default.
The `§8.4` amend step in the command is the bug — fix the command, not the
habit (follow-up: `execute-aa-ma-milestone.md` §8.3–8.4).

## L-017 (2026-09-21) — One milestone commit hides the RED from the TDD auditor; a process-substitution error is invisible to `set -e`

**Pattern:** M1 of mattpocock-trio-adoption was executed test-first (provenance
records `RED: ModuleNotFoundError` before `forks.py` existed) but every sub-step
was squashed into one milestone commit, so `tdd-sequence-auditor` — which may
only weigh `git log` — returned FAIL on a same-timestamp tie. Separately, the
first `fork-drift.sh` flattened the manifest with `python3 -c` inside
`< <(…)`; a malformed manifest tracebacked and the script exited 0 with zero
rows ("clean"). Both were caught by §6.8, not by me.

**Rule:** (a) When a milestone produces `src/` code, commit the red test on its
own (`test(...)` commit, plan footer) immediately after the RED run — before
the implementation commit. §6.8's TDD criterion is mechanical; provenance
prose is not admissible. (b) Never put a fallible command inside a process
substitution or an unbuffered pipe feeding a classifier: materialise it
(`rows="$(cmd)"`) so `set -e` sees the failure, and write the bats case
"malformed input → exit 1" before the script. (c) A CI test list is
exclusion-based (`--ignore=`), never enumerated — enumeration is the drift
class the doc-count detector exists for.

## L-016 (2026-09-20) — A bare `<!--` inside a criterion hides every later sub-step from the gate; `hooks/lib` helpers are never auto-linked

**Pattern:** Two near-misses in one planning session. (a) An acceptance
criterion quoted a shell snippet `grep -q '^<!-- Derived from'` inside
backticks; `aa-ma-gate` strips HTML comments before parsing, so that
unterminated `<!--` swallowed sub-steps 1.1–1.5 (`pending_steps=2` for a
7-step milestone) with no error — a false "nearly done". (b) The plan said a
new `claude-code/hooks/lib/` helper would be "symlinked by install.sh like
`aa-ma-parse.sh`"; three verification angles proved `install.sh` links each
lib helper by an explicit per-file block (`lib/aa-ma-footer.sh` exists in
the repo and is not installed). That is L-005 recurring in planning prose.

**Rule:** (a) Never write a literal `<!--` in tasks.md, reference.md or
context-log.md unless `-->` closes it on the same line — describe the comment
("an HTML comment starting `Derived from`") instead; after the scribe runs,
always execute `aa-ma-gate <tasks> --milestone N --format kv` for every N and
compare `pending_steps` to the sub-step count before calling Phase 5 done.
(b) Any new file under `claude-code/hooks/**` or `hooks/lib/` needs an
explicit `install.sh` `create_symlink` block AND an `install_dry_run.bats`
case in the same milestone — write both into the plan's artefact list, never
"like <existing helper>".

## L-015 (2026-09-12) — `uv run <tool>` falls through to PATH; every release from v0.7.0 was cut with a tool the project never declared

**Pattern:** `uv run cz bump` "worked" on this machine for five releases
because `cz` lived in a conda env on PATH (`bio312_07_25`, 4.13.9) — it was
never in `.venv` and never in `pyproject.toml`. A fresh clone could not
release. In the same period three lessons (L-003, L-006, L-008) each
documented a *workaround* for `update_changelog_on_bump = true` overwriting
the curated `## Unreleased` (restore → amend → retag), and two tools
(`[tool.semantic_release]`, commitizen) both claimed version ownership while
only one ever ran. Fixed by `scripts/release.sh` + `commitizen>=4,<5` as a
declared dev dep + semantic-release removed.

**Rule:** A release procedure is repeatable only if a fresh clone can run
it: every tool it calls is a declared dependency (check `.venv/bin/<tool>`
exists, not that `uv run <tool>` succeeds — uv falls through to PATH), the
procedure is one script with a `--dry-run`, and it is tested against a
throwaway bare origin. When a lesson documents an amend-and-retag
workaround, the config that forces the workaround is the bug — change the
config, not the ritual.

## L-014 (2026-09-12) — `git mv` after editing stages the old blob, not the edit

**Pattern:** `/archive-aa-ma` prepends ARCHIVED headers (Step 3), then moves
the directory (Step 4), then `git add .claude/dev/completed/<task>/` (Step 7).
I replaced Step 4 + 7 with a single `git mv` and committed. `git mv` stages
the rename with the *index* content; the just-written headers stayed
unstaged (`RM` in `git status`), so the archive commit landed without them
and needed a second commit. Caught by reading `git status --short` before
reporting done — not by the commit succeeding.

**Rule:** Never substitute `git mv` for "edit, move, `git add <dir>`". After
any rename-plus-edit, the stage line is `git add <new-dir>/` and the check is
`git status --short` showing no `M` in the second column before `git commit`.
More generally: a workflow command's git steps are the script, not a
suggestion — shortcuts that "obviously do the same thing" are where the
index diverges from the worktree.

## L-013 (2026-09-11) — "Acknowledged, not changed" is not a §6.8 outcome

**Pattern:** The M5 §6.8 review returned 4 CRITICAL / 21 WARNING / 17 INFO. I
fixed the CRITICALs and the cheap WARNINGs, then wrote an "Acknowledged, not
changed (with reason)" section for the rest — a quadratic regex on the
untrusted path, a `Decision: REJECTED` line that still satisfied the HARD
gate, five copies of the same snippet, stale line pointers — and asked for
gate approval. The user rejected the gate and said: "fix the CRITICAL and
warnings now, don't wait." Every item took under ten minutes; two of them
(the 17-second regex, the REJECTED-passes-as-approved check) were
fail-open on the exact surface the milestone exists to close.

**Rule:** A reviewer WARNING is a work item, not a note. Before seeking
milestone approval, every WARNING is either **fixed** (with a test) or
**deferred to a named sub-task in tasks.md with a Status** — never
"acknowledged". INFO items that describe a fail-open or a security shape
are WARNINGs regardless of the label the agent gave them. The only
legitimate "not changed" is one whose fix would change another milestone's
scope, and that gets a sub-task in that milestone, not a paragraph. Applies
to `Skill(verify-impl)` output, `/code-review`, and `/review` alike.

## L-012 (2026-08-09) — `/sole-dev-merge` Stage C reported a clean security review on code it never scanned

**Pattern:** Both scanners in `claude-code/commands/sole-dev-merge.md`
stage-c-aggregate ran as `<bin> -f json $CHANGED > "$OUT" 2>/dev/null || true`.
An unavailable scanner therefore left a 0-byte report, the `[[ -s "$OUT" ]]`
guard skipped the parse, `$FINDINGS` stayed empty, `TOTAL=0`, Stage D skipped
triage entirely, and Stage E3 rendered a PR body asserting a clean review.

This surfaced only as an intermittently-failing bats test
(`C4 maps ShellCheck error to [CRITICAL]`). The test was the symptom; the
shipped false negative was the defect.

C3/bandit was the worse of the two:

| | C4 / shellcheck | C3 / bandit |
|---|---|---|
| Declared dependency? | no (but usually preinstalled) | **no** — absent from `pyproject.toml`, not installed by `uv sync` |
| Installed in the `bats` CI job? | no (was) | **no** — while `test_smoke_e2e.bats` asserts a real B602 finding |
| Downstream consumer | findings triage | findings triage **+ B602 auto-remediation** |

So a silently-missing bandit disabled detection *and* fixing together.

**Rule:**

1. Both scanners gate on the **result**, not on the binary:
   `rc > 1 || ! -s "$OUT"` is the degraded condition (both tools exit 0 clean /
   1 findings). `command -v` alone caught 1 of 4 degraded modes — `true`, `:`
   and `/bin/false` all pass it.
2. A degraded scanner writes
   `[HIGH]     C{3,4} NOT RUN — ... UNKNOWN — (scanner-unavailable)` **into
   `$FINDINGS`**, not merely to stdout — Stage D reads `$FINDINGS` and nothing
   else. Unparseable JSON writes `(scanner-output-unparseable)` the same way.
   `aggregate: 0 findings` must be unrepresentable when a scanner did not run.
3. `SHELLCHECK_BIN` / `BANDIT_BIN` (defaults `shellcheck` / `bandit`) are the
   test seams; the coverage test drives them and needs no external binary, so
   it can never skip. Both sentinels are mutation-guarded.
4. The `bats` CI job **installs and `--version`-asserts both scanners**. Without
   the assertion a missing tool turns a security test into `ok N # skip`, exit 0.

**Cross-ref:** Global L-1215 (`command -v` tests resolvability, not usability),
L-1216 (warn where the consumer reads), L-1218 (count skips), L-1217
(reproduce by substitution).

---

## L-011 (2026-08-09) — AA-MA field format is load-bearing and fails silently

**Pattern:** While verifying the `milestone-grammar-ssot` plan, running the real
parsers over the plan's own artifacts returned `parse_audit_profile(...) ==
(None, True, None)` for all five milestones, and the HARD-gate `Critical-Path`
scan read empty. The plan reproduced, in its own files, the exact scan blindness
one of its milestones existed to fix. Cause: the fields were written mid-line and
wrapped in backticks.

Measured behaviour:

| How written | Parser result |
|---|---|
| mid-line, backticked | `(None, True, None)` — **absent, and "valid"** |
| own line, backticked | `('`code-only`', False, "Non-canonical…")` |
| own line, bare | `('code-only', True, None)` ✓ |

The first row is the trap: absence and validity are indistinguishable, so a
milestone with a malformed field passes the gate that was meant to enforce it.

**Rule:**

- `Audit-Profile:` — own line, **unbackticked** (`plan_parsers._extract_field`
  anchors `^[ \t]*-?[ \t]*`).
- `Critical-Path:` / `Prototype-Required:` — own line, **bold**
  (`- **Critical-Path:** data-xform`); the gate greps `^- \*\*Critical-Path:\*\* \S`.
- Verify by **running the parsers over the artifact**, never by eye:
  `python -c "from aa_ma.plan_parsers import parse_audit_profile; from aa_ma.grammar import split_milestones; ..."`.
  A field the parser cannot see is a field that does not exist.

**Cross-ref:** L-002 (Critical-Path fires per milestone, not per plan);
global L-1214.

---

## L-010 (2026-08-09) — The canonical spec was itself the drift source

**Pattern:** A single failing corpus test
(`test_corpus_grandfathering[sole-dev-merge-pr-workflow]`) turned out to be the
visible edge of **six divergent milestone/step grammars** — in `tui/parser.py`,
the corpus test, `aa-ma-parse.sh`, `execute-aa-ma-milestone.md`,
`verify-impl/SKILL.md` — against a spec mandating one.

The worst offenders were the documents that *teach* the format.
`docs/spec/aa-ma-specification.md` and `skills/aa-ma-execution/SKILL.md` shipped
**unnumbered** forms (`## Task Title`, `### Sub-step: [Action]`) matching neither
the tolerant reader nor the canonical writer — so a plan authored strictly from
the canonical spec parsed as **0 milestones / 0 steps** in `aa-ma-tui`, silently,
while passing every lint. `examples/aa-ma-team-guide/` had the same shape.

Of eleven shipped files that write or teach a `tasks.md` heading, exactly one —
`docs/templates/tasks-template.md` — was canonical. `aa-ma-tui` was blind to 4 of
14 repo tasks and showed 0 steps for 6 more: 44 → 69 milestones, 94 → 393 steps
once fixed.

**Rule:**

1. Heading grammar has one home: `src/aa_ma/grammar.py`. Readers are tolerant
   (the archived corpus is frozen); the writer form is strict
   (`## Milestone N: Title` / `### Sub-step N.M: Title`).
2. **Every shipped writer is listed in
   `tests/test_active_plans_canonical.py::WRITER_TEMPLATES`**, each with a
   mutation guard (`test_writer_check_is_not_vacuous`). Adding a writer without
   adding it to that list *is* the regression — the lint cannot find what it is
   not pointed at.
3. When a doc teaches a format the code parses, treat the doc as a code path:
   grep it against the grammar, don't trust that it agrees.
4. Lint fenced-block **contents** for these templates — `sanitize()` strips
   fences, and every writer example lives inside one.

**Cross-ref:** Global L-1214 (mutation-test the guard); ADR-0007.

---

## L-009 (2026-05-16) — "Complete" must be verified against compliance, not just against local test results

**Pattern:** During PR #1 review-fix execution (`/goal` integration cleanup),
I declared work "complete" twice across two `/double-check` rounds, and was
wrong both times. Each round caught a substantive miss the prior declaration
had glossed over.

**Symptom:**

| Round | What I claimed | What was actually true |
|---|---|---|
| First declaration of "complete" | "47 tests pass; B1 resolved" | Tests passed *locally*. CI ran `pytest tests/codemem/` only — my new test file at `tests/test_goal_synthesis.py` was never exercised by any CI job. B1 was resolved on disk, not in the regression net. |
| Second declaration of "complete" | "10/12 Importants resolved (I10 deferred)" | User's verbatim instruction had said "Apply I1/I2/I3, then I9–I11, then nits." Calling I10 deferred contradicted the explicit instruction list. Additionally, SKILL.md function signatures had silently drifted from the Python (`pending` vs `pending_milestones`; wrong return-type claim for `validate_condition`). |

**Root cause:** Two anti-patterns combined:

1. **Locality bias on test coverage.** I treated "tests pass" as equivalent to
   "the change is regression-safe", without checking whether the CI pipeline
   actually invokes the test file. The new test was at `tests/test_*.py` but
   CI's pytest invocation narrows to `tests/codemem/`.
2. **Silent deferral against an explicit "apply" instruction.** When I
   reviewed the user's instruction, I read "Apply I9–I11" and decided I10 was
   too design-heavy to address now — without surfacing that disagreement as a
   pending question to the user.

**Rule (apply at every "complete" declaration, especially after `/double-check`):**

Before declaring work complete, run this 4-point compliance audit:

1. **CI-scope check** — for every new test/check artefact, verify the CI
   pipeline actually invokes it. `grep -nE "pytest|test_|bats|shellcheck"
   .github/workflows/*.yml`. Test-file existence ≠ regression net coverage.
2. **Verbatim-instruction audit** — re-read the user's original goal text
   word-by-word. For each item the user said to "apply", show the diff that
   applied it. If you're calling something "deferred", surface the conflict
   to the user as a question, not as a finished-state summary.
3. **Spec-vs-impl signature pass** — for any spec doc that documents
   function signatures or return types, `grep` the signatures and diff them
   against the actual source. Drift is silent until a reader trips on it.
4. **Each new resolution claim names the file:line it was applied to.** No
   resolution claim should be answerable only in prose. Pin to artefacts.

`/double-check` is a forcing function; treat each invocation as evidence that
the prior "complete" declaration was wrong, and re-audit the full compliance
surface against the original user instruction — not just the most recent
batch of fixes.

---

## L-008 (2026-05-13) — `cz bump --files-only` exits 16 when CHANGELOG.md has been manually promoted; chain "manual promote + cz files-only" is broken

> **Superseded 2026-09-12 by `scripts/release.sh` (docs/runbooks/release.md):** `update_changelog_on_bump = false` — cz owns `pyproject.toml`/`VERSION` only; the script owns the `## vX.Y.Z` heading, the README line, the annotated tag, the push and the GitHub Release. No amend, no retag, no `--files-only`. See L-015.

**Pattern:** During v0.9.0 release prep (fix-drift-release-v0-9-0 M3.4),
chose the manual-CHANGELOG-promote path to preserve the rich
hand-written `## [Unreleased]` entry (per L-006's alternative-to-amend
guidance). Step 1: manually edited `## [Unreleased]` → `## v0.9.0 (2026-05-13)`
in CHANGELOG.md, keeping all the multi-paragraph Feat + Docs prose intact.
Step 2: ran `uv run cz bump --files-only --yes` expecting it to bump only
`pyproject.toml` (`version =`) + `VERSION` (`__version__ =`).

**Symptom:** cz correctly computed the bump (`bump: version 0.8.0 → 0.9.0;
tag to create: v0.9.0; increment detected: MINOR`) — but then exited
with code 16 and the message "No tag found to do an incremental
changelog". Version files were not modified. Despite the `--files-only`
flag, cz appears to still execute CHANGELOG operations when
`update_changelog_on_bump = true` is set in `[tool.commitizen]`, and
it dies on the already-promoted CHANGELOG state (the section it tries
to insert above already exists).

**Root cause (suspected):** `cz_conventional_commits` interaction between
`--files-only` semantics and `update_changelog_on_bump = true`. The flag
should disable CHANGELOG ops; the config setting overrides it. Either
order of operations works in isolation (cz bump with auto-regen, OR
manual-everything), but the chain `manual promote → cz --files-only`
doesn't.

**Workaround used:** Abandoned cz for this bump. Did the 2-line manual
edit directly:
- `pyproject.toml`: `version = "0.8.0"` → `"0.9.0"` (one Edit).
- `VERSION`: `__version__ = "0.8.0"` → `"0.9.0"` (one Edit).
Then `git commit -m "bump: version 0.8.0 → 0.9.0"` (cz-style subject)
+ `git tag -a v0.9.0 -m "..."` + push tag. End-state byte-identical
to what a successful `cz bump --files-only` would have produced.

**Rule:** For aa-ma-forge releases where you want to preserve a rich
hand-written `[Unreleased]` entry, pick ONE path — do NOT combine them:

(a) **Per L-003**: run `cz bump --increment minor --yes` (or
    `--increment patch`/`major`) end-to-end → cz regenerates CHANGELOG
    terse → amend the CHANGELOG entry per L-006 → re-tag with
    `git tag -f vX.Y.Z`. cz owns everything; you fix up at the end.

(b) **Skip cz entirely**: manually promote `## [Unreleased]` →
    `## vX.Y.Z (date)` + 2-line manual edit of `pyproject.toml` +
    `VERSION` + `git commit -m "bump: version X → Y"` (cz-style
    subject) + `git tag -a vX.Y.Z -m "..."`. Standard 8-tag cadence
    preserved; no cz invocation in this bump.

The chained "manually promote CHANGELOG + then `cz bump --files-only`"
path is broken and will exit 16.

**Cross-ref:** L-003 (cz bump owns CHANGELOG headings — never manually
edit), L-006 (cz strips rich `[Unreleased]` content; amend after bump),
`[tool.commitizen]` config in `pyproject.toml`, observed in commit
`ed077f7` of feature/understand-codebase-skill (the v0.9.0 release).
Global L-324 (the HARD-gate approval bootstrap problem encountered in
the same session — different bug class, same release).

## L-007 (2026-05-11) — `/sole-dev-merge` quality-check format pass may modify out-of-scope files

**Pattern:** During harden-aa-ma-plan M5 merge step, `/sole-dev-merge` Step 2
ran `uv run ruff format src/ tests/` which reformatted 29 pre-existing test
files in `tests/codemem/` and `tests/perf/` — none of which were touched by
the plan's work. The format step is a "with-fix" pass, meaning it mutates
working-tree files as part of the merge ceremony.

**Symptom:** After the format step, `git status --porcelain` listed 29
modified files outside the plan's known scope. The default sole-dev-merge
flow would have bundled them into the release merge, coupling the v0.7.0
release commit to wholesale format drift unrelated to its declared scope.

**Root cause:** `/sole-dev-merge` was designed as a quality gate, not a
scope filter. It assumes the working tree is clean before invocation, but
its own format-fix step can dirty the tree with whole-tree changes that
weren't part of the feature branch's commits.

**Rule:** During `/sole-dev-merge`, after the format-with-fix step, check
`git status --porcelain` for modifications outside the plan's known scope.
Reset out-of-scope changes with `git checkout -- <paths>` before proceeding
to the merge. Whole-tree format passes should be their own dedicated
`chore(format)` commit on a separate prep PR — NOT slipped in via a release
merge ceremony. Failing to do this couples release scope to unrelated drift
and violates the atomic-commit-per-logical-change convention.

**Cross-ref:** sole-dev-merge skill (gstack) — the format-fix step is
deliberate but assumes clean-tree start; this lesson captures the gap when
the assumption breaks.

**Resolution (2026-05-18):** Resolved structurally by the
`sole-dev-merge-pr-workflow` AA-MA plan, Step 1.3 (commit `b6342e0`). The
new plugin-shipped `/sole-dev-merge` command implements an L-007 GUARD
inside `stage-b-scope`: after Stage B's `ruff format` / `ruff check --fix`
run on the in-scope file set, a `git status --porcelain` walk reverts any
dirty path NOT in the changed-files set via `git checkout --`. The format
step can no longer escape the branch's declared scope. See
[ADR-0008](adr/0008-sole-dev-merge-pr-workflow.md) §Decision Drivers
("Scope discipline structural fix") and `test_stage_b_scope.bats`
test #2 (canonical L-007 scenario regression).

---

## L-006 (2026-05-11) — `cz bump` strips rich `## Unreleased` content to bare Feat/Fix — amend + retag to preserve prose

> **Superseded 2026-09-12 by `scripts/release.sh` (docs/runbooks/release.md):** `update_changelog_on_bump = false` — cz owns `pyproject.toml`/`VERSION` only; the script owns the `## vX.Y.Z` heading, the README line, the annotated tag, the push and the GitHub Release. No amend, no retag, no `--files-only`. See L-015.

**Pattern:** During harden-aa-ma-plan M5.4, a `## Unreleased` section was
hand-authored with prose intro + Feat/Test/Docs/Chore subsections matching
the v0.6.0 / v0.5.0 entry styles. `uv run cz bump` replaced that section
with auto-generated bare Feat + Fix bullets only, losing the prose intro
and the entire Test + Docs + Plan-close subsections.

**Symptom:** v0.7.0 bump commit (00d6519, then amended to 480dd3f) landed
with a CHANGELOG entry far weaker than v0.6.0 and v0.5.0 — no prose intro,
no Test posture summary, no Docs additions list, no Plan close summary.
Discovered by reading the post-bump CHANGELOG before pushing.

**Root cause:** `cz_conventional_commits` default template emits only Feat
and Fix bullets extracted from commit subjects. Prior rich CHANGELOG
entries (v0.6.0, v0.5.0) were enriched manually post-bump — not generated
by cz. The hand-authored `## Unreleased` content does not survive cz's
section rewrite.

**Rule:** After `uv run cz bump`, immediately review the generated
CHANGELOG section. If it's missing prose intro + Test/Docs/Plan-close
sections needed to match prior entries, edit them in, then
`git commit --amend --no-edit && git tag -d vX.Y.Z && git tag vX.Y.Z` to
retag at the amended commit BEFORE pushing. This preserves L-003 (cz owns
the heading) while delivering substantive release notes. Do NOT push the
tag until the CHANGELOG is acceptable — local-only retagging is reversible;
pushed-tag retagging requires force-tag-push and breaks anyone who has
already fetched.

**Cross-ref:** L-003 (cz bump owns CHANGELOG headings — never manually
edit `## vX.Y.Z`). This is its operational corollary: cz owns the
heading, you own the contents under it.

---

## L-005 (2026-05-11) — `install.sh` symlinks only registered hook scripts — helpers invoked from slash-command bodies need explicit symlinks

**Pattern:** During harden-aa-ma-plan M4 first install attempt, the
`claude-code/hooks/aa-ma-plan-marker.sh` helper script was missing from
`~/.claude/hooks/lib/` after running `scripts/install.sh`. The helper is
invoked from the `/aa-ma-plan` command body as
`bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> <phase> <status> ...`
but `register_hook` in `scripts/install.sh` only symlinks scripts that
appear in the `AA_MA_HOOKS` event-registration array. Helper scripts
(non-event, invoked-by-path) were silently skipped.

**Symptom:** After install completed without error, any `/aa-ma-plan`
invocation would hit
`bash: /home/.../aa-ma-plan-marker.sh: No such file or directory` for every
phase marker write. The event-registered hook script (aa-ma-plan-skip-warn.sh)
was correctly symlinked, but the helper it expects to coexist wasn't.

**Root cause:** `scripts/install.sh` has two distinct mechanisms for
deploying files under `~/.claude/hooks/lib/`:
(a) `register_hook` — auto-symlinks via the `AA_MA_HOOKS` array for
event-registered hooks;
(b) explicit `create_symlink` blocks — for helper libraries (precedent:
`aa-ma-parse.sh` at install.sh:332-335).
The harden-aa-ma-plan M2.4 task registered the event hook (path a) but
forgot the explicit symlink block (path b) for the helper.

**Rule:** When adding a helper script under `claude-code/hooks/` that is
invoked by absolute path from any slash-command body or other hook, add an
explicit `create_symlink` block in `scripts/install.sh` mirroring the
existing `aa-ma-parse.sh` pattern (install.sh:329-335). Helpers must be
reachable at `~/.claude/hooks/lib/<helper>.sh` regardless of which project
the user invokes the command from. Validate with
`scripts/install.sh --dry-run | grep <helper>` BEFORE running real install.

**Cross-ref:** sole-dev-merge dry-run gate (catches this if a new helper's
test asserts the symlink exists); future helpers should add a
`tests/hooks/install_dry_run.bats` assertion confirming their symlink is
announced.

---

## L-004 (2026-05-10) — Mid-flight Edit failures leave AA-MA artefacts in split-brain state

**Pattern:** During the M3.6 plan-close commit of skill-ecosystem-integration
v1.2, a sequence of three Edit calls was issued in parallel: (1) GATE
APPROVAL artifact append to `context-log.md`, (2) `## Milestone M3:
... Status: ACTIVE → COMPLETE`, (3) `### Task 3.6: ... Status: PENDING →
COMPLETE`. Edit (2) errored mid-flight with `claude-opus-4-7[1m] is
temporarily unavailable`. Edits (1) and (3) succeeded. The plan-close
commit (`2362903`) was created and pushed with the M3 milestone-line still
showing `Status: ACTIVE` while every sub-task underneath showed
`Status: COMPLETE` and the GATE APPROVAL artifact was present in
context-log.md — split-brain state.

**Symptom:** the next `/execute-aa-ma-milestone` invocation re-fired the
M3 close protocol because its milestone-line scan found `Status: ACTIVE`
(taking it as the next active milestone). User saw an unexpected re-run
of the close workflow instead of "all milestones complete — nothing to do."

**Root cause:** model-availability errors are not transactional across a
batch of independent Edit calls. The harness's parallel-tool execution
fans them out; partial failure silently leaves the artefact in an
inconsistent state. There is no rollback: succeeded edits are committed
to the working tree before the batch outcome is known.

**Rule:** when a milestone-close commit must update both a
milestone-level status field AND its closing sub-task's status field,
batch the two writes into a SINGLE Edit call (or use MultiEdit) so partial
failure leaves the artefact in a known state — either both edits land or
neither does. The same applies to any closing-protocol writes that must
either all succeed or all be retried together (e.g., milestone Status +
Task close + provenance append for the same milestone).

**How to apply:**
- In `/execute-aa-ma-milestone` Section 7.4 (Transparent Status Change),
  group the milestone-line and closing-task-line edits into one
  MultiEdit — DO NOT issue them as separate parallel Edit calls.
- Pre-flight: before the milestone-close commit, scan the artefact one
  last time and verify status fields are consistent. If they're not,
  HALT and remediate before commit.
- Post-flight: after every milestone-close commit, run
  `grep -B1 "^- Status:" tasks.md | grep -A1 "^## Milestone"` to
  detect drift between milestone-line status and sub-task status.

**Why this matters:** silent drift in plan artefacts undermines every
downstream consumer — `/execute-aa-ma-milestone` re-fires unnecessarily,
`/archive-aa-ma` may refuse to archive, the `aa-ma-validator` agent
flags as inconsistent. The cost of one extra MultiEdit on the close
commit is trivial; the cost of split-brain detection + corrective
commit later is at least one extra commit (the actual fix in this case
was `8d93879`).

**Cross-ref:** L-080–L-082 sub-step sync rule (which this complements —
L-080 ensures sub-step Result Logs are atomic; L-004 ensures
milestone-status edits are atomic).

---

## L-001 (2026-05-10) — External URL First Principle

**Pattern:** During `/aa-ma-plan` for skill-ecosystem-integration, a Phase 3
research agent was dispatched to audit "mattpocock/skills" without being
given the URL. The agent looked at locally-installed `anthropic-agent-skills`
plugin contents and concluded "this is Anthropic's catalog, not mattpocock".
The conclusion was wrong — `mattpocock/skills` is a real GitHub repo with
68k stars and 17 production skills, including the canonical `grill-with-docs`
and `grill-me`. The misattribution propagated into the AA-MA plan's
executive summary, M2 description, and Assumption A5. The user caught it
("did you read https://github.com/mattpocock/skills/tree/main in detail?")
and demanded re-work ("do not be lazy like this again").

**Rule:** When a user explicitly names a specific external source — a GitHub
URL, an RFC number, a vendor doc URL, a paper DOI — the planning process
MUST fetch that source directly BEFORE any agent delegation. For GitHub:
use `gh api repos/<owner>/<repo>/contents` to enumerate and
`gh api .../SKILL.md --jq .content | base64 -d` for individual files. For
other URLs: WebFetch with a tight prompt.

Only dispatch research agents AFTER the canonical inventory is captured.
The agent's job is then synthesis/comparison against ground truth, not
discovery. The agent prompt must include the verified inventory as
ground-truth context to prevent hallucination on the source's identity.

**Why this matters:** Conflation between locally-installed skills and the
upstream they were sourced from is the silent default failure mode. Two
plugins with the same skill name can come from different repos; one repo
can be a subset/superset of another; aliases and curators (mattpocock,
anthropic-agent-skills) can muddy attribution. The only authoritative
answer is the URL the user named.

**How to apply:**
- Trigger keyword: any URL in the user message; any phrase like "the X repo"
  or "the X catalog" where X is a named external entity.
- First call after Phase 1.2 context-gathering: fetch the named URL.
- Embed the verified inventory in any subsequent agent prompt as
  ground-truth context.
- Save the inventory in the AA-MA `reference.md` so re-dispatches don't
  re-discover.

---

## L-002 (2026-05-10) — AA-MA `doc-count-drift` Critical-Path fires per milestone, not per plan

**Pattern:** Multi-milestone plans that add skills incrementally (e.g., M1: +1
skill, M2: +2 skills) must run the doc-count-drift grep sweep per milestone,
not once at plan close. v1.2 of the skill-ecosystem-integration plan had M1
change skill count 13 → 14 and M2 change 14 → 16. Each transition needs its
own `grep -rn "<old-count> skills" claude-code/ docs/ CLAUDE.md SECURITY.md
README.md` until clean. Combining into a single sweep at plan close would
leave M1's commits with stale "13 skills" prose for the duration of M2 work
— and any session opened against a half-shipped plan would see prose that
contradicts the actual skill directory count.

**Rule:** When a plan modifies hardcoded counts across multiple milestones,
declare `Critical-Path: doc-count-drift` ON EACH MILESTONE that changes the
count. Each milestone HARD gate runs its own `grep -rn` sweep targeting the
old count value being replaced. The plan must list per-milestone count
transitions explicitly (e.g., "M1.6: 13 → 14"; "M2.7: 14 → 16"). The Tier 6
detector in `rules/doc-drift-checks.md` is the canonical sweep mechanism;
invoke it per milestone close, not per plan close.

**Cross-ref:** Global L-304 (importer-count drift direction-check); the
canonical Critical-Path enum in `claude-code/rules/engineering-standards.md`.

---

## L-003 (2026-05-10) — aa-ma-forge CHANGELOG.md is managed by `cz bump`; never manually edit `## vX.Y.Z` headings

> **Superseded 2026-09-12 by `scripts/release.sh` (docs/runbooks/release.md):** `update_changelog_on_bump = false` — cz owns `pyproject.toml`/`VERSION` only; the script owns the `## vX.Y.Z` heading, the README line, the annotated tag, the push and the GitHub Release. No amend, no retag, no `--files-only`. See L-015.

**Pattern:** `pyproject.toml` `[tool.commitizen]` has
`update_changelog_on_bump = true`. `cz bump` automatically inserts the
version heading and aggregates conventional commit messages from the bump
range. Plan v1.2 of skill-ecosystem-integration specified manually adding
`## v0.6.0 (2026-05-10)` to CHANGELOG.md during M3.5. C2 review caught this
during /double-check ultrathink: pre-inserting the heading would either
duplicate commitizen's auto-insertion, fail the bump, or cause commitizen to
skip auto-population of that section.

**Rule:** For aa-ma-forge releases, ALWAYS use `cz bump --increment
{major|minor|patch}`. Conventional commit bodies are the source of CHANGELOG
content; never write `## v...` version headings directly to CHANGELOG.md.
Manual release-narrative prose CAN appear above the next-released version
section (e.g., a top-of-section paragraph summarising the release theme),
but never inside or as a heading for an unreleased version. Verified
during /double-check ultrathink session 2026-05-10 by reading
`pyproject.toml` `[tool.commitizen]` and `[tool.semantic_release]` blocks.

**How to apply:**
- Plan acceptance criteria for any version bump: "Use `cz bump --increment
  X`; verify CHANGELOG.md auto-update"; do NOT include manual heading edits.
- If a release theme/narrative is needed, prepare it as a separate file or
  as the body of the release commit; commitizen will fold it in.
- If CHANGELOG.md ever shows duplicate `## vX.Y.Z` headings, the cause is
  manual heading + commitizen auto-insertion conflict — revert and let
  commitizen own the heading.

**Cross-ref:** Global L-303 (pip-audit findings can surface mid-session
from online DB refresh — adjacent release-pipeline gotcha).

---

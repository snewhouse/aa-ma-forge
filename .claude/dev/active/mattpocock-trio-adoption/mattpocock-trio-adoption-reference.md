# mattpocock-trio-adoption Reference

**Immutable facts and constants for this task.**

_Last Updated: 2026-09-21 (M5 complete; charting shipped, v0.14.0 cut — AD-014..019)_

_Non-negotiable facts extracted from the plan, the design spec (D1–D9), the research note and the verification report. Anchors, not line numbers, locate edits (eng-review OV8). All facts `[valid: 2026-09-20]` unless marked otherwise._

---

## Upstream

| Fact | Value | Notes |
|---|---|---|
| Repo | `https://github.com/mattpocock/skills` | default branch `main`, last push 2026-09-18 |
| Fork sha (HEAD) | `c55ee46073ed923f86ce59a5eb3b6d895095d1b7` | short `c55ee46`; every fork/re-fork in this plan uses this sha; `upstream_sha` in `FORKS.json` is the full 40-char form |
| Fetch recipe | `gh api repos/mattpocock/skills/contents/<path>?ref=c55ee46 --jq .content \| base64 -d` | `gh` CLI must be authenticated |
| Latest upstream tag | `v1.2.3` (2026-08-06) = commit `6acc160` | 54 commits behind `c55ee46` |
| Plugin cache | `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/` = v1.2.3 | **never fork from it** (OV2); no plan step reads it |
| `grilling/SKILL.md` @ c55ee46 | md5 of `tail -n +2` = `284efe9cf334900d08230e572fc6db90` | upstream path `skills/productivity/grilling/SKILL.md` |
| `prototype/SKILL.md` @ c55ee46 | `tail -n +2` md5 = `5c68a2867eb3b9b4cb3e9ad4ba2b5299` | upstream path `skills/engineering/prototype/SKILL.md` |
| `prototype/LOGIC.md` @ c55ee46 | `tail -n +2` md5 = `0c6daa140ef3e83ba9e6b5bfa5161408` | `skills/engineering/prototype/LOGIC.md` |
| `prototype/UI.md` @ c55ee46 | `tail -n +2` md5 = `e3c841746676a0e604c72b5cd459e7ba` | `skills/engineering/prototype/UI.md` |
| `research/SKILL.md` @ c55ee46 | whole-file md5 = `e1dd6af372a9e1d134eff7d8362fe3f7` | `skills/engineering/research/SKILL.md`; M4 recipe: `sed '1d;/^## In this repo/,$d' SKILL.md \| sed 's/^name: aa-ma-research$/name: research/' \| md5sum` |
| Upstream renames | `write-a-skill` → `writing-great-skills` → `writing-for-agents` (removed in 1.0.0, 2026-06-17); `grill-with-docs` split into `grilling` + `domain-modeling` (2026-07) | source: research note §2 |
| Upstream invariant | user-invoked skills orchestrate; model-invoked skills are reusable discipline; a skill may only `Skill`-call model-invoked skills (`.agents/invocation.md`, 2026-08-15) | |

## Local fork facts

### Fork provenance line forms (line 1 of each forked SKILL.md)

- Forked (current): `<!-- Forked from https://github.com/mattpocock/skills/skills/<path> @ c55ee46 on <fork-date> — aa-ma-forge v0.13.0 -->`
- Derived: `<!-- Derived from https://github.com/mattpocock/skills/skills/<path> (forked <date>; <reason>) — aa-ma-forge v0.13.0 -->`
- M5 files carry `v0.14.0`.
- `tests/skills/_helpers.py` (`assert_skill_frontmatter`) requires `mattpocock/skills` + the upstream path substring in that line; the `fm["name"] == skill_dir_name` assertion is kept unchanged.
- `understand-codebase` is **not** a fork (line 1 is the `Maintained in aa-ma-forge …` HTML comment) — excluded from `FORKS.json`.

### Existing fork directories and their ADRs

| Skill dir | ADR | State after plan | Notes |
|---|---|---|---|
| `claude-code/skills/grill-with-docs/` | `docs/adr/0002-grill-with-docs-adoption.md` | derived (M2 ✓) | forked 2026-05-10; M1 state was `upstream_md5.<f>` = local md5 / `derived-from-local-fork`; **since M2 (7030200):** `state: derived`, `upstream_md5` all null, `upstream_md5_source` null (write-a-skill precedent); `files.SKILL.md` = `e552cb8a…` (post-AD-005), `CONTEXT-FORMAT.md` = `03e375e9…`, `ADR-FORMAT.md` unchanged; both companions stay in the dir |
| `claude-code/skills/prototype/` | `docs/adr/0003-prototype-adoption.md` | current, re-forked (M3 ✓) | forked 2026-05-10; ADR-0003 md5s under anchor `MD5 verification (canonical` — three values equal to local `tail -n +2` md5s — `10ace9b5d79140b25d115bb8d840106d` / `d57721452aacaa04caacd0bc7c5c2f49` / `c1eaad6437c90d5660b2ffc9ff91ffb4` (verified 2026-09-21; the design spec's `f59e7362…/5a29fb2c…/0531f4c5…` values were wrong — never appeared in ADR-0003) **Since M3 (20e2359):** `forked_at` 2026-09-21, `upstream_sha` full c55ee46…, `files` = `upstream_md5` = `5c68a286…` / `0c6daa14…` / `e3c84174…`, `upstream_md5_source: gh-api@c55ee46`; ADR-0003 amended (old md5s marked superseded); detector SAME |
| `claude-code/skills/write-a-skill/` | `docs/adr/0004-write-a-skill-adoption.md` | derived (M1) | forked 2026-05-10; upstream `skills/productivity/write-a-skill` deleted in 1.0.0; `upstream_sha: null`, `upstream_md5: {"SKILL.md": null}` |
| `claude-code/skills/grilling/` (new, M2) | ADR-0002 amendment | current | upstream `skills/productivity/grilling` |
| `claude-code/skills/aa-ma-research/` (new, M4) | `docs/adr/0012-*.md` | derived | upstream `skills/engineering/research`; renamed (OV1) |
| charting (M5) | `docs/adr/0013-charting-wayfinder-lite.md` | Adaptation (M5 ✓) | concept from `wayfinder`; **no files forked**, no manifest row; ADR Implemented 2026-09-21 |

### Expected `scripts/fork-drift.sh --sha c55ee46` verdicts (after Step 1.2, before M2/M3)

| Skill | Verdict | Why |
|---|---|---|
| `grill-with-docs` | **ORPHAN** | `CONTEXT-FORMAT.md` / `ADR-FORMAT.md` 404 upstream (moved to `domain-modeling/`); ORPHAN takes precedence over DRIFT in `classify_fork` |
| `prototype` | **DRIFT** | all three files differ from the 2026-05-10 fork |
| `write-a-skill` | **ORPHAN** | upstream path deleted |

After Step 3.4: `prototype` → SAME. Only HTTP 404 maps to ORPHAN; 403/auth/network → exit 1, never ORPHAN.

### MD5 recipes (one each, no line ranges — eng-review 1C)

- `files.<f>` in `FORKS.json` = `tail -n +2 <local file> | md5sum | cut -d' ' -f1`
- `upstream_md5.<f>` = md5 of the **whole** upstream file at `upstream_sha`; `null` per file when unknown (Orphan / Derived)

## File paths

### Files to create

- `claude-code/skills/FORKS.json` — fork manifest SSoT (M1)
- `src/aa_ma/forks.py` — `ForkEntry`, `load_manifest`, `classify_file`, `classify_fork`, `python -m aa_ma.forks classify` CLI (M1)
- `tests/skills/test_fork_manifest.py` — five tests (M1)
- `scripts/fork-drift.sh`, `tests/hooks/fork-drift.bats`, `tests/hooks/fixtures/forks/FORKS.json` (M1)
- `claude-code/skills/grilling/SKILL.md`, `tests/skills/test_grilling_frontmatter.py` (M2)
- `tests/hooks/fixtures/gate-scans/prototype-rollup-tasks.md` (M3)
- `claude-code/skills/aa-ma-research/SKILL.md`, `tests/skills/test_aa_ma_research_frontmatter.py` (M4)
- `claude-code/agents/aa-ma-researcher.md`, `tests/agents/test_aa_ma_researcher_agent.py` (M4)
- `docs/research/mattpocock-trio-adoption-install-backup.md` — M4 prototype-run output
- `claude-code/commands/aa-ma-chart.md`, `claude-code/hooks/lib/aa-ma-chart-guard.sh`, `docs/templates/map-template.md` (M5)
- `tests/hooks/aa-ma-chart-guard.bats`, `tests/hooks/fixtures/charting/{clear,open,claimed,fogless}-map.md` (M5)
- `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md`, `docs/research/writing-for-agents-eval-*.md` — M5 prototype effort (kept; committed `[ad-hoc]`)

### Files to modify

- `tests/skills/_helpers.py`, `.github/workflows/security.yml`, `pyproject.toml`, `uv.lock`, `tests/commands/test_aa_ma_share_command.py`, `.importlinter` (render-is-leaf += `aa_ma.forks`), `docs/lessons.md` (L-017) (M1)
- `claude-code/skills/write-a-skill/SKILL.md`, `docs/adr/0004-write-a-skill-adoption.md`, `docs/adr/0002-grill-with-docs-adoption.md`, `README.md` (M1)
- `claude-code/skills/grill-with-docs/{SKILL,CONTEXT-FORMAT}.md`, `claude-code/skills/FORKS.json`, `tests/skills/test_grill_with_docs_frontmatter.py` (+2 asserts, 3B), `claude-code/commands/aa-ma-plan.md`, `docs/adr/0002-grill-with-docs-adoption.md`, `docs/ATTRIBUTION.md` (M2)
- `claude-code/skills/prototype/{SKILL,LOGIC,UI}.md`, `claude-code/skills/FORKS.json`, `docs/adr/0003-prototype-adoption.md` (re-fork amendment), `src/aa_ma/gate.py`, `tests/test_gate.py`, `tests/hooks/aa-ma-gate-python.bats`, `tests/hooks/fixtures/gate-scans/prototype-rollup-tasks.md` (M3)
- `claude-code/commands/{aa-ma-plan,execute-aa-ma-milestone,execute-aa-ma-step}.md`, `claude-code/rules/engineering-standards.md`, `tests/smoke/aa-ma-engineering-standards-smoke.md`, `docs/spec/aa-ma-specification.md`, `docs/templates/tasks-template.md`, `docs/adr/0011-*.md` (M3)
- `docs/spec/plan-marker-grammar.md`, `claude-code/skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md`, `docs/adr/0012-*.md`, `TODOS.md` (M4)
- `scripts/install.sh`, `tests/hooks/install_dry_run.bats`, `claude-code/rules/aa-ma.md`, `docs/spec/aa-ma-quick-reference.md`, `docs/spec/claude-code-foundations.md`, `docs/templates/README.md`, `docs/adr/0013-*.md` (M5)
- Every milestone: `SECURITY.md`, `README.md`, `docs/spec/claude-code-foundations.md`, `CHANGELOG.md` (`## Unreleased` only), `CLAUDE.md` (local, gitignored)

### Key directories

- `.claude/dev/active/mattpocock-trio-adoption/` — this task
- `.claude/dev/charting/<effort>/` — charting maps (M5); never written by anything else
- `docs/research/` — research files (`<plan-slug>-<topic>.md`)
- `~/.claude/hooks/lib/` — installed helper location (`aa-ma-parse.sh`, `aa-ma-plan-marker.sh`, and after M5 `aa-ma-chart-guard.sh`)

## Contracts (verbatim from plan.md)

### Milestone 1 Contract
```text
# file: claude-code/skills/FORKS.json
{ "<skill-dir>": { "upstream": "skills/<category>/<name>",         # path under mattpocock/skills
                   "upstream_sha": "c55ee46…" | null,                # null for Orphan / Derived-from-deleted
                   "forked_at": "YYYY-MM-DD", "adr": "docs/adr/NNNN-…md",
                   "state": "current" | "derived",
                   "files":        { "<file>": "<md5 of `tail -n +2 <local file>`>" },
                   "upstream_md5": { "<file>": "<md5 of whole upstream file at upstream_sha>" | null },   # ALWAYS per-file; null per file when unknown (Orphan/Derived)
                   "upstream_md5_source": "adr-0003" | "derived-from-local-fork" | "gh-api@<sha>" | null } }   # optional, informational
# file: src/aa_ma/forks.py   (stdlib dataclasses, not Pydantic — no runtime deps; extra keys ignored on load)
Verdict = Literal["SAME", "DRIFT", "ORPHAN"]
@dataclass(frozen=True)
class ForkEntry: name: str; upstream: str; upstream_sha: str | None; forked_at: str; adr: str; state: Literal["current","derived"]; files: dict[str, str]; upstream_md5: dict[str, str | None]
def load_manifest(path: Path) -> dict[str, ForkEntry]           # unknown keys ignored; missing required key → ValueError naming it
def classify_file(expected: str | None, fetched: str | None) -> Verdict   # fetched None → ORPHAN; expected None → SAME (nothing to compare); else DRIFT/SAME
def classify_fork(entry: ForkEntry, fetched: Mapping[str, str | None]) -> Verdict
#   per-skill roll-up over entry.files keys: any ORPHAN → ORPHAN; else any DRIFT → DRIFT; else SAME. A key missing from `fetched` counts as None.
# CLI: uv run --quiet --project "$REPO_ROOT" python -m aa_ma.forks classify <skill> '<json: {file: md5|null}>'
#   stdout: one line per file `<skill> | <file> | <upstream_md5|-> | <fetched|-> | <file verdict>` then one line `<skill> | * | | | <skill verdict>`; exit 0
# file: tests/skills/test_fork_manifest.py
def test_every_fork_dir_is_in_manifest() -> None            # dirs whose SKILL.md line 1 is an HTML comment starting "Forked from" or "Derived from"
def test_manifest_entries_exist_on_disk() -> None
def test_local_md5_matches_manifest() -> None               # hard fail: local edit without manifest update
def test_classify_fork_same_drift_orphan() -> None          # three hand-built fetched dicts; pure, runs in CI
# file: tests/skills/_helpers.py — the existing `fm["name"] == skill_dir_name` assertion is KEPT unchanged (name == directory name always);
#   the only change: when expected_upstream_path is None, derive it as "mattpocock/skills/" + FORKS.json[skill].upstream
def assert_skill_frontmatter(skill_dir_name: str, expected_upstream_path: str | None = None) -> None
# CLI: scripts/fork-drift.sh [--sha <ref>] [--manifest <path>]   exit 0 ok / 1 gh or network failure / 2 usage
#   GH="${GH:-gh}" env seam (release.sh precedent) so bats can stub it; REPO_ROOT derived from $0 (readlink -f) so it runs from any cwd
#   per file: if body=$($GH api "repos/mattpocock/skills/contents/${upstream}/${file}?ref=${SHA:-main}" --jq .content 2>"$err"); then
#                 [ -n "$body" ] || exit 1 (empty content = file >1 MB, refuse); md5=$(printf '%s' "$body" | base64 -d | md5sum | cut -d' ' -f1)
#             elif grep -q 'HTTP 404' "$err"; then md5=null            # ONLY 404 → ORPHAN
#             else cat "$err" >&2; exit 1; fi                          # 403/auth/network → exit 1, never ORPHAN
#   then feeds {file: md5|null} to `python -m aa_ma.forks classify` and prints its rows (per-file verdict + skill roll-up row)
```

**M1 Contract addendum (§6.8 impl review, 2026-09-21 — additive):** `aa_ma.forks` also exposes `DEFAULT_MANIFEST: Path` and two CLI subcommands — `files [--manifest <p>]` (prints `skill<TAB>upstream<TAB>file` rows after `load_manifest` validation) and `classify-all [--manifest <p>]` (reads `skill<TAB>file<TAB>md5|null` from stdin; prints the same per-file + roll-up rows for every manifest skill; absent skill/file → None → ORPHAN). `scripts/fork-drift.sh` is now `files` → gh fetch loop (buffered; any non-404 failure → exit 1 before classification) → `classify-all`; no inline `python3`, one manifest reader, no `${err}.json`. It pre-flights `gh api repos/mattpocock/skills` because GitHub returns 404 (not 403) for a repo the caller cannot see. Usage errors (`--manifest` without a path, unknown skill) exit 2. CI pytest step is exclusion-based: `pytest tests --ignore=tests/codemem --ignore=tests/perf --ignore=tests/test_goal_synthesis.py`.

### Milestone 2 Contract
```text
# file: claude-code/skills/grilling/SKILL.md   (frontmatter: name: grilling; model-invocable)
# file: claude-code/skills/grill-with-docs/SKILL.md
<!-- Derived from https://github.com/mattpocock/skills/skills/engineering/grill-with-docs (forked 2026-05-10; upstream split into grilling + domain-modeling 2026-07; name and domain block retained) — aa-ma-forge v0.13.0 -->
<what-to-do>
Call the Skill tool with "grilling" and run its round-based interview about this plan. During the session apply the domain awareness below: challenge terms against CONTEXT.md, sharpen language, update CONTEXT.md and ADRs inline.
</what-to-do>
# tests/skills/test_grilling_frontmatter.py: assert_skill_frontmatter("grilling", "mattpocock/skills/skills/productivity/grilling")
```

### Milestone 3 Contract
```text
# file: src/aa_ma/gate.py
@dataclass(frozen=True)
class StepsRead:
    pending: int
    prototype_required: bool
def _read_steps(block: Block, heading: str, errors: list[str]) -> StepsRead   # Block from aa_ma.grammar
#   replaces _count_pending (2A: named fields, not a tuple); uses
#   read_enforced_field(step.text, "Prototype-Required", PROTOTYPE_REQUIRED) per step;
#   invalid/empty token → errors.append(...) → exit 2 (same as milestone-level)
# at the selected-milestone override (gate.py:~382):
#   MilestoneRead(**{**asdict(read), "pending_steps": steps.pending,
#                   "prototype_required": read.prototype_required or steps.prototype_required})
# JSON schema (gate.py:99-121) and to_kv unchanged.
# fixture: tests/hooks/fixtures/gate-scans/prototype-rollup-tasks.md
## Milestone 1: Roll-up
- Status: PENDING
- Gate: SOFT
### Sub-step 1.1: plain
- Status: PENDING
### Sub-step 1.2: needs prototype
- Status: PENDING
- Prototype-Required: YES
## Milestone 2: No flags
- Status: PENDING
### Sub-step 2.1: plain
- Status: PENDING
# aa-ma-plan.md Step 2.5 (inside Phase 2, no marker):
**Step 2.5: Prototype Decision** — for each milestone whose design is uncertain, AskUserQuestion
"Prototype-Required for <milestone>? YES/NO"; write `- Prototype-Required: YES` into that milestone
(or the specific sub-step) in tasks.md at Step 5.5; append `prototype=<M-list>` to ENG_STANDARDS_DECLARED.
# provenance grammar additions (spec :302-326):
[ts] PROTOTYPE — <milestone heading> — <verdict>[; branch=prototype/<name>]
[ts] CRITICAL_PATH_REVIEW — <milestone heading> — <Critical-Path value> — <evidence>
[ts] LIVE_CHECK — <milestone heading> — <key>=<value>…
```

**M3 Contract addendum (§6.8 security review, 2026-09-21 — AD-007, additive):** `StepsRead` also carries `critical_path: str | None`; `_read_steps` reads `Critical-Path` per sub-step with `CANONICAL_CRITICAL_PATHS`, collects distinct values, and appends a `conflicting sub-step Critical-Path values` error when more than one is declared (exit 2). Override: `critical_path=read.critical_path or steps.critical_path` (milestone wins). Fixture Milestones 5–8 + 4 tests + bats "sub-step Critical-Path rolls up" cover it. `MilestoneRead` built with `dataclasses.replace`.

### Milestone 4 Contract
```text
# file: claude-code/skills/aa-ma-research/SKILL.md
<!-- Derived from https://github.com/mattpocock/skills/skills/engineering/research @ c55ee46 (forked <fork-date>; renamed aa-ma-research, AA-MA dispatch rules appended) — aa-ma-forge v0.13.0 -->
---  name: aa-ma-research ; description: <upstream description verbatim>  ---
<upstream body verbatim>
## In this repo
- Dispatch the background agent as `aa-ma-researcher` (Agent tool, subagent_type: aa-ma-researcher). It has no Agent tool, so it cannot re-delegate.
- Answer the stated question only. List threads you saw but did not follow under `## Not pursued`.
- "Where the repo already keeps such notes" is `docs/research/<plan-slug>-<topic>.md`, with the header used by `docs/research/skill-ecosystem-audit.md` (Created / Author / Reviewed-Through-Date / Valid-Through / Sources).
# file: claude-code/agents/aa-ma-researcher.md
---
name: aa-ma-researcher
description: Investigates one question against primary sources and writes exactly one cited Markdown file under docs/research/. Spawned by Skill(aa-ma-research). Has no Agent tool; never runs `claude`.
tools: Read, Glob, Grep, Bash, WebSearch, WebFetch, Write
---
# returns ≤10 lines: path written, 3-line summary, "Not pursued" count
# marker: PHASE_3 DONE context7_calls=<N> web_fetches=<N> research_files=<N>
```

### Milestone 5 Contract
```text
# file: claude-code/commands/aa-ma-chart.md
# CLI: /aa-ma-chart chart <effort> "<idea>"   |   /aa-ma-chart work <effort> [<ticket-N>]
# map: .claude/dev/charting/<effort>/<effort>-map.md
# Charting: <effort>
## Destination        (1–2 lines)
## Notes              (domain, skills to consult, standing preferences)
## Decisions so far   (- [Ticket N: Title](#ticket-n-title): one-line gist)
## Tickets
### Ticket N: Title
- Type: research | prototype | grilling | task      (default grilling)
- Mode: HITL | AFK                                 (research → AFK; prototype/grilling → HITL; task → either)
- Status: OPEN | CLAIMED | RESOLVED | RULED_OUT
- Claimed-at: YYYY-MM-DDTHH:MM (present iff CLAIMED; 1B)
- Blocked-by: N, N | —
#### Question
#### Answer                                        (present only when RESOLVED)
## Not yet specified  (fog — bullets)
## Out of scope       (never graduates)
# invariants: claim before work; ≤1 non-research ticket CLAIMED at a time (OV5); chart never writes outside
#   .claude/dev/charting/, docs/research/, prototype/* branches; zero fog at chart → stop.
# guard: aa-ma-chart-guard.sh <check> <map> [<ticket>]   — resolved by the command and by aa-ma-plan.md with the shipped `_cand` pattern:
#   for _cand in "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-chart-guard.sh" "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-chart-guard.sh"; do [ -f "$_cand" ] && GUARD="$_cand" && break; done
#   (never a literal ~/.claude path — the fake-CLAUDE_HOME bats convention and non-installed checkouts depend on this)
#   sources sibling: . "$(dirname "$(readlink -f "$0")")/aa-ma-parse.sh"; honours AA_MA_HOOKS_DISABLE=1 (aa_ma_is_disabled && exit 0)
#   checks: fog|claim|reclaim|from-map|import <map> <task> <provenance>   exit 0 ok / 1 refused (reason on stdout) / 2 usage; every git failure → exit 1 with reason
#   import: cd "$(git rev-parse --show-toplevel)" || exit 1; mkdir -p .claude/dev/active/<task>; if git ls-files --error-unmatch <map> then git mv else mv && git add; append MAP_IMPORTED line to <provenance>
#   task tickets: `work` prints the ticket's Question as a checklist for the human and stops; resolution is the human writing `#### Answer` + `Status: RESOLVED` (the guard's `claim` still applies)
#   work <effort> <ticket> --reclaim: CLAIMED → OPEN (append `- Reclaimed: <ts>` under the ticket) → CLAIMED
# resolvers: research → Skill(aa-ma-research) (≤5 parallel, AFK); prototype → Skill(prototype) on
#   branch prototype/<effort>-<N>; grilling → Skill(grill-with-docs) + AskUserQuestion (never self-answer);
#   task → checklist for the human.
# /aa-ma-plan --from-map <effort> [--dry-run]: refuse unless every ticket is RESOLVED|RULED_OUT and fog is empty;
#   Phase 1 seeded from Decisions so far + Answers; --dry-run prints the seed and exits before Phase 1.3;
#   Step 5.x: guard `import` (see M5 Contract) moves the map to .claude/dev/active/<task>/<task>-map.md; provenance: [ts] MAP_IMPORTED effort=<effort> tickets=<N>
```

### Milestone 5 as-built facts (2026-09-21)
- Guard: `claude-code/hooks/lib/aa-ma-chart-guard.sh` — `fog|claim|reclaim|from-map|import`; exit 0 ok / 1 refused (stdout) / 2 usage (also: effort or task not `^[a-z0-9-]+$`, map header `# Charting: <effort>` not a slug). `AA_MA_HOOKS_DISABLE=1` → fog/claim/reclaim/from-map exit 0 no-op; **import always runs** (AD-016). `claim` checks the one-at-a-time invariant before `Blocked-by`; `set_status` returns 1 when no Status line was rewritten. `from-map` success line: `clear: tickets=<N> resolved=<R> ruled_out=<X>`. `import` refuses an existing `<task>-map.md`.
- Sub-step Status enum has no `ACTIVE` — use `IN_PROGRESS` (gate exit 2 otherwise).
- `/aa-ma-plan --from-map` dry-run first line: `--from-map dry-run: effort=<e> tickets=<N> — no task directory created`; seed is loaded in a `<MAP_SEED>` block (AD-018).
- Release v0.14.0: bump commit `b527241`, tag object `ea6d7d1`, https://github.com/snewhouse/aa-ma-forge/releases/tag/v0.14.0; CI run 35643530138 green. CI shellcheck runs at info severity (SC2015 `A && B || C` fails there) — run `shellcheck -S info` locally.
- Charting artefacts: `.claude/dev/charting/writing-for-agents-eval/writing-for-agents-eval-map.md` (4 tickets, all RESOLVED), `docs/research/writing-for-agents-eval-overlap.md` (25 rule rows: 12 new / 9 partial / 1 dup / 3 conflicts) — commit `6bcef05` `[ad-hoc]`. Decisions locked there: fork `writing-for-agents` verbatim (model-invoked), retire `write-a-skill` (fold sections into `## In this repo`), scribe/Phase 5 do NOT invoke it.

## Provenance line grammars (used by this plan; added to the spec in M3)

| Line | Form | Notes |
|---|---|---|
| PROTOTYPE | `[ts] PROTOTYPE — <milestone heading> — <verdict>[; branch=prototype/<name>]` | M4: `PASS: files=1 nested_agents=0; branch=n/a`; M5: `PASS: tickets=<N> resolved=<N> refused_claims=1; branch=n/a` |
| CRITICAL_PATH_REVIEW | `[ts] CRITICAL_PATH_REVIEW — <milestone heading> — <Critical-Path value> — <evidence>` | 4 fields, matching `execute-aa-ma-milestone.md` §6.7 |
| LIVE_CHECK | `[ts] LIVE_CHECK — <milestone heading> — <key>=<value>…` | new; HITL live criteria (M2: `grilling_rounds=<N> resolved=~/.claude/skills/grilling`) |
| MAP_IMPORTED | `[ts] MAP_IMPORTED effort=<effort> tickets=<N>` | written by the guard's `import` check |
| ENG_STANDARDS_DECLARED | `ENG_STANDARDS_DECLARED: themes=[…] prototype=<M-list>` | `prototype=` suffix added by Step 2.5 (M3) |
| PHASE_3 marker | `PHASE_3 DONE context7_calls=<N> web_fetches=<N> research_files=<N>` | `research_files=` key added in M4 |

`<milestone heading>` = the text after `## ` on the `## Milestone N: …` line, byte-for-byte as `aa-ma-gate` prints `heading=` (the §6.7 grep depends on it; no `## ` prefix). Never emit a `PHASE_2.5` marker (Step 2.5 is a step inside Phase 2).

## Research-file header (M4/M5 and `aa-ma-research`)

`**Created:** · **Author:** · **Reviewed-Through-Date:** · **Valid-Through:** · **Sources:**` — the four fields of `docs/research/skill-ecosystem-audit.md` plus a `Sources` list. `docs/research/mattpocock-trio-2026-09.md` is the first file in this shape. Check: `grep -Ec '^\*\*(Created|Author|Reviewed-Through-Date|Valid-Through|Sources):\*\*' <file>` = 5.

## Count sites (by anchor text — lines as of `c87135b`, never rely on them)

| Site | Anchor | Baseline → after plan |
|---|---|---|
| `SECURITY.md` | "N skills directories" line (count dirs with `find claude-code/skills -mindepth 1 -maxdepth 1 -type d \| wc -l` — `FORKS.json` lives in that dir, so `ls \| wc -l` over-counts by 1); skills list; agents list; commands list; "8 hooks" line (unchanged — guard is `lib/`) | skills 19→20 (M2)→21 (M4); agents 11→12 (M4); commands 12→13 (M5) |
| `docs/spec/claude-code-foundations.md` | `### Commands (N)` / `### Skills (N)` / `### Agents (N)` headings | Commands 11→12 (pre-M1 fix)→13 (M5); Skills 19→20→21; Agents 11→12; `(5 standard + 2 optional)` → `+ 3` (pre-M1) → `+ 4` (M5) |
| `README.md` | "All commands" table (+`/aa-ma-chart` row, M5); skills table (+`grilling` M2, +`aa-ma-research` M4); `write-a-skill` row (M1); prototype row "terminal TUI" wording (M3) | asserted by `tests/commands/test_aa_ma_share_command.py` |
| Taxonomy sites (5 standard + N optional) | `docs/spec/aa-ma-specification.md` §II table; `claude-code/rules/aa-ma.md` file-system table; `docs/spec/aa-ma-quick-reference.md` Optional Files table; `docs/templates/README.md`; `docs/spec/claude-code-foundations.md`; `README.md` | pre-M1: `+ 2` → `+ 3` with `impl-review`; M5: `+ 3` → `+ 4` with `map`. Verify: `grep -rl '+ 2 optional' docs claude-code README.md` empty (pre-M1); `grep -rl '+ 3 optional' …` empty (M5) |
| `claude-code/rules/engineering-standards.md` | Theme 1 prototype sentence ("terminal TUI" → HTML logic demo / `?variant=` / `prototype/<name>`); Critical-Path table byte-identical (`tests/codemem/test_critical_path_parser.py` scrapes it) | M3 |
| `tests/smoke/aa-ma-engineering-standards-smoke.md` | "terminal TUI" wording | M3 → 0 occurrences |
| `claude-code/commands/aa-ma-plan.md` | Phase 1.3 grill-with-docs dispatch prose (M2 agent-cap sentence); Step 2.4 → **Step 2.5: Prototype Decision** → Phase 2 summary (M3); Phase 3.3/3.4 + marker row (M4); Step 5.3–5.5 (`docs/research/` links, M4); `--from-map <effort> [--dry-run]` (M5) | |
| `claude-code/commands/execute-aa-ma-milestone.md` | §6.7 BLOCKED text "Milestone has Prototype-Required: YES" → "milestone or one of its sub-steps" | M3 |
| `claude-code/commands/execute-aa-ma-step.md` | sub-step Prototype-Required advisory → "rolls up to the milestone gate" | M3 |
| `docs/spec/aa-ma-specification.md` | provenance-grammar section (PROTOTYPE / CRITICAL_PATH_REVIEW / LIVE_CHECK); §II file table (map row + `MAP -. optional .-> PLAN` edge) | M3, M5 |
| `docs/templates/tasks-template.md` | four blank `- **Critical-Path:**` / `- **Prototype-Required:**` slots (milestone + sub-step) → removed, comment "add `- <Field>: <value>` only when it applies; an empty value is a gate error (exit 2)" | M3 |
| `docs/spec/plan-marker-grammar.md` | PHASE_3 key list (`research_files=`) | M4 |
| `claude-code/skills/aa-ma-plan-workflow/references/PHASE_3_RESEARCH.md` | tool-hierarchy row (`aa-ma-research`); `research-consolidation` row ("optional") | M4 |
| `docs/adr/0004-write-a-skill-adoption.md` | line 3 = `**Status:** Implemented — Derived (2026-05-10; amended <fork-date>)`; `## Amendment <fork-date>` section | M1 |
| `docs/adr/0002-grill-with-docs-adoption.md` | Implementation Notes rows claiming `rules/aa-ma.md`/`CLAUDE.md` mentions (pre-M1 fix); `## Amendment <fork-date> — Derived; grilling forked` | pre-M1, M2 |
| `docs/adr/0003-prototype-adoption.md` | `MD5 verification (canonical` | source of `prototype` `upstream_md5` (M1); re-fork amendment (M3) |
| `docs/ATTRIBUTION.md` | grilling (M2), aa-ma-research (M4), "charting — concept adapted from wayfinder (mattpocock/skills, c55ee46); no files forked; invariant reworded to '≤1 non-research ticket CLAIMED at a time' (OV5)" (M5) | |
| `TODOS.md` | `_phase_3` fingerprint + `docs/research/README.md` (M4); `_phase_1_3` + `grilling` fingerprint, `/aa-ma-share` map allowlist (M5) | |
| `scripts/aa-ma-share-allow.sh` | allowlist refuses `*-map.md` | out of scope; follow-up in TODOS.md |

## `install.sh` / `uninstall.sh` facts

- `hooks/lib` helpers are **not** auto-discovered: each is linked by an explicit `if [ -f … ]; then create_symlink` block (`scripts/install.sh`, the `aa-ma-parse.sh` / `aa-ma-plan-marker.sh` blocks). `lib/aa-ma-footer.sh` is in the repo and not installed — proof. New helper → own block + `tests/hooks/install_dry_run.bats` case (L-005).
- Skills (`~/.claude/skills/<name>`) and agents are auto-discovered as symlinks; a real directory at the target is backed up first. `~/.claude/skills/research` is a real dir today and stays untouched because ours is named `aa-ma-research` (OV1).
- Installed marker helper: `~/.claude/hooks/lib/aa-ma-plan-marker.sh` (source `claude-code/hooks/aa-ma-plan-marker.sh`).
- `scripts/uninstall.sh` scans `hooks/lib` for repo-pointing links (removes the guard symlink on rollback).
- `CLAUDE.md` (project) is gitignored — local convenience only; never a count site in acceptance criteria or CI; the count test's skip-when-absent branch stays.

## `scripts/release.sh` preconditions

- Exactly one `## Unreleased` heading with ≥1 bullet; clean tree; HEAD == origin/main; `gh auth status` ok.
- Does **not** re-create `## Unreleased` afterwards → Step 5.1 re-adds it before any M5 CHANGELOG edit.
- Re-locks `uv.lock` inside the bump commit (`ea4005c`); tagged tree carries the new version (L-015).
- **v0.13.0 (cut 2026-09-21, Step 4.6):** bump commit `c27250b` (`[ad-hoc]`; CHANGELOG/README/VERSION/pyproject/uv.lock), annotated tag `v0.13.0` (object `68293fb`) → `c27250b`, GitHub Release https://github.com/snewhouse/aa-ma-forge/releases/tag/v0.13.0. `uv.lock` package `aa-ma` 0.13.0 in the tagged tree.
- Invocations: `scripts/release.sh minor --headline "fork manifest, grilling, prototype gate, research agent"` (v0.13.0, Step 4.6 — done); `scripts/release.sh minor --headline "charting: pre-plan decision maps (/aa-ma-chart, --from-map)"` (v0.14.0, Step 5.5). Always `--dry-run` first. Runbook: `docs/runbooks/release.md`.

## Conventions and constraints

| Rule | Value |
|---|---|
| Agent-test helper | `tests/agents/_helpers.split_frontmatter(path) -> (fm, body)` — the single agent-frontmatter parser (mirrors `tests/skills/_helpers.split_frontmatter`); both agent tests import it (§6.8 M4 C-W1) |
| Research header | exactly `Created / Author / Reviewed-Through-Date / Valid-Through / Sources` as `**Field:**` lines — pinned by `HEADER_FIELDS` in `tests/agents/test_aa_ma_researcher_agent.py` against the agent template and the live M4.3 file; slug/topic `[a-z0-9-]+`, file is a direct child of `docs/research/` |
| `claude`-invocation check | count Bash `tool_use.input.command` matching `claude (-p\|--print)` via jq over the subagent `.jsonl`, never a bare `grep -c` (the agent prompt contains the phrase) — AD-013 |
| bats convention | tests target the repo file `HELPER="${REPO_ROOT}/claude-code/hooks/lib/<name>.sh"` with a fake `CLAUDE_HOME` symlink (as `tests/hooks/aa-ma-gate-python.bats`); never `~/.claude/...` (CI has none) |
| Session restart rule | **Falsified in M2 (2026-09-21):** the Skill tool listing hot-reloads mid-session after `install.sh` adds a skill dir (the new entry appeared with our line-1 provenance as its description). Unprefixed `Skill(grilling)` resolved to `~/.claude/skills/grilling` (ours); the plugin copy is only reachable as `mattpocock-skills:grilling`. M4's `aa-ma-research` live criterion may run in-session; still record the resolved path in the Result Log. **Refined in M4 (2026-09-21):** only the *Skill* listing hot-reloads — the *agent* registry does not: after `install.sh` linked `~/.claude/agents/aa-ma-researcher.md`, `Skill(aa-ma-research)` resolved to ours but `Agent(subagent_type: aa-ma-researcher)` failed "Agent type not found" on the *same turn*; the harness announced the new agent type two turns later and the dispatch then succeeded. A live criterion that dispatches a **new agent** needs at least one further turn after `install.sh` (a fresh session is the safe form); one that only calls a new skill does not |
| `[ad-hoc]` | pre-M1 housekeeping commit; commits made *by* charting/research runs during this plan (`.claude/dev/charting/**`, `docs/research/*` from prototype runs) |
| Plan footer | `[AA-MA Plan] mattpocock-trio-adoption .claude/dev/active/mattpocock-trio-adoption` (last footer line); `[no-sync-check]` never used |
| Agent cap | ≤5 concurrent agents (applies inside `grilling` fact-dispatch and `aa-ma-research` parallel runs) |
| "clean" | the named command exits 0 and prints no findings (`<cmd>; test $? -eq 0`) |
| `CHANGELOG.md` | edit `## Unreleased` only (L-003); counts updated per milestone (L-002) |
| Dev deps | `[dependency-groups] dev` in `pyproject.toml` (not `[tool.uv] dev-dependencies`); `pyyaml` declared explicitly (M1) |
| CI pytest step (after M1, AD-003) | exclusion-based: `uv run pytest tests -q --tb=short --ignore=tests/codemem --ignore=tests/perf --ignore=tests/test_goal_synthesis.py` — never enumerate (L-017c) |
| Gate exit codes | `aa-ma-gate` exit 0/1/2/3/4; empty or invalid `Prototype-Required` / `Critical-Path` value → exit 2 at milestone level **and** on any sub-step of the answered milestone (since M3, 1b1cabf / 3c6f92f); sub-steps that disagree on `Critical-Path` → exit 2 |
| Vocabulary | Fork / Re-fork / Drift / Orphan / Adaptation / Adoption per `CONTEXT.md`; "sync", "vendor" banned |
| Banned marker | never emit `PHASE_2.5` |

## Glossary (from `CONTEXT.md`)

| Term | Definition |
|---|---|
| Fork | Lifting upstream files into our tree with a provenance comment on line 1; mechanical and atomic |
| Adoption | Milestone-level workflow wrapping a Fork: fork + ADR + frontmatter test + cross-references + skill-count update |
| Re-fork | A Fork applied to an existing fork dir: content replaced from upstream, provenance date + ADR md5s updated, original ADR amended (no new ADR number) |
| Drift | Fork state: upstream file md5 no longer matches the md5 recorded for the fork. Detected, not judged |
| Orphan | Fork state: upstream path no longer exists. Cannot Drift. Forces Re-fork from successor / keep as Derived / retire |
| Adaptation | Concept borrowed with **no** files forked; own files + ADR; attribution "concept adapted from"; cannot Drift or be Orphaned |
| Derived | Fork state (`state: derived`): local content intentionally diverges from upstream; provenance line is an HTML comment starting `Derived from`; frontmatter `name` may differ from the upstream dir name |

## External references

- Upstream repo: https://github.com/mattpocock/skills (HEAD `c55ee46`)
- Research note: `docs/research/mattpocock-trio-2026-09.md`
- Design spec: `docs/superpowers/specs/2026-09-20-mattpocock-trio-adoption-design.md`
- ADRs: `docs/adr/0011-*.md` (prototype gate), `docs/adr/0012-*.md` (research), `docs/adr/0013-*.md` (charting) — Proposed → Implemented by M3/M4/M5
- Verification report: `mattpocock-trio-adoption-verification.md`

Architecture View: see plan.md §13

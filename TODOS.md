# TODOS

## AA-MA Tooling

### Generate the milestone dependency graph from tasks.md

**What:** `aa-ma-tui --graph` (or an `aa_ma.render` sub-command) emits a mermaid `flowchart` of milestones from their `Dependencies:` fields.

**Why:** The planning standard (element #13, v0.11.0) says the milestone graph is never hand-authored because it is derivable. Today nothing derives it, so no plan has one.

**Context:** Decided during the plan-architecture-views grill (2026-09-11). `src/aa_ma/tui/model.py` already carries `Milestone.dependencies`; `tui/parser.py::discover_tasks` loads every active plan. Start in `src/aa_ma/tui/snapshot.py` next to `render_tree`. Output goes to stdout as a fenced block so it can be pasted or rendered.

**Effort:** S
**Priority:** P3
**Depends on:** milestone-grammar-ssot M5 (reliable `split_milestones`)

### Make aa-ma-tui runnable from any project

**What:** Resolve the aa-ma-forge checkout from the install.sh symlink (`readlink -f ~/.claude/commands/<any>.md` → repo root) and run `uv run --project <root> aa-ma-tui`, via a thin wrapper or documented alias.

**Why:** The TUI only works from inside the aa-ma-forge checkout; every client repo with an active AA-MA plan cannot use it. The same gap was found and fixed for `/aa-ma-share` (plan-eng-review D2, 2026-09-11).

**Context:** The resolution snippet lands in `claude-code/commands/aa-ma-share.md` at plan-architecture-views M3.1; reuse it verbatim. Needs one bats test that the wrapper resolves the root from a symlinked command file.

**Effort:** S
**Priority:** P3
**Depends on:** plan-architecture-views M3 (the snippet)

## Completed

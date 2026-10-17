# Stage state — how values travel between stage blocks

### State between stages

Every stage block runs in its own Bash call, so a shell variable set in one
block is gone in the next (forge L-055). The values travel in a **stage state
file** instead: `"$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"`. It
lives in this worktree's own git-dir, so it is untracked, never pushed, and
separate per worktree.

- **Stage A starts it.** It deletes the last run's file first (an aborted A
  leaves none) and the earlier run dirs, then saves `ORIGINAL_BRANCH`,
  `BASE_REF`, `DEFAULT_BRANCH`, `SLUG` and `SDM_DIR`. Its `Stage state:` line
  prints both paths.
- **Every later block loads it** with the same loader. A non-empty explicit
  env value beats the file. A required value that is still missing (for
  example `REMOTE_CHOICE` in E0, F and G1–G3, or E1's counts in E2) stops the
  block loudly. It is never replaced with a default.
- **Saves are appended** as `KEY=<base64>` by `sdm_save`, and the last write of
  a key wins. B saves `CHANGED_FILES/PY/SH`, E1 `n_github`/`n_gitlab`/`n_other`,
  E2 `REMOTE_CHOICE`, E3 `PR_BODY_FILE`, F `PR_NUM`/`PR_URL`, G1
  `MERGE_STRATEGY`, G2 `CI_STATE` and G3 `MERGE_DISPATCHED` (G4 runs only when
  it is `1`).
- **Run files** live in `SDM_DIR`, a mode-700 directory next to the state file.
  These are the agent outputs, scanner reports, findings, reviewer notes, the
  AUQ bridge and the PR body. No run file is written to the shared temp
  directory.
- **The loader trusts nothing it reads.**
  - It ignores a file written on another branch or with no branch, and says so.
  - It refuses a symlinked file, a group- or world-writable one, or one you
    don't own.
  - It accepts only the keys named in `SDM_KEYS`, and never `eval`s a value.
- **Saving refuses the same files.** `sdm_save` will not write through a
  symlinked state file, one you don't own, or one writable by group or others,
  and the refusal stops the block. A file it creates is mode 600.
- **To re-answer a question** (for example the dual-remote choice), re-run the
  block with the answer set explicitly, such as `REMOTE_CHOICE=github`. The
  block saves the explicit value.

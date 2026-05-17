<!-- ARCHIVED: 2026-03-29 17:50 -->
<!-- Plan: security-quality-remediation - COMPLETE -->
<!-- Total Milestones: 5 -->
# Reference: Security & Quality Remediation

## Immutable Facts

### Codebase
- **Project:** claude-code-project-index (fork of ericbuess/claude-code-project-index)
- **Remote origin:** `https://github.com/snewhouse/claude-code-project-index.git`
- **Baseline commit:** `074ae03` (main)
- **LOC:** ~3,679 across 4 Python + 4 Shell scripts
- **Python version:** 3.8+ (EOL but supported)
- **External deps:** Zero (pure stdlib)

### File Paths & Line References

| File | Lines | Key Sections |
|------|-------|-------------|
| `scripts/i_flag_hook.py` | 778 | VM Bridge: 262-316, SSH sync: 476-492, .python_cmd: 189-200, copy_to_clipboard: 259-564, bare excepts: 60,133,291,434,485,487,505,541 |
| `scripts/stop_hook.py` | 86 | os.chdir: 63, bare excepts: 55,82, Python cmd: 44-46 |
| `scripts/index_utils.py` | 1415 | Dead build_call_graph: 132-158, vestigial call_graph key: 171,935, shell style-1: 983-1057, shell style-2: 1059-1133 |
| `scripts/project_index.py` | 768 | Non-atomic write: 741, stale comments: 106,401, dense format magic keys: 432-439 |
| `install.sh` | 313 | .python_cmd write: 158 |

### Deep Dive Finding IDs

| ID | Severity | Category | Description |
|----|----------|----------|-------------|
| C-1 | Critical | Security | Hardcoded IPs + SSH injection via USER env var |
| C-2 | Critical | Security | Unvalidated .python_cmd executable path |
| H-1 | High | Security | Unauthenticated LAN probing (3 IPs) |
| H-2 | High | Security | os.chdir() global CWD mutation |
| H-3 | High | Security | sys.path.insert with author-specific paths |
| H-4 | High | Security | Non-atomic PROJECT_INDEX.json writes |
| M-1 | Medium | Security | Sensitive data in world-readable CWD file |
| M-2 | Medium | Quality | 12 bare except: blocks suppress KeyboardInterrupt |
| Q-1 | Medium | Quality | Dead build_call_graph function (never called) |
| Q-2 | Medium | Quality | ~130 lines duplicated shell parser |
| Q-3 | High | Testing | Zero test coverage |
| Q-4 | High | Design | copy_to_clipboard god function (305 lines) |
| Q-5 | Medium | Quality | Dense format magic string keys |
| Q-6 | Medium | Design | Hardcoded if/elif parser dispatch |

### Constants

| Name | Value | Location |
|------|-------|----------|
| MAX_FILES | 10000 | project_index.py:36 |
| MAX_INDEX_SIZE | 1MB | project_index.py:37 |
| MAX_TREE_DEPTH | 5 | project_index.py:38 |
| DEFAULT_SIZE_K | 50 | i_flag_hook.py:18 |
| CLAUDE_MAX_K | 100 | i_flag_hook.py:20 |
| EXTERNAL_MAX_K | 800 | i_flag_hook.py:21 |

### Branch Strategy
- Feature branch: `fix/security-and-quality-remediation`
- Base: `main` at `074ae03`
- Merge: squash-merge to main after all milestones pass

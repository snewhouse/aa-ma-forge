<!-- ARCHIVED: 2026-03-29 17:50 -->
<!-- Plan: security-quality-remediation - COMPLETE -->
<!-- Total Milestones: 5 -->
# Security & Quality Remediation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address all issues and recommendations from the codebase deep dive, raising health grade from C+ to B+ across security, quality, testing, and architecture dimensions.

**Architecture:** Sequential phased approach with TDD discipline. Feature branch `fix/security-and-quality-remediation`. Milestones 0-4 in strict order. Each fix: write failing test (red) → apply fix (green) → refactor if needed. Zero new external dependencies.

**Tech Stack:** Python 3.8+ stdlib, pytest (dev dependency), bash

**Baseline Commit:** `074ae03` (main)
**Deep Dive Reports:** `codebase-deep-dive-20260317-024835/`

---

## 1. Executive Summary

Remediate 18 findings from the codebase deep dive across 4 priority tiers: critical security (P0), quality quick wins (P1), refactoring (P2), and architecture (P3). TDD-first approach with characterization tests established before any changes. Feature branch workflow with milestone-level commits.

## 2. Stepwise Implementation Plan

### Milestone 0: Test Infrastructure & Characterization Tests
**Goal:** Establish pytest, write tests capturing current behavior before any changes.
**Measurable:** `pytest tests/ -v` runs green with 15+ characterization tests.

### Milestone 1: Critical Security Fixes (P0)
**Goal:** Eliminate all critical and high security vulnerabilities.
**Measurable:** Zero hardcoded IPs, validated .python_cmd, no os.chdir(), no author-specific paths.

### Milestone 2: Quality Quick Wins (P1)
**Goal:** Fix exception handling, remove dead code, deduplicate shell parser.
**Measurable:** Zero bare `except:` blocks, zero dead functions, shell parser deduplicated.

### Milestone 3: Refactoring (P2)
**Goal:** Decompose god function, implement atomic writes, expand test suite.
**Measurable:** `copy_to_clipboard` < 30 lines (dispatch only), atomic writes for PROJECT_INDEX.json, 25+ tests.

### Milestone 4: Architecture Improvements (P3)
**Goal:** Data-driven parser dispatch, dense format constants, smart stop hook.
**Measurable:** Parser registry dict, no magic string keys, stop hook checks staleness.

## 3. Milestones with Measurable Goals

| Milestone | Goal | Metric | Target |
|-----------|------|--------|--------|
| M0 | Test infrastructure | Tests passing | 15+ green |
| M1 | Security fixes | Critical/High vulns | 0 |
| M2 | Quality wins | Bare excepts | 0 |
| M3 | Refactoring | God function lines | < 30 |
| M4 | Architecture | Magic string keys | 0 |

## 4. Acceptance Criteria Per Step

### M0: Test Infrastructure
- [ ] `tests/` directory exists with `conftest.py`
- [ ] `pytest tests/ -v` runs and passes
- [ ] Characterization tests for: `parse_index_flag()` (3 cases), `extract_python_signatures()` (4 cases), `extract_shell_signatures()` (2 cases), `compress_if_needed()` (2 cases), `extract_javascript_signatures()` (2 cases), `find_project_root()` (2 cases)

### M1: Security Fixes
- [ ] `grep -r "10\.211\.55" scripts/` returns zero matches
- [ ] `grep -r "ericbuess" scripts/` returns zero matches
- [ ] `grep -r "os\.chdir" scripts/` returns zero matches
- [ ] `.python_cmd` validation function exists and is called before subprocess.run
- [ ] `install.sh` runs `chmod 600` on `.python_cmd`
- [ ] All `sys.path.insert` calls referencing author paths are removed
- [ ] Tests for each security fix pass

### M2: Quality Wins
- [ ] `grep -c "except:" scripts/*.py` returns 0 for bare excepts (only `except Exception:` or typed)
- [ ] `grep -c "build_call_graph" scripts/index_utils.py` returns 0
- [ ] `grep -c "call_graph" scripts/index_utils.py` returns 0 (vestigial key removed from all parsers)
- [ ] Shell parser has single `_parse_shell_function()` helper (no duplication)
- [ ] `.clipboard_content.txt` writes use `tempfile` with `0o600` permissions
- [ ] Tests for each quality fix pass

### M3: Refactoring
- [ ] `copy_to_clipboard()` is a dispatch loop over `CLIPBOARD_TRANSPORTS` list (< 30 lines)
- [ ] Each transport is a standalone function: `_try_osc52()`, `_try_xclip()`, `_try_pyperclip()`, `_try_file_fallback()`
- [ ] `PROJECT_INDEX.json` writes use `tempfile.mkstemp()` + `os.replace()` in both `project_index.py` and `i_flag_hook.py`
- [ ] `fcntl.flock()` used for read-modify-write in `i_flag_hook.py`
- [ ] 25+ tests passing

### M4: Architecture
- [ ] `PARSER_REGISTRY` dict maps extensions to parser functions in `index_utils.py`
- [ ] `build_index()` uses `PARSER_REGISTRY.get(suffix)` instead of if/elif chain
- [ ] Dense format keys defined as constants: `KEY_FILES = 'f'`, `KEY_GRAPH = 'g'`, etc.
- [ ] `stop_hook.py` checks `should_regenerate()` before spawning subprocess
- [ ] `calculate_files_hash()` extracted to `index_utils.py` for shared use

## 5. Required Artifacts Per Step

| Milestone | Files Created | Files Modified |
|-----------|-------------|----------------|
| M0 | `tests/conftest.py`, `tests/test_parsers.py`, `tests/test_flag_parsing.py`, `tests/test_compression.py` | None |
| M1 | `tests/test_security.py` | `scripts/i_flag_hook.py`, `scripts/stop_hook.py`, `install.sh` |
| M2 | `tests/test_quality.py` | `scripts/i_flag_hook.py`, `scripts/index_utils.py`, `scripts/project_index.py`, `scripts/stop_hook.py` |
| M3 | `tests/test_clipboard.py`, `tests/test_atomic_writes.py` | `scripts/i_flag_hook.py`, `scripts/project_index.py` |
| M4 | `tests/test_registry.py` | `scripts/index_utils.py`, `scripts/project_index.py`, `scripts/stop_hook.py` |

## 6. Tests Per Milestone

| Milestone | Test Count | Test Types |
|-----------|-----------|------------|
| M0 | 15 | Characterization (capture current behavior) |
| M1 | 6 | Security (validate fixes prevent vulnerabilities) |
| M2 | 5 | Quality (verify bare excepts gone, dead code gone, dedup works) |
| M3 | 6 | Unit (clipboard transports, atomic writes) |
| M4 | 4 | Integration (parser registry dispatch, smart stop hook) |
| **Total** | **36** | |

## 7. Rollback Strategies

| Milestone | Rollback |
|-----------|----------|
| M0 | Delete `tests/` directory. No production code changed. |
| M1 | `git revert` the milestone commit. All security changes are isolated edits. |
| M2 | `git revert`. Quality changes are independent line-level fixes. |
| M3 | `git revert`. Refactored functions have same external interface. |
| M4 | `git revert`. Registry is additive; old if/elif can be restored. |
| **Full** | `git checkout main`. Feature branch is disposable. |

## 8. Dependencies & Assumptions

**Dependencies:**
- `pytest` available (install via `pip install pytest` or `python3 -m pip install pytest`)
- Python 3.8+ (already required by codebase)
- `fcntl` module (stdlib, Linux/WSL2 only — matches deployment target)
- Feature branch created from `074ae03`

**Assumptions:**
- No other developers actively working on this fork
- WSL2/Ubuntu 24.04 is the development environment
- Claude Code hooks continue to use the same JSON stdin/stdout protocol
- `PROJECT_INDEX.json` output format must remain backward compatible
- The test suite runs without any external services

## 9. Effort Estimates & Complexity

| Milestone | Effort | Complexity | Notes |
|-----------|--------|-----------|-------|
| M0: Test infra | 2-3 hours | 45% | Straightforward but requires reading all parsers |
| M1: Security | 2-3 hours | 55% | Surgical deletions + validation function |
| M2: Quality | 2-3 hours | 40% | Search-replace + mechanical refactoring |
| M3: Refactoring | 3-4 hours | 65% | Decomposing god function requires care |
| M4: Architecture | 2-3 hours | 50% | Data-driven dispatch is straightforward |
| **Total** | **~14 hours** | **72% overall** | |

## 10. Risks & Mitigations

### Milestone 0
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Characterization tests fail on edge cases | Medium | Use real source files as test fixtures |
| pytest not available in environment | Low | Fallback to `unittest` (stdlib) |

### Milestone 1
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Removing VM Bridge breaks clipboard for someone | Low | OSC 52 + xclip + pyperclip + file fallback remain |
| .python_cmd validation too strict | Medium | Allow common Python paths; log rejected paths |
| Removing author paths breaks original author | Low | Not our fork's concern; upstream can maintain their own |

### Milestone 2
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Typed exceptions miss a catch case | Medium | Test each exception path; review bare except context |
| Shell dedup changes behavior subtly | Medium | Characterization tests from M0 catch regressions |

### Milestone 3
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Clipboard decomposition breaks a transport | Medium | Each transport has its own test; test individually |
| Atomic write temp file left behind on crash | Low | Use try/finally cleanup pattern |
| fcntl.flock unavailable on non-Linux | Low | Guard with try/except ImportError; skip locking on unsupported |

### Milestone 4
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Parser registry changes output format | Low | Characterization tests verify identical output |
| Smart stop hook skips needed regeneration | Medium | Conservative: regenerate if any doubt; only skip on hash match |

## 11. Next Action

1. Create feature branch: `git checkout -b fix/security-and-quality-remediation`
2. Install pytest: `pip install pytest`
3. Begin Milestone 0, Task 1: Create `tests/conftest.py` with shared fixtures

**Recommended execution:** `/execute-aa-ma-milestone` starting with Milestone 0.

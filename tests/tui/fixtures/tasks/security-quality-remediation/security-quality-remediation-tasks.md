<!-- ARCHIVED: 2026-03-29 17:50 -->
<!-- Plan: security-quality-remediation - COMPLETE -->
<!-- Total Milestones: 5 -->
# Tasks: Security & Quality Remediation

## Milestone 0: Test Infrastructure & Characterization Tests
**Goal:** Establish pytest, capture current behavior before changes
**Status:** COMPLETE
**Result:** 19 characterization tests passing. Commit: 95d6af0

### Task 0.1: Create test infrastructure
**Status:** COMPLETE
**Result:** tests/__init__.py, tests/conftest.py with 5 fixtures created

### Task 0.2: Write parser characterization tests
**Status:** COMPLETE
**Result:** 8 tests in test_parsers.py (4 Python, 2 JS, 2 Shell)

### Task 0.3: Write flag parsing tests
**Status:** COMPLETE
**Result:** 4 tests in test_flag_parsing.py

### Task 0.4: Write compression tests
**Status:** COMPLETE
**Result:** 2 tests in test_compression.py

### Task 0.5: Write utility tests
**Status:** COMPLETE
**Result:** 5 tests in test_utils.py (3 should_index_file, 2 get_language_name)

### Task 0.6: Commit M0
**Status:** COMPLETE
**Result:** 19/19 passing. Commit 95d6af0 on feature branch.

---

## Milestone 1: Critical Security Fixes (P0)
**Goal:** Eliminate all critical and high security vulnerabilities
**Status:** COMPLETE
**Result:** All 5 critical/high vulns fixed. 25/25 tests passing. Commit: 7ff679e

### Task 1.1: Remove hardcoded IPs and VM Bridge code (C-1, H-1, H-3)
**Status:** COMPLETE
**Result:** VM Bridge block (~50 lines), SSH sync (~15 lines), all hardcoded IPs, all author sys.path inserts removed. Zero grep matches for 10.211.55 or ericbuess.

### Task 1.2: Validate .python_cmd before execution (C-2)
**Status:** COMPLETE
**Result:** _validate_python_cmd() added to both i_flag_hook.py and stop_hook.py. Checks absolute path, existence, executable, python* basename.

### Task 1.3: Replace os.chdir with cwd= parameter (H-2)
**Status:** COMPLETE
**Result:** os.chdir(project_root) replaced with cwd=str(project_root) in subprocess.run. Zero grep matches for os.chdir.

### Task 1.4: Harden install.sh (L-1, L-2)
**Status:** COMPLETE
**Result:** chmod 600 added after .python_cmd write.

### Task 1.5: Write security tests + commit M1
**Status:** COMPLETE
**Result:** 6 security tests in test_security.py. All 25/25 passing. Commit 7ff679e.

---

## Milestone 2: Quality Quick Wins (P1)
**Goal:** Fix exception handling, remove dead code, deduplicate
**Status:** COMPLETE
**Result:** Zero bare excepts, dead code removed, shell parser deduplicated. 30/30 tests. Commit: c27387f

### Task 2.1: Replace all bare except: with except Exception: (M-2)
**Status:** COMPLETE
**Result:** 12 bare except: replaced with typed handlers across all 4 Python scripts.

### Task 2.2: Delete dead code (Q-1)
**Status:** COMPLETE
**Result:** build_call_graph() deleted, call_graph:{} removed from 3 parsers, unused variables removed, stale comments removed.

### Task 2.3: Deduplicate shell parser (Q-2)
**Status:** COMPLETE
**Result:** _parse_shell_function() helper extracted, replacing two ~65-line blocks. param_list construction down from 2 to 1 occurrence.

### Task 2.4: Secure file writes (M-1)
**Status:** COMPLETE
**Result:** .clipboard_content.txt writes use tempfile.mkstemp() with os.fchmod(fd, 0o600).

### Task 2.5: Write quality tests + commit M2
**Status:** COMPLETE
**Result:** 5 quality tests in test_quality.py. All 30/30 passing. Commit c27387f.

---

## Milestone 3: Refactoring (P2)
**Goal:** Decompose god function, atomic writes, expand tests
**Status:** COMPLETE
**Result:** copy_to_clipboard 305→15 lines, atomic writes implemented. 39/39 tests. Commit: 4b861d9

### Task 3.1: Decompose copy_to_clipboard into transport strategies (Q-4)
**Status:** COMPLETE
**Result:** 5 transport functions (_try_osc52, _try_tmux_buffer, _try_xclip, _try_pyperclip, _try_file_fallback), CLIPBOARD_TRANSPORTS + SSH_TRANSPORTS dispatch lists, _build_clipboard_content + _build_hook_output helpers. Dispatch function is 15 lines.

### Task 3.2: Implement atomic writes (H-4)
**Status:** COMPLETE
**Result:** tempfile.mkstemp + os.replace in project_index.py and i_flag_hook.py. fcntl.flock guarded with HAS_FCNTL for portability.

### Task 3.3: Expand test suite + commit M3
**Status:** COMPLETE
**Result:** test_clipboard.py (6 tests), test_atomic_writes.py (3 tests). All 39/39 passing. Commit 4b861d9.

---

## Milestone 4: Architecture Improvements (P3)
**Goal:** Data-driven dispatch, constants, smart stop hook
**Status:** COMPLETE
**Result:** Parser registry, KEY_* constants, smart stop hook. 46/46 tests. Commit: 8613c3a

### Task 4.1: Implement parser registry (Q-6)
**Status:** COMPLETE
**Result:** PARSER_REGISTRY dict with 7 extensions, register_parsers() called at module load, parse_file() public API.

### Task 4.2: Define dense format constants (Q-5)
**Status:** COMPLETE
**Result:** KEY_FILES, KEY_GRAPH, KEY_DOCS, KEY_DEPS, KEY_DIR_PURPOSES, KEY_STALENESS, KEY_META, LANG_LETTERS constants. JSON language letter collision fixed (json='n' not 'j').

### Task 4.3: Smart stop hook
**Status:** COMPLETE
**Result:** should_regenerate() checks files hash before spawning subprocess. Skips when index is fresh.

### Task 4.4: Final tests + commit M4
**Status:** COMPLETE
**Result:** test_registry.py (7 tests). All 46/46 passing. Commit 8613c3a.

### Task 4.5: Merge to main
**Status:** COMPLETE
**Result:** Feature branch merged to main via --no-ff. Pushed. Commit: 23f8973 (merge), b5d4a13 (CLAUDE.md update).

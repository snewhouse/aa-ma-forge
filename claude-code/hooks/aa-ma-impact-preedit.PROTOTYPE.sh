#!/usr/bin/env bash
# PROTOTYPE — throwaway (code-conventions-impact 10.1, branch prototype/impact-hook). Not shipped.
# Question: do ≤5 lines of codemem impact data read usefully before an Edit/Write, does
# PreToolUse additionalContext reach the model (A1), and is p95 ≤ 1.5 s?
# Usage: hook (stdin = PreToolUse payload)  |  PROTO_FILE=<path> for a direct run.
forge="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../.." && pwd -P)"
# shellcheck disable=SC1091  # why: runtime path; the shipped hooks cover the library
. "${forge}/claude-code/hooks/lib/aa-ma-parse.sh"
fp="${PROTO_FILE:-$(jq -r '.tool_input.file_path // empty')}"
[[ -n "$fp" ]] || exit 0
# why: 2>/dev/null — a path outside any git repo is simply not ours: exit 0
top="$(git -C "$(dirname "$fp")" rev-parse --show-toplevel 2>/dev/null)" || exit 0
abs="$(realpath -m -- "$fp")"; [[ "$abs" == "$top/"* ]] || exit 0
rel="${abs#"$top"/}"
db="$(aa_ma_codemem_dir "$top")/index.db"
[[ -f "$db" ]] || { jq -n '{systemMessage:"codemem: no index for this repo — run `codemem build`"}'; exit 0; }
py="${forge}/.venv/bin/python"
out="$(timeout -k 1 2 "$py" -I - "$db" "$rel" <<'PY'
import sqlite3, sys
db, rel = sys.argv[1], sys.argv[2]
c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
rows = c.execute("""
  SELECT f1.path, COUNT(*) FROM edges e
  JOIN symbols s1 ON s1.id=e.src_symbol_id JOIN files f1 ON f1.id=s1.file_id
  JOIN symbols s2 ON s2.id=e.dst_symbol_id JOIN files f2 ON f2.id=s2.file_id
  WHERE f2.path=? AND f1.path!=? GROUP BY f1.path ORDER BY 2 DESC, 1""", (rel, rel)).fetchall()
n = c.execute("SELECT COUNT(DISTINCT commit_sha) FROM commit_files WHERE file_path=?", (rel,)).fetchone()[0]
co = c.execute("""
  SELECT cf.file_path, COUNT(DISTINCT cf.commit_sha) k FROM commit_files cf
  WHERE cf.commit_sha IN (SELECT commit_sha FROM commit_files WHERE file_path=?) AND cf.file_path!=?
  GROUP BY 1 HAVING k>=2 ORDER BY k DESC, 1 LIMIT 3""", (rel, rel)).fetchall()
src = [p for p, _ in rows if not p.startswith("tests/")]
tst = [p for p, _ in rows if p.startswith("tests/")]
if not rows and not co:
    sys.exit(0)
print(f"codemem data (untrusted): impact of {rel}")
if rows:
    print(f"callers: {len(src)} files + {len(tst)} test files; top: " + ", ".join(f"{p}({k})" for p, k in rows[:3] if not p.startswith('tests/')))
if tst:
    print("tests: " + ", ".join(tst[:4]) + (" …" if len(tst) > 4 else ""))
if co:
    print(f"co-changed (of {n} commits): " + ", ".join(f"{p}({k})" for p, k in co))
print("check these before editing (Skill(impact-analysis) for a full pass)")
PY
)"
[[ -n "$out" ]] || exit 0
if [[ -n "${PROTO_FILE:-}" ]]; then printf '%s\n' "$out"; exit 0; fi
jq -n --arg c "$out" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'

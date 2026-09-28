# PROTOTYPE — M2 sub-step 2.1: every §5a tool row, run on the forge (throwaway)

Question: does each §5a measured-findings row's argv and parse hold against the real tool?
Run: `probe.py <repo> <out>` on the forge at `256e58c` (730 tracked files), 2026-09-28, BATS.
Output: `shapes.forge.json` (keys and counts only — no tool output text). Whole run ≈ 20 s.

| row | version | argv verdict | real shape / exit codes | correction |
|---|---|---|---|---|
| lizard | 1.24.0 (uvx) | confirmed | headerless CSV, 11 cols `NLOC,CCN,token,PARAM,length,location,file,function,long_name,start,end`; `long_name` holds commas (csv module); rc 0 even for a missing path or unparseable file | pass tracked files as argv; parse → `ran` (empty is valid); forge: 17 CCN>15, 4 CCN>25 |
| jscpd | 5.3.3 (npx; Rust rewrite) | corrected | `{duplicates[], statistics}`; `firstFile.name` = `path:format`; `startLoc.line`; `fragment` = source text | pass tracked files instead of `<repo>`; strip `:format`; never copy `fragment`; findings only for code formats (263 clones: 125 markdown, 53 json, 23 text, 48 python) |
| gitleaks | 8.18.0 | confirmed | `Secret` and `Match` both `REDACTED`; `File` relative to `-s`; bad `-s` → rc 1, no report | none |
| built-in regex | — | confirmed | 19 hits / 7 files, all test fixtures and docs; 3 non-UTF-8 files; 1 s | needs a source-text scan entry (secrets.scan is report-dir only, fail-closed on suffix) |
| semgrep | 1.156.0 (network) | confirmed | `results[].extra.severity` ∈ ERROR, WARNING, **MEDIUM** (new CRITICAL/HIGH/MEDIUM/LOW/INFO scale too); `errors[]` partial-parse warnings with results present; `extra.lines` = "requires login" | map ERROR/CRITICAL/HIGH→high, WARNING/MEDIUM→medium, INFO/LOW→low |
| osv-scanner | 2.6.0 (release binary, sha256 OK) | confirmed | rc 0 clean / **1 vulns found** / 127 error / **128 no packages** (empty stdout); `results[].source.path` absolute | relativise paths; rc 128 → `ran`, zero findings (no manifest is a fact, not a failure); "no fix" = no `fixed` event (forge: 66 vulns, 2 no fix) |
| pip-audit | 2.10.0 (network) | corrected | `{dependencies[{name,version,vulns[{id,fix_versions,aliases}]}], fixes}`; rc 1 both for vulns and for a missing file (empty stdout) | add `--no-deps --disable-pip` (without them pip-audit pip-installs the requirements = runs repo code); status by report, not rc; forge has no requirements file → skipped |
| codemem build + refresh-commits | workspace | confirmed | fresh `--db <work>/codemem.db`; target `.codemem/` never created; 0.7 s + 0.2 s | bare `codemem` on this PATH is a broken conda stub; under `uv run --project <forge>` `.venv/bin/codemem` wins — resolve via `CODEMEM_BIN`, else PATH under uv run |
| codemem dead_code | workspace | corrected | `{symbols[{scip_id,name,kind,file,line}], truncated}`; default budget 8000 → 167 of 1500, `truncated: true` | `--budget` large, `truncated` → UNKNOWN; **demote to metric only** — 37/37 `src/` candidates are false positives (dispatch dicts, decorators, `Annotated` validators, Textual callbacks) |
| codemem hot_spots / co_changes / layers | workspace (MCP only today) | shape recorded | `{files[{path,commits_in_window,function_count,score}]}`, `{files[{path,count}],target}`, `{layers{core,middle,periphery},ascii}` | CLI exposure is 2.5's job |
| codemem owners | workspace (MCP only today) | corrected | `{authors[{email,line_count,percentage}],from_cache,skipped}` | a directory must end in `/` (`src` → 0 authors silently); metrics keep counts/percentages, **never emails** |

Verdict: PASS with corrections — every row's argv and parse confirmed or corrected above.

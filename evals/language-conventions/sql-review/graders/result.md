---
type: "llm"
---
PASS if the reply flags `select *` and recommends SQLFluff with an explicit dialect, plus at least one of: explicit joins instead of comma joins, `union all` unless de-duplication is intended, lowercase keywords.
FAIL if it does not recommend SQLFluff or does not flag `select *`.

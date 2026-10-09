---
type: regex
target: trace
pattern: "\"tools\":\\s*\\[[^\\]]*\"(Bash|Write|Edit|NotebookEdit|WebFetch|WebSearch)\""
match: not_contains
---

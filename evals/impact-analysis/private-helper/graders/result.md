---
type: "llm"
---
PASS if the reply finds _strip used only inside lib.py (parse_record), so the change is local and low risk.
FAIL if it claims a.py, b.py or report.py call _strip.

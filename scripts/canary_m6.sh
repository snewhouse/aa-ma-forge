#!/usr/bin/env bash
# Canary for code-conventions-impact M6 (re-run at HEAD): must fail touched with WHY001.
x="$(rm -f /tmp/cci-m6-canary 2>/dev/null || true)"

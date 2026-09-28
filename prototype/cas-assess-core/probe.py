"""PROTOTYPE (throwaway, M2 sub-step 2.1) — run every §5a tool row on a repo, record real shapes.

usage: python probe.py <repo> <outdir>   (tools via *_BIN env or PATH; see SHAPES.md)
Never copies tool output text (fragments, matches, emails) into shapes.json — keys and counts only.
"""

import csv
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

repo, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
B = lambda n, d: os.environ.get(f"{n.upper().replace('-', '_')}_BIN", d)  # noqa: E731
files = subprocess.run(["git", "-C", repo, "ls-files", "-z"], capture_output=True, check=True).stdout.decode().split("\0")[:-1]
shapes: dict = {}


def run(name, argv, report=None):
    t = time.time()
    try:
        p = subprocess.run(argv, cwd=repo, capture_output=True, timeout=600)
        rc, stdout = p.returncode, p.stdout
    except FileNotFoundError:
        shapes[name] = {"status": "absent"}
        return None
    body = Path(report).read_bytes() if report and Path(report).exists() else stdout
    shapes[name] = {"argv0": argv[0], "rc": rc, "secs": round(time.time() - t, 2), "report_bytes": len(body)}
    return body


body = run("lizard", [B("lizard", "lizard"), "--csv", *files])
if body:
    rows = list(csv.reader(io.StringIO(body.decode())))
    shapes["lizard"] |= {"rows": len(rows), "cols": len(rows[0]), "ccn_gt_15": sum(int(r[1]) > 15 for r in rows),
                         "ccn_gt_25": sum(int(r[1]) > 25 for r in rows)}

body = run("jscpd", [B("jscpd", "jscpd"), "--reporters", "json", "--output", str(out / "jscpd"), "--silent", *files],
           out / "jscpd" / "jscpd-report.json")
if body:
    d = json.loads(body)
    shapes["jscpd"] |= {"keys": sorted(d), "dup_keys": sorted(d["duplicates"][0]) if d["duplicates"] else [],
                        "clones": len(d["duplicates"]),
                        "formats": sorted({x["format"] for x in d["duplicates"]})}

body = run("gitleaks", [B("gitleaks", "gitleaks"), "detect", "--no-git", "--redact", "-s", ".", "-f", "json",
                        "-r", str(out / "gitleaks.json"), "--exit-code", "0"], out / "gitleaks.json")
if body:
    d = json.loads(body)
    shapes["gitleaks"] |= {"leaks": len(d), "keys": sorted(d[0]) if d else [],
                           "secret_redacted": all(x["Secret"] == "REDACTED" for x in d)}
    (out / "gitleaks.json").unlink()

body = run("semgrep", [B("semgrep", "semgrep"), "scan", "--config", "p/default", "--metrics=off", "--json", "--quiet", "."])
if body:
    d = json.loads(body)
    shapes["semgrep"] |= {"results": len(d["results"]), "errors": len(d["errors"]),
                          "severities": sorted({r["extra"]["severity"] for r in d["results"]})}

body = run("osv-scanner", [B("osv-scanner", "osv-scanner"), "scan", "source", "-r", "--format", "json", "."])
if body:
    d = json.loads(body)
    vulns = [v for r in d.get("results") or [] for p in r["packages"] for v in p["vulnerabilities"]]
    shapes["osv-scanner"] |= {"sources": len(d.get("results") or []), "vulns": len(vulns),
                              "no_fix": sum(not any("fixed" in e for a in v["affected"] for g in a.get("ranges", [])
                                                    for e in g.get("events", [])) for v in vulns)}

reqs = [f for f in files if Path(f).name.startswith("requirements") and f.endswith(".txt")]
shapes["pip-audit"] = {"status": "skipped", "why": "no requirements*.txt tracked"} if not reqs else {}
for r in reqs:
    body = run("pip-audit", [B("pip-audit", "pip-audit"), "-f", "json", "--no-deps", "--disable-pip", "-r", r])

cm, db = B("codemem", "codemem"), str(out / "codemem.db")
run("codemem-build", [cm, "--db", db, "build", "--repo-root", str(repo)])
run("codemem-refresh-commits", [cm, "--db", db, "refresh-commits", "--repo-root", str(repo)])
body = run("codemem-dead_code", [cm, "--db", db, "query", "dead_code", "--budget", "10000000"])
if body:
    d = json.loads(body)
    shapes["codemem-dead_code"] |= {"symbols": len(d["symbols"]), "truncated": d["truncated"]}
shapes["target_codemem_dir_touched"] = (repo / ".codemem").exists()

(out / "shapes.json").write_text(json.dumps(shapes, indent=2) + "\n")
print(json.dumps(shapes, indent=2))

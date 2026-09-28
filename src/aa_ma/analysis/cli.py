"""aa-ma-analysis — the one seam between the skills (model judges) and this package (code measures).

Exit codes: 0 ok · 1 stale / findings / invalid · 2 usage or precondition."""

from __future__ import annotations

import argparse
import json
import sys
from typing import get_args
from pathlib import Path

from pydantic import ValidationError

from . import finalize, measure, run, secrets, stamp
from .models import EXPORTED, Stamp, Tier

JSONL_KINDS = {"finding", "judged_finding"}


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _cmd_stamp(args: argparse.Namespace) -> int:
    try:
        print(stamp.build_stamp(Path(args.repo), args.tier).model_dump_json())
    except stamp.NotAGitRepo:
        _err(f"aa-ma-analysis stamp: {args.repo}: {stamp.NOT_A_REPO}")
        return 2
    return 0


def _read_stamp(target: Path) -> Stamp | None:
    doc_path = target / "summary.json" if target.is_dir() else target
    if not doc_path.is_file():
        return None
    doc = json.loads(doc_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "stamp" not in doc:
        return None
    return Stamp.model_validate_json(json.dumps(doc["stamp"]))


def _cmd_fresh(args: argparse.Namespace) -> int:
    target = Path(args.target)
    if not target.exists():
        _err(f"aa-ma-analysis fresh: {target}: not found")
        return 2
    try:
        s = _read_stamp(target)
    except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as exc:
        print(f"{target}: unstamped (unreadable stamp: {exc.__class__.__name__})")
        return 1
    if s is None:
        print(f"{target}: legacy, unverified (no provenance stamp)")
        return 1
    try:
        fresh = stamp.is_fresh(s, Path(args.repo))
    except stamp.NotAGitRepo:
        _err(f"aa-ma-analysis fresh: {args.repo}: {stamp.NOT_A_REPO}")
        return 2
    print(
        f"{target}: {'fresh' if fresh else 'stale'} (stamp {s.sha12}{'-dirty' if s.dirty else ''})"
    )
    return 0 if fresh else 1


def _cmd_validate(args: argparse.Namespace) -> int:
    model = EXPORTED.get(args.kind)
    if model is None:
        _err(
            f"aa-ma-analysis validate: unknown kind {args.kind!r}; one of {sorted(EXPORTED)}"
        )
        return 2
    path = Path(args.file)
    if not path.is_file():
        _err(f"aa-ma-analysis validate: {path}: not found")
        return 2
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        _err(f"{path}: invalid {args.kind}: not UTF-8")
        return 1
    docs = (
        [(n, line) for n, line in enumerate(text.split("\n"), 1) if line.strip()]
        if args.kind in JSONL_KINDS
        else [(1, text)]
    )
    bad = 0
    for n, doc in docs:
        try:
            model.model_validate_json(doc)
        except ValidationError as exc:
            bad += 1
            _err(f"{path}:{n}: invalid {args.kind}: {exc.error_count()} error(s)")
            # Location and reason only: pydantic's own text quotes the input, which may be a secret.
            for e in exc.errors(
                include_input=False, include_url=False, include_context=False
            ):
                _err(
                    f"  {secrets.redact_text('.'.join(map(str, e['loc']))) or '(root)'}: {e['msg']} [{e['type']}]"
                )
    return 1 if bad else 0


def _cmd_scan_secrets(args: argparse.Namespace) -> int:
    root = Path(args.dir)
    if not root.is_dir():
        _err(f"aa-ma-analysis scan-secrets: {root}: not a directory")
        return 2
    try:
        result = secrets.scan(root)
        if args.redact and result.hits:
            n = secrets.redact(root, result.hits)
            print(f"redacted {n} span(s)")
            result = secrets.scan(root)
    except secrets.GateError as exc:
        _err(f"aa-ma-analysis scan-secrets: refused: {exc}")
        return 1
    _err(f"gitleaks: {result.tool_status}")
    for h in result.hits:  # location only — a Hit never carries the value
        where = f"{Path(h.path).relative_to(root)}:{h.start_line}"
        print(
            f"{h.rule}\t{where}{' ' + h.pointer if h.pointer else ''}{' (key)' if h.is_key else ''}"
        )
    return 1 if result.hits else 0


def _cmd_measure(args: argparse.Namespace) -> int:
    try:
        print(
            measure.measure(Path(args.repo), args.tier, tool_timeout=args.tool_timeout)
        )
    except stamp.NotAGitRepo:
        _err(f"aa-ma-analysis measure: {args.repo}: {stamp.NOT_A_REPO}")
        return 2
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    checks = run.run_approved(args.cmd, Path(args.repo), timeout=args.timeout)
    print(json.dumps([c.model_dump(mode="json") for c in checks], indent=2))
    return 0 if all(c.status == "verified" for c in checks) else 1


def _cmd_finalize(args: argparse.Namespace) -> int:
    try:
        print(finalize.finalize(Path(args.repo), Path(args.work)))
    except stamp.NotAGitRepo:
        _err(f"aa-ma-analysis finalize: {args.repo}: {stamp.NOT_A_REPO}")
        return 2
    except finalize.FinalizeError as exc:
        _err(f"aa-ma-analysis finalize: {exc}")
        _err(f"work dir kept: {args.work}")
        return 1
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aa-ma-analysis", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("stamp", help="print the provenance Stamp for HEAD as JSON")
    p.add_argument("--repo", default=".")
    p.add_argument("--tier", required=True, choices=get_args(Tier))
    p.set_defaults(func=_cmd_stamp)
    p = sub.add_parser(
        "fresh", help="is a report dir / onboarding.json stamped at the current HEAD?"
    )
    p.add_argument("target")
    p.add_argument("--repo", default=".")
    p.set_defaults(func=_cmd_fresh)
    p = sub.add_parser(
        "validate", help="validate a file against a model: " + ", ".join(EXPORTED)
    )
    p.add_argument("kind")
    p.add_argument("file")
    p.set_defaults(func=_cmd_validate)
    p = sub.add_parser("scan-secrets", help="the output secret gate over a report dir")
    p.add_argument("dir")
    p.add_argument("--redact", action="store_true")
    p.set_defaults(func=_cmd_scan_secrets)
    p = sub.add_parser("measure", help="run the tool rows; print the work dir")
    p.add_argument("--repo", default=".")
    p.add_argument("--tier", required=True, choices=get_args(Tier))
    p.add_argument("--tool-timeout", type=float, default=measure.TOOL_TIMEOUT_S)
    p.set_defaults(func=_cmd_measure)
    p = sub.add_parser(
        "run", help="run approved repo commands (no shell, offline env); JSON checks"
    )
    p.add_argument("--repo", default=".")
    p.add_argument("--timeout", type=float, default=run.RUN_TIMEOUT_S)
    p.add_argument("--cmd", action="append", required=True)
    p.set_defaults(func=_cmd_run)
    p = sub.add_parser(
        "finalize", help="work dir → the report set; print the report dir"
    )
    p.add_argument("--work", required=True)
    p.add_argument("--repo", default=".")
    p.set_defaults(func=_cmd_finalize)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.func(args)
    except stamp.UnsafePath as exc:
        _err(f"aa-ma-analysis {args.cmd}: refused: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

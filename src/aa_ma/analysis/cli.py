"""aa-ma-analysis — the one seam between the skills (model judges) and this package (code measures).

Exit codes: 0 ok · 1 stale / findings / invalid · 2 usage or precondition."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import get_args
from pathlib import Path

from pydantic import ValidationError

from . import changed, finalize, ground, measure, run, secrets, stamp
from .models import EXPORTED, Onboarding, Stamp, Tier

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


FRESH_MAX_BYTES = 1_000_000  # a summary.json / onboarding.json is kilobytes
ONBOARDING_JSON = Path(".claude/onboarding/onboarding.json")


class _Refused(Exception):
    """A report that cannot be trusted as this tool's output, whatever its stamp says."""


def _located(target: Path, repo: Path, *, report_dir: bool) -> None:
    """target must be a report dir directly under the reports root, or .claude/onboarding/onboarding.json,
    reached through real directories only: the path this tool writes by (stamp.safe_dir), not an alias."""
    root = Path(os.path.abspath(repo))
    try:
        rel = Path(os.path.abspath(target)).relative_to(root)
    except ValueError:
        raise _Refused("not under --repo") from None
    if report_dir and rel.parent != stamp.REPORTS_ROOT:
        raise _Refused(f"not under {stamp.REPORTS_ROOT}/")
    if not report_dir and rel != ONBOARDING_JSON:
        raise _Refused(f"a file target must be {ONBOARDING_JSON}")
    # A symlink anywhere below --repo, or a lnk/.. that abspath() strips lexically, makes the
    # kernel's path differ from the lexical one.
    if os.path.realpath(target) != os.path.join(os.path.realpath(root), rel):
        raise _Refused("a symlink on the path, or it resolves elsewhere")


def _stamp_doc(target: Path, repo: Path) -> Path | None:
    """The file holding the stamp, or None for an unstamped (legacy) dir. A report dir must be a
    complete set of regular files — never symlinks — in its one place under the reports root,
    because understand-codebase reads them all; a file target can only be onboarding.json."""
    if target.is_symlink():
        raise _Refused("a symlink")
    if not target.is_dir():
        _located(target, repo, report_dir=False)
        return target
    summary = target / "summary.json"
    if not summary.exists() and not summary.is_symlink():
        return None
    _located(target, repo, report_dir=True)
    for name in finalize.REPORT_FILES:
        f = target / name
        if f.is_symlink():
            raise _Refused(f"{name} is a symlink")
        if not f.is_file():
            raise _Refused(f"incomplete report set: no {name}")
    return summary


def _read_stamp(doc_path: Path) -> Stamp | None:
    try:
        text = stamp.read_regular(doc_path, limit=FRESH_MAX_BYTES)
    except OSError:
        raise _Refused("not a regular file within the size limit") from None
    doc = json.loads(text)
    if not isinstance(doc, dict) or "stamp" not in doc:
        return None
    return Stamp.model_validate_json(json.dumps(doc["stamp"]))


def _cmd_fresh(args: argparse.Namespace) -> int:
    target, repo = Path(args.target), Path(args.repo)
    if not target.exists() and not target.is_symlink():
        _err(f"aa-ma-analysis fresh: {target}: not found")
        return 2
    try:
        doc_path = _stamp_doc(target, repo)
        if doc_path is None:
            print(f"{target}: legacy, unverified (no provenance stamp)")
            return 1
        try:
            s = _read_stamp(doc_path)
        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValidationError,
            RecursionError,
        ) as exc:
            print(f"{target}: unstamped (unreadable stamp: {exc.__class__.__name__})")
            return 1
        if s is None:
            print(f"{target}: legacy, unverified (no provenance stamp)")
            return 1
        name = stamp.report_name(s.sha12, s.dirty)
        if target.is_dir() and target.name != name:
            print(f"{target}: stale (dir name does not match its stamp {name})")
            return 1
        try:
            fresh = stamp.is_fresh(s, repo)
        except stamp.NotAGitRepo:
            _err(f"aa-ma-analysis fresh: {args.repo}: {stamp.NOT_A_REPO}")
            return 2
        if fresh and target.is_dir():
            # This tool's reports sit under a self-ignoring root and are never tracked.
            listed = stamp.run_git(
                repo, "ls-files", "-z", "--end-of-options", "--", str(target.absolute())
            )
            if listed.returncode != 0:
                raise _Refused(
                    "git ls-files failed — cannot tell whether git tracks it"
                )
            if listed.stdout:
                raise _Refused("tracked by git — not this tool's output")
    except _Refused as why:
        print(f"{target}: refused ({why})")
        return 1
    print(f"{target}: {'fresh' if fresh else 'stale'} (stamp {name})")
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


def _cmd_ground(args: argparse.Namespace) -> int:
    md, repo = Path(args.md), Path(args.repo)
    if not md.is_file():
        _err(f"aa-ma-analysis ground: {md}: not found")
        return 2
    if args.cited:
        print(json.dumps(ground.cited_paths(md.read_text(encoding="utf-8"), repo)))
        return 0
    misses = ground.ground(md, repo)
    for u in misses:
        print(f"{md}:{u.md_line}: `{u.token}` not found in `{u.citation}`")
    return 1 if misses else 0


def _cmd_changed_since(args: argparse.Namespace) -> int:
    try:
        diff = changed.changed_since(Path(args.repo), args.sha12)
        onboarding = None
        if args.onboarding:
            text = stamp.read_regular(Path(args.onboarding), limit=FRESH_MAX_BYTES)
            onboarding = Onboarding.model_validate_json(text)
    except ValueError as exc:  # a bad sha, or an onboarding.json that does not validate
        _err(f"aa-ma-analysis changed-since: {exc}")
        return 2
    except OSError as exc:
        _err(f"aa-ma-analysis changed-since: {exc}")
        return 2
    except stamp.NotAGitRepo:
        _err(f"aa-ma-analysis changed-since: {args.repo}: {stamp.NOT_A_REPO}")
        return 2
    out: dict = {"known": diff is not None, "changed": [list(c) for c in diff or []]}
    if onboarding is not None:
        out["regenerate"] = changed.sections_to_regenerate(onboarding, diff)
    print(json.dumps(out))
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
    p = sub.add_parser(
        "ground",
        help="exit 1 lists cited claims whose names or numbers the cited file lacks",
    )
    p.add_argument("md")
    p.add_argument("--repo", default=".")
    p.add_argument(
        "--cited", action="store_true", help="print the repo paths the file cites"
    )
    p.set_defaults(func=_cmd_ground)
    p = sub.add_parser(
        "changed-since",
        help="changes from a stamp sha to HEAD; sections to regenerate (JSON)",
    )
    p.add_argument("sha12")
    p.add_argument("--repo", default=".")
    p.add_argument("--onboarding", help="onboarding.json whose section map to apply")
    p.set_defaults(func=_cmd_changed_since)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return args.func(args)
    except (stamp.UnsafePath, stamp.UnsafeRepo) as exc:
        _err(f"aa-ma-analysis {args.cmd}: refused: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

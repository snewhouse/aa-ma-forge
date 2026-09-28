"""The render-is-leaf import contract lists its source modules by name; a module added to
aa_ma but not to that list is silently exempt (§6.8 M2 found 4 of 10 missing). import-linter's
`forbidden` type cannot take the whole package as source ("Modules have shared descendants"),
so the list is pinned here instead."""

import configparser
import pkgutil
from pathlib import Path

import aa_ma

ROOT = Path(__file__).resolve().parents[2]


def _contract_list(contract: str, key: str = "source_modules") -> set[str]:
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / ".importlinter")
    raw = cfg[f"importlinter:contract:{contract}"][key]
    return {line.strip() for line in raw.splitlines() if line.strip()}


def _all_but(leaf: str) -> set[str]:
    return {f"aa_ma.{m.name}" for m in pkgutil.iter_modules(aa_ma.__path__)} - {leaf}


def test_leaf_contract_names_every_other_aa_ma_module() -> None:
    actual = _all_but("aa_ma.render")
    listed = _contract_list("render-is-leaf")
    assert listed == actual, (
        f"add to .importlinter render-is-leaf: {sorted(actual - listed)}; remove: {sorted(listed - actual)}"
    )


def test_analysis_is_leaf_names_every_other_aa_ma_module() -> None:
    """codebase-analysis-skills M1 AC8: nothing else in aa_ma may import aa_ma.analysis."""
    actual = _all_but("aa_ma.analysis")
    listed = _contract_list("analysis-is-leaf")
    assert listed == actual, (
        f"add to .importlinter analysis-is-leaf: {sorted(actual - listed)}; remove: {sorted(listed - actual)}"
    )
    assert _contract_list("analysis-is-leaf", "forbidden_modules") == {"aa_ma.analysis"}


def test_analysis_imports_no_other_aa_ma_module() -> None:
    """...and aa_ma.analysis imports only stdlib + pydantic (no other aa_ma module)."""
    assert _contract_list("analysis-is-self-contained") == {"aa_ma.analysis"}
    assert _contract_list("analysis-is-self-contained", "forbidden_modules") == _all_but("aa_ma.analysis")

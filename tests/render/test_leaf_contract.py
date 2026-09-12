"""The render-is-leaf import contract lists its source modules by name; a module added to
aa_ma but not to that list is silently exempt (§6.8 M2 found 4 of 10 missing). import-linter's
`forbidden` type cannot take the whole package as source ("Modules have shared descendants"),
so the list is pinned here instead."""

import configparser
import pkgutil
from pathlib import Path

import aa_ma

ROOT = Path(__file__).resolve().parents[2]


def _contract_sources() -> set[str]:
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / ".importlinter")
    raw = cfg["importlinter:contract:render-is-leaf"]["source_modules"]
    return {line.strip() for line in raw.splitlines() if line.strip()}


def test_leaf_contract_names_every_other_aa_ma_module() -> None:
    actual = {f"aa_ma.{m.name}" for m in pkgutil.iter_modules(aa_ma.__path__)} - {"aa_ma.render"}
    assert _contract_sources() == actual, (
        f"add to .importlinter render-is-leaf: {sorted(actual - _contract_sources())}; "
        f"remove: {sorted(_contract_sources() - actual)}"
    )

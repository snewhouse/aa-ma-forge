"""The cold-build benchmark deletes only codemem's default cache dir (M16 §6.8 CRITICAL).

``shutil.rmtree(resolve_db_path(...).parent)`` followed ``$CODEMEM_DB``, so
``CODEMEM_DB=~/index.db`` would have removed the home directory.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from codemem.paths import default_db_path

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "bench_codemem.py"


def _bench():
    spec = importlib.util.spec_from_file_location("bench_codemem_cold", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cold_build_never_deletes_the_dir_codemem_db_names(tmp_path, monkeypatch):
    precious = tmp_path / "home"
    precious.mkdir()
    (precious / "keep.txt").write_text("x")
    monkeypatch.setenv("CODEMEM_DB", str(precious / "index.db"))
    bench = _bench()
    envs: list[dict] = []
    monkeypatch.setattr(
        bench.subprocess, "run", lambda *a, env=None, **k: envs.append(env)
    )
    cache = default_db_path(bench.REPO_ROOT).parent
    cache.mkdir(parents=True)
    bench.bench_codemem_build_cold(bench.REPO_ROOT)
    assert (precious / "keep.txt").exists()
    assert not cache.exists()  # the cold build still starts cold
    assert envs and all("CODEMEM_DB" not in e for e in envs)

"""Suite-wide: codemem trust records go to a throwaway state dir, never the user's.

codemem keeps one nonce per index directory under ``$XDG_STATE_HOME/codemem/trust``
(M15 §6.8 re-run 2). Tests build hundreds of indexes in tmp dirs; set the variable
once, before any test or subprocess runs, so none of them lands in ~/.local/state.
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile


def pytest_configure(config) -> None:
    state = tempfile.mkdtemp(prefix="codemem-test-state-")
    os.environ["XDG_STATE_HOME"] = state
    atexit.register(shutil.rmtree, state, True)

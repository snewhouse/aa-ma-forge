"""
AA-MA integration glue for codemem's aa_ma_context() MCP tool.

Single source of truth for AA-MA coupling (per Task 1.0 AF-14). When
aa-ma-forge is available on PYTHONPATH, this module activates the
aa_ma_context tool. When absent, the tool returns a structured no-op
response: AA-MA integration unavailable; install aa-ma-forge.

Implementation filled during M3 Step 3.7. Placeholder only.
"""

from typing import TYPE_CHECKING

try:
    # aa-ma-forge imports guarded so standalone pip install codemem-mcp
    # works without the parent framework.
    from aa_ma import __version__ as _aa_ma_version  # noqa: F401
    AA_MA_AVAILABLE = True
except ImportError:
    AA_MA_AVAILABLE = False


def aa_ma_context_available() -> bool:
    """Return True if aa-ma-forge is importable from current Python."""
    return AA_MA_AVAILABLE


if TYPE_CHECKING:
    pass

"""Phase markers for /aa-ma-plan workflow observability.

See docs/spec/plan-marker-grammar.md for the canonical grammar contract.
"""

from aa_ma.plan_markers.parser import Marker, parse_log

__all__ = ["Marker", "parse_log"]

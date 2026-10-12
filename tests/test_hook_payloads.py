"""Guards for the captured hook payloads in tests/fixtures/hook-payloads (M7.5).

The repo is public: a recapture must not commit a username, a home path or a
real session id, and every registered hook event must keep its fixture.
"""

import json
import re
from pathlib import Path

import pytest

from aa_ma.logsetup import mask_secrets

ROOT = Path(__file__).resolve().parents[1]
PAYLOADS = ROOT / "tests" / "fixtures" / "hook-payloads"
FIXTURES = sorted(PAYLOADS.glob("*.json"))
PLACEHOLDER_UUID = re.compile(r"00000000-0000-4000-8000-\d{12}")
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def _registered() -> set[str]:
    """Fixture names for the AA_MA_HOOKS table: Event, or Event-<first matcher>."""
    lib = (ROOT / "scripts" / "lib" / "aa-ma-install-lib.sh").read_text()
    table = lib.split("AA_MA_HOOKS=(", 1)[1].split("\n)", 1)[0]
    names = set()
    for row in re.findall(r'"([^"]+)"', table):
        event, matcher = row.split("|")[:2]
        names.add(f"{event}-{matcher}" if matcher else event)
    return names


def test_every_registered_event_has_a_captured_fixture() -> None:
    assert _registered() <= {p.stem for p in FIXTURES}


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_fixture_is_scrubbed(path: Path) -> None:
    text = path.read_text()
    data = json.loads(text)
    assert data["hook_event_name"] == path.stem.split("-")[0]
    assert set(re.findall(r"/home/[^/\"]+", text)) <= {"/home/capture"}
    assert re.findall(r"/tmp/claude-\d", text) == []
    assert all(PLACEHOLDER_UUID.fullmatch(u) for u in UUID.findall(text))
    assert all(t.startswith("toolu_0000") for t in re.findall(r"toolu_\w+", text))
    assert mask_secrets(text) == text

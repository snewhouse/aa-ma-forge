import pytest


@pytest.fixture(autouse=True)
def _no_real_mmdc(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test may reach a real mmdc: render_status is asserted only via fake binaries."""
    monkeypatch.setenv("MMDC_BIN", "/nonexistent/mmdc")

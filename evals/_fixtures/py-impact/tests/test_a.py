from a import load
from lib import MAX_ROWS


def test_load_caps_rows() -> None:
    assert len(load(["x, 1"] * (MAX_ROWS + 5))) == MAX_ROWS

import lib


def summary(lines: list[str]) -> str:
    rows = [lib.parse_record(line) for line in lines]
    return f"{len(rows)} people"

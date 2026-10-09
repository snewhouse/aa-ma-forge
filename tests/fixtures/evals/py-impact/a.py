from lib import MAX_ROWS, parse_record


def load(lines: list[str]) -> list[dict]:
    return [parse_record(line) for line in lines[:MAX_ROWS]]

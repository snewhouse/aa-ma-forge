from lib import parse_record


def oldest(lines: list[str]) -> dict:
    return max((parse_record(line) for line in lines), key=lambda r: r["age"])

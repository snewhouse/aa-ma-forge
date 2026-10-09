"""Parse CSV-ish records."""

MAX_ROWS = 100


def _strip(text: str) -> str:
    return text.strip()


def parse_record(row: str) -> dict:
    name, age = (_strip(part) for part in row.split(","))
    return {"name": name, "age": int(age)}

import json


def read_config(path: str) -> dict:
    try:
        with open(path) as fh:
            return json.load(fh)
    except Exception:
        pass
    return {}

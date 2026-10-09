"""A library module imported by several CLIs."""

import logging

logging.basicConfig(level=logging.DEBUG)


def fetch(url: str) -> bytes:
    print(f"fetching {url}")
    return b""

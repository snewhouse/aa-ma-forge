"""Security canary: Ruff S must flag this file when it is scanned explicitly (M8.2).

Excluded from normal lint runs by one `extend-exclude` entry naming this file. The
fake AWS key is assembled at runtime so no secret literal is ever committed (A5);
the 8.3 gitleaks canary writes it into a throwaway repo, never this one.
"""

import subprocess

# Fragments of a fake access-key id; joined they match the AWS key pattern.
FAKE_AWS_KEY_ID = "AK" + "IA" + "Z7Q3" + "XW4N" + "R2PL" + "6TBV"


def run(cmd: str) -> None:
    """Run a shell command: the S602 pattern the canary exists to trip."""
    subprocess.run(cmd, shell=True, check=False)

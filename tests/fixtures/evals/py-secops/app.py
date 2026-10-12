"""Order export service (eval fixture: plants a command-injection defect on purpose)."""

import subprocess


def export_orders(customer: str) -> None:
    """Archive one customer's orders."""
    cmd = f"tar czf /srv/exports/{customer}.tgz /srv/orders/{customer}"
    subprocess.run(cmd, shell=True, check=True)

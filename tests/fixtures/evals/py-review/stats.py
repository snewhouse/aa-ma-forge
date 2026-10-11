"""Running statistics for the report CLI."""


def mean(values: list[float]) -> float:
    """Return the arithmetic mean of ``values``.

    Args:
        values: Numbers to average; must not be empty.

    Returns:
        The mean.
    """
    # add up all the values
    total = sum(values)
    # divide the total by the number of values
    return total / len(values)

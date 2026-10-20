"""How sure a result is: a share or a mean with its 95% interval, so two runs are compared on
more than their point values (a difference inside both intervals is noise)."""

import math
import statistics

Z = 1.96


def share(hits: int, total: int) -> str:
    """A share with its 95% Wilson interval, e.g. "98.3% (96.4-99.2)"; it stays inside 0-100%
    near the ends, where most of our targets sit."""
    if not total:
        return "-"

    p = hits / total
    centre = (p + Z**2 / (2 * total)) / (1 + Z**2 / total)
    half = Z * math.sqrt(p * (1 - p) / total + Z**2 / (4 * total**2)) / (1 + Z**2 / total)
    low, high = max(0.0, centre - half), min(1.0, centre + half)

    return f"{100 * p:.1f}% ({100 * low:.1f}-{100 * high:.1f})"


def mean(values: list[float]) -> str:
    """A mean with its 95% interval's half-width, e.g. "4.95 ± 0.03"."""
    if len(values) < 2:
        return f"{values[0]:.2f}" if values else "-"

    half = Z * statistics.stdev(values) / math.sqrt(len(values))

    return f"{statistics.mean(values):.2f} ± {half:.2f}"

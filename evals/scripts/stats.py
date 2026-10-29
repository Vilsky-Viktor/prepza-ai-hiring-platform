"""How sure a result is: a share or a mean with its 95% interval, so two runs are compared on
more than their point values (a difference inside both intervals is noise)."""

import math
import statistics

Z = 1.96


def wilson(hits: int, total: int) -> tuple[float, float, float]:
    """A share and its 95% Wilson interval (low, high), as fractions; it stays inside 0-1 near
    the ends, where most of our targets sit."""
    p = hits / total
    centre = (p + Z**2 / (2 * total)) / (1 + Z**2 / total)
    half = Z * math.sqrt(p * (1 - p) / total + Z**2 / (4 * total**2)) / (1 + Z**2 / total)

    return p, max(0.0, centre - half), min(1.0, centre + half)


def share(hits: int, total: int) -> str:
    """A share with its 95% Wilson interval, e.g. "98.3% (96.4-99.2)"."""
    if not total:
        return "-"

    p, low, high = wilson(hits, total)

    return f"{100 * p:.1f}% ({100 * low:.1f}-{100 * high:.1f})"


def mean_interval(values: list[float]) -> tuple[float, float, float]:
    """A mean and its 95% interval (low, high), ±1.96 standard errors; at least two values."""
    centre = statistics.mean(values)
    half = Z * statistics.stdev(values) / math.sqrt(len(values))

    return centre, centre - half, centre + half


def mean(values: list[float], digits: int = 2) -> str:
    """A mean with its 95% interval's half-width, e.g. "4.95 ± 0.03"."""
    if len(values) < 2:
        return f"{values[0]:.{digits}f}" if values else "-"

    centre, low, _ = mean_interval(values)

    return f"{centre:.{digits}f} ± {centre - low:.{digits}f}"

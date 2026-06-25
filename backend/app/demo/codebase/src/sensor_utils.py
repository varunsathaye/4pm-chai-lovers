"""Shared low-level sensor/signal helpers used across ECU modules.

These are imported by higher-level controllers (e.g. the BMS), so a change
here can break tests that never reference this file directly -- the classic
case where text/AST-based test selection fails but coverage-based selection
succeeds.
"""


def clamp(value, lo, hi):
    """Constrain a value to the inclusive [lo, hi] range."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def moving_average(samples, window):
    """Mean of the most recent `window` samples (sensor smoothing)."""
    if not samples or window <= 0:
        return 0.0
    recent = samples[-window:]
    return round(sum(recent) / len(recent), 4)

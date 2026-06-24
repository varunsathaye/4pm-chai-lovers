"""Shared pytest fixtures for the ECU host-based test suite.

The ``bench`` fixture models the fixed per-test cost of running a test at a
given automotive test level:

    UNIT - pure host logic, almost free
    SIL  - Software-in-the-Loop, model has to settle
    HIL  - Hardware-in-the-Loop, firmware is flashed to a bench rig (slow)

On a real rig HIL cases take seconds-to-minutes each. Here the latency is
scaled down so the full suite still finishes in a few seconds, while
preserving a realistic *relative* cost between levels. This is what makes
"time saved" a real measurement (skipping expensive HIL tests saves far more
than skipping UNIT tests) instead of a hard-coded number.
"""
import time

import pytest

# Per-level simulated bench latency (seconds).
LEVEL_LATENCY = {
    "UNIT": 0.05,
    "SIL": 0.15,
    "HIL": 0.40,
}
DEFAULT_LATENCY = 0.10


@pytest.fixture(autouse=True)
def bench(request):
    """Simulate per-test bench setup/settle latency based on the test level."""
    marker = request.node.get_closest_marker("level")
    level = marker.args[0] if marker and marker.args else "UNIT"
    time.sleep(LEVEL_LATENCY.get(level, DEFAULT_LATENCY))
    yield

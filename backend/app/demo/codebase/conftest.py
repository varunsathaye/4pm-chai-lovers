"""Shared pytest fixtures for the ECU host-based test suite.

The ``hil_bench`` fixture models the fixed per-test cost of a
Hardware-in-the-Loop (HIL) bench: writing the signal set onto the
simulated ECU and letting the plant model settle before assertions.

On a real HIL rig this is seconds-to-minutes per case. Here it is scaled
down so the full suite still finishes in a few seconds, while preserving a
realistic *relative* cost between a full regression run and a
Test-Impact-Analysis run. This is what makes the "time saved" metric a
real measurement rather than a hard-coded number.
"""
import time

import pytest

HIL_SETTLE_SECONDS = 0.18


@pytest.fixture(autouse=True)
def hil_bench():
    """Simulate per-test HIL bench setup/settle latency."""
    time.sleep(HIL_SETTLE_SECONDS)
    yield

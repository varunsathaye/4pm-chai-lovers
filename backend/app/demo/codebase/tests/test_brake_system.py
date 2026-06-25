import pytest

from src.brake_system import abs_modulation, is_wheel_locked, wheel_slip_ratio

# ABS is safety-critical -> validated on the HIL bench.
pytestmark = pytest.mark.level("HIL")


@pytest.mark.req("SR-BRK-001")
@pytest.mark.asil("D")
def test_slip_ratio_rolling():
    assert wheel_slip_ratio(20, 20) == 0.0


@pytest.mark.req("SR-BRK-001")
@pytest.mark.asil("D")
def test_slip_ratio_locked():
    assert wheel_slip_ratio(20, 5) == 0.75


@pytest.mark.req("SR-BRK-001")
@pytest.mark.asil("D")
def test_is_wheel_locked():
    assert is_wheel_locked(20, 5) is True
    assert is_wheel_locked(20, 19) is False


@pytest.mark.req("SR-BRK-002")
@pytest.mark.asil("D")
def test_abs_releases_pressure_on_lock():
    assert abs_modulation(20, 5, 160) == 80.0


@pytest.mark.req("SR-BRK-002")
@pytest.mark.asil("D")
def test_abs_holds_pressure_when_gripping():
    assert abs_modulation(20, 19, 160) == 160.0

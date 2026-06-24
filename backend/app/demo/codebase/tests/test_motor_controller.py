import pytest

from src.motor_controller import (
    clamp_torque_request,
    regen_braking_torque,
    wheel_speed_to_rpm,
)

# Motor torque path is safety-critical -> validated on the HIL bench.
pytestmark = pytest.mark.level("HIL")


@pytest.mark.req("SR-MOT-001")
@pytest.mark.asil("D")
def test_clamp_torque_upper():
    assert clamp_torque_request(500) == 320.0


@pytest.mark.req("SR-MOT-001")
@pytest.mark.asil("D")
def test_clamp_torque_lower():
    assert clamp_torque_request(-500) == -320.0


@pytest.mark.req("SR-MOT-001")
@pytest.mark.asil("D")
def test_clamp_torque_passthrough():
    assert clamp_torque_request(120) == 120


@pytest.mark.req("SR-MOT-002")
@pytest.mark.asil("B")
def test_wheel_speed_to_rpm_standstill():
    assert wheel_speed_to_rpm(0) == 0.0


@pytest.mark.req("SR-MOT-003")
@pytest.mark.asil("C")
def test_regen_zero_at_standstill():
    assert regen_braking_torque(0.5, 100) == 0.0


@pytest.mark.req("SR-MOT-003")
@pytest.mark.asil("C")
def test_regen_scales_with_pedal():
    assert regen_braking_torque(20, 50) > 0

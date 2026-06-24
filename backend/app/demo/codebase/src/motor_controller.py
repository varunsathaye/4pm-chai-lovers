"""Traction motor torque and speed control logic."""

import math

MAX_TORQUE_NM = 320.0
MAX_RPM = 16000
WHEEL_RADIUS_M = 0.33
GEAR_RATIO = 9.0


def clamp_torque_request(requested_nm):
    """Limit a torque request to the motor's safe envelope."""
    if requested_nm < -MAX_TORQUE_NM:
        return -MAX_TORQUE_NM
    if requested_nm > MAX_TORQUE_NM:
        return MAX_TORQUE_NM
    return requested_nm


def wheel_speed_to_rpm(vehicle_speed_mps):
    """Convert vehicle speed (m/s) to motor RPM through the gearbox."""
    wheel_rps = vehicle_speed_mps / (2 * math.pi * WHEEL_RADIUS_M)
    return round(wheel_rps * 60 * GEAR_RATIO, 1)


def regen_braking_torque(vehicle_speed_mps, brake_pedal_pct):
    """Compute available regenerative braking torque (Nm)."""
    if vehicle_speed_mps < 1.0:
        return 0.0  # no regen at standstill
    torque = MAX_TORQUE_NM * (brake_pedal_pct / 100.0) * 0.6
    return round(min(torque, MAX_TORQUE_NM), 2)

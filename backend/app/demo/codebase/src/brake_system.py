"""Anti-lock Braking System (ABS) control logic."""

SLIP_THRESHOLD = 0.2
MAX_BRAKE_PRESSURE_BAR = 180.0


def wheel_slip_ratio(vehicle_speed_mps, wheel_speed_mps):
    """Slip ratio of a wheel (0 = free rolling, 1 = fully locked)."""
    if vehicle_speed_mps <= 0:
        return 0.0
    return round((vehicle_speed_mps - wheel_speed_mps) / vehicle_speed_mps, 3)


def is_wheel_locked(vehicle_speed_mps, wheel_speed_mps):
    """A wheel is locking when slip exceeds the ABS threshold."""
    return wheel_slip_ratio(vehicle_speed_mps, wheel_speed_mps) > SLIP_THRESHOLD


def abs_modulation(vehicle_speed_mps, wheel_speed_mps, driver_pressure_bar):
    """Release brake pressure when a wheel is about to lock."""
    pressure = min(driver_pressure_bar, MAX_BRAKE_PRESSURE_BAR)
    if is_wheel_locked(vehicle_speed_mps, wheel_speed_mps):
        return round(pressure * 0.5, 2)  # bleed off to regain traction
    return round(pressure, 2)

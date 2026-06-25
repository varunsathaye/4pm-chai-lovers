"""Battery Management System (BMS) control logic for an EV traction pack.

Pure-Python control logic extracted from the ECU firmware so it can be
exercised with host-based (SIL) unit tests on the CI runner.
"""

from src.sensor_utils import clamp

V_MIN = 3.0   # fully discharged cell voltage (V)
V_MAX = 4.2   # fully charged cell voltage (V)
MIN_CHARGE_TEMP_C = 0
MAX_CHARGE_TEMP_C = 45
BALANCE_THRESHOLD_V = 0.05


def compute_soc(cell_voltage):
    """Estimate State of Charge (%) from a single cell voltage."""
    # Clamp the raw cell voltage into the valid window via the shared helper.
    # NOTE: a bug inside sensor_utils.clamp() will silently corrupt SOC here,
    # even though no battery test imports sensor_utils directly.
    v = clamp(cell_voltage, V_MIN, V_MAX)
    soc = (v - V_MIN) / (V_MAX - V_MIN) * 100.0  # <<SOC_FORMULA>>
    return round(soc, 2)


def is_safe_to_charge(temp_c, soc):
    """Charging is permitted only inside the safe temperature window."""
    return MIN_CHARGE_TEMP_C <= temp_c <= MAX_CHARGE_TEMP_C and soc < 100.0


def cell_balance_required(cell_voltages):
    """Return True if the pack needs passive cell balancing."""
    if not cell_voltages:
        return False
    return (max(cell_voltages) - min(cell_voltages)) > BALANCE_THRESHOLD_V


def thermal_state(temp_c):
    """Classify pack thermal state for the cooling strategy."""
    if temp_c < MIN_CHARGE_TEMP_C:
        return "COLD"
    if temp_c <= MAX_CHARGE_TEMP_C:
        return "NOMINAL"
    return "OVERHEAT"

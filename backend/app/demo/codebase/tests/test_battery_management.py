from src.battery_management import (
    cell_balance_required,
    compute_soc,
    is_safe_to_charge,
    thermal_state,
)


def test_compute_soc_midpoint():
    assert compute_soc(3.6) == 50.0


def test_compute_soc_clamps_low():
    assert compute_soc(2.5) == 0.0


def test_compute_soc_clamps_high():
    assert compute_soc(4.5) == 100.0


def test_is_safe_to_charge():
    assert is_safe_to_charge(25, 80) is True
    assert is_safe_to_charge(60, 80) is False


def test_cell_balance_required():
    assert cell_balance_required([3.90, 3.91, 4.00]) is True
    assert cell_balance_required([3.90, 3.91, 3.92]) is False


def test_thermal_state():
    assert thermal_state(-5) == "COLD"
    assert thermal_state(30) == "NOMINAL"
    assert thermal_state(60) == "OVERHEAT"

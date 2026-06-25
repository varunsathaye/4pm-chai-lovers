import pytest

from src.battery_management import (
    cell_balance_required,
    compute_soc,
    is_safe_to_charge,
    thermal_state,
)

# Battery logic is validated at Software-in-the-Loop level.
pytestmark = pytest.mark.level("SIL")


@pytest.mark.req("SR-BMS-001")
@pytest.mark.asil("C")
def test_compute_soc_midpoint():
    assert compute_soc(3.6) == 50.0


@pytest.mark.req("SR-BMS-001")
@pytest.mark.asil("C")
def test_compute_soc_clamps_low():
    assert compute_soc(2.5) == 0.0


@pytest.mark.req("SR-BMS-001")
@pytest.mark.asil("C")
def test_compute_soc_clamps_high():
    assert compute_soc(4.5) == 100.0


@pytest.mark.req("SR-BMS-002")
@pytest.mark.asil("C")
def test_is_safe_to_charge():
    assert is_safe_to_charge(25, 80) is True
    assert is_safe_to_charge(60, 80) is False


@pytest.mark.req("SR-BMS-003")
@pytest.mark.asil("B")
def test_cell_balance_required():
    assert cell_balance_required([3.90, 3.91, 4.00]) is True
    assert cell_balance_required([3.90, 3.91, 3.92]) is False


@pytest.mark.req("SR-BMS-004")
@pytest.mark.asil("C")
def test_thermal_state():
    assert thermal_state(-5) == "COLD"
    assert thermal_state(30) == "NOMINAL"
    assert thermal_state(60) == "OVERHEAT"

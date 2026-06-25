import pytest

from src.diagnostics import detect_dtc, is_valid_dtc, severity_for_code

# Diagnostics are pure host logic -> cheap UNIT level.
pytestmark = pytest.mark.level("UNIT")


@pytest.mark.req("SR-DIAG-001")
@pytest.mark.asil("B")
def test_valid_dtc():
    assert is_valid_dtc("P0A80") is True
    assert is_valid_dtc("X1234") is False
    assert is_valid_dtc("P0A8") is False


@pytest.mark.req("SR-DIAG-002")
@pytest.mark.asil("B")
def test_severity_lookup():
    assert severity_for_code("P0A80") == "HIGH"
    assert severity_for_code("Z9999") == "UNKNOWN"


@pytest.mark.req("SR-DIAG-002")
@pytest.mark.asil("B")
def test_detect_dtc_low_voltage():
    assert "P0AFA" in detect_dtc(3.0, True)


@pytest.mark.req("SR-DIAG-002")
@pytest.mark.asil("B")
def test_detect_dtc_comms_loss():
    assert "U0100" in detect_dtc(3.8, False)


@pytest.mark.req("SR-DIAG-002")
@pytest.mark.asil("B")
def test_detect_dtc_healthy():
    assert detect_dtc(3.8, True) == []

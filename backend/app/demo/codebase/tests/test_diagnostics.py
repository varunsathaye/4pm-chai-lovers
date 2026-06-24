from src.diagnostics import detect_dtc, is_valid_dtc, severity_for_code


def test_valid_dtc():
    assert is_valid_dtc("P0A80") is True
    assert is_valid_dtc("X1234") is False
    assert is_valid_dtc("P0A8") is False


def test_severity_lookup():
    assert severity_for_code("P0A80") == "HIGH"
    assert severity_for_code("Z9999") == "UNKNOWN"


def test_detect_dtc_low_voltage():
    assert "P0AFA" in detect_dtc(3.0, True)


def test_detect_dtc_comms_loss():
    assert "U0100" in detect_dtc(3.8, False)


def test_detect_dtc_healthy():
    assert detect_dtc(3.8, True) == []

"""On-board diagnostics: Diagnostic Trouble Code (DTC) handling."""

DTC_SEVERITY = {
    "P0A80": "HIGH",    # Replace hybrid battery pack
    "P0AFA": "HIGH",    # Battery voltage low
    "C0035": "MEDIUM",  # Left front wheel speed sensor
    "U0100": "HIGH",    # Lost communication with ECM/PCM
    "B1000": "LOW",     # ECU general
}

LOW_VOLTAGE_LIMIT = 3.2


def is_valid_dtc(code):
    """A valid DTC is one letter (P/C/B/U) followed by 4 hex digits."""
    if not code or len(code) != 5:
        return False
    if code[0] not in ("P", "C", "B", "U"):
        return False
    return all(c in "0123456789ABCDEF" for c in code[1:])


def severity_for_code(code):
    """Look up the severity class of a DTC."""
    return DTC_SEVERITY.get(code, "UNKNOWN")


def detect_dtc(voltage, comms_ok):
    """Return the list of active DTCs for the current signal snapshot."""
    codes = []
    if voltage < LOW_VOLTAGE_LIMIT:
        codes.append("P0AFA")
    if not comms_ok:
        codes.append("U0100")
    return codes

"""CAN bus signal encoding/decoding helpers (J1939-style)."""


def encode_signal(value, scale=1.0, offset=0.0):
    """Encode a physical value into a raw CAN integer."""
    return int(round((value - offset) / scale))


def decode_signal(raw, scale=1.0, offset=0.0):
    """Decode a raw CAN integer back into a physical value."""
    return round(raw * scale + offset, 4)


def checksum(data_bytes):
    """XOR checksum used to validate a CAN frame payload."""
    cs = 0
    for b in data_bytes:
        cs ^= b & 0xFF
    return cs & 0xFF


def build_can_frame(can_id, data_bytes):
    """Assemble a CAN frame dict with an appended checksum byte."""
    if len(data_bytes) > 7:
        raise ValueError("CAN payload exceeds 7 data bytes (8th is checksum)")
    return {
        "id": can_id & 0x7FF,
        "dlc": len(data_bytes) + 1,
        "data": list(data_bytes) + [checksum(data_bytes)],
    }

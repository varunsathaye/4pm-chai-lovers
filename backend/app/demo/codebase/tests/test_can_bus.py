import pytest

from src.can_bus import build_can_frame, checksum, decode_signal, encode_signal

# CAN helpers are pure host logic -> cheap UNIT level.
pytestmark = pytest.mark.level("UNIT")


@pytest.mark.req("SR-CAN-001")
@pytest.mark.asil("B")
def test_encode_decode_roundtrip():
    raw = encode_signal(80.0, scale=0.5, offset=-40)
    assert decode_signal(raw, scale=0.5, offset=-40) == 80.0


@pytest.mark.req("SR-CAN-002")
@pytest.mark.asil("B")
def test_checksum_xor():
    assert checksum([0x01, 0x02, 0x03]) == 0x00


@pytest.mark.req("SR-CAN-002")
@pytest.mark.asil("B")
def test_build_can_frame_appends_checksum():
    frame = build_can_frame(0x123, [0x10, 0x20])
    assert frame["dlc"] == 3
    assert frame["data"][-1] == checksum([0x10, 0x20])


@pytest.mark.req("SR-CAN-002")
@pytest.mark.asil("B")
def test_build_can_frame_rejects_oversized():
    with pytest.raises(ValueError):
        build_can_frame(0x123, list(range(8)))

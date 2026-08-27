import pytest

from cadparts import create, derive, hex_bolt_metric, hex_nut_metric, plain_washer_metric
from cadparts.errors import InvalidParameterError


def test_m8_hex_bolt_nominal_envelope():
    bolt = hex_bolt_metric("M8", 30)
    size = bolt.bounding_box().size
    assert size.Z == pytest.approx(35.3)
    assert min(size.X, size.Y) == pytest.approx(13)
    assert len(bolt.solids()) == 1
    assert bolt.label.startswith("M8x30")


def test_numeric_size_and_alias_are_model_friendly():
    bolt = create("hex_bolt", size=10, length=40)
    assert bolt.bounding_box().size.Z == pytest.approx(46.4)
    assert derive("hex_bolt", size=10, length=40)["coarse_pitch"] == 1.5


def test_m8_nut_envelope_and_bore_volume():
    nut = hex_nut_metric("8")
    size = nut.bounding_box().size
    assert size.Z == pytest.approx(6.8)
    assert min(size.X, size.Y) == pytest.approx(13)
    assert len(nut.solids()) == 1
    assert nut.volume > 0


def test_m8_washer_dimensions():
    washer = plain_washer_metric("m8")
    size = washer.bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((16, 16, 1.6))
    expected = 3.141592653589793 * (16**2 - 8.4**2) / 4 * 1.6
    assert washer.volume == pytest.approx(expected)


def test_fastener_validation_is_short_and_deterministic():
    with pytest.raises(InvalidParameterError, match="unsupported metric fastener size"):
        plain_washer_metric("M7")
    with pytest.raises(InvalidParameterError, match="length must be > 0"):
        hex_bolt_metric("M8", 0)

import pytest
from build123d import export_step

from cadparts import create


SAMPLES = {
    "bearing.deep_groove": {"code": "6204"},
    "fastener.hex_bolt_metric": {"size": "M8", "length": 30},
    "fastener.hex_nut_metric": {"size": "M8"},
    "fastener.plain_washer_metric": {"size": "M8"},
    "gear.spur": {"module": 1, "teeth": 20, "bore": 5, "width": 6},
    "gear.bevel_straight": {
        "module": 1,
        "teeth": 20,
        "mate_teeth": 20,
        "bore": 4,
        "face_width": 4,
    },
    "key.parallel": {"width": 8, "height": 7, "length": 32},
    "profile.equal_angle": {"leg": 50, "thickness": 5, "length": 100},
    "profile.round_rod": {"diameter": 20, "length": 100},
    "profile.round_tube": {"outer_diameter": 48.3, "wall": 3.2, "length": 100},
    "profile.square_tube": {"side": 40, "wall": 3, "length": 100},
}


@pytest.mark.parametrize("family", sorted(SAMPLES))
def test_every_registered_family_exports_nonempty_step(family, tmp_path):
    shape = create(family, **SAMPLES[family])
    output = tmp_path / f"{family.replace('.', '-')}.step"
    assert export_step(shape, output) is not None
    assert output.stat().st_size > 500

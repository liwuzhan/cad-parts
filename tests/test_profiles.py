import math

import pytest
from build123d import export_step

from cadparts import derive
from cadparts.errors import InvalidParameterError
from cadparts.profiles import square_tube


def test_square_tube_nominal_geometry(tmp_path):
    shape = square_tube(side=40, wall=3, length=100)
    size = shape.bounding_box().size
    assert (size.X, size.Y, size.Z) == pytest.approx((40, 40, 100), abs=1e-7)
    assert shape.volume == pytest.approx((40**2 - 34**2) * 100, rel=1e-10)
    assert len(shape.solids()) == 1
    assert shape.label == "SHS 40x40x3 L=100"

    output = tmp_path / "square_tube.step"
    assert export_step(shape, output) is not None
    assert output.stat().st_size > 1_000


@pytest.mark.parametrize(
    "values",
    [
        {"side": 0, "wall": 1, "length": 10},
        {"side": 40, "wall": 0, "length": 10},
        {"side": 40, "wall": 20, "length": 10},
        {"side": 40, "wall": 2, "length": 0},
        {"side": 40, "wall": 2, "length": 10, "corner_radius": -1},
    ],
)
def test_square_tube_rejects_impossible_dimensions(values):
    with pytest.raises(InvalidParameterError):
        square_tube(**values)


def test_square_tube_volume_scales_linearly_with_length():
    short = square_tube(30, 2, 100)
    long = square_tube(30, 2, 250)
    assert math.isclose(long.volume / short.volume, 2.5, rel_tol=1e-10)


def test_square_tube_rounded_corner_offset():
    shape = square_tube(40, 3, 100, corner_radius=6)
    size = shape.bounding_box().size
    expected_area = (40**2 - (4 - math.pi) * 6**2) - (34**2 - (4 - math.pi) * 3**2)
    assert (size.X, size.Y, size.Z) == pytest.approx((40, 40, 100), abs=1e-7)
    assert shape.volume == pytest.approx(expected_area * 100, rel=1e-8)
    assert len(shape.solids()) == 1


def test_square_tube_derived_dimensions_are_geometry_free():
    dimensions = derive("shs", side=40, wall=3, length=100)
    assert dimensions["inside_side"] == 34
    assert dimensions["sharp_corner_volume"] == pytest.approx((40**2 - 34**2) * 100)

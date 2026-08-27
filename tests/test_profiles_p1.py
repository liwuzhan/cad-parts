from math import pi

import pytest

from cadparts import derive, equal_angle, round_rod, round_tube


def test_round_tube_exact_envelope_and_volume():
    tube = round_tube(48.3, 3.2, 100)
    dimensions = derive("chs", outer_diameter=48.3, wall=3.2, length=100)
    assert tuple(tube.bounding_box().size) == pytest.approx((48.3, 48.3, 100))
    assert tube.volume == pytest.approx(dimensions["volume"])
    assert len(tube.solids()) == 1


def test_round_rod_analytical_volume():
    rod = round_rod(20, 500)
    assert tuple(rod.bounding_box().size) == pytest.approx((20, 20, 500))
    assert rod.volume == pytest.approx(pi * 20**2 / 4 * 500)


def test_equal_angle_sharp_envelope():
    angle = equal_angle(50, 5, 200)
    assert tuple(angle.bounding_box().size) == pytest.approx((50, 50, 200))
    assert angle.volume == pytest.approx((2 * 50 * 5 - 5**2) * 200)
    assert len(angle.solids()) == 1

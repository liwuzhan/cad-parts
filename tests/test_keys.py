from math import pi

import pytest

from cadparts import derive, parallel_key


@pytest.mark.parametrize("end_type", ["A", "B", "C"])
def test_parallel_key_end_types_have_exact_bbox_and_one_solid(end_type):
    key = parallel_key(8, 7, 32, end_type=end_type)
    assert tuple(key.bounding_box().size) == pytest.approx((32, 8, 7))
    assert len(key.solids()) == 1


def test_type_a_key_volume_matches_capsule_formula():
    key = parallel_key(8, 7, 32, end_type="A")
    expected = (8 * (32 - 8) + pi * 8**2 / 4) * 7
    assert key.volume == pytest.approx(expected)
    assert derive("parallel_key", width=8, height=7, length=32)["volume"] == pytest.approx(expected)


def test_minimum_length_end_forms_do_not_create_zero_length_boxes():
    type_a = parallel_key(8, 7, 8, end_type="A")
    type_c = parallel_key(8, 7, 4, end_type="C")
    assert type_a.volume == pytest.approx(pi * 8**2 / 4 * 7)
    assert type_c.volume == pytest.approx(pi * 8**2 / 8 * 7)

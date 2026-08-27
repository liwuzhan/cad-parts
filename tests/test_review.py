import json

import pytest

from cadparts.review import review_part


@pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
def test_multimodal_review_emits_step_png_spec_and_report(tmp_path):
    report = review_part(
        "6204",
        selections={"closure": "2RS"},
        output_dir=tmp_path,
        views=("iso",),
    )
    assert report["valid"] is True
    assert report["interface_count"] == 4
    assert (tmp_path / "bearing-deep_groove-6204.step").stat().st_size > 500
    assert (tmp_path / "bearing-deep_groove-6204.iso.png").stat().st_size > 5_000
    instance = json.loads((tmp_path / "bearing-deep_groove-6204.instance.json").read_text())
    assert instance["purchase"]["order_code"] == "6204-2RS"
    persisted_report = json.loads((tmp_path / "review.json").read_text())
    assert persisted_report["schema"] == "cadparts.review/v1"

from cadparts import instance_spec


def test_instance_spec_resolves_alias_and_pins_library_and_standards():
    spec = instance_spec("hex_bolt", size="M8", length=30)
    assert spec["schema"] == "cadparts.instance/v2"
    assert spec["library"] == "cad-parts"
    assert spec["library_version"] == "0.1.0"
    assert spec["family"] == "fastener.hex_bolt_metric"
    assert spec["catalog_id"] == "fastener.hex_bolt_metric"
    assert spec["parameters"] == {"size": "M8", "length": 30}
    assert spec["derived"]["designation"] == "M8x30"
    assert {item["designation"] for item in spec["standards"]} == {
        "GB/T 5783-2025",
        "ISO 4017:2022",
    }
    assert {item["id"] for item in spec["interfaces"]} == {"thread_axis", "head_bearing_face"}
    assert spec["purchase"]["query"] == "M8x30 hex-head screw"


def test_instance_spec_for_generic_family_keeps_empty_standard_list():
    spec = instance_spec("rod", diameter=20, length=100)
    assert spec["family"] == "profile.round_rod"
    assert spec["standards"] == []
    assert spec["derived"]["volume"] > 0
    assert [item["id"] for item in spec["interfaces"]] == ["axis", "end_min", "end_max"]

"""占位测试：保证测试基建可用，PL-M0 后被真实族测试取代。"""


def test_registry_exists():
    from cadparts import REGISTRY

    assert isinstance(REGISTRY, dict)

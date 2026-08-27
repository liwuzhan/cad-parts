"""cad-parts: 参数化标准件库（占位骨架）。

每个零件族一个模块，验证基准在 tests/。无测试的族不合入。
设计文档见仓库根 DESIGN.md。
"""

__version__ = "0.0.1-placeholder"

# 族注册表：family 名 -> (模块, 工厂函数, 一句话描述)
# PL-M0 实现；首批 P0 四族见 DESIGN.md §5
REGISTRY: dict = {}

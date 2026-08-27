# cad-parts — 面向语言模型的装配占位零件目录

`cad-parts` 基于 [build123d](https://github.com/gumyr/build123d)，为 AI 辅助机械装配提供
标准件和外购件的轻量参数化代理。

它的目标不是替代制造图纸或受力分析，而是让模型能够低上下文地完成：

- 根据型号、自然语言和尺寸约束寻找零件；
- 为外购件预留可信的空间包络；
- 读取安装面、孔、轴和定位面的命名接口；
- 将主要上下文留给装配体中的非标件；
- 输出可复现 STEP、实例元数据、BOM 规格和采购搜索方向。

姊妹项目 [cad-tool](https://github.com/liwuzhan/cad-tool) 提供 AI 原生 CAD 工程包、版本管理、
验证和插件接入。本库也可以被普通 build123d 程序独立使用。

## 给模型的固定入口

模型应首先读取 [CATALOG.md](./CATALOG.md) 或调用 `cadparts search`，不要通过 `ls`、
遍历源码或猜测文件名发现零件。

```text
search → compare → describe → instantiate → 装配/BOM
```

目录源声明位于 `src/cadparts/data/catalog/`，紧凑机器索引是
`src/cadparts/data/catalog/index.json`。每个条目明确说明包络、接口、采购属性、几何精度和省略项。

## 当前内容

当前版本有 11 个 family 和 22 个具体轴承型号：

| family | 主要装配语义 |
|---|---|
| `bearing.deep_groove` | 62/63 系列 d/D/B、轴孔、外圈座和轴向端面 |
| `fastener.hex_bolt_metric` | 名义螺纹轴、头部包络和夹紧面 |
| `fastener.hex_nut_metric` | 名义螺纹孔和两侧夹紧面 |
| `fastener.plain_washer_metric` | 内径、外径、厚度和两侧承压面 |
| `gear.spur` | 轴孔、旋转轴和分度圆参考 |
| `gear.bevel_straight` | 轴孔、旋转轴和节锥布局参考 |
| `key.parallel` | b×h×L 键连接占位 |
| `profile.square_tube` | 方管外形、内腔和切割端面 |
| `profile.round_tube` | 圆管外径、内径和切割端面 |
| `profile.round_rod` | 圆棒直径、轴线和切割端面 |
| `profile.equal_angle` | 等边角钢包络和切割端面 |

标准和尺寸来源见 [docs/STANDARDS.md](./docs/STANDARDS.md)，设计与扩展路线见
[DESIGN.md](./DESIGN.md)。

## 安装

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev,review]'
```

只生成几何、不需要 PNG 审查时可以省略 `review` extra。

## 搜索、比较和生成

```bash
cadparts search "防水防尘 20mm内径轴承"
cadparts search "轴承" --constraints '{"bore":20,"outside_diameter":{"max":50}}'
cadparts compare 6204 6304
cadparts describe 6204
cadparts instantiate 6204 \
  --selection '{"closure":"2RS","clearance":"C3"}' \
  --output 6204-2RS-C3.step
```

Python API：

```python
from cadparts import instantiate, search

candidates = search(
    "防水防尘轴承",
    constraints={"bore": 20, "outside_diameter": {"max": 50}},
)

bearing = instantiate(
    candidates[0]["id"],
    selections={"closure": "2RS", "clearance": "C3"},
)

shape = bearing.shape
interfaces = bearing.interfaces
order_code = bearing.spec["purchase"]["order_code"]
```

闭式类型和游隙改变采购型号，但通常不改变轴承占位几何。这个区分由 `selection` 保存，
不会强行传给几何生成器。

## 实例契约与接口

每次实例化返回 `cadparts.instance/v2`：

- family、具体 `catalog_id` 和库版本；
- 几何参数与采购 `selection`；
- 派生尺寸和实际 B-rep 包络；
- 带原点、轴向和直径的命名接口；
- 采购型号/查询文本；
- 当前几何精度与用途声明。

例如 6204 会暴露 `shaft_bore`、`housing_seat`、`axial_face_min`、
`axial_face_max`。装配模型应直接使用这些接口，而不是观察 STEP 后重新猜测。

## 多模态审查

```bash
cadparts validate-catalog --build-samples
cadparts review 6204 \
  --selection '{"closure":"2RS"}' \
  --output-dir build/review-6204
```

审查目录包含：

- STEP 代理模型；
- 完整实例 JSON；
- 轴测、正、右、俯视 PNG；
- 红色命名接口轴；
- `review.json` 审查问题与产物路径。

GitHub Actions 会验证目录索引、全部代表样件和测试，并上传全目录的多模态审查包。

## 精度边界

必须准确的是外形包络、安装孔/面、轴孔、输入输出轴、接口轴线和必要的采购规格。
内部机构、螺纹螺旋、轴承滚道、非接口圆角、材料、公差、强度和寿命可以明确省略。

直齿伞齿轮当前是装配布局模型，不是生产齿面。任何代理实体都不构成材料、工艺、
公差、额定载荷或标准符合性认证。

## 贡献

新增 family 必须有模型自声明、代表样件、包络/接口测试和 STEP/PNG 审查。
详细要求见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可

[MIT](./LICENSE)

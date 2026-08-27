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

当前索引有 **34 个 family、288 个可直接调用的型号/规格条目，共 322 个发现条目**：

| 类别 | 已实现内容 |
|---|---|
| 轴承与连接 | 深沟球轴承、UCP/UCF/UCFL 带座轴承、柔性联轴器、平键 |
| 电机与减速机 | 方形步进、方形伺服、IEC 电机、NMRV/BKM 直角减速机、直线行星减速机 |
| 直线运动 | MGN/MGW/HGR/HGW 导轨、SFU 丝杠、BK/BF/EK/EF/FK/FF 支撑座、SBR/TBR 圆导轨、LM/LME/LMF/LMK 直线轴承 |
| 传动 | GT2/HTD 同步带轮、06B–12B 链轮、锥套、直齿轮、直齿伞齿轮 |
| 气动与执行 | ISO 6432、ISO 15552、ISO 21287/SDA 气缸，杆式/滑台式电动执行器 |
| 设备附件 | M8–M30 接近传感器、40–140 mm 轴流风扇、调平脚、工业脚轮 |
| 基础件 | 公制螺栓/螺母/垫圈、方管/圆管/圆棒/角钢 |

完整 family 地图和模型读取规则见 [CATALOG.md](./CATALOG.md)。

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
cadparts search "RV63 减速机"
cadparts search "120mm 散热风扇"
cadparts search "ISO15552 63缸径气缸"
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
- 明示的兼容性等级与需要逐项核对的接口字段；
- 运动扫掠、接线、进排气或工具操作所需的建议安全体积；
- 采购型号/查询文本；
- 当前几何精度与用途声明。

例如 6204 会暴露 `shaft_bore`、`housing_seat`、`axial_face_min`、
`axial_face_max`。装配模型应直接使用这些接口，而不是观察 STEP 后重新猜测。

`keepouts` 是给模型看的规划证据，不是自动报警器。模型可以根据具体装配、图片和必要的
临时代码决定是否采用或调整；库不会用粗糙规则替代模型对最终装配质量的判断。

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

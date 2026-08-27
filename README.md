# cad-parts — 语言模型友好的参数化标准件库

基于 [build123d](https://github.com/gumyr/build123d) 的机械标准件库。
每个零件族是一个带验证基准的参数化函数，为 AI 辅助 CAD 装配而生。

> 姊妹仓库：[cad-tool](https://github.com/liwuzhan/cad-tool) —— AI 原生 CAD CLI
> 与 DSH 插件（模型包 / 版本管理 / Checkpoint 验证）。本库可被任何
> build123d 用户独立使用，但设计上优先服务 LLM 装配工作流。

## 为什么需要它

对语言模型而言，**零件库是上下文压缩器**：

```python
# 手画渐开线齿轮：80~150 行易错代码，debug 数轮
# 调库：一行，注意力留给工程决策
gear = spur_gear(module=2, teeth=24, bore=20, width=12)
```

- 库封装"怎么画"，只暴露"选什么参数"；
- 每个族带 **pytest 数值基准**（尺寸查表断言、体积单调性、啮合关系）——
  **无测试的零件族不合入**；
- 装配引用携带规格语义（`6204` / `M8×30` / `40×40×3 方管`），BOM 与干涉豁免
  依赖零件身份而非匿名几何。

## 当前状态

首个可用版本已经实现。当前目录包含 11 个参数化 family：

| family | 关键参数 | 默认几何语义 |
|---|---|---|
| `gear.spur` | module, teeth, bore, width | 真实渐开线工作齿廓；齿根过渡简化 |
| `gear.bevel_straight` | module, teeth, mate_teeth, bore, face_width | 节锥宏观几何正确的装配/布局放样；不是加工齿面 |
| `bearing.deep_groove` | code, detail | 62/63 系列 d/D/B 精确包络；可选启发式滚珠预览 |
| `fastener.hex_bolt_metric` | size, length | 六角头 + 公称螺纹大径圆柱包络 |
| `fastener.hex_nut_metric` | size | 六角包络 + 圆柱螺纹包络孔 |
| `fastener.plain_washer_metric` | size | A 级/普通系列名义包络 |
| `profile.square_tube` | side, wall, length | 方形空心型钢，可选圆角 |
| `profile.round_tube` | outer_diameter, wall, length | 圆形空心型钢 |
| `profile.round_rod` | diameter, length | 通用圆棒包络 |
| `profile.equal_angle` | leg, thickness, length | 等边角钢锐角简化包络 |
| `key.parallel` | width, height, length, end_type | A/B/C 型普通平键 |

完整设计和后续路线见 [DESIGN.md](./DESIGN.md)，标准来源与版权边界见
[docs/STANDARDS.md](./docs/STANDARDS.md)。

## 安装与 Python 调用

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

```python
from cadparts import create, derive, list_families

catalog = list_families(category="gear")

# 不创建几何，先计算分度圆/基圆/齿顶圆/齿根圆等派生规格
dimensions = derive(
    "gear.spur",
    module=2,
    teeth=24,
    bore=10,
    width=12,
)

# 参数确认后再创建 build123d 实体
gear = create("gear.spur", module=2, teeth=24, bore=10, width=12)
bearing = create("bearing.deep_groove", code="6204")
bolt = create("fastener.hex_bolt_metric", size="M8", length=30)
```

## 面向模型的 JSON CLI

CLI 的正常结果与错误都使用紧凑 JSON，适合 Codex、DSH 或其他代理调用：

```bash
cadparts list --category gear
cadparts describe gear.spur
cadparts derive gear.spur \
  --params '{"module":2,"teeth":24,"bore":10,"width":12}'
cadparts spec gear.spur \
  --params '{"module":2,"teeth":24,"bore":10,"width":12}'
cadparts build gear.spur \
  --params '{"module":2,"teeth":24,"bore":10,"width":12}' \
  --output gear.step
```

推荐固定路由为：

```text
list → describe → derive → spec → build → 装配/验证
```

`spec` 不创建几何，返回 `cadparts.instance/v1` JSON：规范 family、库版本、输入参数、
派生尺寸和标准版本都固定在同一对象中，可直接写入装配 manifest 的 `std:` 依赖。

## 精度边界

- 标准引用固定到明确版本；库保存名义尺寸、公式和来源元数据，不分发标准全文。
- 输出是参数化理想实体，不代表材料、热处理、公差、强度、精度或制造符合性认证。
- 螺纹默认是轻量包络；轴承内部 `rings` 仅用于识别性预览。
- 直齿轮的渐开线工作齿廓可用于布局和啮合几何；齿根刀具包络、修形、侧隙与强度需另行设计。
- 直齿伞齿轮当前是布局模型，不能用于接触斑点、切齿数据或生产检验。

## 验证

```bash
pytest -q
```

测试覆盖参数契约、查表尺寸、解析体积、实体数、STEP 导出、齿轮中心距无体积穿插，
并对代表样件执行 STEP 重新解析与 PNG 人工复核。

## 许可

MIT

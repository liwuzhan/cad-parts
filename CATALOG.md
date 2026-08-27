# cad-parts 模型目录入口

> 本文件是语言模型发现零件的固定入口。不要通过 `ls`、遍历源码或猜测文件名寻找零件。

`cad-parts` 是面向装配体的标准件与外购件占位目录。几何用于选型、空间预留、接口设计、
装配定位和 BOM/采购描述；除非零件声明明确说明，否则不代表制造级细节、受力能力或合规认证。

## 推荐读取流程

有 CLI 时使用渐进式查询：

```bash
cadparts search "防水防尘 20mm内径轴承"
cadparts compare 6204 6304
cadparts describe 6204
cadparts instantiate 6204 \
  --selection '{"closure":"2RS","clearance":"C3"}' \
  --output 6204-2RS-C3.step
```

没有 CLI 时：

1. 读取 `src/cadparts/data/catalog/index.json` 的紧凑条目；
2. 根据候选的 `path` 只读取相应 family 声明；
3. 不要一次加载整个目录；
4. 找不到完全匹配时，报告最接近的候选与未满足约束，不得编造型号。

## 当前目录

| 类别 | family | 用途与精度边界 |
|---|---|---|
| 轴承 | `bearing.deep_groove` | 62/63 系列 d/D/B 精确占位；闭式与游隙作为采购属性 |
| 紧固件 | `fastener.hex_bolt_metric` | 六角头、名义螺纹包络与夹紧面 |
| 紧固件 | `fastener.hex_nut_metric` | 六角包络、名义螺纹孔与两端面 |
| 紧固件 | `fastener.plain_washer_metric` | 内径、外径与厚度占位 |
| 齿轮 | `gear.spur` | 直齿轮轴孔、分度圆和外形；不含强度与制造公差 |
| 齿轮 | `gear.bevel_straight` | 直齿伞齿轮布局模型；不是生产齿面 |
| 键 | `key.parallel` | b×h×L 与端部形式 |
| 型材 | `profile.square_tube` | 方管外形、内腔和切割端面 |
| 型材 | `profile.round_tube` | 圆管外径、内径和切割端面 |
| 型材 | `profile.round_rod` | 圆棒直径、长度和轴线 |
| 型材 | `profile.equal_angle` | 等边角钢锐角占位和切割端面 |

当前自动索引包含 11 个 family 和 22 个具体轴承型号。目录声明位于
`src/cadparts/data/catalog/<category>/`，`index.json` 由声明自动生成。

## 实例契约

`cadparts.instance/v2` 同时包含：

- `catalog_id`、family、库版本和生成参数；
- 不改变几何但影响采购的 `selection`；
- 派生尺寸与精确外形包络；
- 带原点和轴向的命名装配接口；
- 采购型号或搜索关键词；
- 几何精度声明与明确省略项。

模型应优先使用这些字段完成装配，不要从 STEP 反向猜测安装孔、轴线或定位面。

## 贡献审查

每个新增 family 必须有自声明、生成器、代表样件和接口测试。审查命令：

```bash
cadparts validate-catalog --build-samples
cadparts review <family-or-item> --output-dir review
```

`review` 生成 STEP、实例 JSON、标准视图 PNG、红色接口轴和机器可读报告，供多模态模型或人工审查。

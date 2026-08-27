# cad-parts 模型目录入口

> 本文件是语言模型发现零件的固定入口。不要通过 `ls`、遍历源码或猜测文件名寻找零件。

`cad-parts` 是面向装配体的标准件与外购件占位目录。几何用于选型、空间预留、接口设计、
装配定位和 BOM/采购描述；除非零件声明明确说明，否则不代表制造级细节、受力能力或合规认证。

## 推荐读取流程

有 CLI 时使用渐进式查询：

```bash
cadparts search "防水防尘 20mm内径轴承"
cadparts search "RV63 减速机"
cadparts search "MGN12 300mm 导轨"
cadparts search "120mm 散热风扇"
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

| 类别 | family | 模型可依赖的主要证据 |
|---|---|---|
| 轴承 | `bearing.deep_groove` | d/D/B、轴孔、外圈座、轴向端面；闭式/游隙为采购属性 |
| 轴承 | `bearing.unit.mounted` | UCP/UCF/UCFL 包络、座孔、底座/法兰孔和轴线 |
| 联轴器 | `coupling.flexible` | 两端轴孔、键/夹紧方式、轴向安装面和外形包络 |
| 电机 | `motor.stepper.square` | 42/56.4/60/85 方框、止口、孔阵列和输出轴 |
| 电机 | `motor.servo.square_flange` | 40–130 方形法兰类、止口、孔阵列、轴和接头安全体积 |
| 电机 | `motor.induction.iec` | IEC 63–132 机座、B3/B5/B14/B35 安装接口和输出轴 |
| 减速机 | `gearbox.right_angle.market` | NMRV/BKM 外形、输入接口、单轴/双轴/空心输出和安装孔 |
| 减速机 | `gearbox.planetary.inline` | 42–130 电机类输入法兰、同轴输出和机体包络 |
| 直线 | `linear.guide.rail` | MGN/MGW/HGR/HGW 导轨、滑块、孔列和完整运动扫掠 |
| 直线 | `linear.ball_screw` | SFU 丝杠、导程、螺母法兰、两端基准和螺母扫掠 |
| 直线 | `linear.screw_support` | BK/BF/EK/EF/FK/FF 轴孔、轴线和端面安装孔阵列 |
| 直线 | `linear.guide.supported_round` | SBR/TBR 支撑圆导轨、滑块和运动扫掠 |
| 直线 | `linear.bushing.ball` | LM/LME/LMF/LMK 轴孔、法兰和长度包络 |
| 传动 | `drive.timing_pulley` | GT2/HTD 节距、齿数、带宽、轴孔和节圆 |
| 传动 | `drive.chain_sprocket` | 06B/08B/10B/12B 节距、齿数、轴孔和链条平面 |
| 传动 | `drive.taper_lock_bush` | 1008–3525 锥套外形、轴孔和轮毂接口 |
| 齿轮 | `gear.spur` | 模数、齿数、轴孔、分度圆和外形；不含强度与公差 |
| 齿轮 | `gear.bevel_straight` | 直齿伞齿轮节锥布局；不是生产齿面 |
| 气动 | `pneumatic.cylinder.iso6432` | 8–25 缸径、前后安装基准、杆端、运动轴和杆扫掠 |
| 气动 | `pneumatic.cylinder.iso15552` | 32–125 缸径、型材包络、安装基准和杆扫掠 |
| 气动 | `pneumatic.cylinder.compact` | ISO 21287/SDA 紧凑气缸包络、安装基准和杆扫掠 |
| 执行器 | `actuator.linear.electric` | 杆式/滑台式机体、输出位置和完整行程安全体积 |
| 传感器 | `sensor.proximity.threaded` | M8/M12/M18/M30 螺纹安装、感应面、后部接线和感应空间 |
| 风扇 | `fan.axial.square` | 40–140 方框、厚度、孔阵列、气流轴和进排气安全体积 |
| 设备附件 | `hardware.leveling_foot` | M8–M30 螺杆、脚垫、地面基准和调节空间 |
| 设备附件 | `hardware.caster` | 50–200 轮径、板/杆安装、地面基准和回转扫掠 |
| 紧固件 | `fastener.hex_bolt_metric` | 六角头、名义螺纹包络与夹紧面 |
| 紧固件 | `fastener.hex_nut_metric` | 六角包络、名义螺纹孔与两端面 |
| 紧固件 | `fastener.plain_washer_metric` | 内径、外径、厚度和承压面 |
| 键 | `key.parallel` | b×h×L、端部形式和接触方向 |
| 型材 | `profile.square_tube` | 方管外形、内腔和切割端面 |
| 型材 | `profile.round_tube` | 圆管外径、内径和切割端面 |
| 型材 | `profile.round_rod` | 圆棒直径、长度和轴线 |
| 型材 | `profile.equal_angle` | 等边角钢锐角包络和切割端面 |

当前自动索引包含 **34 个 family、288 个具体型号/规格条目，共 322 个发现条目**。
目录声明位于 `src/cadparts/data/catalog/<category>/`，`index.json` 由声明自动生成。

## 实例契约

`cadparts.instance/v2` 同时包含：

- `catalog_id`、family、库版本和生成参数；
- 不改变几何但影响采购的 `selection`；
- 派生尺寸与精确外形包络；
- 带原点和轴向的命名装配接口；
- `normative`、`cross_vendor_verified`、`series_compatible` 或 `catalog_specific` 兼容性等级；
- 运动、接线、气流或工具操作所需的建议 `keepouts`；
- 采购型号或搜索关键词；
- 几何精度声明与明确省略项。

模型应优先使用这些字段完成装配，不要从 STEP 反向猜测安装孔、轴线或定位面。
`keepouts` 只是规划证据，不是硬约束或自动合格判定；最终是否接受装配仍由模型结合用途和视觉审查决定。

## 贡献审查

每个新增 family 必须有自声明、生成器、代表样件和接口测试。审查命令：

```bash
cadparts validate-catalog --build-samples
cadparts review <family-or-item> --output-dir review
```

`review` 生成 STEP、实例 JSON、标准视图 PNG、红色接口轴和机器可读报告，供多模态模型或人工审查。

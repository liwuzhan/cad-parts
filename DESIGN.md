# cad-parts 设计文档

- 版本：v2.1（扩展外购件与兼容性证据）
- 日期：2026-08-27
- 状态：首个可用实现

## 1. 定位

机械装配通常同时包含非标设计件和大量标准件/外购件。语言模型最宝贵的上下文应集中在
非标件、结构关系和装配决策上，而不是反复绘制轴承、紧固件、型材、减速机或电机。

本库的目标是让模型能够：

1. 发现和比较可购买的零件方向；
2. 选择足够合理的规格或型号；
3. 在装配体中保留可信的空间包络；
4. 使用明确的安装面、孔、轴和定位基准；
5. 在 BOM 中保存型号和采购关键词；
6. 将上下文窗口留给真正需要设计的非标件。

因此它不是制造级标准数据库，也不负责受力、寿命、材料、热处理、公差或认证。

## 2. 一个零件何时合格

一个代理零件只要满足下列问题，就可以进入目录：

- 模型能否从名称、别名、尺寸和选型属性找到它？
- 外形包络是否足以避免明显空间冲突？
- 所有装配关键接口是否具有尺寸、位置和方向？
- 模型能否据此描述一个可搜索或可询价的采购规格？
- 省略的内部或制造细节是否已明确声明？
- 代码能否稳定生成 STEP 和可供多模态检查的 PNG？

加工级齿面、真实螺纹、轴承滚道等不是所有 family 的准入要求。

## 3. 两层数据模型

### 3.1 family：几何与接口规则

family 定义参数契约、几何生成器、派生尺寸、默认坐标系和接口规则。例如：

```text
bearing.deep_groove
fastener.hex_bolt_metric
gear.spur
profile.square_tube
```

### 3.2 catalog item：可购买的具体方向

item 指向 family 并固定一组常见生成参数，例如：

```json
{
  "id": "bearing.deep_groove.6204",
  "family": "bearing.deep_groove",
  "dimensions_mm": {"bore": 20, "outside_diameter": 47, "width": 14},
  "generator": {"params": {"code": "6204"}}
}
```

不改变包络但影响购买的属性进入 `selection`：

```json
{"closure": "2RS", "clearance": "C3"}
```

这样 `6204`、`6204-ZZ` 和 `6204-2RS-C3` 可以共享同一个代理几何，同时保留不同采购语义。

## 4. 自声明与固定目录

每个 family 在 `src/cadparts/data/catalog/<category>/` 有独立 JSON 自声明，包含：

- 中英文名称、别名和搜索关键词；
- 选型字段；
- 几何精度和明确省略项；
- 命名接口的性质；
- 采购描述模板；
- 代表样件；
- 可选的具体 item 尺寸表。
- 兼容性等级、声明边界和必须核对的接口字段；
- 运动扫掠、接线、气流、维护等建议安全体积。

模型的固定入口是仓库根目录 `CATALOG.md`。工具使用自动生成的
`src/cadparts/data/catalog/index.json`。模型不得依赖文件遍历发现能力。

索引只返回紧凑候选和准确声明路径，避免整个目录进入上下文。

## 5. 渐进式发现

```text
search → compare → describe → instantiate → 装配/BOM
```

### search

接受中文、英文、型号、别名和结构化尺寸约束，只返回少量候选。

### compare

只比较包络、接口、选型属性和几何精度，不加载 B-rep。

### describe

返回单个候选及其 family 契约、自声明路径和生成参数。

### instantiate

生成代理实体和 `cadparts.instance/v2`，包括实际包络、接口和采购描述。

找不到完全匹配时必须返回最接近的候选和违反的约束，不能编造型号或尺寸。

## 6. 装配接口

每个接口至少包含：

```json
{
  "id": "output_shaft",
  "type": "cylindrical_shaft",
  "role": "driven output",
  "frame": {
    "origin_mm": [0, 0, 0],
    "axis": [1, 0, 0]
  },
  "dimensions_mm": {"diameter": 25, "length": 40}
}
```

当前接口类型包括：

- `axis`
- `planar_face`
- `cylindrical_bore`
- `cylindrical_surface`
- `male_thread_envelope`
- `female_thread_envelope`
- `profile_end`
- `pitch_cylinder`
- `pitch_cone`
- `rectangular_key_contact`
- `bolt_pattern` / `rectangular_hole_pattern`
- `motor_flange` / `mounting_flange`
- `cylindrical_shaft` / `hollow_output`
- `linear_motion_axis` / `rotation_axis` / `flow_axis`
- `wheel_contact` / `sensing_face`

接口是放置和审查证据，不是强制求解器。模型可以直接用 frame 变换装配，也可以按面贴合、
轴线同轴或成角等几何关系自行计算变换；库不把最终装配质量交给某个软件或报警规则。

## 7. 兼容性与安全体积

兼容性声明分四级：

- `normative`：某个标准明确规定了主要接口基础，仍需核对标准未覆盖的产品选项；
- `cross_vendor_verified`：关键接口已经跨多个来源逐项比对；
- `series_compatible`：市场通用系列或名义框号，只用于缩小选择，替代前必须核对声明字段；
- `catalog_specific`：来自一个目录或参数集，不作互换性承诺。

`keepouts` 描述完整行程、回转扫掠、接线弯曲、进排气、工具或维护空间。它是模型可选择使用的
估计证据，不是碰撞报警器。程序不因建议安全体积相交就自动否决装配。

## 8. 精度层级

### 必须准确

- 外形包络；
- 安装面与安装孔；
- 输入输出轴、通孔和法兰；
- 接口直径、伸出长度、位置和轴向；
- 型号、关键选型属性与采购描述。

### 可以简化

- 非接口圆角、加强筋和散热片；
- 螺纹外观；
- 轴承滚珠、滚道和保持架；
- 减速机、电机的内部结构；
- 不影响选型和干涉的装饰细节。

### 当前不做

- 受力、寿命、材料和热处理；
- 制造公差、表面粗糙度和加工数据；
- 产品认证和完整标准符合性；
- 实时价格、库存或供应商推荐。

采购字段只提供型号与搜索/询价方向。未来可以由交易系统解析这些字段，但不进入当前实现范围。

## 9. `cadparts.instance/v2`

实例对象保存：

- 库名与版本；
- family 与具体 `catalog_id`；
- 几何参数与采购 `selection`；
- 派生尺寸；
- B-rep 实际包络；
- 命名接口；
- 兼容性等级和需核对字段；
- 建议安全体积；
- 采购型号或查询文本；
- 几何精度声明；
- 标准或产品系列来源。

装配系统应记录整个实例 JSON，而不是只记录一个匿名 STEP 路径。

## 10. 多模态贡献审查

每个 PR 的代表样件通过相同流水线：

```text
声明校验 → 索引一致性 → 生成实体 → STEP 导出
         → 标准四视图 PNG → 接口轴叠加 → 机器/多模态审查
```

`cadparts review` 输出：

- STEP；
- 实例 JSON；
- 轴测、正、右、俯视 PNG；
- 红色接口轴；
- `review.json` 与固定审查问题。

合并门槛：

- 自声明完整；
- 自动索引无漂移；
- 代表样件有效且可导出；
- 包络和接口测试通过；
- 四视图与零件性质相符；
- 省略项没有被误宣称为制造精度。

## 11. 当前实现与路线

### 已完成

- 34 个 family、288 个可直接实例化的型号/规格条目；
- 电机、直角/行星减速机、轴承座、联轴器；
- 导轨、丝杠、支撑座、直线轴承和带/链传动；
- ISO/市场系列气缸、电动执行器、传感器、风扇和设备附件；
- 固定模型入口与包内 JSON 自声明；
- `search/compare/describe/instantiate`；
- `cadparts.instance/v2` 和具体装配接口；
- 明示的兼容性等级与建议安全体积；
- STEP/PNG 多模态审查；
- 目录一致性和代表样件门禁。

### 后续按真实装配需求扩展

优先级按“装配频率 × 手动画占用的模型上下文 × 接口重要性”排序：

1. 轴用/孔用挡圈、更多轴承与英制紧固件；
2. 液压缸、阀岛、泵和常见管接头；
3. 机器人法兰、工装夹具和更多机架附件；
4. 经来源核实的更多市场系列与厂商目录项。

具体厂商系列可以进入目录，但必须保留来源和 series/vendor 身份；未经验证不得把不同厂商的
相似型号假定为完全相同接口。

## 12. 与 cad-tool 的集成

`cad-tool` 安装流程可以同时安装本库；模型侧只需发现以下目录操作：

```text
cad_parts op=search
cad_parts op=compare
cad_parts op=describe
cad_parts op=instantiate
```

装配依赖记录 `catalog_id + selection + library_version`，生成的 STEP 作为几何缓存，
接口 JSON 作为自动定位与 BOM 的语义来源。

交易系统联动、实时供应商目录、询价、库存和采购代理属于未来扩展，不改变当前目录契约。

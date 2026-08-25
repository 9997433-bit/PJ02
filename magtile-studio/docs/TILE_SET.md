# 磁力片片型总表 (Tile Set)

本文档是 MagTile Studio 全部磁力片片型的权威清单与约定说明。几何数据的唯一事实来源是 `data/tile_catalog.json`, C++ 侧的稳定标识定义在 `include/magtile/core/types.hpp` (`TileType`), 两者必须一一对应 (见第 5 节新增片型清单)。

## 1. 通用约定

- **单位**: 1.0 = 标准正方形边长, 实物约 70mm (`unit_mm`)。
- **顶点**: 位于本地 XY 平面, 逆时针排列; 除扇形以圆心角顶点为本地原点外, 其余形状均以质心为本地原点。
- **磁力边**: 边 i 连接顶点 i 与 i+1, `magnet_edges` 列出带磁条的边索引; 磁力吸合按整边端点重合判定 (R1, 见 `docs/PHYSICS_RULES.md`)。
- **套装分层 `tier`**: `core` = 核心片型 (实物基础套装的 5 种片型, 依据实物照片确认; 免费模型库默认只用这些); `expansion` = 扩展包片型 (进阶内容可用)。产品分层细节与磁石排布见 `docs/TILE_CATALOG.md`。
- **语义标记 `hollow` / `variant` / `wheeled`**: 仅供教程文案、BOM 与渲染区分外观; **物理校验与拼接规则一律使用外框多边形**, 不因镂空/车轮而改变。

## 2. 核心片型 (tier = core, 共 5 种, 依据实物照片确认)

| 标识 (type) | 中文名 | 外形尺寸 | 磁力边 (实物磁石数) | 用途说明 |
| --- | --- | --- | --- | --- |
| `square` | 正方形 | 边长 1 | 4 边全带 (每边约 2 颗) | 地面与墙体的主力形状 |
| `equilateral_triangle` | 等边三角形 | 边长 1 | 3 边全带 | 屋顶、城齿与球面结构 |
| `right_triangle` | 直角三角形 | 两直角边长 1, 斜边 √2 | 3 边全带 | 等腰直角, 斜坡与转角填充 |
| `isosceles_triangle` | 等腰三角形 (瘦高) | 底 1, 高 2, 腰 √4.25 ≈ 2.06 | 3 边全带 (长腰各约 3 颗, 短底 2 颗) | 尖塔、桅帆与骨架肋片 |
| `rectangle` | 长方形 | 2 x 1 (两个正方形并排) | 4 边全带 (短边 1 颗, 长边 2 颗) | 长边与两个正方形拼接等长, 中央常带菱形压纹 |

核心片型清单 (中文): **正方形、等边三角形、直角三角形、等腰三角形、长方形** —— 免费模型库默认只使用这 5 种 (见 `docs/CONTENT_STRATEGY.md` 的 core-5 质检规则与 `tools/check_core5_usage.py`)。

## 3. 扩展片型 (tier = expansion, 共 8 种)

| 标识 (type) | 中文名 | 外形尺寸 | 磁力边 | 语义标记 | 用途说明 |
| --- | --- | --- | --- | --- | --- |
| `rhombus` | 菱形 | 边长 1, 锐角 60° | 4 边全带 | - | 星形与花瓣图案 |
| `trapezoid` | 梯形 | 下底 2, 上底 1, 腰 1 (底角 60°) | 4 边全带 | - | 屋檐、帐篷与放射环带 |
| `hexagon` | 六边形 | 边长 1 正六边形 | 6 边全带 | - | 塔楼底座与蜂窝结构 |
| `sector` | 扇形 | 四分之一圆, 半径 1 | 仅 2 条直边 | - | 弧边为装饰边 (6 段折线近似), 拱顶与圆角 |
| `large_square` | 大正方形 | 边长 2 (= 4 小方) | 4 边全带 | - | 大面积地台与墙面, 每边与长方形长边等长, 显著减少片数 |
| `window_square` | 窗格方 | 外框同正方形 (边长 1) | 4 边全带 | `variant: "window"` | 面内为窗格造型, 物理按实心正方形处理 |
| `door_frame` | 门框方 | 外框同正方形 (边长 1) | 4 边全带 | `hollow: true`, `variant: "door"` | 中心镂空作门洞或滚珠出口, 边磁力与重叠检测仍用外框 |
| `wheel_base` | 车轮底座 | 外框同长方形 (2 x 1) | 4 边全带 (长边长 2, 短边长 1) | `wheeled: true`, `variant: "wheeled"` | 底面装有滚动车轮, 作车辆底盘; 顶面/侧面拼接与物理校验按长方形处理 |

## 4. 语义标记详解

| 标记 | 类型 | 含义 |
| --- | --- | --- |
| `tier` | 字符串 | 套装分层: `core` / `expansion`; 免费模型库默认只使用 core 片型 |
| `hollow` | 布尔 | 中心镂空 (如门框方的门洞); 教程文案与 BOM 用, 物理仍按外框实心多边形 |
| `variant` | 字符串 | 外观变体标识 (`window` / `door` / `wheeled`), 空 = 标准实心片; 供渲染与教程文案区分 |
| `wheeled` | 布尔 | 底面带滚动车轮 (车轮底座); 车辆教程文案与车辆模型语义用, 拼接与校验不受影响 |

这些标记加载进 C++ 的 `core::TileShape` (`tier` / `hollow` / `variant` / `wheeled` 字段), 解析在 `src/core/json_io.cpp`。

## 5. 新增片型的修改清单

1. `data/tile_catalog.json`: 追加条目 (type / tier / 名称 / 顶点 / magnet_edges / 语义标记);
2. `include/magtile/core/types.hpp`: `TileType` 枚举加值, `kTileTypeCount` 加一;
3. `src/core/types.cpp`: `kTileTypes` 表加一行 (稳定字符串标识 + 中文名);
4. 本文档 (`docs/TILE_SET.md`) 的对应片型表加一行;
5. `tests/test_inventory_cli.sh` 的"满配库存"用例补上新片型;
6. 库存 CLI (`magtile_app inventory set/show/match`) 与形状目录 (`magtile_app catalog`) 无需改代码 —— 二者按 `TileType` 枚举与 `tile_catalog.json` 数据驱动, 自动识别新片型。

## 6. CLI 速查

```bash
# 查看全部片型 (含 tier 与语义标记说明)
magtile_app catalog

# 登记家里的磁力片库存 (标识见上表, 含车轮底座)
magtile_app inventory set square 40 large_square 8 window_square 6 door_frame 2 wheel_base 4

# 查看库存 / 对照库存列出能搭建的模型
magtile_app inventory show
magtile_app inventory match
```

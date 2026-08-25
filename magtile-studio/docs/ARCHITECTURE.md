# MagTile Studio 架构设计

本文档描述 MagTile Studio 的模块划分、核心数据模型、坐标与几何约定、渲染技术选型以及数据文件格式。目标读者: 参与开发的工程师与内容工具开发者。

## 1. 设计原则

1. **内容即数据**: 形状目录与模型定义全部是 JSON 数据, C++ 代码不硬编码任何具体模型。500+ 模型的内容生产不需要改代码、不需要重新发版。
2. **质检前置**: 物理校验器是内容管线的强制关卡, 校验失败的模型不允许进入发布包。校验覆盖教程的每一个中间状态, 而不仅是成品。
3. **渲染可替换**: 核心逻辑 (core / physics / tutorial) 不依赖任何图形库, 渲染后端隐藏在 `IRenderer` 接口之后, 可在不触碰业务代码的情况下替换。
4. **最小依赖**: 第一阶段唯一的第三方依赖是单头文件的 nlohmann/json (已内置于 `third_party/`), 构建不需要网络。

## 2. 模块划分

```
┌─────────────────────────────────────────────┐
│                 app (CLI / 未来 GUI)          │
├──────────────┬───────────────┬──────────────┤
│   tutorial   │    physics    │    render    │
│  分步教程引擎  │  物理规则校验   │  IRenderer   │
├──────────────┴───────────────┴──────────────┤
│                    core                      │
│   类型 / 数学 / 目录 / 模型数据结构 / JSON IO   │
└─────────────────────────────────────────────┘
```

| 模块 | 目录 | 职责 | 依赖 |
| --- | --- | --- | --- |
| core | `src/core` | `TileType`、`TileInstance`、`BuildStep`、`ModelDefinition`、`TileCatalog`、JSON 读写、向量/矩阵 | nlohmann/json (仅 .cpp 内) |
| physics | `src/physics` | 世界坐标几何 (`TransformedTile`)、分离轴重叠检测、凸包、`PhysicsValidator` | core |
| tutorial | `src/tutorial` | `TutorialEngine`: 步骤导航、场景查询、步骤一致性质检 | core |
| render | `src/render` | `IRenderer` 接口 + `NullRenderer`; GL 后端规划中 | core |
| app | `src/app` | 命令行入口 (`catalog` / `validate` / `tutorial`) | 全部 |

依赖方向严格自上而下, core 不反向依赖任何模块。所有公共头文件位于 `include/magtile/<module>/`, 命名空间与目录一一对应 (`magtile::core` 等)。

## 3. 核心数据模型

```
TileCatalog ──包含──▶ TileShape (每种 TileType 一份: 本地顶点 + 磁力边索引)
ModelDefinition
  ├── final_assembly: vector<TileInstance>   最终成品的全部磁力片
  └── steps: vector<BuildStep>               分步教程 (tiles_to_add 恰好覆盖全部片)
TileInstance = { id, type, position, rotation_deg, color }
BuildStep    = { step_number, description(中文), tip, tiles_to_add[], highlight_tiles[] }
```

关键不变量 (由 `json_io` 加载校验 + `TutorialEngine::checkConsistency` 质检):

- 模型内磁力片 `id` 唯一; `total_pieces == final_assembly.size()`。
- 步骤序号从 1 连续递增; 每片磁力片恰好被一个步骤放置; 引用的 id 必须存在。
- `difficulty ∈ [1, 5]`。

## 4. 坐标与几何约定

- 右手系, **Z 轴竖直向上**, 地面为 `z = 0` 平面。
- 长度单位: `1.0 = 标准正方形磁力片边长` (实物约 70mm, 记录于目录的 `unit_mm`)。
- 形状本地顶点位于 XY 平面 (z=0), 逆时针排列, 凸多边形; 边 `i` 连接顶点 `i` 与 `i+1`, `magnet_edges` 列出带磁条的边 (扇形的弧边无磁条)。
- 实例旋转为欧拉角 (度), 施加顺序 `R = Rz · Ry · Rx`:
  - 平铺: `(0, 0, yaw)`;
  - 南北向立片: `(90, 0, 0)` — 片位于 `y = const` 平面;
  - 东西向立片: `(90, 0, 90)` — 片位于 `x = const` 平面。
- `physics::transformTile` 把实例展开为世界坐标快照 (顶点 / 法向 / 质心 / 面积 / 最低点), 全部校验都基于该快照, 不重复做矩阵运算。

## 5. 渲染技术选型

**结论: GLFW + OpenGL 4.1 Core Profile (glad 加载), 通过 `IRenderer` 接口隔离。**

评估过程:

| 方案 | 优点 | 缺点 | 结论 |
| --- | --- | --- | --- |
| GLFW + OpenGL 4.1 | 三平台原生可用 (macOS 上限 4.1), 生态成熟, 团队上手快, 满足磁力片渲染需求 (半透明平面 + 描边高亮 + 简单光照) | 特性上限低于 Vulkan | ✅ 第一阶段采用 |
| GLFW + Vulkan | 性能上限高, 现代 API | 样板代码量大, macOS 需经 MoltenVK 转译, 对本项目画面复杂度属于过度设计 | 保留为后端演进选项 |
| 游戏引擎 (Unity/Godot) | 工具链完整 | 与 C++ 核心库/内容管线集成成本高, 商业授权与包体不可控 | 不采用 |

磁力片渲染的真实需求是: 数百个半透明凸多边形 + 磁吸点提示 + 教程高亮描边 + 轨道相机。OpenGL 4.1 足以覆盖, 且三平台单一代码路径。`IRenderer` 只暴露 `beginFrame / submitTile / endFrame`, 未来切换 Vulkan/Metal 后端不影响 core、physics、tutorial 与内容数据。

第一阶段仓库内仅包含 `NullRenderer` (无窗口, 供 CLI/CI 使用); GL 后端将以 CMake 选项 `MAGTILE_BUILD_GL_RENDERER` 引入, GLFW 通过 `find_package` + `FetchContent` 回退获取。

## 6. 数据文件格式

### 6.1 形状目录 `data/tile_catalog.json`

```jsonc
{
  "schema_version": 1,
  "unit_mm": 70,
  "tiles": [
    {
      "type": "square",            // 与 TileType 的稳定标识一致
      "name_zh": "正方形",
      "vertices": [[-0.5,-0.5], [0.5,-0.5], [0.5,0.5], [-0.5,0.5]],
      "magnet_edges": [0, 1, 2, 3] // 带磁条的边索引
    }
  ]
}
```

### 6.2 模型定义 `data/models/<id>.json`

```jsonc
{
  "schema_version": 1,
  "id": "castle_foundation_01",
  "name": "城堡地基与城墙",
  "difficulty": 3,                  // 1~5
  "total_pieces": 72,
  "final_assembly": [
    { "id": "g_0_0", "type": "square",
      "position": [0.5, 0.5, 0.0], "rotation": [0, 0, 0], "color": "blue" }
  ],
  "steps": [
    { "step_number": 1,
      "description": "在平整桌面上铺设地台第 1 排…",   // 中文, 面向用户
      "tip": "…",                                    // 可选提示
      "tiles_to_add": ["g_0_0", "g_1_0"],
      "highlight_tiles": [] }
  ]
}
```

`schema_version` 用于未来格式演进; 加载器遇到不认识的字段一律忽略, 保证旧版本应用可读新数据的子集。

## 7. 内容生产管线 (现状与方向)

```
设计师建模 (未来: 可视化编辑器)
   └─▶ 模型 JSON ──▶ magtile_app validate ──▶ 通过 ──▶ 入库 / 打包发布
                        │ 失败: 输出中文错误 (含涉事磁力片 id) 返工
tools/generate_castle_model.py   ← 程序化生成示例 (对称建筑类模型效率极高)
```

CI 中 `ctest` 会对仓库内全部模型执行 `validate`, 物理不合法的内容无法合入主干。

## 8. 后续架构演进

- **render**: GL 后端落地 (窗口、相机、拾取、步骤动画)。
- **app**: 由 CLI 升级为 GUI 应用 (Dear ImGui 做工具面板, 教程 UI 自绘)。
- **core**: 用户进度存档、多语言文案表 (当前中文内嵌于数据)。
- **physics**: 规则从"基础版"演进 (见 PHYSICS_RULES.md 第 5 节)。
- **编辑器**: 面向内容团队的可视化模型/教程编辑器, 复用同一核心库。

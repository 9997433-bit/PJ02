# 测试指南

MagTile Studio 的测试目标只有一个: **保证每一个入库模型都是用户可以真实搭出来的、有搭建价值的教程内容**。为此测试分为六类, 全部注册为 CTest 用例, 一条命令即可跑完。

## 构建

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release   # 图形后端默认开启
cmake --build build -j
```

- 图形后端开关: `-DMAGTILE_BUILD_GL_RENDERER=ON|OFF` (默认 ON)。OFF 时不需要网络与 X11 开发库, CLI 与 CTest 完全不受影响。
- 测试开关: `-DMAGTILE_BUILD_TESTS=ON|OFF` (默认 ON)。
- Linux 依赖: `sudo apt install libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev`; 若缺少 `wayland-scanner`, 构建会自动退回仅 X11 后端。
- 若默认编译器链接失败 (例如某些环境的 Clang 找不到 `-lstdc++`), 显式指定: `-DCMAKE_CXX_COMPILER=g++`。
- 脚本类测试需要 `bash` 与 `python3` (CMake 配置时自动探测, 缺失则跳过注册并给出警告)。

## 运行全部测试

```bash
ctest --test-dir build --output-on-failure
```

## 测试分类

### 1. 目录冒烟 (`print_tile_catalog`)

打印磁力片形状目录, 确认 `data/tile_catalog.json` 可以正常加载、9 种形状定义完整。

### 2. 单模型质检 (`validate_<模型名>` / `tutorial_<模型名>`)

CMake 配置时自动扫描 `data/models/*.json` (`CONFIGURE_DEPENDS`, 新增模型无需改 CMake), 为每个模型注册两个用例:

- `validate_<模型名>`: 完整物理与教程质检 —— 接地支撑 (R1)、磁力连接 (R2)、无重叠 (R3)、重心稳定 (R4), 且对**每一个教程步骤完成后的中间状态**重复全部检查, 保证用户搭到一半也不会塌;
- `tutorial_<模型名>`: 终端分步教程完整走一遍。

手动等价命令:

```bash
./build/magtile_app validate data/models/castle_foundation_01.json --data-dir data
./build/magtile_app tutorial data/models/castle_foundation_01.json --data-dir data
```

### 3. 模型库全量质检 (`all_models_quality_gate`)

脚本: `tests/test_all_models.sh <magtile_app> <项目根目录> [最低片数]`

逐一校验 `data/models/` 下的**全部**模型 (运行时扫描, 不依赖 CMake 重新配置), 报告每个模型的磁力片数与步骤数, 并执行规模门槛:

- 任何模型磁力片总数 **< 40 片即失败** —— 太小的模型对用户没有搭建价值, 不允许入库。

```bash
tests/test_all_models.sh build/magtile_app . 40
```

### 4. 反平凡模型检查 (`anti_trivial_models`)

脚本: `tests/test_anti_trivial.py <models目录或模型文件...>`

商业教程内容不能是"几片拼个平面"的敷衍货, 以下任意一条即拒绝入库 (FAIL):

| 规则 | 判定 | 结果 |
| --- | --- | --- |
| 规模 | 总片数 < 40 | FAIL |
| 形状多样性 | 使用的磁力片形状 < 3 种 | FAIL |
| 结构高度 | Z 层数 < 2 (纯平面模型) | FAIL |
| 立体性 | 所有磁力片都是平铺的 (旋转均接近 0,0,0) | FAIL |
| 步骤质量 | 超过 50% 的步骤只放 1~2 片 | WARN (不阻断) |

其中"平铺"按与 C++ 一致的旋转约定 (R = Rz·Ry·Rx) 计算面法向: 法向 z 分量 |cos rx · cos ry| ≈ 1 即视为平铺, 因此仅绕 Z 轴旋转的片仍算平铺。

```bash
python3 tests/test_anti_trivial.py data/models
```

### 5. 教程完整性 (`tutorial_integrity`)

脚本: `tests/test_tutorial_integrity.sh <magtile_app> <项目根目录>`

对每个模型做两轮走查:

1. **静态走查**: 逐步累加 `tiles_to_add`, 验证步骤序号从 1 连续递增、每片磁力片恰好被一个步骤放置 (不重复、不遗漏)、走完全部步骤后的累计片数 == `final_assembly` 数 == `total_pieces`;
2. **运行时走查**: 用 `magtile_app tutorial` 把教程引擎完整跑一遍, 退出码必须为 0, 且引擎最终报告的放置片数与 `total_pieces` 一致。

```bash
tests/test_tutorial_integrity.sh build/magtile_app .
```

### 6. 物理负例 (`physics_negative_*`)

目录: `tests/test_physics_negative/`, 执行器: `tests/test_physics_negative.sh`

这些夹具是**物理上不成立的反面教材**, `magtile_app validate` 必须以非零退出码拒绝, 并且输出必须包含期望的错误码 (防止因 JSON 解析失败等无关原因"碰巧"非零):

| 夹具 | 物理缺陷 | 期望错误码 |
| --- | --- | --- |
| `floating_tile.json` | 一片磁力片悬空, 无磁力连接也无支撑路径 | `floating_tile` |
| `unstable_cantilever.json` | 连接合法但重心水平投影远超接地区域, 必然倾倒 | `unstable_center_of_mass` |
| `overlapping_tiles.json` | 两片在同一平面上完全重合 | `tile_overlap` |

```bash
tests/test_physics_negative.sh build/magtile_app data \
    tests/test_physics_negative/floating_tile.json floating_tile
```

新增负例的方法: 在 `tests/test_physics_negative/` 放入夹具 JSON (须能通过 JSON 加载, 只在物理层失败), 然后在顶层 `CMakeLists.txt` 的负例列表中追加 `"文件名|期望错误码"` 一行。

## 启动 3D 交互教程 (GUI)

```bash
./build/magtile_app tutorial data/models/castle_foundation_01.json --gui
```

操作: 鼠标左键旋转 / 右键平移 / 滚轮缩放, `←` `→` 或 HUD 按钮切换步骤, `R` 重置, `Esc` 退出。需要支持 OpenGL 4.1 的显示环境 (无独显机器上 Mesa llvmpipe 软件渲染亦可)。

## 图形后端冒烟测试 (无头 / CI)

```bash
tests/test_gl_smoke.sh          # 默认使用 build/ 下的可执行文件
tests/test_gl_smoke.sh mybuild  # 或指定构建目录
```

脚本自动选择运行方式: 优先 `xvfb-run` (需 `apt install xvfb`), 其次现有 `DISPLAY`; 渲染 5 帧并保存 PPM 截图, 校验截图尺寸与内容非纯色。两者都不可用时退化为链接检查 (确认 `--gui` 代码路径已编译进二进制)。

手动等价命令:

```bash
xvfb-run -a ./build/magtile_app tutorial data/models/castle_foundation_01.json \
    --gui --frames 30 --screenshot /tmp/magtile.ppm
```

`--frames N` 渲染 N 帧后自动退出, `--screenshot FILE` 在最后一帧保存画面, 两者专为 CI 冒烟测试设计。

## 内容入库标准 (Definition of Done)

一个模型 JSON 只有同时满足以下条件才允许合入 `data/models/`:

1. `validate_<模型名>` 通过 (物理 R1~R4, 含全部中间步骤);
2. `all_models_quality_gate` 通过 (≥ 40 片);
3. `anti_trivial_models` 通过 (≥ 3 种形状、≥ 2 个 Z 层、存在立置片);
4. `tutorial_integrity` 通过 (步骤恰好覆盖全部磁力片)。

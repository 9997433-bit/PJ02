# 测试指南

MagTile Studio 的测试目标只有一个: **保证每一个入库模型都是用户可以真实搭出来的、有搭建价值的教程内容**。因此这里的"测试"远不止软件单元测试 —— 模型的物理合理性 (搭得起来)、教程逻辑 (讲得通)、内容体量与多样性 (值得搭) 全部是自动化质量关卡的对象。

## 0. 一键全量 QA

```bash
tests/run_full_qa.sh              # 默认构建目录 build
tests/run_full_qa.sh mybuild      # 或指定构建目录
```

按固定顺序执行全部关卡, 输出彩色分项报告, 任何一关失败即整体红灯 (退出码 1):

| # | 关卡 | 内容 |
| --- | --- | --- |
| 1 | CMake 配置 | 仓库任何状态下必须可配置 |
| 2 | 增量构建 | 零警告要求 (`-Wall -Wextra -Wpedantic` / `/W4`) |
| 3 | CTest 全量回归 | 下文全部注册用例 |
| 4 | 模型库全量质检 | 逐模型 validate + 片数 ≥ 40 门槛 |
| 5 | 反平凡模型检查 | ≥ 3 种片形、≥ 2 个 Z 层、有立置片 |
| 6 | 模型逻辑质检 | 步骤粒度 / 中文说明 / 对账 / 难度区间 / BOM |
| 7 | 教程完整性 | 静态走查 + 教程引擎实跑 |
| 8 | 物理负例 × N | 不成立的结构必须被拒绝, 且错误码正确 |
| 9 | 物理正例 × N | 预算内的合法结构必须放行 |
| 10 | GL 渲染冒烟 | 无头渲染 + 截图校验 (无显示环境自动降级) |

环境变量: `MAGTILE_CMAKE_ARGS` 追加配置参数 (如 `-DMAGTILE_BUILD_GL_RENDERER=OFF`); `FORCE_COLOR=1` 在 CI 中强制彩色; `NO_COLOR=1` 禁用颜色。

CI 中每次 push 自动运行同一脚本 (见第 4 节), 本地跑绿 = CI 跑绿。

## 1. 测试金字塔全景

软件层 (本文档, 全自动) 与实物层 (见 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md), 按难度分级) 合成完整的质量金字塔:

```
                 ▲ 成本/模型 高, 覆盖频率 低
                ╱ ╲
               ╱实物╲      L3 实物搭建验证 (人 + 真实磁力片)
              ╱ 验证 ╲        捕捉: 品牌磁力差异、儿童手部抖动、
             ╱────────╲             装配手感、"手伸不进去"的实操死角
            ╱ 物理仿真 ╲    L2 刚体仿真抽检 (规划中, 被标记模型)
           ╱   抽检     ╲      捕捉: 微小错位累积坍塌、扰动回稳性
          ╱──────────────╲
         ╱   GL 渲染冒烟   ╲  test_gl_smoke.sh
        ╱                   ╲   捕捉: 渲染后端链接损坏、纯色/空白画面
       ╱─────────────────────╲
      ╱   内容质量关卡 (L1)    ╲ 全部模型 · 每次提交 · 秒级
     ╱  物理: R1~R8 (validate)  ╲  捕捉: 悬空/穿插/失稳/悬挂超重/
    ╱  逻辑: test_model_logic.py ╲       悬臂折落/放不进去/顺序写反
   ╱  体量: test_anti_trivial.py  ╲ 捕捉: 空步骤/说明缺失/BOM 骗人/
  ╱  教程: test_tutorial_integrity ╲      难度虚标/敷衍小模型/教程漏片
 ╱──────────────────────────────────╲
╱      C++ 回归 (CTest 注册用例)      ╲ 捕捉: 目录加载/JSON 解析/
        catalog·validate·tutorial·progress    教程引擎/进度存档的代码回归
                 ▼ 成本/模型 低, 覆盖频率 高 (每次提交全量)
```

各层职责与边界:

- **C++ 回归** 保证代码不退化 —— 但代码全对, 内容照样可能是垃圾;
- **内容质量关卡 (L1)** 保证每个模型"搭得起来、讲得通、值得搭" —— 这是本项目区别于普通软件测试的核心层, 覆盖物理常识 (静力学预算)、教程逻辑 (逐片放置可行) 与商业合理性 (体量/难度/BOM);
- **GL 冒烟** 保证 3D 教程画面真的画得出来;
- **L2/L3 实物层** 兜住纯软件无法覆盖的真实世界因素 (品牌差异、手感、儿童行为), 分级要求与规程见 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md)。

## 2. 构建

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release   # 图形后端默认开启
cmake --build build -j
```

- 图形后端开关: `-DMAGTILE_BUILD_GL_RENDERER=ON|OFF` (默认 ON)。OFF 时不需要网络与 X11 开发库, CLI 与 CTest 完全不受影响。
- 测试开关: `-DMAGTILE_BUILD_TESTS=ON|OFF` (默认 ON)。
- Linux 依赖: `sudo apt install libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev`; 若缺少 `wayland-scanner`, 构建会自动退回仅 X11 后端。
- 若默认编译器链接失败 (例如某些环境的 Clang 找不到 `-lstdc++`), 显式指定: `-DCMAKE_CXX_COMPILER=g++`。
- 脚本类测试需要 `bash` 与 `python3` (CMake 配置时自动探测, 缺失则跳过注册并给出警告)。

运行全部注册用例:

```bash
ctest --test-dir build --output-on-failure
```

## 3. 测试分类

### 3.1 目录冒烟 (`print_tile_catalog`)

打印磁力片形状目录, 确认 `data/tile_catalog.json` 可以正常加载、9 种形状定义完整。

### 3.2 单模型质检 (`validate_<模型名>` / `tutorial_<模型名>`)

CMake 配置时自动扫描 `data/models/*.json` (`CONFIGURE_DEPENDS`, 新增模型无需改 CMake), 为每个模型注册两个用例:

- `validate_<模型名>`: 完整物理与教程质检 —— 几何规则 R1 接地支撑、R2 磁力连接、R3 无重叠、R4 重心稳定, 静力学/工艺规则 R5 悬挂承重、R6 悬臂力矩、R7 装配可达 (按步骤内顺序逐片模拟放置)、R8 结构冗余警告; 且对**每一个教程步骤完成后的中间状态**重复全部静态检查, 保证用户搭到一半也不会塌 (规则定义见 [PHYSICS_RULES.md](PHYSICS_RULES.md));
- `tutorial_<模型名>`: 终端分步教程完整走一遍。

手动等价命令:

```bash
./build/magtile_app validate data/models/castle_foundation_01.json --data-dir data
./build/magtile_app tutorial data/models/castle_foundation_01.json --data-dir data
```

### 3.3 模型库全量质检 (`all_models_quality_gate`)

脚本: `tests/test_all_models.sh <magtile_app> <项目根目录> [最低片数]`

逐一校验 `data/models/` 下的**全部**模型 (运行时扫描, 不依赖 CMake 重新配置), 报告每个模型的磁力片数与步骤数, 并执行规模门槛:

- 任何模型磁力片总数 **< 40 片即失败** —— 太小的模型对用户没有搭建价值, 不允许入库。

```bash
tests/test_all_models.sh build/magtile_app . 40
```

### 3.4 反平凡模型检查 (`anti_trivial_models`)

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

### 3.5 模型逻辑质检 (`model_logic_gate`)

脚本: `tests/test_model_logic.py <models目录或模型文件...>`

物理校验器保证"搭得起来", 本关保证**教程讲得通、元数据不骗人**:

| 规则 | 判定 | 结果 |
| --- | --- | --- |
| 步骤粒度 | 某步骤放 0 片 (空步骤) 或 > 15 片 (信息量爆炸) | FAIL |
| 步骤粒度 | 某步骤放 13~15 片 (超出推荐的 1~12 片/步) | WARN |
| 步骤说明 | description 为空或不含中文 | FAIL |
| 教程对账 | 各步骤 `tiles_to_add` 之和 ≠ `final_assembly` 片数, 或存在重复/幽灵/漏放 id | FAIL |
| 难度定级 | `difficulty` 与片数区间不匹配 (D1: 12–28 / D2: 28–48 / D3: 48–75 / D4: 75–110 / D5: 110–180, 见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 2.1 节) | FAIL |
| 步骤节奏 | 步骤数超出该难度参考区间 | WARN |
| BOM 备料清单 | `content_meta.structural_signature.tile_histogram` 缺失, 或与 `final_assembly` 实际片形用量不一致 | FAIL |

BOM 一致性是产品承诺: 用户按"所需磁力片清单"备料, 不允许出现搭到一半发现缺片。BOM 由生成工具写入 (如 `tools/generate_castle_model.py`), 严禁手写。

```bash
python3 tests/test_model_logic.py data/models
```

### 3.6 教程完整性 (`tutorial_integrity`)

脚本: `tests/test_tutorial_integrity.sh <magtile_app> <项目根目录>`

对每个模型做两轮走查:

1. **静态走查**: 逐步累加 `tiles_to_add`, 验证步骤序号从 1 连续递增、每片磁力片恰好被一个步骤放置 (不重复、不遗漏)、走完全部步骤后的累计片数 == `final_assembly` 数 == `total_pieces`;
2. **运行时走查**: 用 `magtile_app tutorial` 把教程引擎完整跑一遍, 退出码必须为 0, 且引擎最终报告的放置片数与 `total_pieces` 一致。

```bash
tests/test_tutorial_integrity.sh build/magtile_app .
```

### 3.7 物理负例 (`physics_negative_*`)

目录: `tests/test_physics_negative/`, 执行器: `tests/test_physics_negative.sh`

这些夹具是**物理上不成立的反面教材**, `magtile_app validate` 必须以非零退出码拒绝, 并且输出必须包含期望的错误码 (防止因 JSON 解析失败等无关原因"碰巧"非零):

| 夹具 | 物理缺陷 | 期望错误码 | 规则 |
| --- | --- | --- | --- |
| `floating_tile.json` | 一片磁力片悬空, 无磁力连接也无支撑路径 | `floating_tile` | R1 |
| `unstable_cantilever.json` | 连接合法但重心水平投影远超接地区域, 必然倾倒 | `unstable_center_of_mass` | R4 |
| `overlapping_tiles.json` | 两片在同一平面上完全重合 | `tile_overlap` | R3 |
| `hanging_chain_overload.json` | 5 片竖链 (~150g) 全部吊在一条磁力边下, 超出 120g 悬挂预算 | `hanging_chain_overload` | R5 |
| `cantilever_overload.json` | 墙顶外挑 2 片, 力矩 60 g·单位 远超 20 g·单位 铰链预算 (**旧版 R1~R4 全绿**, 是"校验通过但实搭掉落"的典型标本) | `cantilever_overload` | R6 |
| `enclosed_placement.json` | 全封闭盒子完成后才放内部隔断, 手伸不进去 (成品本身合法, 错在顺序) | `enclosed_placement` | R7b |
| `unplaceable_order.json` | 步骤内 tiles_to_add 顺序写反, 上层片放下瞬间无处吸附 | `unplaceable_tile` | R7a |

R5~R7 的 4 个夹具由 `tools/generate_test_models.py` 生成 (含每个夹具对应的实物失效对照说明), R1~R4 的 3 个为手工维护。

```bash
tests/test_physics_negative.sh build/magtile_app data \
    tests/test_physics_negative/floating_tile.json floating_tile
```

新增负例的方法: 在 `tests/test_physics_negative/` 放入夹具 JSON (须能通过 JSON 加载, 只在物理层失败), 然后在顶层 `CMakeLists.txt` 的负例列表中追加 `"文件名|期望错误码"` 一行; 若错误码与文件名不同, 同时在 `tests/run_full_qa.sh` 的 `expected_code_for` 映射中登记。

### 3.8 物理正例 (`physics_positive_*`)

目录: `tests/test_physics_positive/`, 执行器: `tests/test_physics_positive.sh`

负例的**对照组**: 处于承载预算之内的合法结构, `validate` 必须放行 (退出码 0 且输出"可发布"结论), 防止 R5/R6 静力规则矫枉过正、误杀磁力片的常规玩法:

| 夹具 | 结构 | 必须放行的理由 |
| --- | --- | --- |
| `single_cantilever_within_budget.json` | 墙顶水平外挑单片 | 力矩 15 g·单位 < 20 g·单位 预算, 实物立得住, 是常规玩法 |

正例夹具按 `CONFIGURE_DEPENDS` 自动注册, 新增只需把 JSON 放进目录后重新配置。**每放宽/收紧一次 PhysicsConfig 预算参数, 都必须同时补一对正/负例夹具钉住新边界** (见 PHYSICS_RULES.md "调参纪律")。

### 3.9 C++ 回归 (`progress_roundtrip` / `progress_cli_smoke`)

进度存档 (SQLite) 的保存/读取往返、完成/收藏/成就/库存、跨连接持久化与重置删除的 C++ 级回归, 以及空库 CLI 冒烟。随代码演进持续追加此类用例 —— 注册进 CTest 即自动纳入全量 QA 关卡 3。

### 3.10 GL 渲染冒烟 (`tests/test_gl_smoke.sh`)

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

## 4. 持续集成 (CI)

`.github/workflows/qa.yml` 在**每次 push** 时于 Ubuntu runner 上执行 `tests/run_full_qa.sh` 全流程:

- 安装 X11 开发库 (FetchContent 源码构建 GLFW) 与 xvfb + Mesa (llvmpipe 软件渲染), 因此 CI 中 GL 冒烟跑的是**真渲染 + 截图校验**, 不是降级检查;
- GLFW/ImGui 源码按 CMakeLists 哈希缓存, 不重复克隆;
- 失败时自动上传各关卡分项日志 (`qa-stage-logs` 工件);
- 本地与 CI 跑的是同一个脚本: 提交前先 `tests/run_full_qa.sh` 跑绿, CI 不会有意外。

## 5. 如何新增一个模型 (必须全绿才能入库)

1. **生成或搭建模型 JSON**: 用编辑器/生成工具产出 `data/models/<model_id>.json`, BOM 等元数据由工具写入 `content_meta` (勿手写);
2. **对照内容策略自检**: 难度与片数区间匹配 (CONTENT_STRATEGY.md 2.1 节)、≥ 3 种片形、≥ 2 个 Z 层、步骤 1~12 片/步、每步中文说明;
3. **重新配置一次 CMake** (`cmake -S . -B build`): `validate_<模型名>` / `tutorial_<模型名>` 用例自动注册 (glob 是 `CONFIGURE_DEPENDS`, 但新文件仍需触发一次配置);
4. **跑全量 QA**: `tests/run_full_qa.sh`, 新模型必须让全部关卡保持绿灯 —— 物理 R1~R8 (含每个中间步骤)、体量门槛、逻辑质检、教程完整性一个都不能少;
5. **有 Warning 先处理**: `disconnected_assembly` 等 Warning 须在教程文案中有对应分组说明; R8 结构冗余警告的点位建议按 PHYSICS_RULES.md 加固;
6. **高难模型走实物层**: difficulty ≥ 3 按 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 完成实物验证 (T3+ 硬性要求), difficulty ≥ 4 另需目标年龄段儿童测试;
7. **提交**: CI 会在 push 时把第 4 步整套重跑一遍, 红灯不允许合入。

## 6. 内容入库标准 (Definition of Done)

一个模型 JSON 只有同时满足以下条件才允许合入 `data/models/`:

1. `validate_<模型名>` 通过 (物理 R1~R8, 含全部中间步骤与逐片放置模拟);
2. `all_models_quality_gate` 通过 (≥ 40 片);
3. `anti_trivial_models` 通过 (≥ 3 种形状、≥ 2 个 Z 层、存在立置片);
4. `model_logic_gate` 通过 (步骤粒度、中文说明、教程对账、难度区间、BOM 一致);
5. `tutorial_integrity` 通过 (步骤恰好覆盖全部磁力片, 教程引擎实跑成功);
6. 按难度分级完成实物验证要求 (BUILD_VERIFICATION.md 第 2 节)。

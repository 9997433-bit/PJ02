# 测试指南

MagTile Studio 的测试目标只有一个: **保证每一个入库模型都是用户可以真实搭出来的、有搭建价值的教程内容**。因此这里的"测试"远不止软件单元测试 —— 模型的物理合理性 (搭得起来)、教程逻辑 (讲得通)、内容体量与多样性 (值得搭) 全部是自动化质量关卡的对象。

上架前的**用户路径验收**另见 [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) (V1 必测路径矩阵 + 自动子集一键跑 `tools/run_e2e_smoke.sh`, 见第 8 节)。

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
| 7 | 逐步装配质检 | 逐片零差错 P1~P8 (见 [MODEL_QUALITY.md](MODEL_QUALITY.md)) |
| 8 | 模型库唯一性 | 结构签名两两比对, 拒绝换皮克隆 |
| 9 | 片型分层检查 | core-9 覆盖率 + 需要扩展装标签 + 免费层 ≥80% 红线 (`--strict` 硬闸门) |
| 10 | 免费层清单对齐核验 | 可选 (`MAGTILE_FREE_TIER_CHECK=1`): 免费标签数=30 + 全 core-9 + 与 starter 打包清单一致 (见 3.14 节) |
| 11 | 教程完整性 | 静态走查 + 教程引擎实跑 |
| 12 | 物理负例回归 | 夹具注册表完整性 (缺夹具即 FAIL) + 每个负例按 sidecar 期望报错/报警 |
| 13 | 物理正例 × N | 预算内的合法结构必须放行 |
| 14 | GL 渲染冒烟 | 无头渲染 + 截图校验 (无显示环境自动降级) |
| 15 | 弱磁严格档全库巡检 | 可选 (`MAGTILE_STRICT_AUDIT=1`): strict 零警告审计 + 逐步装配质检 |
| 16 | L3 实物复核缺口报告 | 报告型: 输出 D4+ 未实物复核模型数量, 仅报告不阻断 (见 3.13 节) |
| 17 | 教程步进性能基准 | 可选 (`MAGTILE_TUTORIAL_BENCH=1`): 小/中/大代表模型逐步计时 nextStep/goToStep, 每步 ms 与 P95, 超预算退出 1 (见 3.16 节; CTest 关卡已含同口径回归) |

环境变量: `MAGTILE_CMAKE_ARGS` 追加配置参数 (如 `-DMAGTILE_BUILD_GL_RENDERER=OFF`); `MAGTILE_FREE_TIER_CHECK=1` 开启可选关卡 10; `MAGTILE_STRICT_AUDIT=1` 开启可选关卡 15; `MAGTILE_TUTORIAL_BENCH=1` 开启可选关卡 17; `FORCE_COLOR=1` 在 CI 中强制彩色; `NO_COLOR=1` 禁用颜色。

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
- **内容质量关卡 (L1)** 保证每个模型"搭得起来、讲得通、值得搭" —— 这是本项目区别于普通软件测试的核心层, 覆盖物理常识 (静力学预算)、教程逻辑 (逐片放置可行)、商业合理性 (体量/难度/BOM), 以及**逐片零差错** (`test_step_assembly.py`) 与**全库唯一性** (`test_library_uniqueness.py`, 克隆检测), 见 [MODEL_QUALITY.md](MODEL_QUALITY.md);
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

打印磁力片形状目录, 确认 `data/tile_catalog.json` 可以正常加载、13 种形状定义完整 (核心 9 [6 基础 + 3 变体] + 扩展 4, 见 `docs/TILE_CATALOG.md`)。

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
| 难度定级 | `difficulty` 与片数区间不匹配 (D1: 20–28 / D2: 28–48 / D3: 48–75 / D4: 75–110 / D5: 110–180, 见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 2.1 与 2.4 节) | FAIL |
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

### 3.7 物理负例回归 (`physics_fixture_registry` / `physics_negative_*`)

目录: `tests/test_physics_negative/`, 执行器: `tests/test_physics_negative.sh`, 注册表关卡: `tests/test_physics_fixture_registry.sh`

这些夹具是**物理上不成立 (或数据非法) 的反面教材**, 是防止校验器"该拒未拒"回归的核心防线。每个夹具 JSON 旁必须放一个同名 `.expected` sidecar 声明期望:

```
expected_fail_rule=<grep 正则>   # validate 输出必须匹配的错误/警告码
severity=error|warning           # 期望级别
```

执行器按 severity 双向断言:

- `severity=error`: `magtile_app validate` 必须以**非零退出码拒绝**, 且输出匹配 `expected_fail_rule` (防止因 JSON 解析失败等无关原因"碰巧"非零);
- `severity=warning`: validate 必须以**零退出码放行** (Warning 不阻断发布, 见 PHYSICS_RULES.md 第 6 节的人工评审分工), 且输出必须包含匹配的 `[警告]` 行 —— 同时锁住"必须报告"与"不得擅自升级为错误"两个方向的回归。

夹具按目录 glob 自动注册进 CTest (`CONFIGURE_DEPENDS`)。**负例套件不允许悄悄缩水**: `physics_fixture_registry` 关卡断言必备负例清单齐全、每个夹具与 sidecar 一一对应 (双向查孤儿)、正例目录非空 —— 误删夹具或漏写 sidecar 会让该关卡 FAIL, 而不是让对应用例静默消失。

| 夹具 | 缺陷 | 期望 (expected_fail_rule) | 级别 | 规则 |
| --- | --- | --- | --- | --- |
| `below_ground_tile.json` | 立墙底边穿入桌面 (最低顶点 z = -0.2), 实物摆不出来; **修复前的校验器把它当接地片放行** (2026-08 回填) | `below_ground_tile` | Error | R1 前置 |
| `floating_tile.json` | 一片磁力片悬空, 无磁力连接也无支撑路径 | `floating_tile` | Error | R1 |
| `isolated_tile.json` | 错位半搭孤立片, 磁条对不齐吸不住 | `isolated_tile` | Error | R2 |
| `disconnected_assembly.json` | 断开装配: 两座各自接地的孤岛, 教程未分组说明 | `disconnected_assembly` | Warning | R2 |
| `overlapping_tiles.json` | 两片在同一平面上完全重合 | `tile_overlap` | Error | R3 |
| `unstable_cantilever.json` | 连接合法但重心水平投影远超接地区域, 必然倾倒 | `unstable_center_of_mass` | Error | R4 |
| `hanging_chain_overload.json` | 单铰过重: 5 片竖链 (~150g) 全部吊在一条磁力边下, 超出 120g 悬挂预算 | `hanging_chain_overload` | Error | R5 |
| `hanging_chain_long.json` | 5 片 90g 吊挂链未超承重预算, 但超过单边 4 片建议上限 (轻碰整串脱落) | `hanging_chain_long` | Warning | R5 |
| `cantilever_overload.json` | 悬挑超预算: 墙顶外挑 2 片, 力矩 60 g·单位 远超 20 g·单位 铰链预算 (**旧版 R1~R4 全绿**, 是"校验通过但实搭掉落"的典型标本) | `cantilever_overload` | Error | R6 |
| `enclosed_placement.json` | 全封闭盒子完成后才放内部隔断, 手伸不进去 (成品本身合法, 错在顺序) | `enclosed_placement` | Error | R7b |
| `unplaceable_order.json` | 步骤内 tiles_to_add 顺序写反, 上层片放下瞬间无处吸附 | `unplaceable_tile` | Error | R7a |
| `single_point_of_failure.json` | 环形底座上 3 片天线杆全部悬在一条磁力连接上, 撞一下整段脱落 | `single_point_of_failure` | Warning | R8 |
| `no_structural_redundancy.json` | 3.0 单位高的纯树状塔, 没有任何三角桁架/闭合环 | `no_structural_redundancy` | Warning | R8 |
| `unbraced_wall_too_tall.json` | 无桁架纯树状高墙超过 4.0 上限, 错误级一票否决 | `unbraced_wall_too_tall` | Error | R8 |
| `unknown_tile_type.json` | 非法片型: type 为形状目录中不存在的形状, 必须在 JSON 加载层拒绝, 不允许静默降级 | `未知的磁力片形状` | Error | 数据层 |
| `midstep_collapse.json` | 步骤中间态塌陷: 最终成品是 R1~R8 全绿的口字拱架, 但教程先挂远端墙后立支撑柱, 第 6 步完成后的半成品重心失稳会当场倾倒 | `第 6 步完成后.*unstable_center_of_mass` | Error | 中间态 (R4) |

R5~R7 的 4 个历史夹具由 `tools/generate_test_models.py` 生成 (含每个夹具对应的实物失效对照说明), 其余为手工维护。手动执行单个负例 (期望从 sidecar 读取):

```bash
tests/test_physics_negative.sh build/magtile_app data \
    tests/test_physics_negative/floating_tile.json
```

新增负例的方法: 在 `tests/test_physics_negative/` 放入夹具 JSON 与同名 `.expected` sidecar, 并在 `tests/test_physics_fixture_registry.sh` 的必备清单 (`REQUIRED_NEGATIVE`) 中登记, 然后重新配置一次 CMake (`cmake -S . -B build`) 即自动注册; `run_full_qa.sh` 为运行时扫描, 无需额外改动。

回填闭环 (PHYSICS_RULES.md 第 5/6 节): 实物验证或巡检发现"软件放行但实搭失败"的, 一律**先回填负例夹具锁住教训, 再修规则/参数** —— 2026-08 的负例回归加强即按此流程发现并修复了穿地片漏洞 (`below_ground_tile`: 历史版本把 z ≤ 0.02 的顶点一律当作接地, 穿入桌面的片反而被判为稳定接地片放行)。

### 3.8 物理正例 (`physics_positive_*`)

目录: `tests/test_physics_positive/`, 执行器: `tests/test_physics_positive.sh`

负例的**对照组**: 处于承载预算之内的合法结构, `validate` 必须放行 (退出码 0 且输出"可发布"结论), 防止 R5/R6 静力规则矫枉过正、误杀磁力片的常规玩法:

| 夹具 | 结构 | 必须放行的理由 |
| --- | --- | --- |
| `single_cantilever_within_budget.json` | 墙顶水平外挑单片 | 力矩 15 g·单位 < 20 g·单位 预算, 实物立得住, 是常规玩法 |

正例夹具按 `CONFIGURE_DEPENDS` 自动注册, 新增只需把 JSON 放进目录后重新配置。**每放宽/收紧一次 PhysicsConfig 预算参数, 都必须同时补一对正/负例夹具钉住新边界** (见 PHYSICS_RULES.md "调参纪律")。

### 3.9 C++ 回归 (`progress_roundtrip` / `progress_cli_smoke` / `parent_gate` / `age_tts` / `inventory_cli` / `settings_cli_smoke` / `settings_tts_cli`)

进度存档 (SQLite) 的保存/读取往返、完成/收藏/成就、磁力片库存 (`tile_inventory` 表登记/读取、`canBuild`/`missingPieces` BOM 对照、v1 库存 JSON 迁移)、跨连接持久化与重置删除的 C++ 级回归, 以及空库 CLI 冒烟。`age_tts` (`tests/test_age_tts.cpp`) 覆盖年龄分层映射、界面设置 (字号三档/减少动效) 与步骤朗读总开关 (`tts_enabled` 键: 默认开/往返/脏值按开兜底/跨连接持久化) 的 SQLite 契约, 以及 TTS 引擎 stub (NullTts 无叠音语义、系统后端探测与静音降级)。`inventory_cli` (`tests/test_inventory_cli.sh`) 覆盖库存 CLI 全流程: set/show/match、非法输入拒绝、匹配边界 (满配库存全库能搭 / 全 0 库存能搭数为 0 且缺片清单按缺片数升序)。`settings_cli_smoke` 覆盖 `settings set-age` 写入与 `show` 回读; `settings_tts_cli` (`tests/test_settings_tts_cli.sh`) 覆盖 `settings set-tts on|off|1|0` 与 `show` 对 `tts_enabled` 键的读写 —— 默认开、跨进程持久化、非法值以退出码 2 拒绝且不改动存档、终端教程 `--tts` 在总开关关闭时静音降级; 该键与图形版教程页眉朗读开关、Qt 版设置页开关是同一 `progress/ui_settings` 持久化契约 (三端任一处改动, 其余两端下次会话生效)。`inventory_gui_smoke` (`tests/test_inventory_gui.sh`) 覆盖图形录入与 CLI 共库承诺: 无头渲染库存录入界面截图、只浏览不保存则不落盘、`--smoke-inventory` 自动驾驶经图形路径保存后 CLI `inventory show/match` 从同一 SQLite 读到、未指定片型按 0 落库 (「明确没有」); 无显示环境自动降级为链接检查。`parent_gate` (`tests/test_parent_gate.cpp`) 覆盖家长门模块 (SECURITY_AND_PRIVACY.md §6.2 要求单测的三个域): 乘法题生成域、中文大写数字转换/解析与验证逻辑、3 次答错冷却状态机、15 分钟内存会话有效期 (时间经显式注入, 测试不真实等待)。随代码演进持续追加此类用例 —— 注册进 CTest 即自动纳入全量 QA 关卡 3。

### 3.10 GL 渲染冒烟 (`tests/test_gl_smoke.sh`)

```bash
tests/test_gl_smoke.sh          # 默认使用 build/ 下的可执行文件
tests/test_gl_smoke.sh mybuild  # 或指定构建目录
```

脚本自动选择运行方式: 优先 `xvfb-run` (需 `apt install xvfb`), 其次现有 `DISPLAY`; 渲染 5 帧并保存 PPM 截图, 校验截图尺寸与内容非纯色。两者都不可用时退化为链接检查 (确认 `--dev-gui` 代码路径已编译进二进制)。GL/ImGui 图形壳已退役为内部开发工具 (入口 `--dev-gui`, 旧拼写 `--gui` 一期保留为别名并打温和提示, 冒烟含别名回归检查), 用户面向的图形界面见 Qt 版 `magtile_studio_qt`。

手动等价命令:

```bash
xvfb-run -a ./build/magtile_app tutorial data/models/castle_foundation_01.json \
    --dev-gui --frames 30 --screenshot /tmp/magtile.ppm
```

`--frames N` 渲染 N 帧后自动退出, `--screenshot FILE` 在最后一帧保存画面, 两者专为 CI 冒烟测试设计。

图形教程页眉带步骤朗读开关 (UI_UX_SPEC.md §4.2): 读/写进度存档 `tts_enabled` 设置键 (与 Qt 版设置页 / CLI `settings set-tts` 同一契约), 关闭立即停止朗读, 打开立即朗读当前步骤; 自动朗读 (进入/切换步骤即读) 只在 4-6 岁启蒙模式或显式 `--tts` 下开启, 且同样受总开关约束。手动验证:

```bash
./build/magtile_app settings set-age 4 --db /tmp/t.db     # 启蒙模式自动朗读
./build/magtile_app tutorial data/models/castle_foundation_01.json --dev-gui --db /tmp/t.db
./build/magtile_app settings set-tts off --db /tmp/t.db   # 总开关关闭 -> 全端静音
```

### 3.11 逐步装配质检 (`step_assembly_gate`)

脚本: `tests/test_step_assembly.py <models目录或模型文件...> [--catalog tile_catalog.json]`

**逐片零差错**承诺 (P1~P8) 的数据层关卡, 承诺的精确定义与规模化方案见 [MODEL_QUALITY.md](MODEL_QUALITY.md)。教程是逐片摆放的, 本关保证 4 万次放置指令 (500 模型规划规模) 中没有一片错乱:

| 检查 | 判定 | 结果 |
| --- | --- | --- |
| 1 (P1) | `final_assembly` 中片 id 重复 | FAIL |
| 2/3 (P2/P3) | 某片被多个步骤放置 (含同一步内重复), 或第 K 步的片已在第 J < K 步出现 | FAIL |
| 4 (P4) | `highlight_tiles` 引用了本步才放 / 尚未放 / 不存在的片 | FAIL |
| 5 (P6) | `final_assembly` id 集合 ≠ 全部 `tiles_to_add` id 集合 (孤儿片 / 幽灵片), 或 `total_pieces` 不符 | FAIL |
| 6 (P6) | 片数据损坏: type 未登记 / position・rotation 非 3 维有限数值 / 两片位姿完全相同 / 步骤内嵌数据与成品漂移 | FAIL |
| 7 (P7) | 空间连续性: 某片放下瞬间既不接地 (z ≤ 0.02) 也没有磁力边与已放置结构吸合 (容差 0.02) | FAIL |
| 8 (P8) | `step_number` 非 1..N 严格连续 | FAIL |

几何复算 (旋转 R = Rz·Ry·Rx、磁力边吸合、接地) 与 C++ 端严格一致, 实现在 `tests/magtile_geom.py`。纯数据层, 不依赖构建产物, 全库秒级; 失败输出人类可读差异明细 (哪一步、哪一片、期望什么、实际什么)。

```bash
python3 tests/test_step_assembly.py data/models
```

### 3.12 模型库唯一性 (`library_uniqueness_gate`)

脚本: `tests/test_library_uniqueness.py <models目录或模型文件...> [--catalog tile_catalog.json]`

批量克隆检测 (承诺 P10)。对全库模型两两计算结构签名相似度 (算法见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 5.2 节): `sim = 0.6 × WL 连接图指纹 Jaccard + 0.25 × 片形直方图余弦 + 0.15 × 步骤节奏 DTW`。WL 指纹对颜色、全局平移/旋转、id 命名不敏感——换色与镜像翻版无法规避。

| 判定 | 结果 |
| --- | --- |
| 任意一对模型 sim > 0.85 | FAIL (换皮克隆, 拒绝入库) |
| 0.70 < sim ≤ 0.85 | WARN (边界案例送人工比对) |
| 同主题 (`content_meta.series`) + 同主技法 (`technique_tags.primary`) 的模型 > 2 个 | WARN (组合过度开采) |

签名每模型只计算一次, 两两比对为纯字典运算; 500 模型 (124,750 对) 在单机分钟级以内, 报告只展开可疑对与全库最相似对。

```bash
python3 tests/test_library_uniqueness.py data/models
```

### 3.13 L3 实物复核缺口报告 (`tools/list_physical_pending.py`)

软件全绿不替代实物复核: difficulty ≥ 4 的模型必须按 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md) 完成实物搭建复核 (敲击/提起/记录模板), 通过后在模型 `content_meta` 写入 `physical_verified` / `physical_verified_at` / `physical_notes` 三个可选字段 (schema 见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 5.1 节), 或落盘 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 5.2 节的旁车验证文件 (内容哈希绑定, 模型改动自动作废)。

```bash
python3 tools/list_physical_pending.py data/models                    # 人类可读清单
python3 tools/list_physical_pending.py data/models --json             # 机器可读
python3 tools/list_physical_pending.py data/models --fail-on-pending  # 发布门禁模式
```

全量 QA 中该关卡**只报告未复核数量, 不阻断 CI** (实物复核是线下人工流程, 进度不应卡住代码/内容合入); 发布打包前可用 `--fail-on-pending` 作为终防线 (一键入口: `tools/run_release_gate.sh --fail-on-pending`, 见第 5 节)。

复核排产按 **V1 上架优先抽样包**先行: `tools/physical_sample_pack.py` 用确定性规则 (免费层 D4+ 全数 + D5 全数 + 付费 D4 高片数按主题补足, 约 10 个) 生成可签核抽样清单 [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md), 并为真人桌边核对打印每个模型的备料 BOM 与逐步片型摘要; `--fail-on-missing-sample` 在抽样包存在未复核模型时退出码 1 (默认仅报告), 判定口径与 `list_physical_pending.py` 同源。

```bash
python3 tools/physical_sample_pack.py                          # 抽样清单 + 逐模型 BOM 摘要
python3 tools/physical_sample_pack.py --fail-on-missing-sample # 门禁挂接模式
```

### 3.14 免费层清单对齐核验 (`tools/verify_free_tier.py`)

免费层在三条分发链路上各有一份"清单": 模型 `tags` 的 `免费` 标签 (运行时事实来源)、Windows starter 打包清单 `platforms/windows/packaging/starter_models.txt` (打包投影)、Android APK (全量打包, 靠标签生效)。本工具固化 [FREE_TIER_MANIFEST.md](FREE_TIER_MANIFEST.md) 的对齐决议: **免费标签数恰好 30 + 免费层全部只用核心 9 片型 + starter 清单与标签集合相等**, 任一失败退出码 1, 不一致时逐条列出两侧差异。

```bash
python3 tools/verify_free_tier.py                # 仓库默认路径, 日常裸跑
MAGTILE_FREE_TIER_CHECK=1 tests/run_full_qa.sh   # 随全量 QA (可选关卡 10)
```

全量 QA 中默认跳过 (免费层清单只在选品换血时变化, 日常内容合入不受它约束), **发布打包前必须开启** (一键入口: `tools/run_release_gate.sh`, 见第 5 节); 片型红线本身另有常开关卡 9 兜底 (`check_core5_usage.py --strict`)。换血流程见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §2.5.1。

### 3.15 Qt 界面测试 (`qt_backend_bridges` / `qt_gui_smoke`)

仅在 `-DMAGTILE_BUILD_QT=ON` 时注册 (默认 OFF 的构建完全不受影响), 两者都**无需显示环境**:

- `qt_backend_bridges` (`tests/test_qt_backends.cpp`): QT-2 两座后端桥的 C++ 单测。`SettingsBackend` 的字号三档 / 减少动效 / 年龄段 SQLite 往返、跨实例持久化、非法值忽略, 以及**与 GL 版/CLI 的共库契约** (Qt 桥写入的键 progress 层原样读回, 反向亦然); `ParentGateBackend` 的出题 / 答对开会话 / 答错温和提示 / 3 次答错进冷却 (冷却期拒答) / 锁定会话。
- `qt_gui_smoke` (`tests/test_qt_smoke.sh`): offscreen 平台无头加载 QML 多路径连跑 (完整路径清单以脚本自身为准) —— 默认启动 (首页)、`--parent-gate` 深链 (家长门界面)、`--smoke-parent-flow` 自动驾驶 (家长门 → 提交标准答案过门 → 家长中心 → 设置 → 订阅逐页实例化, 全程无误 `Main.qml` 才置 `smokeParentFlowOk`, 否则进程非零退出)、`--smoke-complete-model` 完成链路 (庆祝页 + 存档 `completed_at` 断言) 等; 全程输出扫描 QML 运行时错误 (ReferenceError/TypeError) 一票否决。`--smoke-open-progress` 进度页深链由 `tools/run_e2e_smoke.sh` 的 E2E-12a 项覆盖 (见第 8 节)。

```bash
cmake -S . -B build-qt -DMAGTILE_BUILD_QT=ON
cmake --build build-qt -j
ctest --test-dir build-qt -R "qt_backend_bridges|qt_gui_smoke" --output-on-failure
```

### 3.16 教程步进性能基准 (`bench_tutorial_step`)

商用承诺: 大模型 (100+ 片) 的教程步进不能卡死。`tests/bench_tutorial_step.cpp` 编译出的 `magtile_bench_tutorial` 对**小/中/大三个代表模型** (beach_hut_01 44 片/12 步、castle_foundation_01 72 片/16 步、skyscraper_01 122 片/26 步, 覆盖全库 44~122 片的完整规模区间) 逐步计时 `TutorialEngine` 的完整"每步工作量" —— `nextStep` / `goToStep` 导航加上渲染层每步都要调用的场景查询 (`currentStep` / `visibleTiles` / `tilesAddedThisStep` / `highlightTiles` / `progress`), 与 Qt `TutorialViewport::rebuildSceneTiles` 及 Android JNI 每步实际执行的引擎调用一致 (进度落盘 SQLite 与 GPU 上传不在本基准范围, 分别由 `progress_roundtrip` 与 GL 冒烟覆盖)。**顺序走查**与**钟摆远跳** (goToStep 在 0 与最后一步间来回, 对应进度页"继续搭建"/拖动步骤条的最坏情况, 每次都重建完整可见集) 两种导航模式都测, 输出每步中位 ms 与全样本 P95。

判定: 任一步中位数或 P95 超出预算即**退出码 1** (性能回归)。预算默认 **500 ms/步** —— 刻意温和的上限, 目的是抓"卡死/量级劣化"而不是抓噪声 (参考基线为微秒级, 见下)。基准纯 CPU, 不依赖 GPU/显示环境, 无 GPU 的 CI 正常执行; 负载极不稳定的共享 runner 可用 `MAGTILE_BENCH_BUDGET_MS` 放宽预算, 或 `MAGTILE_BENCH_SKIP=1` 跳过 (退出码 77, ctest 记 SKIP 而非 FAIL)。

参考基线 (2026-08, Release, Linux x86_64 CI 容器): skyscraper_01 (122 片) 最慢步中位 **0.0034 ms** / P95 0.0033 ms; castle_foundation_01 (72 片) 0.0023 / 0.0023 ms; beach_hut_01 (44 片) 0.0013 / 0.0013 ms —— 距预算约 5 个数量级。引擎每步查询复杂度为 O(已放置片数), `tilesUpToStep` 已按成品片数预留容量避免逐步扩容。

```bash
ctest --test-dir build -R bench_tutorial_step --output-on-failure  # 随 CTest 全量回归
python3 tools/bench_tutorial_step.py --build-dir build             # 独立入口 (完整每步耗时表)
python3 tools/bench_tutorial_step.py --budget-ms 50 \
    --models data/models/skyscraper_01.json                        # 自定义模型/预算
MAGTILE_TUTORIAL_BENCH=1 tests/run_full_qa.sh                      # 随全量 QA (可选关卡 17)
```

## 4. 持续集成 (CI)

`.github/workflows/qa.yml` 在**每次 push** 时于 Ubuntu runner 上执行 `tests/run_full_qa.sh` 全流程:

- 安装 X11 开发库 (FetchContent 源码构建 GLFW) 与 xvfb + Mesa (llvmpipe 软件渲染), 因此 CI 中 GL 冒烟跑的是**真渲染 + 截图校验**, 不是降级检查;
- GLFW/ImGui 源码按 CMakeLists 哈希缓存, 不重复克隆;
- 失败时自动上传各关卡分项日志 (`qa-stage-logs` 工件);
- 本地与 CI 跑的是同一个脚本: 提交前先 `tests/run_full_qa.sh` 跑绿, CI 不会有意外。

发布专项关卡 (可选关卡 10/15) 不在每次 push 的 qa.yml 内, 由手动触发的 `.github/workflows/release-gate.yml` 补齐, 见第 5 节。

## 5. 发布门禁 (Release Gate)

日常 push CI 为控制流水线时长默认跳过两道发布专项关卡 (可选关卡 10 免费层清单对齐、15 strict 全库巡检)。**内容批量合入后与发布打包前**必须用发布门禁把它们补齐, 一键入口:

```bash
tools/run_release_gate.sh              # 快检档: 三道发布专项 (默认构建目录 build)
tools/run_release_gate.sh --full       # 发布档: 16 关全量 QA + 发布专项一次跑全
                                       #   = MAGTILE_FREE_TIER_CHECK=1 MAGTILE_STRICT_AUDIT=1 tests/run_full_qa.sh
tools/run_release_gate.sh --fail-on-pending   # 终防线: D4+ 实物待复核非空即红灯
tools/run_release_gate.sh --report docs/reports/STRICT_AUDIT_$(date +%F).md  # 附带 strict 巡检 Markdown 报告
tools/run_release_gate.sh --dry-run    # 只打印将执行的关卡与命令
tools/run_release_gate.sh --help       # 完整用法
```

### 5.1 门禁关卡

| 关卡 | 工具 | 阻断性 | 依据 |
| --- | --- | --- | --- |
| 免费层清单对齐核验 | `tools/verify_free_tier.py` (3.14 节) | 阻断 | 免费标签恰 30 + 全 core-9 + 与 starter 打包清单一致, 决议见 [FREE_TIER_MANIFEST.md](FREE_TIER_MANIFEST.md) |
| 弱磁严格档全库巡检 | `tools/run_strict_audit.sh` | 阻断 | strict 零警告审计 + 逐步装配质检 (缺 `magtile_app` 时自动构建), 政策见 [STRICT_PHYSICS_AUDIT.md](STRICT_PHYSICS_AUDIT.md) |
| L3 实物复核缺口报告 | `tools/list_physical_pending.py` (3.13 节) | 报告型, 与 run_full_qa.sh 关卡 16 同一口径; `--fail-on-pending` 时升级为硬闸门 | 规程见 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md) |

退出码与 run_full_qa.sh 同一约定: 0 = 全部阻断关卡通过, 1 = 存在失败关卡, 2 = 环境/参数不满足; 结尾输出 PASS/FAIL 分项摘要, 失败时保留分项日志目录。

可选挂钩: 在 `--fail-on-pending` 全集终防线之前, 可先挂 `tools/physical_sample_pack.py --fail-on-missing-sample` 作为「V1 抽样包先行」中间闸门 (抽样包定义与签核表见 [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md), 3.13 节) —— V1 上架签核至少要求抽样包全绿, 当前默认不阻断。

### 5.2 何时跑哪一档

| 时机 | 命令 | 说明 |
| --- | --- | --- |
| 内容批量合入后 (一次合入多个模型 / 免费层选品变动) | `tools/run_release_gate.sh` | 快检: 日常 CI 跳过的两道专项 + 待复核缺口盘点 |
| 发布打包前 (Windows / Qt 桌面 / Android 出包) | `tools/run_release_gate.sh --full` | 全量 QA 与发布专项一次跑全, 全绿才进入打包手册流程: [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) / [../scripts/package_windows.md](../scripts/package_windows.md) |
| 正式对外发布 (终防线) | 上一档追加 `--fail-on-pending` | D4+ 模型必须全部完成实物复核 (3.13 节口径) |
| 上架商用验收 (用户路径) | `tools/run_e2e_smoke.sh --strict` | 核心用户路径 E2E 自动子集 (第 8 节); 人工路径按 [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) 逐条打钩 |

CI 侧: `.github/workflows/release-gate.yml` 仅 `workflow_dispatch` 手动触发 (发布门禁不拖慢日常 PR —— push/PR 仍只跑 qa.yml), Actions 页可选 `mode` (full / gate-only) 与 `fail_on_pending`, 跑的与本地是同一个脚本。

## 6. 如何新增一个模型 (必须全绿才能入库)

1. **生成或搭建模型 JSON**: 用编辑器/生成工具产出 `data/models/<model_id>.json`, BOM 等元数据由工具写入 `content_meta` (勿手写);
2. **对照内容策略自检**: 难度与片数区间匹配 (CONTENT_STRATEGY.md 2.1 节)、≥ 3 种片形、≥ 2 个 Z 层、步骤 1~12 片/步、每步中文说明;
3. **重新配置一次 CMake** (`cmake -S . -B build`): `validate_<模型名>` / `tutorial_<模型名>` 用例自动注册 (glob 是 `CONFIGURE_DEPENDS`, 但新文件仍需触发一次配置);
4. **跑全量 QA**: `tests/run_full_qa.sh`, 新模型必须让全部关卡保持绿灯 —— 物理 R1~R8 (含每个中间步骤)、体量门槛、逻辑质检、教程完整性一个都不能少;
5. **有 Warning 先处理**: `disconnected_assembly` 等 Warning 须在教程文案中有对应分组说明; R8 结构冗余警告的点位建议按 PHYSICS_RULES.md 加固;
6. **高难模型走实物层**: difficulty ≥ 3 按 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 完成实物验证 (T3+ 硬性要求), difficulty ≥ 4 另需目标年龄段儿童测试; 作者级逐步实搭规程与结论落盘方式见 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md), 待复核清单由 `tools/list_physical_pending.py` 跟踪;
7. **提交**: CI 会在 push 时把第 4 步整套重跑一遍, 红灯不允许合入。

## 7. 内容入库标准 (Definition of Done)

一个模型 JSON 只有同时满足以下条件才允许合入 `data/models/`:

1. `validate_<模型名>` 通过 (物理 R1~R8, 含全部中间步骤与逐片放置模拟);
2. `all_models_quality_gate` 通过 (≥ 40 片);
3. `anti_trivial_models` 通过 (≥ 3 种形状、≥ 2 个 Z 层、存在立置片);
4. `model_logic_gate` 通过 (步骤粒度、中文说明、教程对账、难度区间、BOM 一致);
5. `step_assembly_gate` 通过 (逐片零差错 P1~P8: id 唯一、每片恰好放置一次、高亮只引用已放置片、无孤儿/幽灵、逐片空间连续, 见 [MODEL_QUALITY.md](MODEL_QUALITY.md));
6. `library_uniqueness_gate` 通过 (与全库任何模型的结构签名相似度 ≤ 0.85);
7. `tutorial_integrity` 通过 (步骤恰好覆盖全部磁力片, 教程引擎实跑成功);
8. 按难度分级完成实物验证要求 (BUILD_VERIFICATION.md 第 2 节; 执行规程 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md)); D4+ 复核通过后写入 `content_meta.physical_verified` 三字段或旁车验证文件, 否则一直挂在 `tools/list_physical_pending.py` 的待复核清单上。

## 8. 核心用户路径 E2E 冒烟 (上架验收)

前面各节保证"代码不退化、内容搭得起来"; 上架前还要以**用户视角**把
完整路径 (安装 → 浏览 → 搭建 → 庆祝 → 付费边界) 走一遍。路径清单、
平台与优先级 (P0/P1)、Auto/Manual 标注统一维护在
[E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md); 其中已自动化的子集一键跑:

```bash
tools/run_e2e_smoke.sh                 # 默认: SKIP 不阻断 (日常回归)
tools/run_e2e_smoke.sh --strict        # 验收档: 任何 SKIP 也按失败处理 (上架签核)
tools/run_e2e_smoke.sh --skip-android  # 无 NDK 环境跳过 Android 项
tools/run_e2e_smoke.sh --help          # 完整用法
```

自动子集当前覆盖 (矩阵编号见 E2E_TEST_MATRIX.md 第 1 节):

- **E2E-01a** CLI 启动冒烟: `magtile_app catalog` 目录加载, 13 种片型齐全;
- **E2E-11a** 免费层清单对齐: `tools/verify_free_tier.py` (3.14 节同一工具);
- **E2E-11b** CLI 免费筛选对账: `library --free-only` 数量与 starter 打包
  清单一致 + 抽样免费模型在列 + 目录元数据对账通过;
- **E2E-06a** CLI 免费模型教程步进: 教程引擎全程步进, 放置片数与
  `total_pieces` 对账 (免费用户"打开就能搭完"的最短闭环);
- **E2E-QT** Qt 无头冒烟: `tests/test_qt_smoke.sh` 全部路径 (3.15 节);
- **E2E-12a** Qt 进度页深链: `--smoke-complete-model` 造非空存档后
  `--smoke-open-progress` 实例化进度页/成就墙数据源, QML 运行时错误
  一票否决;
- **E2E-14a** Android JNI 符号断言: NDK 交叉编译 `libmagtile_core.so` 并
  断言 JNI 符号齐全 —— 符号清单**运行时解析自 CI `android.yml`**, 与
  流水线口径自动同步; 无 NDK 环境自动 SKIP (CI 由 `android.yml` 兜底)。

退出码: 0 = 全部执行项通过 (默认档 SKIP 不算失败, `--strict` 下算);
1 = 存在失败项; 2 = 环境/参数不满足。缺 `magtile_app` 时自动构建;
缺 `magtile_studio_qt` 时尝试自动构建, 环境无 Qt6 则记 SKIP。

与发布门禁的关系: `run_release_gate.sh` 管**软件/内容/实物**三层质量,
`run_e2e_smoke.sh` 管**用户路径**健康度, 上架签核两者都要全绿, 人工侧
再按 E2E_TEST_MATRIX.md 第 3 节的签核规则补齐 Manual 项。

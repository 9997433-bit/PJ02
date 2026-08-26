# 发布门禁状态报告 (Release Gate Status)

- 生成时间: 2026-08-26 03:40 UTC
- 基线提交: `b31e933` (`cursor/magtile-studio-foundation-a95b`, 内容库 250 模型; 自上一基线 `8ee2fc7` 以来为纯内容排产批 —— D1 入门批 ×5 共 20 个模型、D5 大师批 +5 个模型 (`b212b74` 双模型 + `20d9349` 三模型), 按 B1 配额置换退役 25 个 D3, 缩略图同步再生 —— 未触碰 C++ 引擎源码)
- 构建配置: CMake Release, `/tmp/wt-risk-report/magtile-studio` worktree (@ `b31e933`, 工作区干净) 增量构建 → **退出码 0**
- 执行命令:
  1. `tools/run_release_gate.sh --full --fail-on-pending` → **退出码 1** —— 两个门禁关卡均红: 全量 QA 5 个子关卡失败 (见 §3), L3 实物复核 51 个待复核在 `--fail-on-pending` 硬闸门口径下红灯 (见 §4)
  2. `tools/check_v1_readiness.sh --quick` → **退出码 1** —— 25 项: 14 PASS / 2 FAIL / 9 SKIP, P0 失败仅 R6/R7 (实物复核, 用户侧)
- 口径变化 (与上一基线 `8ee2fc7` 的差异):
  - **难度配额守卫 (QA 关卡 41, strict) 首次转绿**: D1 20/20、D5 6/6 双双达标, D3 冻结解除 (上一基线为预期红)
  - 本次带 `--fail-on-pending`, L3 从报告型转为硬闸门口径 (上一基线未带)
  - 全量 QA 关卡表仍 22 关 / 42 子关卡, CTest 仍 556 项, `--full` 档发布专项环境变量仍 4 个全开 —— 门禁语义本身无变化; 红项从「1 个预期红」变为「5 个内容侧真红」(见 §3)

## 1. 结论速览

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 难度配额守卫 (QA 关卡 41, strict) | **GREEN (新)** | D1 20 (8.0%) / D2 23 (9.2%) / D3 156 (62.4%) / D4 45 (18.0%) / D5 6 (2.4%), 解冻线 D1 ≥ 20 与 D5 ≥ 6 同时达标, **D3 冻结解除** (详见 §2) |
| 全量 QA (42 子关卡: 34 过 3 可选跳过 5 失败) | **FAIL** | CTest 553/556 (3 失败: `all_models_quality_gate` / `anti_trivial_models` / `model_logic_gate`); 关卡 4 全量质检与关卡 5 反平凡各拒 20 个新 D1 模型 (片数 20~27 < 40 下限); 关卡 6 逻辑质检拒 2 个新 D5 (片数低于 D5 区间 [110, 180]); 关卡 35 strict 巡检 D4+ 抖动阶段 2 个新 D5 失败 —— 全部为本批新内容引入, 明细见 §3。其余全绿: 逐步装配 250/250, 唯一性 31125 对 0 警告, strict 静态档全库 249 过 1 豁免 0 警告, 免费层 30/30, 教程完整性过, 系列归类矩阵内 201 + 矩阵外 49 (缺失/非法 0), 儿童文案 301 文件 8556 段全绿; 耗时 94s |
| L3 实物复核缺口 (硬闸门, `--fail-on-pending`) | **FAIL (预期)** | 扫描 250 模型, D4+ 51 个待复核 0/51 (45 D4 + 6 D5; 较上基线 46 增加 5 个新 D5) —— 用户侧人手实搭, 非软件缺陷 (§4) |
| V1 就绪快检 (`--quick`) | **FAIL (预期)** | 14 PASS / 2 FAIL / 9 SKIP; P0 失败仅 R6 (实物抽样包复核缺口) 与 R7 (D4+ 实物复核清零), 与 L3 同源; R1/R2/R3/R8~R16/R18 全过, R4/R5/R17 与 M1~M6 按 `--quick` 口径跳过 |

**工程侧判定: 路径 B 配额解冻目标已达成 —— 难度配额守卫 strict 档正式转绿, D3 冻结解除。** 但解锁配额的内容批自身引入 5 个软件侧真红 (§3): 20 个新 D1 模型全部低于全库 40 片质检下限, 2 个新 D5 模型低于 D5 片数区间且 2 个新 D5 抖动仿真失败。与此前「预期红」不同, 这些是须内容返工或治理决策的实质缺陷, `--full` 档在修复前无法全绿。L3 待复核 51/51 仍为用户侧实搭事项 (排产单: `docs/reports/PHYSICAL_REVIEW_QUEUE.md`, 注意 5 个新 D5 尚未纳入既有排产/风险报告, 需同步刷新)。

## 2. 难度配额守卫转绿 (D3 冻结解除)

`--full` 档强制开启 `MAGTILE_DIFFICULTY_QUOTA=1`, QA 关卡 41 以 `check_difficulty_quota.py --strict` 运行, 本次实跑分布与判定:

| 难度 | 数量 | 占比 | 解冻线 | 较上基线 |
| --- | --- | --- | --- | --- |
| D1 (入门) | 20 | 8.0% | ≥ 20, **已达标** | +20 (批 1~5, `fdc4557`/`8e16b4c`/`f8b0167`/`85bd8ca`/`b31e933`) |
| D2 (进阶) | 23 | 9.2% | — | 不变 |
| D3 (熟练) | 156 | 62.4% | **冻结解除** | −25 (B1 配额置换退役) |
| D4 (挑战) | 45 | 18.0% | — | 不变 |
| D5 (大师) | 6 | 2.4% | ≥ 6, **已达标** | +5 (`b212b74` ×2, `20d9349` ×3) |

D1 20 ≥ 20 且 D5 6 ≥ 6, strict 档以退出码 0 通过, 关卡 41 绿灯; 冻结期批次评审 `--batch` 对新增 D3 的拦截随之失效 (恢复常规评审口径)。总量保持 250 (+25 新增 / −25 退役)。

## 3. 本批新增软件侧红项 (须内容返工或治理决策)

上一基线 `8ee2fc7` 上模型库 250/250 全过 (validate/反平凡/逻辑/逐步装配/教程), 本批 5 个红项全部由新内容引入:

### 3.1 20 个新 D1 模型低于全库 40 片下限 (QA 关卡 4 + 5, CTest #514 `all_models_quality_gate` / #550 `anti_trivial_models`)

新入库的 20 个 D1 模型片数全部在 20~27 片 (入门难度按设计做小), 而全库质检与反平凡检查执行 ≥ 40 片统一下限, 两关各拒 20 个:

`castle_guard_post_01` (20) / `cup_coaster_01` (24) / `duckling_pond_01` (20) / `farm_wagon_01` (20) / `festival_gate_01` (22) / `garden_pavilion_01` (26) / `harbor_ferry_01` (20) / `ladybug_01` (21) / `magic_pinwheel_mill_01` (21) / `marble_starter_slope_01` (21) / `napkin_holder_01` (22) / `pencil_cup_01` (24) / `phone_cradle_01` (20) / `pinwheel_mosaic_01` (21) / `plank_bridge_01` (27) / `rainbow_zigzag_wall_01` (20) / `seedling_greenhouse_01` (22) / `snack_tray_01` (21) / `space_probe_01` (23) / `trilithon_ring_01` (23)

**冲突本质**: D1 入门定位 (低片数) 与全库 40 片下限互斥。两条出路任选其一, 均须走正式评审而非静默放宽: ① 内容返工 —— 将 20 个 D1 扩到 ≥ 40 片同时保持入门装配难度; ② 治理决策 —— 在质检/反平凡闸门为 D1 增设片数豁免带 (联动 CONTENT_STRATEGY.md 2.1 节 D1 区间定义与 CTest 双闸门), 决策记录落盘后同步 docs/TESTING.md。

### 3.2 2 个新 D5 模型低于 D5 片数区间 [110, 180] (QA 关卡 6, CTest #551 `model_logic_gate`)

| 模型 | 实际片数 | 要求 | 处置 |
| --- | --- | --- | --- |
| `giant_ferris_wheel_01` | 102 | [110, 180] | 扩规模至 ≥ 110 片或降难度 (降级将破坏 D5 ≥ 6 解冻线, 须补新 D5) |
| `marble_grand_cascade_01` | 87 | [110, 180] | 同上 |

### 3.3 2 个新 D5 模型 strict 抖动仿真失败 (QA 关卡 35 弱磁严格档巡检)

静态 strict 档全库 250 过 (249 过 + 1 白名单豁免 `suspension_bridge_01`, 零未豁免警告); 红项集中在 D4+ 抖动阶段 (蒙特卡洛 ±1.5mm / ±2.0°, 50 轮): 51 个 D4+ 中 49 过 2 失败 ——

- `giant_ferris_wheel_01`: `validate --jitter` 非零退出 (与 §3.2 同模型, 返工时一并处理)
- `strait_rainbow_bridge_01` (110 片, 片数区间达标): 50 轮中 12 轮违反 `enclosed_placement` —— 第 25 步磁力片 `hge_n_c1` 在抖动下被完成结构完全包围, 须按 docs/PHYSICS_RULES.md R9 节把该片移到封闭结构合拢之前放置

既有 R9 修复保持有效: `ball_run_tower_01` / `marble_run_spiral_01` / `rainforest_canopy_01` 在本次 D4+ 抖动阶段全绿 (`lego_style_house_01` 为 D3 不在 D4+ 巡检范围, 本次未带 `--l2` 未单独复验)。

## 4. L3 实物复核缺口 (硬闸门红, 预期)

本次带 `--fail-on-pending`, L3 走硬闸门口径: 扫描 250 模型, D4+ 51 个全部待复核 (45 D4 + 6 D5), 门禁关卡 2 以退出码 1 结束。`check_v1_readiness.sh --quick` 对应 R6/R7 两项 P0 FAIL —— 用户侧人手实搭事项, 待按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭后回填 `physical_verified`。注意: 较上基线新增 5 个 D5 待复核 (`giant_ferris_wheel_01` / `marble_grand_cascade_01` / `stellar_launch_gantry_01` / `strait_rainbow_bridge_01` + `royal_citadel_01` 批内新增), 既有排产/风险文档 (`PHYSICAL_REVIEW_QUEUE.md` / `PHYSICAL_FAMILY_PACK.md` / `PHYSICAL_RISK_REPORT.md`, 均为 46 个基线) 需刷新至 51 个口径; 其中 2 个新 D5 尚有 §3 软件侧红项, 建议返工完成后再排实搭。

## 5. 下一步

1. **内容返工 (P0, 软件侧)**: 修复 §3 三组红项 —— 2 个 D5 扩规模至 ≥ 110 片并通过 `validate --profile strict --jitter 50`, `strait_rainbow_bridge_01` 第 25 步封闭放置重排; 20 个 D1 的 40 片下限冲突按 §3.1 两条出路走评审决策 (修复期间 `--full` 档保持红灯, 不许占位交差)
2. **排产文档刷新**: L3 队列/家族包/风险报告从 46 基线刷新至 51 (含 5 个新 D5), 实物排产顺延
3. **用户侧**: 按 `docs/USER_HANDOFF.md` §4 完成实物/行政/实机/沙盒验收 (L3 待复核 51 清零)
4. **正式出包前**: 以 `tools/run_release_gate.sh --full --l2 --fail-on-pending` 复跑终防线 (须 §3 红项清零 + L3 清零后方能全绿; 难度配额守卫已转绿, 维持 D1 ≥ 20 / D5 ≥ 6 即可)

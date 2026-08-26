# 发布门禁状态报告 (Release Gate Status)

- 生成时间: 2026-08-26 01:50 UTC
- 基线提交: `8ee2fc7` (`cursor/magtile-studio-foundation-a95b`, 内容库 250 模型; 自上一基线 `b369bad` 以来均为文档/工具/治理批 —— 路径 B1 配额置换与退役工具、实物排产队列导出、软著源程序导出工具、工程天花板/阻塞项决策单/路径 A 开工单等文档、QA 可选关卡 22 矩阵快照挂钩、Android DC7 备份规则 —— 未触碰 `data/models` 与 C++ 引擎源码)
- 构建配置: CMake Release, `/tmp/wt-gate-clean-40b8/magtile-studio` 干净 detached worktree (@ `8ee2fc7`) 全新构建 → **退出码 0** (约 39s; 干净 worktree 用于隔离并行内容排产工作区的未提交文件, 保证严格按 250 模型已提交基线取数)
- 执行命令:
  1. `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4` → **退出码 0**
  2. `tools/run_release_gate.sh --full --l2` → **退出码 1 (预期红)** —— 唯一失败子项为 QA 关卡 41 难度配额守卫 strict 档 (D3 冻结生效期间按设计红灯, 见 §4); 本次基线刷新未加 `--fail-on-pending`, L3 走报告型口径 (红色状态见下表与 §3)
- 门禁口径 (与上一基线 `b369bad` 的差异):
  - 全量 QA 关卡表 21 关 → **22 关** (新增可选关卡 22 矩阵进度快照刷新 `MAGTILE_MATRIX_REPORT=1`, 日常与 `--full` 档默认跳过, 门禁语义不变; docs/TESTING.md 3.19)
  - 子关卡计数 41 → **42** (38 过 3 可选跳过 1 预期红; 新增跳过行即关卡 22)
  - `--full` 档发布专项环境变量保持 **4 个全开**, CTest 保持 **556** —— 本批无新增闸门, 无软件侧口径变化

## 1. 结论速览

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 全量 QA (42 子关卡: 38 过 3 可选跳过 1 预期红) | **PASS (软件侧)** | CTest 556/556, 模型库 250/250 全过 (validate/反平凡/逻辑/逐步装配/教程), 唯一性 31125 对 0 警告, strict 零警告审计 (249 过 1 豁免 0 警告 0 失败), 免费层 30/30 对齐, 系列归类机检矩阵内 176 + 矩阵外 74 (缺失/非法 0), 儿童文案 301 文件 8874 段全绿; 唯一红项为关卡 41 难度配额守卫 (预期, 见下), 耗时 89s |
| L2 抗扰动档 (D4+ jitter 50) | **PASS** | 46/46 D4+ 模型 50/50 轮全绿 (`run_strict_audit.sh --jitter-only --jitter require` 实跑, 32s) |
| L3 实物复核缺口 | **RED (预期)** | 扫描 250 模型, D4+ 46 个待复核 0/46 —— 用户侧人手实搭, 非软件缺陷; 本次未加 `--fail-on-pending`, 该项按报告型记录, 正式出包终防线仍会红 |
| 难度配额守卫 (QA 关卡 41, strict) | **RED (预期)** | D3 冻结生效: D1 0/20, D5 1/6 (D2 23 / D3 181 / D4 45); 解冻线 D1 ≥ 20 且 D5 ≥ 6 两项同时达标, D1/D5 补齐入库前 `--full` 档按设计保持红灯, 不许占位交差 (docs/TESTING.md 3.19) |

**工程侧判定: 软件门禁在 8ee2fc7 基线上保持上限状态, 与上一基线 `b369bad` 结论逐项一致。** 本批 21 个提交均为文档/工具/治理载体 (未增删模型、未改引擎), 未引入任何软件侧回归; 本次 `--full --l2` 总退出码 1 完全来自难度配额守卫这一预期红。两个红项均为预期的治理/线下状态而非软件缺陷: L3 待复核 46/46 按设计须用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭清零 (排产单: `docs/reports/PHYSICAL_REVIEW_QUEUE.md`, 缩减流程见 `docs/USER_HANDOFF.md` §4.3); 难度配额红灯须内容排产补齐 D1/D5 后自动转绿 (§4, 置换/退役路径工具已就位: `tools/plan_quota_substitution.py` / `tools/retire_models.sh`)。

## 2. R9 抖动敏感模型 —— 修复保持有效

| 模型 | 修复提交 | 手法 | 8ee2fc7 基线复验 |
| --- | --- | --- | --- |
| `ball_run_tower_01` | `8d07fe5` / `5b915a0` | 西线转角外缘双层门式立柱 (94 片) | 50/50 全绿 (L2 档内) |
| `marble_run_spiral_01` | `114c154` | 三块转角台下挂直角三角斜撑 (80 片) | 50/50 全绿 (L2 档内) |
| `rainforest_canopy_01` | `2ffc06e` | 树冠平台板根斜撑 (90 片) | 50/50 全绿 (L2 档内) |
| `lego_style_house_01` | `24fd0ec` | 第 14 步补片顺序重排 (封闭前放置) | 50/50 全绿 (D3, L2 档外单模型 `validate --profile strict --jitter 50` 单独复验) |

存量 46 个 D4+ 全部保持全绿 (含 `stonehenge_01` D4 91 片), 与 b369bad 基线结果一致。

## 3. L3 实物复核缺口

扫描 250 模型, D4+ 46 个全部待复核 (与 b369bad 基线同一清单, 本批为纯文档/工具批未增减模型)。`check_v1_readiness.sh --quick` 对应 R6/R7 两项 P0 FAIL —— 预期状态, 待用户实搭后回填 `physical_verified` 标记 (本次同场刷新见 `docs/reports/READINESS_FULL_2026-08-26.md`)。族去重后必搭 36 个 (≈ 42.8h), 可缓建 10 个, 明细见 `docs/reports/PHYSICAL_REVIEW_QUEUE.md` / `docs/reports/PHYSICAL_FAMILY_PACK.md` 与 `docs/reports/PHYSICAL_RISK_REPORT.md` (同为 250 基线)。

## 4. 难度配额守卫红灯 (D3 冻结, 预期)

`--full` 档强制开启 `MAGTILE_DIFFICULTY_QUOTA=1`, QA 关卡 41 以 `check_difficulty_quota.py --strict` 运行。本次实跑分布与判定:

| 难度 | 数量 | 占比 | 解冻线 |
| --- | --- | --- | --- |
| D1 (入门) | 0 | 0.0% | ≥ 20, 缺 20 |
| D2 (进阶) | 23 | 9.2% | — |
| D3 (熟练) | 181 | 72.4% | 冻结中 (新增 D3 由批次评审 `--batch` 闸门拦截) |
| D4 (挑战) | 45 | 18.0% | — |
| D5 (大师) | 1 | 0.4% | ≥ 6, 缺 5 |

D3 冻结生效中 (D1 0/20, D5 1/6), strict 档以退出码 1 结束 —— 这是 CI 对主库分布状态的告警闸, 与 L2 抗扰动档同一「不许占位交差」口径: 在 D1 补 20 个、D5 补 5 个入库前, `--full` 档保持红灯属预期告警, 不允许通过放宽阈值或跳过关卡的方式「转绿」。同口径常开报告型 (不带环境变量) 与 CTest 硬闸门 `difficulty_quota_gate` (冻结不阻断、难度值非法才失败) 语义见 docs/TESTING.md 3.19。置换/退役决策工具见 `tools/plan_quota_substitution.py` (规划) 与 `tools/retire_models.sh` (执行), 决策单见 `docs/reports/QUOTA_SUBSTITUTION_PLAN_2026-08-25.md`。

## 5. 下一步

1. 内容排产: 补齐 D1 × 20 与 D5 × 5 达到解冻线后, 关卡 41 自动转绿, `--full` 档方可全绿 (冻结期间新增 D3 会被 `tools/review_content_batch.sh` 批次评审闸门拒绝; D5 扩库批目前在并行工作区推进, 入库须过同一批次评审)
2. 用户侧: 按 `docs/USER_HANDOFF.md` §4 完成实物/行政/实机/沙盒验收 (L3 待复核 46 清零, 排产单 `docs/reports/PHYSICAL_REVIEW_QUEUE.md`)
3. 正式出包前: 以 `tools/run_release_gate.sh --full --l2 --fail-on-pending` 复跑终防线 (须 D3 解冻 + L3 清零后方能全绿)

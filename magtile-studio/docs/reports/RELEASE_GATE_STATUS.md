# 发布门禁状态报告 (Release Gate Status)

- 生成时间: 2026-08-26 04:53 UTC
- 基线提交: `53615ea` (`cursor/magtile-studio-foundation-a95b`, 内容库 250 模型; 自上一基线 `9aa146d` 以来为**批 P 扩展装置换波次** —— 按 `BATCH_P_MERGE_PLAN_2026-08-26.md` 从 `cursor/expansion-batch-p-a95b` 摘取 10 个扩展装模型 (1 D1 + 7 D2 + 1 D3 + 1 D4) 并按计划附录 B 退役 10 个矩阵外 D3, 总量 250 保持; 其中 4 个 D2 为满足本线难度感知片数闸门返工扩规模, `sector_rotunda_01` 走 D3 白名单策展豁免 (`BATCH_P_D3_WHITELIST.txt`); 另含 `mark_physical_verified.py` 签核 CLI (`573e0cc`) 与治理文档换版 (`d9ebeff`) —— C++ 引擎源码未变更, 仅模型 JSON/生成器/目录/系列词表/缩略图/工具与文档)
- 构建配置: CMake Release, `/tmp/wt-risk-report/magtile-studio` worktree (@ `53615ea` + 排产三件套刷新 `8974b4b`, 均不触及引擎源码) 增量构建 → **退出码 0**
- 执行命令:
  1. `tools/run_release_gate.sh --full --fail-on-pending` → **退出码 1** —— **全量 QA 关卡保持全绿** (42 子关卡: 39 过 + 3 可选跳过, 0 失败, 耗时 96s); 唯一红灯仍为 L3 实物复核, 批 P 后 **52 个待复核** 在 `--fail-on-pending` 硬闸门口径下红灯 (见 §4)
  2. `tools/check_v1_readiness.sh --quick` → **退出码 1** —— 25 项: 14 PASS / 2 FAIL / 9 SKIP, P0 失败仅 R6/R7 (实物复核, 用户侧)
- 口径变化 (与上一基线 `9aa146d` 的差异):
  - **L3 全集 51 → 52**: 批 P 净增 1 个 D4 (`expansion_orb_01`, 扩展装轨道球体, 风险分 54.1), D4+ 全集变为 46 D4 + 6 D5 = 52, 全部待复核; 排产三件套已刷新至 52 口径 (`8974b4b`, 见 §4)
  - **CTest 556 → 557**, 全过 (+1 为签核 CLI 自测闸门 `mark_physical_verified_gate`, 随 `573e0cc` 注册; 模型置换 10 进 10 出的 validate/tutorial 双测数量互抵); 全量质检/唯一性/strict 巡检等按 250 新构成重跑, 判定口径 (难度感知片数下限 D1 ≥ 20 / 其余 ≥ 40, strict 零未豁免警告) 无变化
  - 难度分布变化: D1 20→21 / D2 23→30 / D3 156→147 / D4 45→46 / D5 6 不变 —— 解冻线 (D1 ≥ 20, D5 ≥ 6) 继续达标, D3 解冻维持 (§3)
  - 系列归类矩阵内 201 → **211** (批 P 10 个全部入矩阵格), 矩阵外 49 → **39** (退役 10 个均为矩阵外 D3); 儿童文案段数 8571 → 8493 (随置换内容变化, 301 文件全绿)

## 1. 结论速览

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 全量 QA (42 子关卡: 39 过 3 可选跳过 0 失败) | **GREEN (保持)** | 批 P 置换后首次全量实跑仍 0 失败。CTest 557/557; 全量质检 250/250 (难度感知下限); 反平凡/逻辑质检/逐步装配全过; 唯一性 250 模型两两比对 0 警告; strict 巡检三阶段全绿 —— 静态档 249 过 + 1 白名单豁免 (`suspension_bridge_01`) 0 未豁免警告, 逐步装配过, **D4+ 抗扰动 52/52 × 50 轮全绿** (含新入库 `expansion_orb_01`); 免费层 30/30 全 core-9; 系列归类矩阵内 211 + 矩阵外 39 (缺失/非法 0); 儿童文案 301 文件 8493 段全绿; 可选跳过 3 项为教程步进性能基准 / L2 独立加闸 / 矩阵快照刷新 (均非 `--full` 档默认项); 耗时 96s |
| 难度配额守卫 (QA 关卡 41, strict) | **GREEN (保持)** | D1 21 (8.4%) / D2 30 (12.0%) / D3 147 (58.8%) / D4 46 (18.4%) / D5 6 (2.4%), 解冻线 D1 ≥ 20 与 D5 ≥ 6 保持达标, **D3 冻结解除状态维持** (§3) |
| L3 实物复核缺口 (硬闸门, `--fail-on-pending`) | **FAIL (预期, 唯一红灯)** | 扫描 250 模型, D4+ **52 个待复核 0/52** (46 D4 + 6 D5, 批 P 净增 `expansion_orb_01`) —— 用户侧人手实搭, 非软件缺陷; 排产三件套已同步 52 口径 (§4) |
| V1 就绪快检 (`--quick`) | **FAIL (预期)** | 14 PASS / 2 FAIL / 9 SKIP; P0 失败仅 R6 (抽样包缺口 10/10, 命中 S1=0 S2=6 S3=4 —— 6 个 D5 全部进入抽样包, 预计 1000 分钟 ≈ 16.7 小时) 与 R7 (D4+ 52 待复核清零), 与 L3 同源; R1/R2/R3/R8~R16/R18 全过, R4/R5/R17 与 M1~M6 按 `--quick` 口径跳过 |

**工程侧判定: 批 P 置换入库后软件门禁保持 `--full --fail-on-pending` 档全绿 (除 L3)。** 批 P 的 10 个模型在本线基线上通过内容批评审五道闸 (`BATCH_P_MERGE_PLAN_2026-08-26.md`) 后摘取入库, 本次全量实跑确认置换未引入任何软件侧红项 —— 无静默放宽、无占位判绿 (`sector_rotunda_01` 的 D3 白名单为策展书面豁免, 留痕 `BATCH_P_D3_WHITELIST.txt`)。当前距全绿仅剩 L3 实物复核 52/52 (用户侧实搭, 排产单 `docs/reports/PHYSICAL_REVIEW_QUEUE.md`: 族去重必搭 41 ≈ 52.8h + 可缓建 11 ≈ 12.8h)。

## 2. 批 P 置换明细 (本波次唯一内容变更)

| 项 | 内容 |
| --- | --- |
| 入库 10 个 | `plaza_canopy_01` (D1) / `conservatory_01`、`hex_honeycomb_01`、`marble_splitter_01`、`rhombus_patchwork_01`、`streetcar_01`、`switchback_ramp_01`、`trapezoid_awning_01` (D2) / `sector_rotunda_01` (D3, 白名单) / `expansion_orb_01` (D4) —— 全部为扩展装片型系列, 4 个 D2 (`hex_honeycomb` 32→44 片, `rhombus_patchwork` 39→41, `marble_splitter` 30→40, `trapezoid_awning` 31→40) 为满足本线难度感知片数闸门返工扩规模, 逐个 strict 零警告 |
| 退役 10 个 | `er_entrance_01`、`bamboo_house_01`、`bike_rack_park_01`、`climbing_wall_01`、`diving_tower_01`、`hydro_dam_01`、`dental_clinic_01`、`lego_style_house_01`、`flag_plaza_01`、`skate_park_01` —— 按计划附录 B 在本线基线重算的矩阵外 D3 Top 10, 系列词表同步除名 |
| 未随批合入 | 批 P 分支的 J~M 批血统与其余差异 (合并计划评估: 全量合并将超 250 上限 26 个且有 3 处冲突, 故走摘取而非合并; 见 `BATCH_P_MERGE_PLAN_2026-08-26.md`) |

本次验证: 全量质检/反平凡/逻辑质检/逐步装配/唯一性/strict 三阶段/系列归类/难度配额 strict 全部按 250 新构成实跑通过 (§1), CTest 557/557 含 10 个新模型的 validate/tutorial 双测与系列 (`content_series_gate`) / 配额 (`difficulty_quota_gate`) 常开闸门。

## 3. 难度配额守卫保持绿灯 (D3 解冻状态维持)

`--full` 档强制开启 `MAGTILE_DIFFICULTY_QUOTA=1`, QA 关卡 41 以 `check_difficulty_quota.py --strict` 运行, 本次实跑分布与判定:

| 难度 | 数量 | 占比 | 解冻线 | 较上基线 |
| --- | --- | --- | --- | --- |
| D1 (入门) | 21 | 8.4% | ≥ 20, 达标 | +1 (`plaza_canopy_01`) |
| D2 (进阶) | 30 | 12.0% | — | +7 (批 P 扩展装 D2) |
| D3 (熟练) | 147 | 58.8% | 冻结解除维持 | −9 (退役 10 + 入库 1 白名单) |
| D4 (挑战) | 46 | 18.4% | — | +1 (`expansion_orb_01`) |
| D5 (大师) | 6 | 2.4% | ≥ 6, 达标 | 不变 |

批 P 置换 +10/−10 总量保持 250, strict 档退出码 0, 解冻状态与上基线一致 (解冻线由 CTest 常开闸门与批次评审机检持续守卫)。

## 4. L3 实物复核缺口 (硬闸门红, 唯一剩余红灯; 51 → 52)

本次带 `--fail-on-pending`, L3 走硬闸门口径: 扫描 250 模型, D4+ **52 个全部待复核 (46 D4 + 6 D5)**, 门禁关卡 2 以退出码 1 结束。较上基线净增 1 个: 批 P 入库的 `expansion_orb_01` (D4, 风险分 54.1, 队列第 8 位)。`check_v1_readiness.sh --quick` 对应 R6/R7 两项 P0 FAIL —— 用户侧人手实搭事项, 待按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭后回填 `physical_verified` (签核 CLI `tools/mark_physical_verified.py`)。

排产三件套已刷新至 52 口径 (`8974b4b`):

- `PHYSICAL_REVIEW_QUEUE.md/.csv` — 52 行: **必搭 41 (3170 分钟 ≈ 52.8h) + 可缓建 11 (770 分钟 ≈ 12.8h) = 3940 分钟 ≈ 65.7h**, 无快照告警;
- `PHYSICAL_RISK_REPORT.md/.json` — 风险 Top3: `skyscraper_01` 63.9 / `stellar_launch_gantry_01` 61.8 / `marble_grand_cascade_01` 57.6 (第 3 位换人: 两个 D5 扩规模模型此前风险快照按旧 87/102 片几何计分, 本次按现行 123/122 片重算, `marble_grand_cascade_01` 54.6→57.6 越过 `strait_rainbow_bridge_01` 56.8); L2 标记 145 / `l2_required` 155 / 缺 L2 凭据 152 (退役 10 个矩阵外 D3 多为 2b 命中, 故较上基线 148/158/155 净降);
- `PHYSICAL_FAMILY_PACK.md` — 250 模型聚 195 族 (多成员族 43 / 单模型族 152), 族去重省 20% 人手 (11 个可缓建全部为 D4 同族成员, 须策展签核, 不豁免全集清零)。

R6 抽样包命中 S1=0 S2=6 S3=4 —— 6 个 D5 全部纳入优先抽样, S3 按片数取 `stadium_gate_01` / `ferry_terminal_01` / `treehouse_02` / `elephant_01`, 预计 1000 分钟 ≈ 16.7 小时。

## 5. 下一步

1. **用户侧 (唯一 P0 阻塞)**: 按 `docs/USER_HANDOFF.md` §4 完成实物签核 —— L3 待复核 **52** 清零 (排产单 `docs/reports/PHYSICAL_REVIEW_QUEUE.md`, 建议从 R6 抽样包 10 个起步, 优先 6 个 D5; 落盘用 `tools/mark_physical_verified.py`); 另有行政/实机/沙盒/法务 Manual P0 项并行推进
2. **工程侧**: 无待修红项 —— 软件门禁全绿, 保持 D1 ≥ 20 / D5 ≥ 6 与 250 上限即可; 新增内容一律走 `review_content_batch.sh` 常规评审 (批 P 剩余血统若再合入, 按 `BATCH_P_MERGE_PLAN_2026-08-26.md` 口径重新评审)
3. **正式出包前**: 以 `tools/run_release_gate.sh --full --l2 --fail-on-pending` 复跑终防线 (本次 `--full` 档 strict 巡检阶段 3 已实跑 D4+ 抗扰动 52/52 全绿, L2 独立加闸预期同绿; 唯 L3 清零后方能整体全绿)

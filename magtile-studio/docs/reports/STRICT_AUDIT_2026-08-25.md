# 全库 strict 物理巡检报告

- 生成时间: 2026-08-25 21:50
- 基线提交: `b369bad` (`cursor/magtile-studio-foundation-a95b` 治理波次收官, 250 模型, 难度分布 D2 x23 / D3 x181 / D4 x45 / D5 x1)
- 生成工具: `tools/run_strict_audit.sh` (`magtile_app validate --profile strict` 零警告审计 + `tests/test_step_assembly.py` 逐步装配质检 + D4+ 抗扰动巡检 jitter 挂钩, 见 `docs/TESTING.md` 3.17)
- 校验档位: `strict_consumer` (悬挂额定 120g/单位边长, 抗碰撞安全系数 0.7 → 有效悬挂预算 84g/边长, 有效抗弯预算 17.5 g·单位; 参数依据见 `docs/PHYSICS_RULES.md` 1.4 节)
- 零警告政策与豁免白名单: `tools/audit_strict_physics.sh` / `docs/STRICT_PHYSICS_AUDIT.md`

## 1. 总览

| 指标 | 数值 |
| --- | --- |
| 模型总数 | 250 |
| strict 通过 (零警告零错误) | 249 |
| 白名单豁免 (警告经书面论证) | 1 |
| 未豁免警告 (拦截) | 0 |
| 失败 (Error 级) | 0 |
| 逐步装配质检 | 250 通过 / 0 失败 |
| D4+ 抗扰动巡检 (jitter, L2 挂钩) | 全绿 (46 个 D4+ 模型 x 50 次采样) |
| 巡检结论 | **全绿** |

## 2. 按规则分类 (R1~R8)

统计口径: strict 档全库审计输出的每一条问题行 (同一模型多个步骤重复报告的问题按行计, 与审计日志一致)。

| 规则 | Error | 拦截 Warning | 豁免 Warning |
| --- | --- | --- | --- |
| R1 接地支撑 | 0 | 0 | 0 |
| R2 磁力连接 | 0 | 0 | 5 |
| R3 无重叠 | 0 | 0 | 0 |
| R4 重心稳定 | 0 | 0 | 0 |
| R5 悬挂承重 | 0 | 0 | 0 |
| R6 悬臂力矩 | 0 | 0 | 0 |
| R7 装配可达 | 0 | 0 | 0 |
| R8 结构冗余 | 0 | 0 | 0 |

问题代码分布:

- `disconnected_assembly`: 5 条

## 3. 问题明细

无 —— 全库不存在任何 Error 级问题与未豁免 Warning。

## 4. 豁免清单

| 模型 | 代码 | 条数 | 论证出处 |
| --- | --- | --- | --- |
| `suspension_bridge_01` | `disconnected_assembly` | 5 | `docs/STRICT_PHYSICS_AUDIT.md` |

## 5. D4+ 实物复核清单 (L3)

以下 46 个 difficulty ≥ 4 模型软件校验全绿后, 按 `docs/BUILD_VERIFICATION.md` 必须逐个完成 L3 实物复核 (计时分步搭建 / 敲击 / 提起 / 拆解重搭 / 儿童实测), 结论写入旁车文件 `data/verification/<model_id>.json` 并与内容哈希绑定。**strict 全绿是入库必要条件, 不替代实物复核。**

| 模型 | 难度 | 片数 | strict 结果 |
| --- | --- | --- | --- |
| `aircraft_carrier_01` | D4 | 84 | 通过 |
| `airport_terminal_01` | D4 | 77 | 通过 |
| `apartment_block_01` | D4 | 99 | 通过 |
| `ball_run_tower_01` | D4 | 94 | 通过 |
| `basketball_arena_01` | D4 | 83 | 通过 |
| `cargo_ship_01` | D4 | 87 | 通过 |
| `castle_drawbridge_01` | D4 | 99 | 通过 |
| `covered_bridge_01` | D4 | 94 | 通过 |
| `dinosaur_hall_01` | D4 | 84 | 通过 |
| `eiffel_tower_01` | D4 | 95 | 通过 |
| `elephant_01` | D4 | 95 | 通过 |
| `ferry_terminal_01` | D4 | 100 | 通过 |
| `fire_station_01` | D4 | 81 | 通过 |
| `freight_yard_01` | D4 | 85 | 通过 |
| `hanging_garden_01` | D4 | 85 | 通过 |
| `harbor_crane_01` | D4 | 86 | 通过 |
| `helicopter_01` | D4 | 87 | 通过 |
| `hospital_01` | D4 | 98 | 通过 |
| `ice_rink_01` | D4 | 84 | 通过 |
| `library_building_01` | D4 | 90 | 通过 |
| `lighthouse_01` | D4 | 77 | 通过 |
| `marble_run_spiral_01` | D4 | 80 | 通过 |
| `parking_garage_01` | D4 | 82 | 通过 |
| `pet_clinic_01` | D4 | 96 | 通过 |
| `post_office_01` | D4 | 97 | 通过 |
| `race_track_01` | D4 | 82 | 通过 |
| `rainforest_canopy_01` | D4 | 90 | 通过 |
| `rescue_hq_01` | D4 | 101 | 通过 |
| `rocket_launchpad_01` | D4 | 82 | 通过 |
| `roman_aqueduct_01` | D4 | 79 | 通过 |
| `school_bus_01` | D4 | 98 | 通过 |
| `skyscraper_01` | D5 | 122 | 通过 |
| `soccer_goal_01` | D4 | 81 | 通过 |
| `stadium_gate_01` | D4 | 103 | 通过 |
| `steam_locomotive_01` | D4 | 99 | 通过 |
| `stonehenge_01` | D4 | 91 | 通过 |
| `submarine_dock_01` | D4 | 89 | 通过 |
| `subway_station_01` | D4 | 87 | 通过 |
| `temple_greek_01` | D4 | 95 | 通过 |
| `tennis_court_01` | D4 | 86 | 通过 |
| `train_station_01` | D4 | 75 | 通过 |
| `treehouse_01` | D4 | 79 | 通过 |
| `treehouse_02` | D4 | 99 | 通过 |
| `triumphal_arch_01` | D4 | 88 | 通过 |
| `volcano_base_01` | D4 | 83 | 通过 |
| `warehouse_01` | D4 | 97 | 通过 |

## 6. 本次巡检记录 (2026-08-25 治理波次合入后刷新, 人工执行部分)

第 1~5 节由 `tools/run_strict_audit.sh --report ... --jitter require` 自动生成 (基线提交 `b369bad`, CMake Release 干净构建, `--jitter require` 档 —— 占位不判绿, D4+ 抗扰动必须实跑)。本节记录本轮刷新的背景与人工核查结论, 取代 250 模型首版报告 (基线 `2b2c4ff`, 第 6 节由 `d1e97e5` 登记) 的第 6 节。

### 6.1 本轮刷新背景

1. **内容库无增减**: 基线自 `2b2c4ff` (批 I 收官) 前移至 `b369bad`, 其间合入的是内容治理波次 (系列归类机检 / D3 冻结难度配额守卫 / 治理守卫接入 QA 与发布门禁, 及配套文档), 不含任何模型增删改 —— 模型总数与难度分布与 250 首版一致 (D2 x23 / D3 x181 / D4 x45 / D5 x1), 第 5 节 L3 实物复核清单维持 46 个 (45 × D4 + 1 × D5) 不变;
2. **CTest 计数 554 → 556**: 治理波次把两道治理守卫注册为 CTest 常开关卡 (`content_series_gate` #555 + `difficulty_quota_gate` #556, 语义见 6.2), 全量回归计数自批 I 收官登记的 554 刷新至 **556**; 本轮在同一干净构建实跑 `ctest -j 4`: **556/556 全过, 0 失败** (含两道新闸门);
3. **刷新动机**: strict 巡检报告与 CTest/治理闸门共用同一基线口径, 治理波次落地后按惯例全库复跑一轮, 确认治理侧改动 (纯脚本/CMake/文档) 未触碰物理校验与内容数据。

### 6.2 治理闸门登记 (本轮新挂, 随 CTest 全量回归常开)

1. **`content_series_gate` (硬闸门)**: `tools/check_content_series.py --strict` —— 每个模型必须带 `content_meta.series` (13 主题词值) 或 `matrix_bucket` (矩阵外桶) 恰好其一, 词值对照权威词表 `data/content_series_map.json`; 新增模型漏归类 / 词值走样即失败。本轮实跑全绿 (矩阵内 176 + 矩阵外 74, 缺失/非法 0)。QA 可选关卡 20 (`MAGTILE_SERIES_CHECK=1`) 为同口径的独立分项入口;
2. **`difficulty_quota_gate` (报告型)**: `tools/check_difficulty_quota.py` 常开报告 D1–D5 分布与 D3 冻结状态, 冻结与否只报告不拦截 (存量 181 个 D3 不追责), 难度值非法 / 模型不可读仍按结构错误硬失败; strict 守卫档另经 QA 可选关卡 21 (`MAGTILE_DIFFICULTY_QUOTA=1`) 与发布门禁 `--full` 档开启 —— 冻结生效 (当前 D1 0/20, D5 1/6) 即红灯, 属预期告警 (见 6.5);
3. **门禁接线口径**: `run_release_gate.sh --full` = 四道发布专项环境变量全开 (`FREE_TIER_CHECK` / `STRICT_AUDIT` / `SERIES_CHECK` / `DIFFICULTY_QUOTA`, 即全量 QA 关卡 10/15/20/21); 内容批 PR 评审侧由一键机检 `tools/review_content_batch.sh` 把 series 归类与 D3 冻结 (`--batch`) 两道闸串进五道阻断关卡 (用法见 `docs/CONTENT_STRATEGY.md` §4.3)。

### 6.3 本轮结果

1. **全库 strict 审计**: 250 个模型逐一 `validate --profile strict` 零警告政策, 249 通过 + 1 白名单豁免 + 0 拦截警告 + 0 失败 —— 与 250 首版逐项一致;
2. **逐步装配质检**: `tests/test_step_assembly.py` 250/250 通过;
3. **D4+ 抗扰动巡检**: 46/46 个 D4+ 模型 `--profile strict --jitter 50` 全绿, 本轮以 `--jitter require` 档执行 —— CLI 未实装时按失败处理, 实跑判绿非占位;
4. **CTest 全量回归**: 同基线干净构建 556/556 全过 (计数 554 → 556, 新增即 6.2 两道治理闸门, 其余关卡零回归);
5. **巡检结论: 全绿** —— 治理波次为纯脚本/CMake/文档改动, 物理校验与内容数据零回归, 与 `2b2c4ff` 收官登记的巡检结论一致。

### 6.4 豁免复核

豁免清单与 250 首版一致, 无增减: 唯一豁免 `suspension_bridge_01:disconnected_assembly` × 5 为既有白名单条目 (悬索桥双岸合龙教学叙事, 论证见 `docs/STRICT_PHYSICS_AUDIT.md`), 本轮复核维持豁免结论; 治理波次未申请任何新豁免。

### 6.5 遗留事项

- **D4+ 实物复核 (L3)**: 第 5 节 46 个模型 (45 × D4 + 1 × D5 `skyscraper_01`) 按 `docs/BUILD_VERIFICATION.md` 逐个走实物复核, 软件全绿 (含 jitter) 不豁免此步 —— `check_v1_readiness.sh` 的 R6/R7 两项 P0 (实物复核回填 `physical_verified`) 仍为 FAIL, 发布门禁 `run_release_gate.sh --full --l2 --fail-on-pending` 的 L3 硬闸门在复核清零前保持红灯; 本轮刷新不标记任何发布目标完成;
- **难度配额 strict 守卫预期红**: QA 关卡 21 / 发布门禁 `--full` 档的 strict 守卫在内容侧补齐 D1 ≥ 20 且 D5 ≥ 6 (随即 D3 解冻) 前保持预期红灯 —— 属内容缺口治理告警, 不影响本报告 strict 物理巡检全绿结论 (常开的 CTest `difficulty_quota_gate` 为报告型, 556/556 中判绿);
- 多铰链连锁剥离与共面环出平面刚度细化仍跟踪于 `docs/PHYSICS_VERIFICATION_DEEP_DIVE.md` 第 5 节 (与 250 首版一致, 本轮无新增)。

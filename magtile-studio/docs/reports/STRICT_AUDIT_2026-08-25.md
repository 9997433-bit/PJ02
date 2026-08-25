# 全库 strict 物理巡检报告

- 生成时间: 2026-08-25 20:42
- 基线提交: `2b2c4ff` (`cursor/magtile-studio-foundation-a95b` 250 模型终态, 难度分布 D2 x23 / D3 x181 / D4 x45 / D5 x1)
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

## 6. 本次巡检记录 (2026-08-25 内容库扩容至 250 模型后刷新, 人工执行部分)

第 1~5 节由 `tools/run_strict_audit.sh --report ... --jitter require` 自动生成 (基线提交 `2b2c4ff`, 独立工作树 CMake Release 干净构建, `--jitter require` 档 —— 占位不判绿, D4+ 抗扰动必须实跑)。本节记录本轮刷新的背景与人工核查结论, 取代 234 模型版报告 (基线 `3d24d74`, 第 6 节由 `3767088` 登记) 的第 6 节。

### 6.1 本轮刷新背景

1. **内容库扩容**: 234 模型版报告以来, 内容批 F~I 共 16 个新模型分批合入 foundation (234 → 250), 终态构成:
   - 批 F (`e346ecf` 合入): `pipe_organ_01` / `peacock_01` / `stonehenge_01` / `mushroom_grove_01`;
   - 批 G (`67485eb` 合入): `kangaroo_01` / `pirate_ship_01` / `truss_bridge_01` / `yurt_01`;
   - 批 H (`4636148` 合入): `pumpkin_lantern_01` / `hedgehog_01` / `circus_tent_01` / `fireboat_01`;
   - 批 I (`94bf13c` 合并后收官): `recycling_center_01` / `santa_sleigh_01` / `octopus_01` / `swing_set_01`;
2. **撞车处置不影响审计口径**: 批 I 曾独立产出同名 `kangaroo_01` / `pumpkin_lantern_01` / `stonehenge_01`, 与批 G/H/F 撞车, 合并 (`94bf13c`) 时取批 G/H/F 版本 (现库内 kangaroo D3 70 片 / pumpkin_lantern D3 62 片 / stonehenge D4 91 片), 批 I 净新增即上列 4 席; 处置均在入库前完成, 本轮审计对象即 foundation 终态 250 模型;
3. **新增 16 模型难度构成 D2 x3 / D3 x12 / D4 x1**: 唯一新增 D4 为批 F 旗舰 `stonehenge_01` (四门环阵巨石阵), 第 5 节 L3 实物复核清单由 45 个扩至 **46 个** (45 × D4 + 1 × D5), 系抖动修复版以来该清单首次扩容。

### 6.2 本轮结果

1. **全库 strict 审计**: 250 个模型逐一 `validate --profile strict` 零警告政策, 249 通过 + 1 白名单豁免 + 0 拦截警告 + 0 失败 —— 16 个新模型全部零警告零豁免;
2. **逐步装配质检**: `tests/test_step_assembly.py` 250/250 通过;
3. **D4+ 抗扰动巡检**: 46/46 个 D4+ 模型 `--profile strict --jitter 50` 全绿 (含新入清单的 `stonehenge_01`), 本轮以 `--jitter require` 档执行 —— CLI 未实装时按失败处理, 实跑判绿非占位;
4. **巡检结论: 全绿** —— 与批 I 收官提交 (`2b2c4ff`) 登记的全库 38 关卡 QA 结论一致, 未发现任何回归。

### 6.3 豁免复核

豁免清单与 234 模型版一致, 无增减: 唯一豁免 `suspension_bridge_01:disconnected_assembly` × 5 为既有白名单条目 (悬索桥双岸合龙教学叙事, 论证见 `docs/STRICT_PHYSICS_AUDIT.md`), 本轮复核维持豁免结论; 16 个新模型未申请任何豁免。

### 6.4 遗留事项

- **D4+ 实物复核 (L3)**: 第 5 节 46 个模型 (45 × D4 + 1 × D5 `skyscraper_01`) 按 `docs/BUILD_VERIFICATION.md` 逐个走实物复核, 软件全绿 (含 jitter) 不豁免此步 —— `check_v1_readiness.sh` 的 R6/R7 两项 P0 (实物复核回填 `physical_verified`) 仍为 FAIL, 发布门禁 `run_release_gate.sh --full --l2 --fail-on-pending` 的 L3 硬闸门在复核清零前保持红灯; 本轮刷新不标记任何发布目标完成;
- 多铰链连锁剥离与共面环出平面刚度细化仍跟踪于 `docs/PHYSICS_VERIFICATION_DEEP_DIVE.md` 第 5 节 (与 234 模型版一致, 本轮无新增)。

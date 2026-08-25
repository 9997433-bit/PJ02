# 全库 strict 物理巡检报告

- 生成时间: 2026-08-25 10:48
- 生成工具: `tools/run_strict_audit.sh` (`magtile_app validate --profile strict` 零警告审计 + `tests/test_step_assembly.py` 逐步装配质检)
- 校验档位: `strict_consumer` (悬挂额定 120g/单位边长, 抗碰撞安全系数 0.7 → 有效悬挂预算 84g/边长, 有效抗弯预算 17.5 g·单位; 参数依据见 `docs/PHYSICS_RULES.md` 1.4 节)
- 零警告政策与豁免白名单: `tools/audit_strict_physics.sh` / `docs/STRICT_PHYSICS_AUDIT.md`

## 1. 总览

| 指标 | 数值 |
| --- | --- |
| 模型总数 | 131 |
| strict 通过 (零警告零错误) | 130 |
| 白名单豁免 (警告经书面论证) | 1 |
| 未豁免警告 (拦截) | 0 |
| 失败 (Error 级) | 0 |
| 逐步装配质检 | 131 通过 / 0 失败 |
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

以下 41 个 difficulty ≥ 4 模型软件校验全绿后, 按 `docs/BUILD_VERIFICATION.md` 必须逐个完成 L3 实物复核 (计时分步搭建 / 敲击 / 提起 / 拆解重搭 / 儿童实测), 结论写入旁车文件 `data/verification/<model_id>.json` 并与内容哈希绑定。**strict 全绿是入库必要条件, 不替代实物复核。**

| 模型 | 难度 | 片数 | strict 结果 |
| --- | --- | --- | --- |
| `aircraft_carrier_01` | D4 | 84 | 通过 |
| `airport_terminal_01` | D4 | 77 | 通过 |
| `apartment_block_01` | D4 | 99 | 通过 |
| `ball_run_tower_01` | D4 | 90 | 通过 |
| `basketball_arena_01` | D4 | 83 | 通过 |
| `cargo_ship_01` | D4 | 87 | 通过 |
| `castle_drawbridge_01` | D4 | 99 | 通过 |
| `covered_bridge_01` | D4 | 94 | 通过 |
| `eiffel_tower_01` | D4 | 95 | 通过 |
| `elephant_01` | D4 | 95 | 通过 |
| `ferry_terminal_01` | D4 | 100 | 通过 |
| `fire_station_01` | D4 | 81 | 通过 |
| `hanging_garden_01` | D4 | 85 | 通过 |
| `harbor_crane_01` | D4 | 86 | 通过 |
| `helicopter_01` | D4 | 87 | 通过 |
| `hospital_01` | D4 | 98 | 通过 |
| `ice_rink_01` | D4 | 84 | 通过 |
| `library_building_01` | D4 | 90 | 通过 |
| `lighthouse_01` | D4 | 77 | 通过 |
| `marble_run_spiral_01` | D4 | 77 | 通过 |
| `parking_garage_01` | D4 | 82 | 通过 |
| `pet_clinic_01` | D4 | 96 | 通过 |
| `post_office_01` | D4 | 97 | 通过 |
| `race_track_01` | D4 | 82 | 通过 |
| `rainforest_canopy_01` | D4 | 84 | 通过 |
| `rescue_hq_01` | D4 | 101 | 通过 |
| `rocket_launchpad_01` | D4 | 82 | 通过 |
| `roman_aqueduct_01` | D4 | 79 | 通过 |
| `school_bus_01` | D4 | 98 | 通过 |
| `skyscraper_01` | D5 | 122 | 通过 |
| `soccer_goal_01` | D4 | 81 | 通过 |
| `stadium_gate_01` | D4 | 103 | 通过 |
| `steam_locomotive_01` | D4 | 99 | 通过 |
| `subway_station_01` | D4 | 87 | 通过 |
| `temple_greek_01` | D4 | 95 | 通过 |
| `train_station_01` | D4 | 75 | 通过 |
| `treehouse_01` | D4 | 79 | 通过 |
| `treehouse_02` | D4 | 99 | 通过 |
| `triumphal_arch_01` | D4 | 88 | 通过 |
| `volcano_base_01` | D4 | 83 | 通过 |
| `warehouse_01` | D4 | 97 | 通过 |

## 6. 本次巡检记录 (2026-08-25, 人工执行部分)

第 1~5 节由 `tools/run_strict_audit.sh --report` 自动生成; 本节记录本轮巡检的人工核查动作与发现, 供复核追溯。

### 6.1 巡检范围与方法

1. **全库 strict 审计**: 131 个模型逐一 `validate --profile strict`, 零警告政策 (`tools/audit_strict_physics.sh`), 结果 130 通过 + 1 白名单豁免 + 0 失败;
2. **逐步装配质检**: `tests/test_step_assembly.py` 逐片连通/引用对账/步骤粒度, 131/131 通过;
3. **CTest 全量回归**: 291/291 通过 (含 3 个旗舰 `validate_strict_*` 用例与 9 个物理负例夹具);
4. **档位差分探针** (防"strict 假绿"): 构造 3 片正方形悬挂链 (90g) 临时夹具 —— 落在 default 预算 (120g/边长) 之内、strict 预算 (84g/边长) 之外。实测 default 档不报 R5、strict 档正确报 `hanging_chain_overload` 并拒绝, 证明 strict 档参数真实生效而非空转。

### 6.2 发现并修复的引擎缺陷 (非内容问题)

**R5 悬挂超重文案硬编码安全系数**: `src/physics/physics_validator.cpp` 中 `hanging_chain_overload` 的错误文案把抗碰撞裕量硬编码为 "x 80%", 而 `--profile strict` 实际生效的是 70% (`knock_safety_factor = 0.7`)。预算数值计算本身正确 (84g = 120 × 0.7), 属纯文案缺陷, 但会误导内容作者按 80% 反推预算、得出错误的加固余量。

- **修复**: 文案改为按 `config_.knock_safety_factor` 动态输出百分比 (最小修改, 不触碰任何判定逻辑与参数);
- **回归测试**: 新增 `tests/test_strict_profile_message.sh` (CTest 用例 `strict_profile_message`), 对悬挂超重负例夹具双档断言: default 档文案 "x 80%"、strict 档文案 "x 70%" 且不得残留 80%; 两档均须以 `hanging_chain_overload` 拒绝;
- **影响面复核**: 修复前后全库 strict 审计与全部负例/正例夹具结果逐一比对, 判定结果零变化 (仅文案变化), 无误杀无误放。

### 6.3 内容缺陷

本轮未发现内容缺陷: 全库 131 个模型 strict 档零 Error、零未豁免 Warning, 无需修改任何模型 JSON。唯一豁免 `suspension_bridge_01:disconnected_assembly` 为既有白名单条目 (悬索桥双岸合龙教学叙事, 论证见 `docs/STRICT_PHYSICS_AUDIT.md`), 本轮复核维持豁免结论。

### 6.4 遗留事项

- **D4+ 实物复核 (L3)**: 第 5 节 41 个模型 (40 × D4 + 1 × D5 `skyscraper_01`) 按 `docs/BUILD_VERIFICATION.md` 逐个走实物复核, 软件全绿不豁免此步;
- **已知校验盲区** (非本轮缺陷, 跟踪于 `docs/PHYSICS_VERIFICATION_DEEP_DIVE.md` 第 5 节): 多铰链连锁剥离 (P1-1)、共面环出平面刚度细化 (P1-2)、蒙特卡洛容差抖动 (P1-3) 尚未落地, D4+ 模型在这些盲区内的风险由 L3 实物复核兜底。

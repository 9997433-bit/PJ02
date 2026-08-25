# 全库 strict 物理巡检报告

- 生成时间: 2026-08-25 17:46
- 生成工具: `tools/run_strict_audit.sh` (`magtile_app validate --profile strict` 零警告审计 + `tests/test_step_assembly.py` 逐步装配质检 + D4+ 抗扰动巡检 jitter 挂钩, 见 `docs/TESTING.md` 3.17)
- 校验档位: `strict_consumer` (悬挂额定 120g/单位边长, 抗碰撞安全系数 0.7 → 有效悬挂预算 84g/边长, 有效抗弯预算 17.5 g·单位; 参数依据见 `docs/PHYSICS_RULES.md` 1.4 节)
- 零警告政策与豁免白名单: `tools/audit_strict_physics.sh` / `docs/STRICT_PHYSICS_AUDIT.md`

## 1. 总览

| 指标 | 数值 |
| --- | --- |
| 模型总数 | 209 |
| strict 通过 (零警告零错误) | 208 |
| 白名单豁免 (警告经书面论证) | 1 |
| 未豁免警告 (拦截) | 0 |
| 失败 (Error 级) | 0 |
| 逐步装配质检 | 209 通过 / 0 失败 |
| D4+ 抗扰动巡检 (jitter, L2 挂钩) | 全绿 (45 个 D4+ 模型 x 50 次采样) |
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

以下 45 个 difficulty ≥ 4 模型软件校验全绿后, 按 `docs/BUILD_VERIFICATION.md` 必须逐个完成 L3 实物复核 (计时分步搭建 / 敲击 / 提起 / 拆解重搭 / 儿童实测), 结论写入旁车文件 `data/verification/<model_id>.json` 并与内容哈希绑定。**strict 全绿是入库必要条件, 不替代实物复核。**

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

## 6. 本次巡检记录 (2026-08-25 抖动修复后刷新, 人工执行部分)

第 1~5 节由 `tools/run_strict_audit.sh build --report` 自动生成 (基线提交 `95c26cd`, CMake Release 干净构建)。本节记录本轮刷新的背景与人工核查结论, 取代同日上午版报告的第 6 节 (彼时全库 131 模型、`--jitter` CLI 尚未实装、阶段 3 为占位)。

### 6.1 本轮刷新背景

1. **内容库扩容**: 上午版报告以来全库 131 → 209 模型 (D4+ 实物复核清单 41 → 45 个, 新增 `dinosaur_hall_01` / `freight_yard_01` / `submarine_dock_01` / `tennis_court_01`);
2. **D4+ 抗扰动巡检 (jitter) 由占位转实跑**: L2 任务落地 `validate --jitter` CLI 并登记进 `--help` 用法文本后, 本脚本阶段 3 按挂钩契约自动启用 —— 本轮为 45 个 D4+ 模型逐个 `--profile strict --jitter 50` 实跑;
3. **R9 抖动敏感模型修复批已全部入库**: D4+ 首巡 (基线 `262ebc3`, 留痕见 `docs/reports/RELEASE_GATE_STATUS.md`) 抓出 4 个抖动敏感模型, 加固全部合入 foundation 后本轮复跑确认:

| 模型 | 首巡失败 | 修复提交 | 手法 |
| --- | --- | --- | --- |
| `ball_run_tower_01` (D4) | 4/50 轮 `cantilever_overload` 35.3 > 35.0 | `8d07fe5` / `5b915a0` | 西线转角外缘双层门式立柱 (90 → 94 片) |
| `marble_run_spiral_01` (D4) | 3/50 轮 `cantilever_overload` 35.1 > 35.0 | `114c154` | 三块转角台下挂直角三角斜撑成环 (77 → 80 片) |
| `rainforest_canopy_01` (D4) | 3/50 轮 `cantilever_overload` 18.6 > 17.5 | `2ffc06e` | 六片树冠平台配板根斜撑成环 (84 → 90 片) |
| `lego_style_house_01` (D3, 默认档) | 7/50 轮 `enclosed_placement` | `24fd0ec` | 山花改在北坡合脊前放置 (纯步骤重排) |

处置纪律零例外: 全部修模型 (加支撑成环 / 调放置顺序), 未放宽任何物理预算参数 (登记见 `docs/PHYSICS_RULES.md` R9 节)。

### 6.2 本轮结果

1. **全库 strict 审计**: 209 个模型逐一 `validate --profile strict` 零警告政策, 208 通过 + 1 白名单豁免 + 0 拦截警告 + 0 失败;
2. **逐步装配质检**: `tests/test_step_assembly.py` 209/209 通过;
3. **D4+ 抗扰动巡检**: 45/45 个 D4+ 模型 `--profile strict --jitter 50` 全绿 (含上表 3 个 D4 修复模型), 首巡 42/45 红灯清零;
4. **巡检结论: 全绿** —— 与 `docs/reports/RELEASE_GATE_STATUS.md` (基线 `5b915a0`) 的 L2 门禁复跑结论一致。

### 6.3 豁免复核

豁免清单与上午版一致, 无增减: 唯一豁免 `suspension_bridge_01:disconnected_assembly` × 5 为既有白名单条目 (悬索桥双岸合龙教学叙事, 论证见 `docs/STRICT_PHYSICS_AUDIT.md`), 本轮复核维持豁免结论; jitter 巡检下该模型同样通过, 不新增豁免。

### 6.4 遗留事项

- **D4+ 实物复核 (L3)**: 第 5 节 45 个模型 (44 × D4 + 1 × D5 `skyscraper_01`) 按 `docs/BUILD_VERIFICATION.md` 逐个走实物复核, 软件全绿 (含 jitter) 不豁免此步 —— 发布门禁 `run_release_gate.sh --full --l2 --fail-on-pending` 的 L3 硬闸门在复核清零前保持红灯;
- 上午版第 6.2 节记录的 R5 悬挂超重文案缺陷修复 (`strict_profile_message` 回归用例) 已入库, 本轮不再复述; 蒙特卡洛容差抖动盲区 (原 P1-3) 已由 `--jitter` 实装收口, 多铰链连锁剥离与共面环出平面刚度细化仍跟踪于 `docs/PHYSICS_VERIFICATION_DEEP_DIVE.md` 第 5 节。

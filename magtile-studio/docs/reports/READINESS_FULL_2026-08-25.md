# V1 上架就绪全量探测报告 (Full Readiness Run)

- 生成时间: 2026-08-25 20:41 UTC (250 模型库复跑; 前次 234 模型基线 `3d24d74` 的结果已由本次覆盖)
- 基线提交: `2b2c4ff` (`2b2c4ff3781436adeec2ebe3dd0f34718a64c2e4`, 内容批 F~I 全部并入后的 250 模型库 —— 200~250 上限目标达成)
- 构建配置: CMake Release x2 (CLI `build` Make + Qt `build-qt`, Qt 6.4.2); 本次为增量构建复用 —— 自 `8b424be` (validate --jitter 特性) 后无源码改动, 增量重建确认全部目标最新, 二进制含 `--jitter` 特性 (R17 前置探测通过)
- 执行命令: `tools/check_v1_readiness.sh` (**全量档**, 非 `--quick` —— R4 E2E / R5 发布门禁 / R17 扰动抽检全部实跑; 总耗时约 109s)
- 退出码: **1** (仅 R6/R7 两项 L3 实物复核 P0 失败, 属预期硬闸门, 非软件缺陷)

## 1. 结论速览

**合计 24 项: 16 PASS / 2 FAIL / 6 SKIP (P0 失败 2 项, 全部为实物复核硬闸门)。**

工程侧判定: 软件门禁保持全绿, 与 234 基线 (`3d24d74`) 及更早 209 基线 (`95c26cd`) 结论一致 —— 内容批 F~I 扩容 (234 -> 250, 内容库收官) 后不变。全部自动可探测项 (含三个长跑项 R4/R5/R17) 全绿; 唯二失败 R6/R7 为 D4+ 实物复核缺口, 按设计须用户实搭清零 (`docs/PHYSICAL_REBUILD_CHECKLIST.md`), 不属工程可修复范围。本次运行无任何工程可修复的失败项。

与 234 基线的唯一口径变化: 内容批 F 新增 D4 模型 stonehenge_01 (巨石阵, 91 片/19 步, `4522fd7`), D4+ 待复核全集从 45 增至 **46** (R5 门禁阶段 3 与 R6/R7 计数随之 +1, 见 §4/§6)。

## 2. 逐项结果

| 检查 | 级别 | 结果 | 耗时 | 说明 |
| --- | --- | --- | --- | --- |
| R1 内容体量 | P0 | **PASS** | 0s | 模型 JSON 250 个 >= 门槛 200 (目标区间 200~250 上限达成) |
| R2 目录/缩略图对账 | P1 | **PASS** | 0s | 模型 250 / 目录登记 250 / 缩略图就绪 250, 三方一致 |
| R3 免费层清单对齐 | P0 | **PASS** | 0s | 免费标签 30 x starter 清单 x core-9 三条断言全过 |
| R4 E2E 冒烟 (全量) | P0 | **PASS** | 38s | 8 项通过 / 1 项 SKIP (详见 §3) |
| R5 发布门禁快检 (全量) | P0 | **PASS** | 60s | 3 个门禁关卡全过 (详见 §4) |
| R6 实物抽样包缺口 | P0 | **FAIL** | 0s | 预期失败: 抽样包缺口 10/10 (详见 §6) |
| R7 D4+ 实物复核清零 | P0 | **FAIL** | 0s | 预期失败: D4+ 46 个待复核 0/46 (详见 §6) |
| R8 隐私合规文档 | P0 | **PASS** | 0s | SECURITY_AND_PRIVACY + PRIVACY_POLICY_DRAFT 在位 |
| R9 桌面打包资产 | P0 | **PASS** | 0s | 打包手册/CPack/WiX/starter 清单/第三方声明/CI 齐备 |
| R10 计费适配层单测 | P1 | **PASS** | 0s | `magtile_billing_test` 实跑通过 (41 断言全绿) |
| R11 Google Play 计费接线 | P0 | **PASS** | 0s | 四项接线证据在位 (沙盒付费验收属人工项 B3) |
| R11W Windows 商店计费接线 | P0 | **PASS** | 0s | 五项接线证据在位 (MSIX 实包验收属人工项 B3/M1) |
| R12 Android 构建链路资产 | P1 | **PASS** | 0s | android.yml + build.gradle.kts + README + JNI 在位 |
| R13 Android release 签名 | P0 | **PASS** | 0s | signingConfigs + keystore.properties.example 齐备 |
| R14 商店上架文档守卫 | P0 | **PASS** | 0s | validate_store_listing 全过 (15+5 章节, 内链全有效) |
| R15 国内合规清单守卫 | P0 | **PASS** | 0s | 51 条 (P0 30 / P1 21) 全带级别与负责方, 交叉引用 5 项就位 |
| R16 儿童友好文案守卫 | P0 | **PASS** | 0s | 301 文件 / 8874 段用户可见中文文案, 零红线 |
| R17 D4+ 扰动仿真抽检 (全量) | P1 | **PASS** | 11s | 10/10 全绿, 每模型 --jitter 50 (详见 §5) |
| M1~M6 人工项 | P0 | SKIP x6 | - | 实机打包/真机验收/法务定稿/矩阵签核/实搭签核/备案 |

## 3. R4 E2E 冒烟明细 (全量实跑)

| 路径 | 结果 |
| --- | --- |
| E2E-01a CLI 启动冒烟 (catalog 13 片型) | PASS |
| E2E-11a 免费层清单对齐 (verify_free_tier) | PASS |
| E2E-11b CLI 免费筛选对账 (--free-only, 全库 250 中 30 个) | PASS |
| E2E-06a CLI 免费模型教程步进 (beach_hut_01, 44 片对账) | PASS |
| E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读 + 全量互通断言) | PASS |
| E2E-QT Qt 无头冒烟 (test_qt_smoke.sh, offscreen, 6 步) | PASS |
| E2E-12a Qt 进度页深链 (--smoke-open-progress) | PASS |
| E2E-04a/09a/11c/12b Qt 按钮级路径冒烟 (锁样本 aircraft_carrier_01) | PASS |
| E2E-14a Android JNI 符号断言 | SKIP |

E2E-14a SKIP 原因: 本环境无 Android NDK (默认档不阻断, CI 由 `android.yml` 兜底; 上架签核档 `--strict` 需补齐 NDK 环境)。

## 4. R5 发布门禁明细 (全量实跑)

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 1. 免费层清单对齐核验 | PASS | 免费标签 30 x starter 清单 x core-9 对齐 |
| 2. 弱磁严格档全库巡检 (strict) | PASS | 250 模型 strict 零警告审计 + 逐步装配质检 250/250 + D4+ 抗扰动巡检 46/46 (strict --jitter 50) 三阶段全绿 |
| 3. L3 实物复核缺口报告 (报告型) | PASS | 报告型关卡, 缺口列报不阻断 (硬闸门见 R6/R7) |

结论: 全部 3 个门禁关卡通过, 可进入打包流程。

## 5. R17 D4+ 扰动仿真抽检明细 (全量实跑)

抽样规则: D5 全数优先 + 大体量 D4 按总片数降序补足, 目标 10 个; 每模型 `validate --jitter 50`。抽样名单与 234 库时完全一致 —— 新入池的 stonehenge_01 (91 片) 未达大体量补足线 (第 10 名 school_bus_01 为 98 片), 不改变抽样。

| # | 模型 | 难度 | 片数 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | skyscraper_01 | D5 | 122 | PASS |
| 2 | stadium_gate_01 | D4 | 103 | PASS |
| 3 | rescue_hq_01 | D4 | 101 | PASS |
| 4 | ferry_terminal_01 | D4 | 100 | PASS |
| 5 | apartment_block_01 | D4 | 99 | PASS |
| 6 | castle_drawbridge_01 | D4 | 99 | PASS |
| 7 | steam_locomotive_01 | D4 | 99 | PASS |
| 8 | treehouse_02 | D4 | 99 | PASS |
| 9 | hospital_01 | D4 | 98 | PASS |
| 10 | school_bus_01 | D4 | 98 | PASS |

10/10 全绿, 软件侧不豁免 S1/S2 实搭。另: R5 门禁关卡 2 的阶段 3 已对全部 46 个 D4+ 模型 (含 stonehenge_01) 做 strict --jitter 50 全量巡检 (46/46 全绿), 覆盖面超出本抽检。

## 6. R6/R7 失败详情 (预期硬闸门, 非工程可修复)

- **R6**: 实物抽样包缺口 10/10 —— D4+ 46 个全部待复核, 抽样命中 S1=0 / S2=1 / S3=9 (skyscraper_01 / stadium_gate_01 / ferry_terminal_01 / castle_drawbridge_01 / treehouse_02 / elephant_01 / ball_run_tower_01 / stonehenge_01 / subway_station_01 / tennis_court_01), 预计实搭总耗时约 750 分钟 (约 12.5 小时)。已标注 `physical_verified` 的 3 个 D3 模型 (castle_foundation_01 / great_wall_01 / tokyo_tower_01) 一致性核对通过。
- **R7**: 扫描 250 模型, D4+ 共 46 个: 已复核 0, 待复核 46 (`--fail-on-pending` 生效)。

两项均为 L3 实物复核硬闸门: 需用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭后回填 `physical_verified` 标记 (缩减流程见 `docs/USER_HANDOFF.md` §4.3)。内容批 F~I 扩容 (234 -> 250) 新增 1 个 D4 模型 stonehenge_01, 待复核集合从 45 增至 46; 其余 45 个与前次运行完全一致。本次运行无任何非预期 / 工程可修复的失败项。

## 7. 下一步

1. 用户侧: 按 `docs/USER_HANDOFF.md` §4 完成实物 (R6/R7 清零)、行政、实机、沙盒验收
2. 签核档补充: 配 Android NDK 后以 `--strict` 复跑 E2E, 消除 E2E-14a SKIP

## 附录: 全量运行完整输出 (/tmp/readiness_full.log)

<details>
<summary>点开查看完整日志 (1396 行, NO_COLOR=1)</summary>

```text
==============================================================
 MagTile Studio V1 上架就绪自动探测
 对账清单: docs/V1_LAUNCH_CHECKLIST.md
 项目根: /workspace/magtile-studio
 档位: 全量
 内容体量门槛: 200 (上架目标区间 200~250)
==============================================================

==============================================================
 R1 [P0] 内容体量 (模型 JSON >= 200)
==============================================================
模型 JSON: 250 个 (门槛 200, 上架目标区间 200~250)
[断言通过] 内容体量达标
[通过] R1 内容体量 (模型 JSON >= 200)

==============================================================
 R2 [P1] 目录登记 / 缩略图对账
==============================================================
模型 JSON 250 / 目录登记 250 / 缩略图就绪 250
[断言通过] 模型 / 目录 / 缩略图三方对账一致
[通过] R2 目录登记 / 缩略图对账

==============================================================
 R3 [P0] 免费层清单对齐 (verify_free_tier)
==============================================================
==============================================================
 免费层三端清单对齐核验 (docs/FREE_TIER_MANIFEST.md)
==============================================================
扫描模型:            250
带 "免费" 标签:      30  (要求恰好 30)
免费层用扩展片型:    0  (要求 0, 全 core-9)
starter 清单条目:    30
两侧清单差异:        0  (要求 0)

三条断言全部通过: 免费标签 x starter 清单 x core-9 对齐。
==============================================================
[通过] R3 免费层清单对齐 (verify_free_tier)

==============================================================
 R4 [P0] E2E 冒烟 (run_e2e_smoke.sh)
==============================================================
==============================================================
 MagTile Studio 核心用户路径 E2E 冒烟
 路径矩阵: docs/E2E_TEST_MATRIX.md
 项目根: /workspace/magtile-studio
 CLI 构建: /workspace/magtile-studio/build / Qt 构建: /workspace/magtile-studio/build-qt
 档位: 默认 (SKIP 不阻断)
==============================================================

==============================================================
 E2E 冒烟 1: E2E-01a CLI 启动冒烟 (catalog 13 片型)
==============================================================
磁力片形状目录 (共 13 种, 其中核心 9 种):

[断言通过] 目录加载成功, 13 种片型齐全
[通过] E2E-01a CLI 启动冒烟 (catalog 13 片型)

==============================================================
 E2E 冒烟 2: E2E-11a 免费层清单对齐 (verify_free_tier)
==============================================================
==============================================================
 免费层三端清单对齐核验 (docs/FREE_TIER_MANIFEST.md)
==============================================================
扫描模型:            250
带 "免费" 标签:      30  (要求恰好 30)
免费层用扩展片型:    0  (要求 0, 全 core-9)
starter 清单条目:    30
两侧清单差异:        0  (要求 0)

三条断言全部通过: 免费标签 x starter 清单 x core-9 对齐。
==============================================================
[通过] E2E-11a 免费层清单对齐 (verify_free_tier)

==============================================================
 E2E 冒烟 3: E2E-11b CLI 免费筛选对账 (--free-only)
==============================================================
结论: 全库 250 个模型中 30 个属于免费层 (带「免费」标签) (目录对账通过)
提示: 家庭用户图形界面请使用 Qt 版 magtile_studio_qt (docs/QT_UI_PLAN.md);
      magtile_app library --dev-gui 为内容制作/调试用的开发者图形模型库
[断言通过] 免费筛选 30 个与清单一致, 抽样 beach_hut_01 在列, 目录对账通过
[通过] E2E-11b CLI 免费筛选对账 (--free-only)

==============================================================
 E2E 冒烟 4: E2E-06a CLI 免费模型教程步进 (beach_hut_01)
==============================================================

教程结束, 共放置 44 片磁力片。
[断言通过] 免费模型 beach_hut_01 教程全程步进, 44 片对账一致
[通过] E2E-06a CLI 免费模型教程步进 (beach_hut_01)

==============================================================
 E2E 冒烟 5: E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读)
==============================================================
  (a) CLI 写入端: settings set-age 4 (age_mode 键) ...
  (b) 独立读取端: python sqlite 直读 settings 表键契约 ...
  (c) CLI 回读端: settings show 读回启蒙模式 ...
  (d) 全量跨端互通断言 (magtile_cross_platform_test) ...
[通过] 写入端: 3 个完成记录落盘
[通过] 写入端: 成就统一收口解锁 1/3 两档
[通过] 写入端: 未达档成就不提前解锁
[通过] schema: age_4_6 持久化标识不漂移 (core/age_mode)
[通过] schema: age_mode 键按稳定标识编码落盘
[通过] schema: onboarding_age_done 键以 "1" 落盘
[通过] schema: subscription_active 键以 "1" 落盘
[通过] schema: subscription_product_id 键记录生效档位
[通过] schema: 样例存档 settings 表恰好 4 个契约键 (无隐藏键漂移)
[通过] 读取端: getAgeMode 读到写入端的启蒙模式
[通过] 读取端: 引导完成标记可读 (Qt 首启不再弹引导)
[通过] 读取端: 订阅状态可读 (免费层锁放行口径)
[通过] 读取端: 订阅档位 id 一致
[通过] 读取端: 完成列表 3 个模型
[通过] 读取端: 每个完成记录均带完成时刻
[通过] 读取端: 进行中记录保留断点步骤
[通过] 读取端: 成就墙恰好 2 枚 (1/3 两档, 无重复)
[通过] 读取端: 成就 id 全部出自 kAchievementTiers 档位表
[通过] 前向兼容: 未知设置键不影响契约键读取

跨端进度存档互通测试全部通过
[断言通过] 跨端存档 settings 键契约一致 (CLI 写 -> sqlite 直读 -> CLI 回读)
[通过] E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读)

==============================================================
 E2E 冒烟 6: E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)
==============================================================
[1/6] 默认启动 (首页) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[2/6] --parent-gate 深链 (家长门界面) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[3/6] --smoke-parent-flow 自动驾驶 (进度页->成就墙->门->家长中心->设置->订阅) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[4/6] --smoke-complete-model 完成链路 (完成存档 -> 庆祝页, QT-4) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[5/6] --smoke-age-onboarding 首启年龄段引导 (引导出现 -> 选档落盘, QT-5) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[6/6] --smoke-age-onboarding 同库二次启动 (引导只出现一次, QT-5) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
Qt 界面 QML 加载冒烟通过
[通过] E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)

==============================================================
 E2E 冒烟 7: E2E-12a Qt 进度页深链 (--smoke-open-progress)
==============================================================
  (a) --smoke-complete-model beach_hut_01 造非空存档 ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
  (b) --smoke-open-progress 深链实例化进度页 ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[断言通过] 完成存档落盘 + 进度页深链实例化, 无 QML 运行时错误
[通过] E2E-12a Qt 进度页深链 (--smoke-open-progress)

==============================================================
 E2E 冒烟 8: E2E-04a/09a/11c/12b Qt 按钮级路径冒烟
==============================================================
抽样: 免费=beach_hut_01 非免费=aircraft_carrier_01 片型=13 种
[1/4] --smoke-library-filters 筛选切换对账 (免费/主题/难度/清除, E2E-04a) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[2/4] --smoke-open-inventory 库存页深链 (步进 +3 -> 保存落盘, E2E-09a) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[3/4] --smoke-locked-model 非免费锁 (aircraft_carrier_01: 上锁 -> 家长门, E2E-11c) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
[4/4] --smoke-progress-data 进度页有数据断言 (完成造档 -> 成就非空, E2E-12b) ...
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-ubuntu'
Qt 界面按钮级路径冒烟通过
[通过] E2E-04a/09a/11c/12b Qt 按钮级路径冒烟

[跳过] E2E-14a Android JNI 符号断言 —— 未检测到 Android NDK (设 ANDROID_NDK 或 ANDROID_HOME 后重试; CI 由 android.yml 兜底)

==============================================================
 E2E 冒烟报告 (路径矩阵: docs/E2E_TEST_MATRIX.md)
==============================================================
  PASS   E2E-01a CLI 启动冒烟 (catalog 13 片型)         0s
  PASS   E2E-11a 免费层清单对齐 (verify_free_tier)     0s
  PASS   E2E-11b CLI 免费筛选对账 (--free-only)         0s
  PASS   E2E-06a CLI 免费模型教程步进 (beach_hut_01)  0s
  PASS   E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读) 0s
  PASS   E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)            16s
  PASS   E2E-12a Qt 进度页深链 (--smoke-open-progress)   5s
  PASS   E2E-04a/09a/11c/12b Qt 按钮级路径冒烟         17s
  SKIP   E2E-14a Android JNI 符号断言                     -
--------------------------------------------------------------
 提醒: 1 项 SKIP (默认档不阻断); 上架签核请用 --strict 并补齐环境
 结论: 8 项通过 (1 项跳过), 自动子集全绿
 人工侧: 按 docs/E2E_TEST_MATRIX.md 第 1 节 P0 的 Manual 要点逐条打钩
[通过] R4 E2E 冒烟 (run_e2e_smoke.sh)

==============================================================
 R5 [P0] 发布门禁快检 (run_release_gate.sh)
==============================================================
==============================================================
 MagTile Studio 发布门禁 (Release Gate)
 项目根: /workspace/magtile-studio
 构建目录: /workspace/magtile-studio/build
 档位: 默认 (三道发布专项)
==============================================================

==============================================================
 门禁关卡 1: 免费层清单对齐核验
 $ /usr/bin/python3 /workspace/magtile-studio/tools/verify_free_tier.py --models-dir /workspace/magtile-studio/data/models --catalog /workspace/magtile-studio/data/tile_catalog.json
==============================================================
==============================================================
 免费层三端清单对齐核验 (docs/FREE_TIER_MANIFEST.md)
==============================================================
扫描模型:            250
带 "免费" 标签:      30  (要求恰好 30)
免费层用扩展片型:    0  (要求 0, 全 core-9)
starter 清单条目:    30
两侧清单差异:        0  (要求 0)

三条断言全部通过: 免费标签 x starter 清单 x core-9 对齐。
==============================================================
[通过] 免费层清单对齐核验

==============================================================
 门禁关卡 2: 弱磁严格档全库巡检 (strict)
 $ bash /workspace/magtile-studio/tools/run_strict_audit.sh /workspace/magtile-studio/build
==============================================================

>> 阶段 1/3: 全库 validate --profile strict (零警告政策)
==============================================================
 弱磁严格档物理审计: 共 250 个模型 (--profile strict, 零警告政策)
==============================================================
[通过] aircraft_carrier_01
[通过] airport_terminal_01
[通过] airport_terminal_02
[通过] ambulance_01
[通过] amphitheater_01
[通过] apartment_block_01
[通过] apiary_01
[通过] aquarium_tunnel_01
[通过] art_gallery_01
[通过] asteroid_mining_01
[通过] astronaut_training_01
[通过] bakery_shop_01
[通过] ball_run_tower_01
[通过] bamboo_house_01
[通过] basketball_arena_01
[通过] basketball_court_01
[通过] beach_hut_01
[通过] bike_rack_park_01
[通过] birthday_party_01
[通过] bowling_alley_01
[通过] boxing_ring_01
[通过] bridge_wood_01
[通过] bulldozer_01
[通过] bullet_train_01
[通过] butterfly_01
[通过] butterfly_garden_01
[通过] cabin_lake_01
[通过] cable_car_01
[通过] cactus_desert_01
[通过] campfire_site_01
[通过] canal_lock_01
[通过] canoe_01
[通过] capsule_recovery_01
[通过] cargo_plane_01
[通过] cargo_ship_01
[通过] carousel_01
[通过] car_repair_shop_01
[通过] car_wash_01
[通过] castle_drawbridge_01
[通过] castle_foundation_01
[通过] castle_tower_01
[通过] cement_mixer_01
[通过] chicken_coop_01
[通过] chinese_garden_01
[通过] christmas_market_01
[通过] circus_tent_01
[通过] city_bus_stop_01
[通过] climbing_wall_01
[通过] clock_tower_01
[通过] combine_harvester_01
[通过] control_tower_01
[通过] conveyor_factory_01
[通过] coral_reef_01
[通过] coral_reef_02
[通过] corn_maze_01
[通过] covered_bridge_01
[通过] crane_tower_01
[通过] crane_tower_02
[通过] crocodile_01
[通过] cruise_ship_01
[通过] deep_sea_lab_01
[通过] dental_clinic_01
[通过] desk_organizer_01
[通过] dinosaur_hall_01
[通过] dinosaur_stego_01
[通过] diving_tower_01
[通过] dragon_boat_01
[通过] dragon_cave_01
[通过] drawbridge_01
[通过] drive_in_cinema_01
[通过] drone_pad_01
[通过] drum_set_01
[通过] dump_truck_01
[通过] eiffel_tower_01
[通过] elephant_01
[通过] elephant_pavilion_01
[通过] er_entrance_01
[通过] excavator_01
[通过] eye_clinic_01
[通过] fairy_castle_01
[通过] farm_barn_01
[通过] farm_silo_01
[通过] ferris_wheel_frame_01
[通过] ferry_terminal_01
[通过] fireboat_01
[通过] fire_station_01
[通过] fire_truck_01
[通过] fireworks_show_01
[通过] fishing_boat_01
[通过] flag_plaza_01
[通过] food_truck_01
[通过] forklift_01
[通过] fountain_plaza_01
[通过] freight_yard_01
[通过] gas_station_01
[通过] geodesic_dome_01
[通过] gingerbread_house_01
[通过] giraffe_01
[通过] great_wall_01
[通过] greenhouse_01
[通过] greenhouse_dome_01
[通过] hangar_01
[通过] hanging_garden_01
[通过] harbor_crane_01
[通过] hedgehog_01
[通过] helicopter_01
[通过] helicopter_pad_01
[通过] horse_stable_01
[通过] hospital_01
[通过] hot_air_balloon_01
[通过] hydro_dam_01
[通过] ice_cream_truck_01
[通过] ice_rink_01
[通过] igloo_01
[通过] jungle_gym_01
[通过] kangaroo_01
[通过] kindergarten_01
[通过] knight_armor_01
[通过] lantern_festival_01
[通过] lego_style_house_01
[通过] library_building_01
[通过] lifeguard_tower_01
[通过] lighthouse_01
[通过] lighthouse_pier_01
[通过] lion_dance_01
[通过] lunar_lander_01
[通过] magic_tree_01
[通过] marble_dash_lane_01
[通过] marble_run_spiral_01
[通过] marching_band_01
[通过] mars_habitat_01
[通过] mars_rover_01
[通过] medieval_gate_01
[通过] merry_go_round_01
[通过] mission_control_01
[通过] monorail_01
[通过] moon_festival_altar_01
[通过] moon_lander_01
[通过] mountain_rail_01
[通过] museum_01
[通过] mushroom_grove_01
[通过] oasis_01
[通过] observatory_01
[通过] octopus_01
[通过] open_air_cinema_01
[通过] owl_01
[通过] pagoda_01
[通过] panda_bamboo_01
[通过] parking_garage_01
[通过] particle_accelerator_01
[通过] peacock_01
[通过] pedestrian_overpass_01
[通过] penguin_01
[通过] penguin_pool_01
[通过] pet_clinic_01
[通过] piano_stage_01
[通过] pipe_organ_01
[通过] pirate_ship_01
[通过] planetarium_01
[通过] planetarium_02
[通过] police_car_01
[通过] police_station_01
[通过] post_office_01
[通过] pumpkin_lantern_01
[通过] puppet_theater_01
[通过] pyramid_giza_01
[通过] race_track_01
[通过] radio_telescope_01
[通过] railway_crossing_01
[通过] rainforest_canopy_01
[通过] recycling_center_01
[通过] rehab_park_01
[通过] rescue_hq_01
[通过] rice_terrace_01
[通过] road_construction_01
[通过] robot_01
[通过] robot_arm_01
[通过] robot_lab_01
[通过] rocket_crawler_01
[通过] rocket_launchpad_01
[通过] roller_coaster_hill_01
[通过] roller_coaster_loop_01
[通过] roman_aqueduct_01
[通过] rose_pergola_01
[通过] safari_lodge_01
[通过] sailboat_01
[通过] sandbox_park_01
[通过] santa_sleigh_01
[通过] satellite_dish_01
[通过] scaffolding_site_01
[通过] school_bus_01
[通过] schoolyard_stand_01
[通过] science_lab_01
[通过] sculpture_plaza_01
[通过] sheep_farm_01
[通过] skate_park_01
[通过] ski_jump_01
[通过] ski_lodge_01
[通过] skyscraper_01
[通过] slide_playground_01
[通过] snowman_01
[通过] snowplow_01
[通过] soccer_goal_01
[通过] solar_farm_01
[通过] space_elevator_01
[通过] space_shuttle_01
[通过] space_station_01
[通过] spider_bot_01
[通过] stadium_gate_01
[通过] steam_locomotive_01
[通过] stonehenge_01
[通过] submarine_01
[通过] submarine_dock_01
[通过] subway_station_01
[通过] supermarket_01
[豁免] suspension_bridge_01 (5 条已豁免警告, 理由见 docs/STRICT_PHYSICS_AUDIT.md)
        [警告] 第 7 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 8 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 9 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 10 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 11 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
[通过] suspension_rail_01
[通过] swimming_pool_01
[通过] swing_set_01
[通过] sydney_opera_01
[通过] taxi_01
[通过] temple_greek_01
[通过] tennis_court_01
[通过] tessellation_screen_01
[通过] tokyo_tower_01
[通过] toll_station_01
[通过] tow_truck_01
[通过] tractor_01
[通过] traffic_light_junction_01
[通过] trailer_home_01
[通过] train_station_01
[通过] trebuchet_01
[通过] treehouse_01
[通过] treehouse_02
[通过] trex_skeleton_01
[通过] triumphal_arch_01
[通过] truss_bridge_01
[通过] turtle_beach_01
[通过] violin_shop_01
[通过] volcano_base_01
[通过] warehouse_01
[通过] water_slide_park_01
[通过] water_tower_01
[通过] weather_station_01
[通过] whale_01
[通过] whale_watching_01
[通过] windmill_01
[通过] wind_turbine_01
[通过] wizard_tower_01
[通过] yurt_01

==============================================================
 汇总: 通过 249 / 豁免 1 / 警告 0 / 失败 0 (共 250 个模型)
==============================================================
 结果: 全库 250 个模型 strict 档零未豁免警告零错误 (含 1 个白名单豁免)

>> 阶段 2/3: 全库逐步装配质检 (test_step_assembly.py)
==============================================================
 逐步装配质检 (逐片零差错 P1~P8): 共 250 个模型
 形状目录: /workspace/magtile-studio/data/tile_catalog.json
==============================================================

[PASS] aircraft_carrier_01.json: 84 片 / 18 步 / 高亮引用 28 处 / 逐片连通检查 84 片

[PASS] airport_terminal_01.json: 77 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 77 片

[PASS] airport_terminal_02.json: 72 片 / 14 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] ambulance_01.json: 53 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 53 片

[PASS] amphitheater_01.json: 70 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 70 片

[PASS] apartment_block_01.json: 99 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 99 片

[PASS] apiary_01.json: 47 片 / 10 步 / 高亮引用 10 处 / 逐片连通检查 47 片

[PASS] aquarium_tunnel_01.json: 52 片 / 12 步 / 高亮引用 11 处 / 逐片连通检查 52 片

[PASS] art_gallery_01.json: 69 片 / 13 步 / 高亮引用 17 处 / 逐片连通检查 69 片

[PASS] asteroid_mining_01.json: 67 片 / 14 步 / 高亮引用 21 处 / 逐片连通检查 67 片

[PASS] astronaut_training_01.json: 48 片 / 10 步 / 高亮引用 12 处 / 逐片连通检查 48 片

[PASS] bakery_shop_01.json: 72 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 72 片

[PASS] ball_run_tower_01.json: 94 片 / 19 步 / 高亮引用 38 处 / 逐片连通检查 94 片

[PASS] bamboo_house_01.json: 62 片 / 17 步 / 高亮引用 29 处 / 逐片连通检查 62 片

[PASS] basketball_arena_01.json: 83 片 / 18 步 / 高亮引用 42 处 / 逐片连通检查 83 片

[PASS] basketball_court_01.json: 52 片 / 15 步 / 高亮引用 22 处 / 逐片连通检查 52 片

[PASS] beach_hut_01.json: 44 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 44 片

[PASS] bike_rack_park_01.json: 62 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 62 片

[PASS] birthday_party_01.json: 69 片 / 14 步 / 高亮引用 20 处 / 逐片连通检查 69 片

[PASS] bowling_alley_01.json: 56 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 56 片

[PASS] boxing_ring_01.json: 46 片 / 10 步 / 高亮引用 10 处 / 逐片连通检查 46 片

[PASS] bridge_wood_01.json: 64 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 64 片

[PASS] bulldozer_01.json: 72 片 / 16 步 / 高亮引用 28 处 / 逐片连通检查 72 片

[PASS] bullet_train_01.json: 60 片 / 12 步 / 高亮引用 16 处 / 逐片连通检查 60 片

[PASS] butterfly_01.json: 55 片 / 16 步 / 高亮引用 22 处 / 逐片连通检查 55 片

[PASS] butterfly_garden_01.json: 73 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 73 片

[PASS] cabin_lake_01.json: 66 片 / 17 步 / 高亮引用 28 处 / 逐片连通检查 66 片

[PASS] cable_car_01.json: 64 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 64 片

[PASS] cactus_desert_01.json: 72 片 / 15 步 / 高亮引用 23 处 / 逐片连通检查 72 片

[PASS] campfire_site_01.json: 66 片 / 16 步 / 高亮引用 23 处 / 逐片连通检查 66 片

[PASS] canal_lock_01.json: 53 片 / 12 步 / 高亮引用 17 处 / 逐片连通检查 53 片

[PASS] canoe_01.json: 68 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 68 片

[PASS] capsule_recovery_01.json: 42 片 / 10 步 / 高亮引用 12 处 / 逐片连通检查 42 片

[PASS] car_repair_shop_01.json: 45 片 / 10 步 / 高亮引用 9 处 / 逐片连通检查 45 片

[PASS] car_wash_01.json: 58 片 / 12 步 / 高亮引用 16 处 / 逐片连通检查 58 片

[PASS] cargo_plane_01.json: 69 片 / 13 步 / 高亮引用 21 处 / 逐片连通检查 69 片

[PASS] cargo_ship_01.json: 87 片 / 18 步 / 高亮引用 31 处 / 逐片连通检查 87 片

[PASS] carousel_01.json: 54 片 / 17 步 / 高亮引用 27 处 / 逐片连通检查 54 片

[PASS] castle_drawbridge_01.json: 99 片 / 21 步 / 高亮引用 47 处 / 逐片连通检查 99 片

[PASS] castle_foundation_01.json: 72 片 / 16 步 / 高亮引用 68 处 / 逐片连通检查 72 片

[PASS] castle_tower_01.json: 75 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 75 片

[PASS] cement_mixer_01.json: 69 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 69 片

[PASS] chicken_coop_01.json: 62 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 62 片

[PASS] chinese_garden_01.json: 52 片 / 17 步 / 高亮引用 25 处 / 逐片连通检查 52 片

[PASS] christmas_market_01.json: 68 片 / 14 步 / 高亮引用 20 处 / 逐片连通检查 68 片

[PASS] circus_tent_01.json: 73 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 73 片

[PASS] city_bus_stop_01.json: 46 片 / 10 步 / 高亮引用 16 处 / 逐片连通检查 46 片

[PASS] climbing_wall_01.json: 62 片 / 14 步 / 高亮引用 18 处 / 逐片连通检查 62 片

[PASS] clock_tower_01.json: 67 片 / 16 步 / 高亮引用 28 处 / 逐片连通检查 67 片

[PASS] combine_harvester_01.json: 74 片 / 14 步 / 高亮引用 26 处 / 逐片连通检查 74 片

[PASS] control_tower_01.json: 62 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 62 片

[PASS] conveyor_factory_01.json: 71 片 / 15 步 / 高亮引用 24 处 / 逐片连通检查 71 片

[PASS] coral_reef_01.json: 55 片 / 16 步 / 高亮引用 20 处 / 逐片连通检查 55 片

[PASS] coral_reef_02.json: 57 片 / 14 步 / 高亮引用 22 处 / 逐片连通检查 57 片

[PASS] corn_maze_01.json: 75 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 75 片

[PASS] covered_bridge_01.json: 94 片 / 18 步 / 高亮引用 40 处 / 逐片连通检查 94 片

[PASS] crane_tower_01.json: 68 片 / 16 步 / 高亮引用 20 处 / 逐片连通检查 68 片

[PASS] crane_tower_02.json: 75 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 75 片

[PASS] crocodile_01.json: 53 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 53 片

[PASS] cruise_ship_01.json: 67 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 67 片

[PASS] deep_sea_lab_01.json: 64 片 / 13 步 / 高亮引用 14 处 / 逐片连通检查 64 片

[PASS] dental_clinic_01.json: 61 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 61 片

[PASS] desk_organizer_01.json: 42 片 / 10 步 / 高亮引用 13 处 / 逐片连通检查 42 片

[PASS] dinosaur_hall_01.json: 84 片 / 18 步 / 高亮引用 19 处 / 逐片连通检查 84 片

[PASS] dinosaur_stego_01.json: 69 片 / 17 步 / 高亮引用 27 处 / 逐片连通检查 69 片

[PASS] diving_tower_01.json: 62 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 62 片

[PASS] dragon_boat_01.json: 72 片 / 17 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] dragon_cave_01.json: 75 片 / 14 步 / 高亮引用 17 处 / 逐片连通检查 75 片

[PASS] drawbridge_01.json: 66 片 / 13 步 / 高亮引用 19 处 / 逐片连通检查 66 片

[PASS] drive_in_cinema_01.json: 70 片 / 14 步 / 高亮引用 13 处 / 逐片连通检查 70 片

[PASS] drone_pad_01.json: 75 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 75 片

[PASS] drum_set_01.json: 57 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 57 片

[PASS] dump_truck_01.json: 74 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 74 片

[PASS] eiffel_tower_01.json: 95 片 / 21 步 / 高亮引用 25 处 / 逐片连通检查 95 片

[PASS] elephant_01.json: 95 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 95 片

[PASS] elephant_pavilion_01.json: 75 片 / 15 步 / 高亮引用 24 处 / 逐片连通检查 75 片

[PASS] er_entrance_01.json: 63 片 / 13 步 / 高亮引用 22 处 / 逐片连通检查 63 片

[PASS] excavator_01.json: 55 片 / 18 步 / 高亮引用 28 处 / 逐片连通检查 55 片

[PASS] eye_clinic_01.json: 71 片 / 13 步 / 高亮引用 16 处 / 逐片连通检查 71 片

[PASS] fairy_castle_01.json: 66 片 / 13 步 / 高亮引用 18 处 / 逐片连通检查 66 片

[PASS] farm_barn_01.json: 65 片 / 17 步 / 高亮引用 26 处 / 逐片连通检查 65 片

[PASS] farm_silo_01.json: 69 片 / 16 步 / 高亮引用 23 处 / 逐片连通检查 69 片

[PASS] ferris_wheel_frame_01.json: 56 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 56 片

[PASS] ferry_terminal_01.json: 100 片 / 19 步 / 高亮引用 32 处 / 逐片连通检查 100 片

[PASS] fire_station_01.json: 81 片 / 19 步 / 高亮引用 26 处 / 逐片连通检查 81 片

[PASS] fire_truck_01.json: 69 片 / 16 步 / 高亮引用 30 处 / 逐片连通检查 69 片

[PASS] fireboat_01.json: 63 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 63 片

[PASS] fireworks_show_01.json: 73 片 / 13 步 / 高亮引用 18 处 / 逐片连通检查 73 片

[PASS] fishing_boat_01.json: 63 片 / 16 步 / 高亮引用 28 处 / 逐片连通检查 63 片

[PASS] flag_plaza_01.json: 60 片 / 13 步 / 高亮引用 15 处 / 逐片连通检查 60 片

[PASS] food_truck_01.json: 51 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 51 片

[PASS] forklift_01.json: 46 片 / 10 步 / 高亮引用 15 处 / 逐片连通检查 46 片

[PASS] fountain_plaza_01.json: 73 片 / 17 步 / 高亮引用 26 处 / 逐片连通检查 73 片

[PASS] freight_yard_01.json: 85 片 / 20 步 / 高亮引用 33 处 / 逐片连通检查 85 片

[PASS] gas_station_01.json: 64 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 64 片

[PASS] geodesic_dome_01.json: 49 片 / 15 步 / 高亮引用 18 处 / 逐片连通检查 49 片

[PASS] gingerbread_house_01.json: 45 片 / 9 步 / 高亮引用 9 处 / 逐片连通检查 45 片

[PASS] giraffe_01.json: 52 片 / 16 步 / 高亮引用 23 处 / 逐片连通检查 52 片

[PASS] great_wall_01.json: 72 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 72 片

[PASS] greenhouse_01.json: 56 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 56 片

[PASS] greenhouse_dome_01.json: 66 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 66 片

[PASS] hangar_01.json: 74 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 74 片

[PASS] hanging_garden_01.json: 85 片 / 18 步 / 高亮引用 31 处 / 逐片连通检查 85 片

[PASS] harbor_crane_01.json: 86 片 / 19 步 / 高亮引用 31 处 / 逐片连通检查 86 片

[PASS] hedgehog_01.json: 53 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 53 片

[PASS] helicopter_01.json: 87 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 87 片

[PASS] helicopter_pad_01.json: 71 片 / 17 步 / 高亮引用 30 处 / 逐片连通检查 71 片

[PASS] horse_stable_01.json: 56 片 / 13 步 / 高亮引用 12 处 / 逐片连通检查 56 片

[PASS] hospital_01.json: 98 片 / 18 步 / 高亮引用 33 处 / 逐片连通检查 98 片

[PASS] hot_air_balloon_01.json: 69 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 69 片

[PASS] hydro_dam_01.json: 62 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 62 片

[PASS] ice_cream_truck_01.json: 73 片 / 16 步 / 高亮引用 30 处 / 逐片连通检查 73 片

[PASS] ice_rink_01.json: 84 片 / 19 步 / 高亮引用 28 处 / 逐片连通检查 84 片

[PASS] igloo_01.json: 66 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 66 片

[PASS] jungle_gym_01.json: 65 片 / 13 步 / 高亮引用 19 处 / 逐片连通检查 65 片

[PASS] kangaroo_01.json: 70 片 / 13 步 / 高亮引用 16 处 / 逐片连通检查 70 片

[PASS] kindergarten_01.json: 61 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 61 片

[PASS] knight_armor_01.json: 56 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 56 片

[PASS] lantern_festival_01.json: 57 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 57 片

[PASS] lego_style_house_01.json: 61 片 / 17 步 / 高亮引用 25 处 / 逐片连通检查 61 片

[PASS] library_building_01.json: 90 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 90 片

[PASS] lifeguard_tower_01.json: 48 片 / 11 步 / 高亮引用 10 处 / 逐片连通检查 48 片

[PASS] lighthouse_01.json: 77 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 77 片

[PASS] lighthouse_pier_01.json: 72 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 72 片

[PASS] lion_dance_01.json: 75 片 / 14 步 / 高亮引用 14 处 / 逐片连通检查 75 片

[PASS] lunar_lander_01.json: 63 片 / 16 步 / 高亮引用 39 处 / 逐片连通检查 63 片

[PASS] magic_tree_01.json: 58 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 58 片

[PASS] marble_dash_lane_01.json: 53 片 / 12 步 / 高亮引用 19 处 / 逐片连通检查 53 片

[PASS] marble_run_spiral_01.json: 80 片 / 18 步 / 高亮引用 36 处 / 逐片连通检查 80 片

[PASS] marching_band_01.json: 74 片 / 14 步 / 高亮引用 18 处 / 逐片连通检查 74 片

[PASS] mars_habitat_01.json: 64 片 / 12 步 / 高亮引用 11 处 / 逐片连通检查 64 片

[PASS] mars_rover_01.json: 56 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 56 片

[PASS] medieval_gate_01.json: 66 片 / 12 步 / 高亮引用 16 处 / 逐片连通检查 66 片

[PASS] merry_go_round_01.json: 75 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 75 片

[PASS] mission_control_01.json: 52 片 / 13 步 / 高亮引用 17 处 / 逐片连通检查 52 片

[PASS] monorail_01.json: 56 片 / 12 步 / 高亮引用 21 处 / 逐片连通检查 56 片

[PASS] moon_festival_altar_01.json: 55 片 / 12 步 / 高亮引用 19 处 / 逐片连通检查 55 片

[PASS] moon_lander_01.json: 63 片 / 15 步 / 高亮引用 22 处 / 逐片连通检查 63 片

[PASS] mountain_rail_01.json: 61 片 / 13 步 / 高亮引用 22 处 / 逐片连通检查 61 片

[PASS] museum_01.json: 68 片 / 16 步 / 高亮引用 30 处 / 逐片连通检查 68 片

[PASS] mushroom_grove_01.json: 51 片 / 12 步 / 高亮引用 15 处 / 逐片连通检查 51 片

[PASS] oasis_01.json: 72 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 72 片

[PASS] observatory_01.json: 53 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 53 片

[PASS] octopus_01.json: 53 片 / 10 步 / 高亮引用 9 处 / 逐片连通检查 53 片

[PASS] open_air_cinema_01.json: 54 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 54 片

[PASS] owl_01.json: 52 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 52 片

[PASS] pagoda_01.json: 73 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 73 片

[PASS] panda_bamboo_01.json: 65 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 65 片

[PASS] parking_garage_01.json: 82 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 82 片

[PASS] particle_accelerator_01.json: 72 片 / 14 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] peacock_01.json: 50 片 / 12 步 / 高亮引用 14 处 / 逐片连通检查 50 片

[PASS] pedestrian_overpass_01.json: 65 片 / 13 步 / 高亮引用 18 处 / 逐片连通检查 65 片

[PASS] penguin_01.json: 54 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 54 片

[PASS] penguin_pool_01.json: 63 片 / 13 步 / 高亮引用 17 处 / 逐片连通检查 63 片

[PASS] pet_clinic_01.json: 96 片 / 18 步 / 高亮引用 25 处 / 逐片连通检查 96 片

[PASS] piano_stage_01.json: 67 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 67 片

[PASS] pipe_organ_01.json: 74 片 / 13 步 / 高亮引用 16 处 / 逐片连通检查 74 片

[PASS] pirate_ship_01.json: 74 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 74 片

[PASS] planetarium_01.json: 68 片 / 17 步 / 高亮引用 29 处 / 逐片连通检查 68 片

[PASS] planetarium_02.json: 74 片 / 12 步 / 高亮引用 15 处 / 逐片连通检查 74 片

[PASS] police_car_01.json: 53 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 53 片

[PASS] police_station_01.json: 75 片 / 17 步 / 高亮引用 30 处 / 逐片连通检查 75 片

[PASS] post_office_01.json: 97 片 / 19 步 / 高亮引用 30 处 / 逐片连通检查 97 片

[PASS] pumpkin_lantern_01.json: 62 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 62 片

[PASS] puppet_theater_01.json: 46 片 / 10 步 / 高亮引用 11 处 / 逐片连通检查 46 片

[PASS] pyramid_giza_01.json: 64 片 / 17 步 / 高亮引用 49 处 / 逐片连通检查 64 片

[PASS] race_track_01.json: 82 片 / 18 步 / 高亮引用 30 处 / 逐片连通检查 82 片

[PASS] radio_telescope_01.json: 62 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 62 片

[PASS] railway_crossing_01.json: 62 片 / 13 步 / 高亮引用 22 处 / 逐片连通检查 62 片

[PASS] rainforest_canopy_01.json: 90 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 90 片

[PASS] recycling_center_01.json: 65 片 / 13 步 / 高亮引用 15 处 / 逐片连通检查 65 片

[PASS] rehab_park_01.json: 41 片 / 9 步 / 高亮引用 13 处 / 逐片连通检查 41 片

[PASS] rescue_hq_01.json: 101 片 / 18 步 / 高亮引用 69 处 / 逐片连通检查 101 片

[PASS] rice_terrace_01.json: 74 片 / 15 步 / 高亮引用 25 处 / 逐片连通检查 74 片

[PASS] road_construction_01.json: 72 片 / 15 步 / 高亮引用 22 处 / 逐片连通检查 72 片

[PASS] robot_01.json: 74 片 / 16 步 / 高亮引用 22 处 / 逐片连通检查 74 片

[PASS] robot_arm_01.json: 46 片 / 10 步 / 高亮引用 14 处 / 逐片连通检查 46 片

[PASS] robot_lab_01.json: 64 片 / 13 步 / 高亮引用 19 处 / 逐片连通检查 64 片

[PASS] rocket_crawler_01.json: 49 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 49 片

[PASS] rocket_launchpad_01.json: 82 片 / 18 步 / 高亮引用 31 处 / 逐片连通检查 82 片

[PASS] roller_coaster_hill_01.json: 60 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 60 片

[PASS] roller_coaster_loop_01.json: 57 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 57 片

[PASS] roman_aqueduct_01.json: 79 片 / 18 步 / 高亮引用 24 处 / 逐片连通检查 79 片

[PASS] rose_pergola_01.json: 43 片 / 9 步 / 高亮引用 13 处 / 逐片连通检查 43 片

[PASS] safari_lodge_01.json: 72 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] sailboat_01.json: 68 片 / 15 步 / 高亮引用 30 处 / 逐片连通检查 68 片

[PASS] sandbox_park_01.json: 63 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 63 片

[PASS] santa_sleigh_01.json: 47 片 / 10 步 / 高亮引用 10 处 / 逐片连通检查 47 片

[PASS] satellite_dish_01.json: 67 片 / 14 步 / 高亮引用 21 处 / 逐片连通检查 67 片

[PASS] scaffolding_site_01.json: 73 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 73 片

[PASS] school_bus_01.json: 98 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 98 片

[PASS] schoolyard_stand_01.json: 75 片 / 15 步 / 高亮引用 20 处 / 逐片连通检查 75 片

[PASS] science_lab_01.json: 67 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 67 片

[PASS] sculpture_plaza_01.json: 56 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 56 片

[PASS] sheep_farm_01.json: 74 片 / 15 步 / 高亮引用 19 处 / 逐片连通检查 74 片

[PASS] skate_park_01.json: 60 片 / 15 步 / 高亮引用 21 处 / 逐片连通检查 60 片

[PASS] ski_jump_01.json: 54 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 54 片

[PASS] ski_lodge_01.json: 55 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 55 片

[PASS] skyscraper_01.json: 122 片 / 26 步 / 高亮引用 73 处 / 逐片连通检查 122 片

[PASS] slide_playground_01.json: 67 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 67 片

[PASS] snowman_01.json: 72 片 / 14 步 / 高亮引用 13 处 / 逐片连通检查 72 片

[PASS] snowplow_01.json: 44 片 / 10 步 / 高亮引用 14 处 / 逐片连通检查 44 片

[PASS] soccer_goal_01.json: 81 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 81 片

[PASS] solar_farm_01.json: 53 片 / 13 步 / 高亮引用 21 处 / 逐片连通检查 53 片

[PASS] space_elevator_01.json: 72 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 72 片

[PASS] space_shuttle_01.json: 68 片 / 15 步 / 高亮引用 19 处 / 逐片连通检查 68 片

[PASS] space_station_01.json: 69 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 69 片

[PASS] spider_bot_01.json: 62 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 62 片

[PASS] stadium_gate_01.json: 103 片 / 18 步 / 高亮引用 33 处 / 逐片连通检查 103 片

[PASS] steam_locomotive_01.json: 99 片 / 18 步 / 高亮引用 34 处 / 逐片连通检查 99 片

[PASS] stonehenge_01.json: 91 片 / 19 步 / 高亮引用 24 处 / 逐片连通检查 91 片

[PASS] submarine_01.json: 75 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 75 片

[PASS] submarine_dock_01.json: 89 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 89 片

[PASS] subway_station_01.json: 87 片 / 18 步 / 高亮引用 30 处 / 逐片连通检查 87 片

[PASS] supermarket_01.json: 67 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 67 片

[PASS] suspension_bridge_01.json: 74 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 74 片

[PASS] suspension_rail_01.json: 75 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 75 片

[PASS] swimming_pool_01.json: 64 片 / 16 步 / 高亮引用 22 处 / 逐片连通检查 64 片

[PASS] swing_set_01.json: 47 片 / 10 步 / 高亮引用 13 处 / 逐片连通检查 47 片

[PASS] sydney_opera_01.json: 57 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 57 片

[PASS] taxi_01.json: 53 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 53 片

[PASS] temple_greek_01.json: 95 片 / 18 步 / 高亮引用 34 处 / 逐片连通检查 95 片

[PASS] tennis_court_01.json: 86 片 / 20 步 / 高亮引用 27 处 / 逐片连通检查 86 片

[PASS] tessellation_screen_01.json: 42 片 / 9 步 / 高亮引用 17 处 / 逐片连通检查 42 片

[PASS] tokyo_tower_01.json: 69 片 / 17 步 / 高亮引用 29 处 / 逐片连通检查 69 片

[PASS] toll_station_01.json: 69 片 / 12 步 / 高亮引用 19 处 / 逐片连通检查 69 片

[PASS] tow_truck_01.json: 44 片 / 10 步 / 高亮引用 9 处 / 逐片连通检查 44 片

[PASS] tractor_01.json: 55 片 / 16 步 / 高亮引用 28 处 / 逐片连通检查 55 片

[PASS] traffic_light_junction_01.json: 74 片 / 13 步 / 高亮引用 15 处 / 逐片连通检查 74 片

[PASS] trailer_home_01.json: 67 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 67 片

[PASS] train_station_01.json: 75 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 75 片

[PASS] trebuchet_01.json: 57 片 / 12 步 / 高亮引用 15 处 / 逐片连通检查 57 片

[PASS] treehouse_01.json: 79 片 / 18 步 / 高亮引用 27 处 / 逐片连通检查 79 片

[PASS] treehouse_02.json: 99 片 / 18 步 / 高亮引用 31 处 / 逐片连通检查 99 片

[PASS] trex_skeleton_01.json: 73 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 73 片

[PASS] triumphal_arch_01.json: 88 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 88 片

[PASS] truss_bridge_01.json: 73 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 73 片

[PASS] turtle_beach_01.json: 48 片 / 8 步 / 高亮引用 8 处 / 逐片连通检查 48 片

[PASS] violin_shop_01.json: 64 片 / 13 步 / 高亮引用 17 处 / 逐片连通检查 64 片

[PASS] volcano_base_01.json: 83 片 / 18 步 / 高亮引用 33 处 / 逐片连通检查 83 片

[PASS] warehouse_01.json: 97 片 / 18 步 / 高亮引用 28 处 / 逐片连通检查 97 片

[PASS] water_slide_park_01.json: 65 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 65 片

[PASS] water_tower_01.json: 74 片 / 12 步 / 高亮引用 21 处 / 逐片连通检查 74 片

[PASS] weather_station_01.json: 47 片 / 10 步 / 高亮引用 9 处 / 逐片连通检查 47 片

[PASS] whale_01.json: 60 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 60 片

[PASS] whale_watching_01.json: 61 片 / 14 步 / 高亮引用 21 处 / 逐片连通检查 61 片

[PASS] wind_turbine_01.json: 53 片 / 16 步 / 高亮引用 20 处 / 逐片连通检查 53 片

[PASS] windmill_01.json: 55 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 55 片

[PASS] wizard_tower_01.json: 75 片 / 12 步 / 高亮引用 17 处 / 逐片连通检查 75 片

[PASS] yurt_01.json: 41 片 / 9 步 / 高亮引用 9 处 / 逐片连通检查 41 片

==============================================================
 结果: 全部 250 个模型逐步装配质检通过

>> 阶段 3/3: D4+ 抗扰动巡检 (validate --profile strict --jitter 50)
   [通过] aircraft_carrier_01
   [通过] airport_terminal_01
   [通过] apartment_block_01
   [通过] ball_run_tower_01
   [通过] basketball_arena_01
   [通过] cargo_ship_01
   [通过] castle_drawbridge_01
   [通过] covered_bridge_01
   [通过] dinosaur_hall_01
   [通过] eiffel_tower_01
   [通过] elephant_01
   [通过] ferry_terminal_01
   [通过] fire_station_01
   [通过] freight_yard_01
   [通过] hanging_garden_01
   [通过] harbor_crane_01
   [通过] helicopter_01
   [通过] hospital_01
   [通过] ice_rink_01
   [通过] library_building_01
   [通过] lighthouse_01
   [通过] marble_run_spiral_01
   [通过] parking_garage_01
   [通过] pet_clinic_01
   [通过] post_office_01
   [通过] race_track_01
   [通过] rainforest_canopy_01
   [通过] rescue_hq_01
   [通过] rocket_launchpad_01
   [通过] roman_aqueduct_01
   [通过] school_bus_01
   [通过] skyscraper_01
   [通过] soccer_goal_01
   [通过] stadium_gate_01
   [通过] steam_locomotive_01
   [通过] stonehenge_01
   [通过] submarine_dock_01
   [通过] subway_station_01
   [通过] temple_greek_01
   [通过] tennis_court_01
   [通过] train_station_01
   [通过] treehouse_01
   [通过] treehouse_02
   [通过] triumphal_arch_01
   [通过] volcano_base_01
   [通过] warehouse_01
   小计: D4+ 共 46 个模型, 通过 46, 失败 0

==============================================================
 strict 巡检结论: 全绿 (strict 零警告审计 + 逐步装配质检均通过;
                  D4+ 抗扰动巡检: 全绿 (46 个 D4+ 模型 x 50 次采样))
[通过] 弱磁严格档全库巡检 (strict)

==============================================================
 门禁关卡 3: L3 实物复核缺口报告 (报告型)
 $ /usr/bin/python3 /workspace/magtile-studio/tools/list_physical_pending.py /workspace/magtile-studio/data/models
==============================================================
== 实物搭建复核跟踪 (D4+, 规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
扫描 250 个模型, D4+ 共 46 个: 已复核 0, 待复核 46

-- 待复核 (46) --
模型                           难度     片数   步骤
skyscraper_01                D5    122   26
aircraft_carrier_01          D4     84   18
airport_terminal_01          D4     77   18
apartment_block_01           D4     99   18
ball_run_tower_01            D4     94   19
basketball_arena_01          D4     83   18
cargo_ship_01                D4     87   18
castle_drawbridge_01         D4     99   21
covered_bridge_01            D4     94   18
dinosaur_hall_01             D4     84   18
eiffel_tower_01              D4     95   21
elephant_01                  D4     95   18
ferry_terminal_01            D4    100   19
fire_station_01              D4     81   19
freight_yard_01              D4     85   20
hanging_garden_01            D4     85   18
harbor_crane_01              D4     86   19
helicopter_01                D4     87   18
hospital_01                  D4     98   18
ice_rink_01                  D4     84   19
library_building_01          D4     90   18
lighthouse_01                D4     77   16
marble_run_spiral_01         D4     80   18
parking_garage_01            D4     82   18
pet_clinic_01                D4     96   18
post_office_01               D4     97   19
race_track_01                D4     82   18
rainforest_canopy_01         D4     90   18
rescue_hq_01                 D4    101   18
rocket_launchpad_01          D4     82   18
roman_aqueduct_01            D4     79   18
school_bus_01                D4     98   18
soccer_goal_01               D4     81   18
stadium_gate_01              D4    103   18
steam_locomotive_01          D4     99   18
stonehenge_01                D4     91   19
submarine_dock_01            D4     89   18
subway_station_01            D4     87   18
temple_greek_01              D4     95   18
tennis_court_01              D4     86   20
train_station_01             D4     75   18
treehouse_01                 D4     79   18
treehouse_02                 D4     99   18
triumphal_arch_01            D4     88   18
volcano_base_01              D4     83   18
warehouse_01                 D4     97   18

待复核数量: 46
[通过] L3 实物复核缺口报告 (报告型)

==============================================================
 发布门禁报告
==============================================================
  PASS   免费层清单对齐核验                  1s
  PASS   弱磁严格档全库巡检 (strict)         59s
  PASS   L3 实物复核缺口报告 (报告型)      0s
--------------------------------------------------------------
 提醒: L3 实物复核为报告型不阻断; 正式出包前追加 --fail-on-pending 作为终防线
 结论: 全部 3 个门禁关卡通过, 可进入打包流程
 打包手册: scripts/package_qt_desktop.md / scripts/package_windows.md
[通过] R5 发布门禁快检 (run_release_gate.sh)

==============================================================
 R6 [P0] 实物抽样包 V1 复核缺口 (physical_sample_pack)
==============================================================
== V1 上架 D4+ 实物复核优先抽样包 (规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
D4+ 共 46 个 (待复核 46); 免费层 D4+ 0 个; 抽样目标 10 个, 命中 S1=0 S2=1 S3=9

#   模型                       难度    片数   步骤 主题     层      预计 状态
1   skyscraper_01            D5   122   26 建筑地标   S2  120min 待复核
2   stadium_gate_01          D4   103   18 城市生活   S3   70min 待复核
3   ferry_terminal_01        D4   100   19 海洋航行   S3   70min 待复核
4   castle_drawbridge_01     D4    99   21 城堡王国   S3   70min 待复核
5   treehouse_02             D4    99   18 自然世界   S3   70min 待复核
6   elephant_01              D4    95   18 动物     S3   70min 待复核
7   ball_run_tower_01        D4    94   19 滚珠乐园   S3   70min 待复核
8   stonehenge_01            D4    91   19 古代建筑   S3   70min 待复核
9   subway_station_01        D4    87   18 城市交通   S3   70min 待复核
10  tennis_court_01          D4    86   20 运动     S3   70min 待复核

预计总耗时: 750 分钟 (约 12.5 小时, 难度预算口径见规程第 2 节)

-- 已标注 physical_verified 的模型 (3, 一致性核对) --
  [OK ] castle_foundation_01     D3 2026-08-25 via content_meta (2026-08-25)
  [OK ] great_wall_01            D3 2026-08-25 via content_meta (2026-08-25)
  [OK ] tokyo_tower_01           D3 2026-08-25 via content_meta (2026-08-25)

抽样包缺口: 10 / 10 (存在缺口, --fail-on-missing-sample 生效)
[失败] R6 实物抽样包 V1 复核缺口 (physical_sample_pack) (退出码 1, 日志: /tmp/magtile_v1_readiness_YJWS1V/06_R6.log)

==============================================================
 R7 [P0] D4+ 实物复核全集清零 (list_physical_pending)
==============================================================
== 实物搭建复核跟踪 (D4+, 规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
扫描 250 个模型, D4+ 共 46 个: 已复核 0, 待复核 46

-- 待复核 (46) --
模型                           难度     片数   步骤
skyscraper_01                D5    122   26
aircraft_carrier_01          D4     84   18
airport_terminal_01          D4     77   18
apartment_block_01           D4     99   18
ball_run_tower_01            D4     94   19
basketball_arena_01          D4     83   18
cargo_ship_01                D4     87   18
castle_drawbridge_01         D4     99   21
covered_bridge_01            D4     94   18
dinosaur_hall_01             D4     84   18
eiffel_tower_01              D4     95   21
elephant_01                  D4     95   18
ferry_terminal_01            D4    100   19
fire_station_01              D4     81   19
freight_yard_01              D4     85   20
hanging_garden_01            D4     85   18
harbor_crane_01              D4     86   19
helicopter_01                D4     87   18
hospital_01                  D4     98   18
ice_rink_01                  D4     84   19
library_building_01          D4     90   18
lighthouse_01                D4     77   16
marble_run_spiral_01         D4     80   18
parking_garage_01            D4     82   18
pet_clinic_01                D4     96   18
post_office_01               D4     97   19
race_track_01                D4     82   18
rainforest_canopy_01         D4     90   18
rescue_hq_01                 D4    101   18
rocket_launchpad_01          D4     82   18
roman_aqueduct_01            D4     79   18
school_bus_01                D4     98   18
soccer_goal_01               D4     81   18
stadium_gate_01              D4    103   18
steam_locomotive_01          D4     99   18
stonehenge_01                D4     91   19
submarine_dock_01            D4     89   18
subway_station_01            D4     87   18
temple_greek_01              D4     95   18
tennis_court_01              D4     86   20
train_station_01             D4     75   18
treehouse_01                 D4     79   18
treehouse_02                 D4     99   18
triumphal_arch_01            D4     88   18
volcano_base_01              D4     83   18
warehouse_01                 D4     97   18

待复核数量: 46 (存在待复核, --fail-on-pending 生效)
[失败] R7 D4+ 实物复核全集清零 (list_physical_pending) (退出码 1, 日志: /tmp/magtile_v1_readiness_YJWS1V/07_R7.log)

==============================================================
 R8 [P0] 隐私合规文档存在性
==============================================================
  存在: docs/SECURITY_AND_PRIVACY.md
  存在: docs/PRIVACY_POLICY_DRAFT.md
  提示: 隐私政策仍为草稿, 法务定稿属人工项 (清单 §5 V2)
[断言通过] 隐私合规文档齐备
[通过] R8 隐私合规文档存在性

==============================================================
 R9 [P0] 桌面打包资产完备
==============================================================
  存在: scripts/package_qt_desktop.md
  存在: scripts/package_windows.md
  存在: scripts/smoke_qt_linux_pack.sh
  存在: scripts/check_lgpl_compliance.sh
  存在: platforms/windows/packaging/starter_models.txt
  存在: platforms/windows/packaging/THIRD_PARTY_NOTICES.md
  存在: platforms/windows/packaging/CPackWindows.cmake
  存在: platforms/windows/packaging/Product.wxs
  存在: .github/workflows/windows-release.yml (草案, 真实 runner 首跑属人工项 M1)
[断言通过] 桌面打包资产齐备
[通过] R9 桌面打包资产完备

==============================================================
 R10 [P1] 计费适配层单测 (magtile_billing_test)
==============================================================
[通过] 初始未订阅
[通过] 未订阅时付费模型上锁
[通过] 免费层模型永远解锁 (is_free 口径不受订阅影响)
[通过] 三档占位商品 (月/年/家庭年)
[通过] 商品 id / 中文名 / 价格文本齐全
[通过] 商品 id / 中文名 / 价格文本齐全
[通过] 商品 id / 中文名 / 价格文本齐全
[通过] 存在主推档位 (年度, COMMERCIAL_PLAN §3.2)
[通过] 未知商品 id 拒绝 (Unavailable)
[通过] 被拒购买不改变订阅状态
[通过] 假购买年度档成功
[通过] 假购买后订阅立即生效
[通过] 生效档位为所购档位
[通过] 假购买后付费模型解锁
[通过] 纯内存已订阅时 restore 回放
[通过] 纯内存新实例 restore 无可恢复
[通过] 全新存档默认未订阅
[通过] 全新存档无生效档位
[通过] 带存档构造时载入未订阅状态
[通过] 假购买家庭年度档成功
[通过] progress 层直读到购买写入的订阅状态 (同一 settings 键)
[通过] progress 层直读到生效档位
[通过] 订阅状态跨实例持久化
[通过] 生效档位跨实例持久化
[通过] 重启后付费模型仍解锁
[通过] 脏值按未订阅兜底
[通过] 脏值下不返回档位
[通过] 开发开关关闭后本地未订阅
[通过] 关闭状态已落盘
[通过] 关闭后付费模型重新上锁
[通过] restore 从假商店回执恢复
[通过] 恢复后订阅重新生效
[通过] 恢复的档位与回执一致
[通过] 恢复状态已落盘 (界面锁立即可读)
[通过] 无回执账户 restore 无可恢复
[通过] 无可恢复时保持未订阅
[通过] 空实现档商品表为空 (界面退回占位)
[通过] 空实现档购买 Unavailable
[通过] 空实现档恢复 Unavailable
[通过] 空实现档绝不误报已订阅
[通过] 空实现档付费模型保持上锁

计费适配层单元测试全部通过
[通过] R10 计费适配层单测 (magtile_billing_test)

==============================================================
 R11 [P0] 真实商店计费接入 (Google Play 接线)
==============================================================
  就绪: store_billing_client.cpp Google Play 分支已移除未接入守卫
  就绪: PlayBillingManager.kt (Kotlin 壳层 Play Billing 接线)
  就绪: 购买/恢复回执经 setSubscriptionActive 写契约键 (与 FakeBilling 同键)
  就绪: Play Billing Library 依赖已登记 (app/build.gradle.kts)
[断言通过] Google Play 计费已接线 (部分就绪: Windows 商店档见 R11W; 沙盒付费验收仍属人工项 B3)
[通过] R11 真实商店计费接入 (Google Play 接线)

==============================================================
 R11W [P0] 真实商店计费接入 (Windows 商店档接线)
==============================================================
  就绪: store_billing_client.cpp Windows 分支已移除未接入守卫
  就绪: WinRT Windows.Services.Store 接入 (StoreContext)
  就绪: 收银台购买流 (RequestPurchaseAsync) 与许可证恢复 (AddOnLicenses) 在位
  就绪: 购买/恢复回执经 setSubscriptionActive 写契约键 (与 FakeBilling / Google Play 同键)
  就绪: 构建接线 (根 CMakeLists MAGTILE_BILLING_WINDOWS_STORE 选项 + windowsapp 链接)
[断言通过] Windows 商店计费已接线 (部分就绪: MSIX 商店包出包 + Partner Center 商品配置 + 沙盒付费验收仍属人工项 B3/M1)
[通过] R11W 真实商店计费接入 (Windows 商店档接线)

==============================================================
 R12 [P1] Android 构建链路资产
==============================================================
  存在: platforms/android/README.md
  存在: platforms/android/app/build.gradle.kts
  存在: platforms/android/jni/magtile_jni.cpp
  存在: .github/workflows/android.yml
[断言通过] Android 构建链路资产齐备
[通过] R12 Android 构建链路资产

==============================================================
 R13 [P0] Android release 签名配置
==============================================================
  存在: signingConfigs 块 (app/build.gradle.kts)
  存在: platforms/android/keystore.properties.example (配置模板)
[断言通过] release 签名已接线 (真实 keystore 生成与商店出包仍属人工项 M2, 见 SIGNING.md)
[通过] R13 Android release 签名配置

==============================================================
 R14 [P0] 商店上架文档守卫 (validate_store_listing)
==============================================================
[通过] docs/STORE_LISTING.md 必填章节齐全 (15 个)
[通过] docs/STORE_LISTING.md 相对内链全部有效
[通过] store_assets/README.md 必填章节齐全 (5 个)
[通过] store_assets/README.md 相对内链全部有效

结论: 商店上架文档结构完整, 内链全部有效。
[通过] R14 商店上架文档守卫 (validate_store_listing)

==============================================================
 R15 [P0] 国内合规清单守卫 (check_china_compliance_docs)
==============================================================
[通过] CHINA_STORE_COMPLIANCE.md: 七大章节 + 五家商店小节齐全; checklist 条目 51 条 (P0 30 / P1 21) 全部带级别与负责方; 交叉引用 5 项就位。
[通过] R15 国内合规清单守卫 (check_china_compliance_docs)

==============================================================
 R16 [P0] 儿童友好文案守卫 (check_child_friendly_copy)
==============================================================
儿童友好文案守卫: 通过 —— 301 个文件 / 8874 段用户可见中文文案, 无恐吓词与催促话术
[通过] R16 儿童友好文案守卫 (check_child_friendly_copy)

==============================================================
 R17 [P1] D4+ 扰动仿真抽检 (validate --jitter 50)
==============================================================
抽样规则: D5 全数优先 + 大体量 D4 补足, 目标 10 个; 每模型 --jitter 50
  [ 1] skyscraper_01.json           D5  122 片  通过
  [ 2] stadium_gate_01.json         D4  103 片  通过
  [ 3] rescue_hq_01.json            D4  101 片  通过
  [ 4] ferry_terminal_01.json       D4  100 片  通过
  [ 5] apartment_block_01.json      D4   99 片  通过
  [ 6] castle_drawbridge_01.json    D4   99 片  通过
  [ 7] steam_locomotive_01.json     D4   99 片  通过
  [ 8] treehouse_02.json            D4   99 片  通过
  [ 9] hospital_01.json             D4   98 片  通过
  [10] school_bus_01.json           D4   98 片  通过
[断言通过] D4+ 扰动仿真抽检全绿 (10/10, 每个 50 次扰动; 不豁免 S1/S2 实搭)
[通过] R17 D4+ 扰动仿真抽检 (validate --jitter 50)

[跳过] M1 [P0] Windows/macOS 实机打包验收 + 代码签名/公证 —— Manual, 见清单 §3 D2~D6

[跳过] M2 [P0] Android 真机验收 + 商店上架资料 —— Manual, 见清单 §4 A4/A5

[跳过] M3 [P0] 隐私政策法务定稿 + 合规自查单 —— Manual, 见清单 §5 V2/V4

[跳过] M4 [P0] E2E 矩阵 P0 人工要点打钩与签核记录 —— Manual, 见 E2E_TEST_MATRIX.md §3

[跳过] M5 [P0] 实物抽样实搭签核 (R6/R7 只报告缺口) —— Manual, 见清单 §8 与 PHYSICAL_REBUILD_CHECKLIST.md

[跳过] M6 [P0] 软著 / ICP 备案 / 开发者账号 / 运营主体 —— Manual, 见清单 §9 与 CHINA_STORE_COMPLIANCE.md (文档完整性已由 R15 守卫)

==============================================================
 V1 上架就绪探测报告 (对账清单: docs/V1_LAUNCH_CHECKLIST.md)
==============================================================
  PASS   R1   [P0] 内容体量 (模型 JSON >= 200)              0s
  PASS   R2   [P1] 目录登记 / 缩略图对账                 0s
  PASS   R3   [P0] 免费层清单对齐 (verify_free_tier)       0s
  PASS   R4   [P0] E2E 冒烟 (run_e2e_smoke.sh)                  38s
  PASS   R5   [P0] 发布门禁快检 (run_release_gate.sh)       60s
  FAIL   R6   [P0] 实物抽样包 V1 复核缺口 (physical_sample_pack) 0s
  FAIL   R7   [P0] D4+ 实物复核全集清零 (list_physical_pending) 0s
  PASS   R8   [P0] 隐私合规文档存在性                    0s
  PASS   R9   [P0] 桌面打包资产完备                       0s
  PASS   R10  [P1] 计费适配层单测 (magtile_billing_test)   0s
  PASS   R11  [P0] 真实商店计费接入 (Google Play 接线)  0s
  PASS   R11W [P0] 真实商店计费接入 (Windows 商店档接线) 0s
  PASS   R12  [P1] Android 构建链路资产                     0s
  PASS   R13  [P0] Android release 签名配置                   0s
  PASS   R14  [P0] 商店上架文档守卫 (validate_store_listing) 0s
  PASS   R15  [P0] 国内合规清单守卫 (check_china_compliance_docs) 0s
  PASS   R16  [P0] 儿童友好文案守卫 (check_child_friendly_copy) 0s
  PASS   R17  [P1] D4+ 扰动仿真抽检 (validate --jitter 50)  11s
  SKIP   M1   [P0] Windows/macOS 实机打包验收 + 代码签名/公证 -
  SKIP   M2   [P0] Android 真机验收 + 商店上架资料      -
  SKIP   M3   [P0] 隐私政策法务定稿 + 合规自查单     -
  SKIP   M4   [P0] E2E 矩阵 P0 人工要点打钩与签核记录 -
  SKIP   M5   [P0] 实物抽样实搭签核 (R6/R7 只报告缺口) -
  SKIP   M6   [P0] 软著 / ICP 备案 / 开发者账号 / 运营主体 -
--------------------------------------------------------------
 合计 24 项: 16 PASS / 2 FAIL / 6 SKIP (其中 P0 失败 2 项)
 结论: 存在 2 项 P0 失败 —— 未达上架就绪, 逐项对照清单补齐
 分项日志: /tmp/magtile_v1_readiness_YJWS1V
```

</details>

# V1 上架就绪全量探测报告 (Full Readiness Run)

- 生成时间: 2026-08-25 19:24 UTC (234 模型库复跑; 前次 209 模型基线 `95c26cd` 的结果已由本次覆盖)
- 基线提交: `3d24d74` (`cursor/magtile-studio-foundation-a95b`, 内容批 A~E 全部并入后的 234 模型库)
- 构建配置: CMake Release 干净构建 x2 (CLI `build` + Qt `build-qt`, Ninja, Qt 6.4.2)
- 执行命令: `tools/check_v1_readiness.sh` (**全量档**, 非 `--quick` —— R4 E2E / R5 发布门禁 / R17 扰动抽检全部实跑)
- 退出码: **1** (仅 R6/R7 两项 L3 实物复核 P0 失败, 属预期硬闸门, 非软件缺陷)

## 1. 结论速览

**合计 24 项: 16 PASS / 2 FAIL / 6 SKIP (P0 失败 2 项, 全部为实物复核硬闸门)。**

工程侧判定: 软件门禁已达上限, 与 `RELEASE_GATE_STATUS.md` (基线 `5b915a0`) 结论一致, 且在 209 -> 234 模型扩容后保持不变。全部自动可探测项 (含三个长跑项 R4/R5/R17) 全绿; 唯二失败 R6/R7 为 D4+ 实物复核缺口, 按设计须用户实搭清零 (`docs/PHYSICAL_REBUILD_CHECKLIST.md`), 不属工程可修复范围。本次运行无任何工程可修复的失败项。

## 2. 逐项结果

| 检查 | 级别 | 结果 | 耗时 | 说明 |
| --- | --- | --- | --- | --- |
| R1 内容体量 | P0 | **PASS** | 0s | 模型 JSON 234 个 >= 门槛 200 (目标区间 200~250) |
| R2 目录/缩略图对账 | P1 | **PASS** | 1s | 模型 234 / 目录登记 234 / 缩略图就绪 234, 三方一致 |
| R3 免费层清单对齐 | P0 | **PASS** | 0s | 免费标签 30 x starter 清单 x core-9 三条断言全过 |
| R4 E2E 冒烟 (全量) | P0 | **PASS** | 34s | 8 项通过 / 1 项 SKIP (详见 §3) |
| R5 发布门禁快检 (全量) | P0 | **PASS** | 48s | 3 个门禁关卡全过 (详见 §4) |
| R6 实物抽样包缺口 | P0 | **FAIL** | 0s | 预期失败: 抽样包缺口 10/10 (详见 §6) |
| R7 D4+ 实物复核清零 | P0 | **FAIL** | 0s | 预期失败: D4+ 45 个待复核 0/45 (详见 §6) |
| R8 隐私合规文档 | P0 | **PASS** | 0s | SECURITY_AND_PRIVACY + PRIVACY_POLICY_DRAFT 在位 |
| R9 桌面打包资产 | P0 | **PASS** | 0s | 打包手册/CPack/WiX/starter 清单/第三方声明/CI 齐备 |
| R10 计费适配层单测 | P1 | **PASS** | 0s | `magtile_billing_test` 实跑通过 |
| R11 Google Play 计费接线 | P0 | **PASS** | 0s | 四项接线证据在位 (沙盒付费验收属人工项 B3) |
| R11W Windows 商店计费接线 | P0 | **PASS** | 0s | 五项接线证据在位 (MSIX 实包验收属人工项 B3/M1) |
| R12 Android 构建链路资产 | P1 | **PASS** | 0s | android.yml + build.gradle.kts + README + JNI 在位 |
| R13 Android release 签名 | P0 | **PASS** | 0s | signingConfigs + keystore.properties.example 齐备 |
| R14 商店上架文档守卫 | P0 | **PASS** | 0s | validate_store_listing 全过 |
| R15 国内合规清单守卫 | P0 | **PASS** | 0s | check_china_compliance_docs 全过 |
| R16 儿童友好文案守卫 | P0 | **PASS** | 0s | 全库文案扫描零红线 |
| R17 D4+ 扰动仿真抽检 (全量) | P1 | **PASS** | 11s | 10/10 全绿, 每模型 --jitter 50 (详见 §5) |
| M1~M6 人工项 | P0 | SKIP x6 | - | 实机打包/真机验收/法务定稿/矩阵签核/实搭签核/备案 |

## 3. R4 E2E 冒烟明细 (全量实跑)

| 路径 | 结果 |
| --- | --- |
| E2E-01a CLI 启动冒烟 (catalog 13 片型) | PASS |
| E2E-11a 免费层清单对齐 (verify_free_tier) | PASS |
| E2E-11b CLI 免费筛选对账 (--free-only, 全库 234 中 30 个) | PASS |
| E2E-06a CLI 免费模型教程步进 (beach_hut_01, 44 片对账) | PASS |
| E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读 + 全量互通断言) | PASS |
| E2E-QT Qt 无头冒烟 (test_qt_smoke.sh, offscreen) | PASS |
| E2E-12a Qt 进度页深链 (--smoke-open-progress) | PASS |
| E2E-04a/09a/11c/12b Qt 按钮级路径冒烟 | PASS |
| E2E-14a Android JNI 符号断言 | SKIP |

E2E-14a SKIP 原因: 本环境无 Android NDK (默认档不阻断, CI 由 `android.yml` 兜底; 上架签核档 `--strict` 需补齐 NDK 环境)。

## 4. R5 发布门禁明细 (全量实跑)

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 1. 免费层清单对齐核验 | PASS | 免费标签 x starter 清单 x core-9 对齐 |
| 2. 弱磁严格档全库巡检 (strict) | PASS | 234 模型 strict 零警告审计 + 逐步装配质检 234/234 + D4+ 抗扰动巡检 45/45 (strict --jitter 50) 三阶段全绿 |
| 3. L3 实物复核缺口报告 (报告型) | PASS | 报告型关卡, 缺口列报不阻断 (硬闸门见 R6/R7) |

结论: 全部 3 个门禁关卡通过, 可进入打包流程。

## 5. R17 D4+ 扰动仿真抽检明细 (全量实跑)

抽样规则: D5 全数优先 + 大体量 D4 按总片数降序补足, 目标 10 个; 每模型 `validate --jitter 50`。抽样名单与 209 库时一致 —— 内容批 A~E 新增 25 个模型全部为 D3 及以下, 不进入 D4+ 抽样池。

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

10/10 全绿 (含此前修复过抖动敏感问题的结构族代表), 软件侧不豁免 S1/S2 实搭。另: R5 门禁关卡 2 的阶段 3 已对全部 45 个 D4+ 模型做 strict --jitter 50 全量巡检 (45/45 全绿), 覆盖面超出本抽检。

## 6. R6/R7 失败详情 (预期硬闸门, 非工程可修复)

- **R6**: 实物抽样包缺口 10/10 —— D4+ 45 个全部待复核, 抽样命中 S1=0 / S2=1 / S3=9, 预计实搭总耗时约 750 分钟 (约 12.5 小时)。已标注 `physical_verified` 的 3 个 D3 模型 (castle_foundation_01 / great_wall_01 / tokyo_tower_01) 一致性核对通过。
- **R7**: 扫描 234 模型, D4+ 共 45 个: 已复核 0, 待复核 45 (`--fail-on-pending` 生效)。

两项均为 L3 实物复核硬闸门: 需用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭后回填 `physical_verified` 标记 (缩减流程见 `docs/USER_HANDOFF.md` §4.3)。内容批 A~E 扩容 (209 -> 234) 未新增 D4+ 模型, 待复核集合与前次运行完全一致。本次运行无任何非预期 / 工程可修复的失败项。

## 7. 下一步

1. 用户侧: 按 `docs/USER_HANDOFF.md` §4 完成实物 (R6/R7 清零)、行政、实机、沙盒验收
2. 签核档补充: 配 Android NDK 后以 `--strict` 复跑 E2E, 消除 E2E-14a SKIP

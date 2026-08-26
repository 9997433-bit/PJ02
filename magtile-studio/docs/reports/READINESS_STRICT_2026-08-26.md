# V1 上架就绪严格档探测报告 (2026-08-26, --strict 全量档)

- 生成时间: 2026-08-26 05:10 UTC (批 P 扩展装置换波次后 --strict 全量档复跑; 同基线 --quick 档记录见 `READINESS_FULL_2026-08-26.md` 同日刷新版 @ `ad6d35c`, 两报告可互为对照 —— 本报告补齐其 R4/R5/R17 三个长跑项的 --strict 实跑证据)
- 基线提交: `ad6d35c` (`ad6d35c72f232a69d866e6d263072bb45554368d`, `cursor/magtile-studio-foundation-a95b`) —— 自 `9aa146d` 以来完成批 P 扩展装置换 (内容置换 `53615ea`: +10 扩展装 (1 D1 + 7 D2 + 1 D3 白名单 + 1 D4) / −10 矩阵外 D3, 总量 250 保持) 与排产三件套/治理留痕刷新至 52 口径: 难度分布变为 D1 21 / D2 30 / D3 147 / D4 46 / D5 6, **D3 解冻状态维持** (D1 ≥ 20 且 D5 ≥ 6 双达标, 见 §7)
- 工作区: `/tmp/wt-risk-report/magtile-studio` (worktree 数据与引擎同 `ad6d35c`, 与 origin 同步); 构建: CMake Release 增量构建 (`build` CLI / `build-qt` Qt), 构建退出码 0
- 环境: `ANDROID_NDK=/opt/android-sdk/ndk/27.2.12479018` (android.yml 钉住版本), `NO_COLOR=1`
- 执行命令与退出码:
  1. `tools/check_v1_readiness.sh --strict` (**全量档, 非 --quick**): 退出码 **1** (仅 R6/R7 两项 L3 实物复核 P0 失败, 属预期硬闸门, 非软件缺陷); 总耗时约 1 分 31 秒
  2. `tools/run_e2e_smoke.sh --strict` (独立复跑): 退出码 **0**, 9/9 全绿 0 SKIP; 总耗时约 34 秒
- 完整日志: 附录 A (readiness --strict, 1492 行) / 附录 B (E2E --strict 独立跑, 151 行)

## 1. 结论速览

**readiness --strict 合计 25 项: 17 PASS / 2 FAIL / 6 SKIP (P0 失败 2 项, 全部为实物复核硬闸门; SKIP 全部为 M1~M6 纯人工项)。**

- 与 --quick 档相比, 三个长跑项 R4 (E2E --strict) / R5 (发布门禁) / R17 (扰动抽检) 本次全部实跑并 **全绿** —— 自动探测侧无任何 SKIP, 工程可探测项全部通过。
- `run_e2e_smoke.sh --strict` 独立复跑 9/9 全绿 (含 E2E-14a Android NDK 交叉编译 + 34 个 JNI 符号断言), 退出码 0 —— E2E 自动子集达到上架签核档口径。
- 唯二失败 R6/R7 为 D4+ 实物复核缺口 (52 个, 较 `9aa146d` 基线 51 个净增 1 个 —— 批 P 入库的 D4 `expansion_orb_01` 所致), 按设计须用户实搭清零, 不属工程可修复范围。
- **路径 B 维持闭环**: 难度配额 D3 冻结在本基线保持解冻 (D1 21 ≥ 20, D5 6 ≥ 6), `LAUNCH_BLOCKERS_2026-08-26.md` 维持单红灯口径; 剩余阻塞仅路径 A (实物签核 R6/R7) 与路径 C (Manual P0, M1~M6)。

### --strict 档逐项裁决 (交付口径速查)

| 结果 | 项目 |
| --- | --- |
| **PASS (17)** | R1, R2, R3, R4 (E2E --strict 9/9), R5 (门禁 3/3), R8, R9, R10, R11, R11W, R12, R13, R14, R15, R16, R17 (10/10 x 50 扰动), R18 |
| **FAIL (2)** | R6, R7 (均为 P0 实物复核硬闸门, 预期失败, 须用户实搭清零) |
| **SKIP (6)** | M1~M6 (纯人工项: 实机打包/真机验收/法务定稿/矩阵签核/实搭签核/备案 —— 设计上不参与自动判定) |

## 2. 逐项结果 (tools/check_v1_readiness.sh --strict)

| 检查 | 级别 | 结果 | 耗时 | 说明 |
| --- | --- | --- | --- | --- |
| R1 内容体量 | P0 | **PASS** | 0s | 模型 JSON 250 个 >= 门槛 200 (目标区间上限达成) |
| R2 目录/缩略图对账 | P1 | **PASS** | 0s | 模型 250 / 目录登记 250 / 缩略图就绪 250, 三方一致 |
| R3 免费层清单对齐 | P0 | **PASS** | 0s | 免费标签 30 x starter 清单 x core-9 三条断言全过 |
| R4 E2E 冒烟 (--strict) | P0 | **PASS** | 35s | 9/9 全绿 0 SKIP, 含 Android JNI (明细见 §3) |
| R5 发布门禁快检 | P0 | **PASS** | 43s | 3/3 关卡全过, 含 52 D4+ x 50 扰动全绿 (明细见 §4) |
| R6 实物抽样包缺口 | P0 | **FAIL** | 0s | 预期失败: 抽样包缺口 10/10, 含 6 个 D5 (详见 §6) |
| R7 D4+ 实物复核清零 | P0 | **FAIL** | 0s | 预期失败: D4+ 52 个待复核 0/52 (详见 §6) |
| R8 隐私合规文档 | P0 | **PASS** | 0s | SECURITY_AND_PRIVACY + PRIVACY_POLICY_DRAFT 在位 |
| R9 桌面打包资产 | P0 | **PASS** | 0s | 打包手册/CPack/WiX/starter 清单/第三方声明/CI 齐备 |
| R10 计费适配层单测 | P1 | **PASS** | 0s | `magtile_billing_test` 实跑通过 (41 断言全绿) |
| R11 Google Play 计费接线 | P0 | **PASS** | 0s | 四项接线证据在位 (沙盒付费验收属人工项 B3) |
| R11W Windows 商店计费接线 | P0 | **PASS** | 0s | 五项接线证据在位 (MSIX 实包验收属人工项 B3/M1) |
| R12 Android 构建链路资产 | P1 | **PASS** | 0s | android.yml + build.gradle.kts + README + JNI 在位 |
| R13 Android release 签名 | P0 | **PASS** | 0s | signingConfigs + keystore.properties.example 齐备 |
| R14 商店上架文档守卫 | P0 | **PASS** | 0s | validate_store_listing 全过 (15+5 章节, 内链全有效) |
| R15 国内合规清单守卫 | P0 | **PASS** | 0s | 51 条 (P0 30 / P1 21) 全带级别与负责方, 交叉引用就位 |
| R16 儿童友好文案守卫 | P0 | **PASS** | 1s | 301 文件 / 8493 段用户可见中文文案, 零红线 |
| R17 D4+ 扰动仿真抽检 | P1 | **PASS** | 12s | 10/10 全绿, D5 全数 6 + 大体量 D4 补 4 (明细见 §5) |
| R18 内容系列归类机检 | P1 | **PASS** | 0s | 250 归类齐全: 矩阵内 211 + 矩阵外 39, 缺失/非法 0 |
| M1~M6 人工项 | P0 | SKIP x6 | - | 实机打包/真机验收/法务定稿/矩阵签核/实搭签核/备案 |

## 3. R4 E2E 冒烟明细 (--strict 签核档, readiness 内嵌实跑)

readiness --strict 把 `--strict` 透传给 `run_e2e_smoke.sh`, 9 项全部实跑通过, **0 SKIP** (--strict 档 SKIP 即失败, 本次无一触发):

| 关卡 | 结果 | 耗时 | 说明 |
| --- | --- | --- | --- |
| E2E-01a CLI 启动冒烟 | PASS | 0s | catalog 13 种片型齐全 |
| E2E-11a 免费层清单对齐 | PASS | 0s | verify_free_tier 三断言全过 |
| E2E-11b CLI 免费筛选对账 | PASS | 1s | --free-only 30 个与 starter 清单一致, 目录对账通过 |
| E2E-06a CLI 免费模型教程步进 | PASS | 0s | beach_hut_01 全程步进, 片数对账一致 |
| E2E-17a 跨端存档键契约 | PASS | 0s | CLI 写 -> sqlite 直读 -> CLI 回读 + 全量跨端互通断言 (19 断言) |
| E2E-QT Qt 无头冒烟 | PASS | 15s | test_qt_smoke.sh 全路径 (offscreen) |
| E2E-12a Qt 进度页深链 | PASS | 4s | 完成存档落盘 + 进度页实例化, 无 QML 运行时错误 |
| E2E-04a/09a/11c/12b Qt 按钮级路径冒烟 | PASS | 14s | 筛选切换/库存深链/家长门/成就列表四路径全过 |
| E2E-14a Android JNI 符号断言 | PASS | 1s | NDK 27.2.12479018 arm64-v8a 增量复用 build-android 产物 (引擎自上次交叉编译未变更), 34 个 JNI 符号与 android.yml 同口径全在位 |

## 4. R5 发布门禁明细 (默认档实跑)

`run_release_gate.sh` 3/3 关卡全过, 结论「可进入打包流程」:

| 关卡 | 结果 | 耗时 | 说明 |
| --- | --- | --- | --- |
| 1 免费层清单对齐核验 | PASS | 0s | 与 R3 同载体复验 |
| 2 弱磁严格档全库巡检 (strict) | PASS | 43s | 三阶段全绿: 250 模型 validate --profile strict 零警告 + 全库逐步装配质检 + **D4+ 抗扰动巡检 52 个 x 50 次采样全绿** |
| 3 L3 实物复核缺口报告 (报告型) | PASS | 0s | 待复核 52 (报告不阻断; 正式出包终防线用 --fail-on-pending) |

注: 门禁关卡 2 的阶段 3/3 已对 **全部 52 个 D4+ 模型** 实跑 strict + jitter 50, 是 R17 十模型抽样的超集 —— 本基线 (含批 P 新晋 D4 `expansion_orb_01`) 的搭建误差稳健性在全集口径上验证通过。与同基线 `RELEASE_GATE_STATUS.md` 同日刷新版 (--full 档 42 子关卡全绿 + CTest 557/557 + D4+ jitter 52/52) 结论一致。

## 5. R17 D4+ 扰动仿真抽检明细 (全量实跑)

抽样规则: D5 全数优先 + 大体量 D4 补足, 目标 10 个; 每模型 `validate --jitter 50`。10/10 全绿:

| # | 模型 | 难度 | 片数 | 结果 |
| --- | --- | --- | --- | --- |
| 1 | royal_citadel_01 | D5 | 124 | 通过 |
| 2 | marble_grand_cascade_01 | D5 | 123 | 通过 |
| 3 | giant_ferris_wheel_01 | D5 | 122 | 通过 |
| 4 | skyscraper_01 | D5 | 122 | 通过 |
| 5 | stellar_launch_gantry_01 | D5 | 116 | 通过 |
| 6 | strait_rainbow_bridge_01 | D5 | 110 | 通过 |
| 7 | stadium_gate_01 | D4 | 103 | 通过 |
| 8 | rescue_hq_01 | D4 | 101 | 通过 |
| 9 | ferry_terminal_01 | D4 | 100 | 通过 |
| 10 | apartment_block_01 | D4 | 99 | 通过 |

与前次全量档 (b369bad, D5 仅 1 个) 相比, 本次 D5 全数 6 个悉数进入抽样 —— 扩库 D5 批的软件侧稳健性前哨全绿 (不豁免 S1/S2 实搭); 批 P 新晋 D4 `expansion_orb_01` (78 片) 未达大体量补足线, 由 R5 门禁的 52 全集 jitter 巡检覆盖。

## 6. R6/R7 失败详情 (预期硬闸门, 非工程可修复)

- **R6**: 实物抽样包缺口 10/10 —— D4+ 52 个全部待复核, 抽样命中 S1=0 / S2=6 / S3=4 (royal_citadel_01 / marble_grand_cascade_01 / giant_ferris_wheel_01 / skyscraper_01 / stellar_launch_gantry_01 / strait_rainbow_bridge_01 / stadium_gate_01 / ferry_terminal_01 / treehouse_02 / elephant_01), 预计实搭总耗时约 1000 分钟 (约 16.7 小时, 与上基线 `9aa146d` 相同 —— 批 P 新晋 D4 78 片未改变按片数排序的抽样命中集合)。已标注 `physical_verified` 的 3 个 D3 模型 (castle_foundation_01 / great_wall_01 / tokyo_tower_01) 一致性核对通过。
- **R7**: 扫描 250 模型, D4+ 共 52 个: 已复核 0, 待复核 52 (`--fail-on-pending` 生效)。待复核集合 = 46 D4 + 6 D5, 较 `9aa146d` 基线 51 个净增 1 个 (批 P 新晋 D4: `expansion_orb_01`, 入库前已过内容批评审五道闸与 strict --jitter 50)。

两项均为 L3 实物复核硬闸门: 需用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭后回填 `physical_verified` 标记 (签核 CLI `tools/mark_physical_verified.py`; 排产单 `docs/reports/PHYSICAL_REVIEW_QUEUE.md`: 必搭 41 ≈ 52.8h + 可缓建 11 ≈ 12.8h; 缩减流程见 `docs/USER_HANDOFF.md` §4.3)。本次运行无任何非预期 / 工程可修复的失败项。

## 7. 难度配额快照: D3 解冻状态维持 (路径 B 保持闭环)

readiness 失败尾注自动带出的配额快照显示 (对照 `CONTENT_GAP_AUDIT.md` 7.3 节):

| 难度 | 数量 | 占比 | 解冻线 | 状态 |
| --- | --- | --- | --- | --- |
| D1 (入门) | 21 | 8.4% | >= 20 | **已达标** |
| D2 (进阶) | 30 | 12.0% | - | - |
| D3 (熟练) | 147 | 58.8% | - | - |
| D4 (挑战) | 46 | 18.4% | - | - |
| D5 (大师) | 6 | 2.4% | >= 6 | **已达标** |

**D3 冻结状态: 已解冻** (D1 21 >= 20 且 D5 6 >= 6)。批 P 置换 +10/−10 后解冻线继续达标, `LAUNCH_BLOCKERS_2026-08-26.md` 维持单红灯口径 (路径 B 已闭环); readiness 脚本尾部的三路径指引已随 `d9ebeff` 刷新 —— 路径 B 行标注「已完成 2026-08-26」, 现实阻塞仅剩路径 A (R6/R7 实物) 与路径 C (Manual P0)。

## 8. 独立复跑: tools/run_e2e_smoke.sh --strict (退出码 0)

按签核流程在同一基线独立复跑 E2E 冒烟 --strict 档: **9/9 PASS / 0 FAIL / 0 SKIP, 退出码 0**, 结论「自动子集全绿」。各关卡结果与 §3 (readiness 内嵌跑) 完全一致; E2E-14a 复用已就绪的 `build-android` 增量产物, 1s 完成 34 个 JNI 符号断言。完整输出见附录 B。

负向验证 (--strict 闸门有效性): 未配置 `ANDROID_NDK` 时同命令 E2E-14a 记 SKIP, 脚本按约定判「--strict 档存在 1 项 SKIP, 上架签核不放行」退出码 1 —— strict 档不允许静默跳过的设计按预期工作。签核环境须保证 NDK 可用 (本次: `ANDROID_NDK=/opt/android-sdk/ndk/27.2.12479018`)。

## 9. 下一步

1. 路径 A (唯一自动侧红灯): 按 `docs/reports/PHYSICAL_REVIEW_QUEUE.md` 实搭 52 个 D4+ (含 6 个 D5) 并回填 `physical_verified` (签核 CLI `tools/mark_physical_verified.py`), 清零 R6/R7
2. 路径 C: M1~M6 人工项按 `docs/USER_HANDOFF.md` §4 逐条完成 (实机打包/真机验收/法务定稿/矩阵签核/实搭签核/备案)
3. 路径 B 已闭环, 无需进一步动作; 后续批次评审可恢复接收 D3 模型 (D3 冻结已解冻, 解冻线由 CTest 常开闸门与批次评审机检持续守卫)

## 附录 A: readiness --strict 全量档完整输出 (/tmp/readiness_strict_20260826_batchp.log)

<details>
<summary>点开查看完整日志 (1492 行, NO_COLOR=1)</summary>

```text
==============================================================
 MagTile Studio V1 上架就绪自动探测
 对账清单: docs/V1_LAUNCH_CHECKLIST.md
 项目根: /tmp/wt-risk-report/magtile-studio
 档位: 全量 + --strict (E2E 签核档)
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
 R4 [P0] E2E 冒烟 (run_e2e_smoke.sh --strict)
==============================================================
==============================================================
 MagTile Studio 核心用户路径 E2E 冒烟
 路径矩阵: docs/E2E_TEST_MATRIX.md
 项目根: /tmp/wt-risk-report/magtile-studio
 CLI 构建: /tmp/wt-risk-report/magtile-studio/build / Qt 构建: /tmp/wt-risk-report/magtile-studio/build-qt
 档位: --strict (SKIP 按失败处理)
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

==============================================================
 E2E 冒烟 9: E2E-14a Android JNI 符号断言 (NDK 交叉编译)
==============================================================
  NDK: /opt/android-sdk/ndk/27.2.12479018
-- Configuring done (0.0s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/wt-risk-report/magtile-studio/build-android
ninja: no work to do.
  (符号清单解析自 /tmp/wt-risk-report/.github/workflows/android.yml)
[断言通过] JNI 符号断言通过 (34 个, 与 android.yml 同口径)
[通过] E2E-14a Android JNI 符号断言 (NDK 交叉编译)

==============================================================
 E2E 冒烟报告 (路径矩阵: docs/E2E_TEST_MATRIX.md)
==============================================================
  PASS   E2E-01a CLI 启动冒烟 (catalog 13 片型)         0s
  PASS   E2E-11a 免费层清单对齐 (verify_free_tier)     0s
  PASS   E2E-11b CLI 免费筛选对账 (--free-only)         1s
  PASS   E2E-06a CLI 免费模型教程步进 (beach_hut_01)  0s
  PASS   E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读) 0s
  PASS   E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)            15s
  PASS   E2E-12a Qt 进度页深链 (--smoke-open-progress)   4s
  PASS   E2E-04a/09a/11c/12b Qt 按钮级路径冒烟         14s
  PASS   E2E-14a Android JNI 符号断言 (NDK 交叉编译)  1s
--------------------------------------------------------------
 结论: 9 项通过 (0 项跳过), 自动子集全绿
 人工侧: 按 docs/E2E_TEST_MATRIX.md 第 1 节 P0 的 Manual 要点逐条打钩
[通过] R4 E2E 冒烟 (run_e2e_smoke.sh --strict)

==============================================================
 R5 [P0] 发布门禁快检 (run_release_gate.sh)
==============================================================
==============================================================
 MagTile Studio 发布门禁 (Release Gate)
 项目根: /tmp/wt-risk-report/magtile-studio
 构建目录: /tmp/wt-risk-report/magtile-studio/build
 档位: 默认 (三道发布专项)
==============================================================

==============================================================
 门禁关卡 1: 免费层清单对齐核验
 $ /usr/bin/python3 /tmp/wt-risk-report/magtile-studio/tools/verify_free_tier.py --models-dir /tmp/wt-risk-report/magtile-studio/data/models --catalog /tmp/wt-risk-report/magtile-studio/data/tile_catalog.json
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
 $ bash /tmp/wt-risk-report/magtile-studio/tools/run_strict_audit.sh /tmp/wt-risk-report/magtile-studio/build
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
[通过] asteroid_mining_01
[通过] astronaut_training_01
[通过] bakery_shop_01
[通过] ball_run_tower_01
[通过] basketball_arena_01
[通过] basketball_court_01
[通过] beach_hut_01
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
[通过] castle_guard_post_01
[通过] castle_tower_01
[通过] cement_mixer_01
[通过] chicken_coop_01
[通过] chinese_garden_01
[通过] christmas_market_01
[通过] city_bus_stop_01
[通过] clock_tower_01
[通过] combine_harvester_01
[通过] conservatory_01
[通过] control_tower_01
[通过] coral_reef_01
[通过] coral_reef_02
[通过] covered_bridge_01
[通过] crane_tower_01
[通过] crane_tower_02
[通过] crocodile_01
[通过] cruise_ship_01
[通过] cup_coaster_01
[通过] desk_organizer_01
[通过] dinosaur_hall_01
[通过] dinosaur_stego_01
[通过] dragon_boat_01
[通过] dragon_cave_01
[通过] drawbridge_01
[通过] drone_pad_01
[通过] drum_set_01
[通过] duckling_pond_01
[通过] dump_truck_01
[通过] eiffel_tower_01
[通过] elephant_01
[通过] elephant_pavilion_01
[通过] excavator_01
[通过] expansion_orb_01
[通过] fairy_castle_01
[通过] farm_barn_01
[通过] farm_wagon_01
[通过] ferris_wheel_frame_01
[通过] ferry_terminal_01
[通过] festival_gate_01
[通过] fireboat_01
[通过] fire_station_01
[通过] fire_truck_01
[通过] fireworks_show_01
[通过] fishing_boat_01
[通过] food_truck_01
[通过] forklift_01
[通过] freight_yard_01
[通过] garden_pavilion_01
[通过] gas_station_01
[通过] geodesic_dome_01
[通过] giant_ferris_wheel_01
[通过] gingerbread_house_01
[通过] giraffe_01
[通过] great_wall_01
[通过] greenhouse_01
[通过] greenhouse_dome_01
[通过] hangar_01
[通过] hanging_garden_01
[通过] harbor_crane_01
[通过] harbor_ferry_01
[通过] hedgehog_01
[通过] helicopter_01
[通过] helicopter_pad_01
[通过] hex_honeycomb_01
[通过] horse_stable_01
[通过] hospital_01
[通过] hot_air_balloon_01
[通过] ice_cream_truck_01
[通过] ice_rink_01
[通过] igloo_01
[通过] kangaroo_01
[通过] kindergarten_01
[通过] knight_armor_01
[通过] ladybug_01
[通过] lantern_festival_01
[通过] library_building_01
[通过] lifeguard_tower_01
[通过] lighthouse_01
[通过] lighthouse_pier_01
[通过] lion_dance_01
[通过] lunar_lander_01
[通过] magic_pinwheel_mill_01
[通过] magic_tree_01
[通过] marble_dash_lane_01
[通过] marble_grand_cascade_01
[通过] marble_run_spiral_01
[通过] marble_splitter_01
[通过] marble_starter_slope_01
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
[通过] napkin_holder_01
[通过] oasis_01
[通过] observatory_01
[通过] octopus_01
[通过] open_air_cinema_01
[通过] owl_01
[通过] pagoda_01
[通过] panda_bamboo_01
[通过] parking_garage_01
[通过] peacock_01
[通过] pedestrian_overpass_01
[通过] pencil_cup_01
[通过] penguin_01
[通过] penguin_pool_01
[通过] pet_clinic_01
[通过] phone_cradle_01
[通过] pinwheel_mosaic_01
[通过] pirate_ship_01
[通过] planetarium_01
[通过] planetarium_02
[通过] plank_bridge_01
[通过] plaza_canopy_01
[通过] police_car_01
[通过] post_office_01
[通过] pumpkin_lantern_01
[通过] puppet_theater_01
[通过] pyramid_giza_01
[通过] race_track_01
[通过] radio_telescope_01
[通过] railway_crossing_01
[通过] rainbow_zigzag_wall_01
[通过] rainforest_canopy_01
[通过] rehab_park_01
[通过] rescue_hq_01
[通过] rhombus_patchwork_01
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
[通过] royal_citadel_01
[通过] safari_lodge_01
[通过] sailboat_01
[通过] sandbox_park_01
[通过] santa_sleigh_01
[通过] satellite_dish_01
[通过] school_bus_01
[通过] sculpture_plaza_01
[通过] sector_rotunda_01
[通过] seedling_greenhouse_01
[通过] sheep_farm_01
[通过] ski_jump_01
[通过] ski_lodge_01
[通过] skyscraper_01
[通过] slide_playground_01
[通过] snack_tray_01
[通过] snowman_01
[通过] snowplow_01
[通过] soccer_goal_01
[通过] solar_farm_01
[通过] space_elevator_01
[通过] space_probe_01
[通过] space_shuttle_01
[通过] space_station_01
[通过] spider_bot_01
[通过] stadium_gate_01
[通过] steam_locomotive_01
[通过] stellar_launch_gantry_01
[通过] stonehenge_01
[通过] strait_rainbow_bridge_01
[通过] streetcar_01
[通过] submarine_01
[通过] submarine_dock_01
[通过] subway_station_01
[豁免] suspension_bridge_01 (5 条已豁免警告, 理由见 docs/STRICT_PHYSICS_AUDIT.md)
        [警告] 第 7 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 8 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 9 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 10 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
        [警告] 第 11 步完成后: 模型由多个互不相连的部分组成, 建议在教程中明确分组说明 (disconnected_assembly)
[通过] suspension_rail_01
[通过] swing_set_01
[通过] switchback_ramp_01
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
[通过] trapezoid_awning_01
[通过] trebuchet_01
[通过] treehouse_01
[通过] treehouse_02
[通过] trex_skeleton_01
[通过] trilithon_ring_01
[通过] triumphal_arch_01
[通过] truss_bridge_01
[通过] turtle_beach_01
[通过] volcano_base_01
[通过] warehouse_01
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
 形状目录: /tmp/wt-risk-report/magtile-studio/data/tile_catalog.json
==============================================================

[PASS] aircraft_carrier_01.json: 84 片 / 18 步 / 高亮引用 28 处 / 逐片连通检查 84 片

[PASS] airport_terminal_01.json: 77 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 77 片

[PASS] airport_terminal_02.json: 72 片 / 14 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] ambulance_01.json: 53 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 53 片

[PASS] amphitheater_01.json: 70 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 70 片

[PASS] apartment_block_01.json: 99 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 99 片

[PASS] apiary_01.json: 47 片 / 10 步 / 高亮引用 10 处 / 逐片连通检查 47 片

[PASS] aquarium_tunnel_01.json: 52 片 / 12 步 / 高亮引用 11 处 / 逐片连通检查 52 片

[PASS] asteroid_mining_01.json: 67 片 / 14 步 / 高亮引用 21 处 / 逐片连通检查 67 片

[PASS] astronaut_training_01.json: 48 片 / 10 步 / 高亮引用 12 处 / 逐片连通检查 48 片

[PASS] bakery_shop_01.json: 72 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 72 片

[PASS] ball_run_tower_01.json: 94 片 / 19 步 / 高亮引用 38 处 / 逐片连通检查 94 片

[PASS] basketball_arena_01.json: 83 片 / 18 步 / 高亮引用 42 处 / 逐片连通检查 83 片

[PASS] basketball_court_01.json: 52 片 / 15 步 / 高亮引用 22 处 / 逐片连通检查 52 片

[PASS] beach_hut_01.json: 44 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 44 片

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

[PASS] castle_guard_post_01.json: 20 片 / 7 步 / 高亮引用 11 处 / 逐片连通检查 20 片

[PASS] castle_tower_01.json: 75 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 75 片

[PASS] cement_mixer_01.json: 69 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 69 片

[PASS] chicken_coop_01.json: 62 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 62 片

[PASS] chinese_garden_01.json: 52 片 / 17 步 / 高亮引用 25 处 / 逐片连通检查 52 片

[PASS] christmas_market_01.json: 68 片 / 14 步 / 高亮引用 20 处 / 逐片连通检查 68 片

[PASS] city_bus_stop_01.json: 46 片 / 10 步 / 高亮引用 16 处 / 逐片连通检查 46 片

[PASS] clock_tower_01.json: 67 片 / 16 步 / 高亮引用 28 处 / 逐片连通检查 67 片

[PASS] combine_harvester_01.json: 74 片 / 14 步 / 高亮引用 26 处 / 逐片连通检查 74 片

[PASS] conservatory_01.json: 41 片 / 9 步 / 高亮引用 16 处 / 逐片连通检查 41 片

[PASS] control_tower_01.json: 62 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 62 片

[PASS] coral_reef_01.json: 55 片 / 16 步 / 高亮引用 20 处 / 逐片连通检查 55 片

[PASS] coral_reef_02.json: 57 片 / 14 步 / 高亮引用 22 处 / 逐片连通检查 57 片

[PASS] covered_bridge_01.json: 94 片 / 18 步 / 高亮引用 40 处 / 逐片连通检查 94 片

[PASS] crane_tower_01.json: 68 片 / 16 步 / 高亮引用 20 处 / 逐片连通检查 68 片

[PASS] crane_tower_02.json: 75 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 75 片

[PASS] crocodile_01.json: 53 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 53 片

[PASS] cruise_ship_01.json: 67 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 67 片

[PASS] cup_coaster_01.json: 24 片 / 5 步 / 高亮引用 7 处 / 逐片连通检查 24 片

[PASS] desk_organizer_01.json: 42 片 / 10 步 / 高亮引用 13 处 / 逐片连通检查 42 片

[PASS] dinosaur_hall_01.json: 84 片 / 18 步 / 高亮引用 19 处 / 逐片连通检查 84 片

[PASS] dinosaur_stego_01.json: 69 片 / 17 步 / 高亮引用 27 处 / 逐片连通检查 69 片

[PASS] dragon_boat_01.json: 72 片 / 17 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] dragon_cave_01.json: 75 片 / 14 步 / 高亮引用 17 处 / 逐片连通检查 75 片

[PASS] drawbridge_01.json: 66 片 / 13 步 / 高亮引用 19 处 / 逐片连通检查 66 片

[PASS] drone_pad_01.json: 75 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 75 片

[PASS] drum_set_01.json: 57 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 57 片

[PASS] duckling_pond_01.json: 20 片 / 5 步 / 高亮引用 5 处 / 逐片连通检查 20 片

[PASS] dump_truck_01.json: 74 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 74 片

[PASS] eiffel_tower_01.json: 95 片 / 21 步 / 高亮引用 25 处 / 逐片连通检查 95 片

[PASS] elephant_01.json: 95 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 95 片

[PASS] elephant_pavilion_01.json: 75 片 / 15 步 / 高亮引用 24 处 / 逐片连通检查 75 片

[PASS] excavator_01.json: 55 片 / 18 步 / 高亮引用 28 处 / 逐片连通检查 55 片

[PASS] expansion_orb_01.json: 78 片 / 18 步 / 高亮引用 20 处 / 逐片连通检查 78 片

[PASS] fairy_castle_01.json: 66 片 / 13 步 / 高亮引用 18 处 / 逐片连通检查 66 片

[PASS] farm_barn_01.json: 65 片 / 17 步 / 高亮引用 26 处 / 逐片连通检查 65 片

[PASS] farm_wagon_01.json: 20 片 / 7 步 / 高亮引用 12 处 / 逐片连通检查 20 片

[PASS] ferris_wheel_frame_01.json: 56 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 56 片

[PASS] ferry_terminal_01.json: 100 片 / 19 步 / 高亮引用 32 处 / 逐片连通检查 100 片

[PASS] festival_gate_01.json: 22 片 / 5 步 / 高亮引用 7 处 / 逐片连通检查 22 片

[PASS] fire_station_01.json: 81 片 / 19 步 / 高亮引用 26 处 / 逐片连通检查 81 片

[PASS] fire_truck_01.json: 69 片 / 16 步 / 高亮引用 30 处 / 逐片连通检查 69 片

[PASS] fireboat_01.json: 63 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 63 片

[PASS] fireworks_show_01.json: 73 片 / 13 步 / 高亮引用 18 处 / 逐片连通检查 73 片

[PASS] fishing_boat_01.json: 63 片 / 16 步 / 高亮引用 28 处 / 逐片连通检查 63 片

[PASS] food_truck_01.json: 51 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 51 片

[PASS] forklift_01.json: 46 片 / 10 步 / 高亮引用 15 处 / 逐片连通检查 46 片

[PASS] freight_yard_01.json: 85 片 / 20 步 / 高亮引用 33 处 / 逐片连通检查 85 片

[PASS] garden_pavilion_01.json: 26 片 / 6 步 / 高亮引用 8 处 / 逐片连通检查 26 片

[PASS] gas_station_01.json: 64 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 64 片

[PASS] geodesic_dome_01.json: 49 片 / 15 步 / 高亮引用 18 处 / 逐片连通检查 49 片

[PASS] giant_ferris_wheel_01.json: 122 片 / 30 步 / 高亮引用 20 处 / 逐片连通检查 122 片

[PASS] gingerbread_house_01.json: 45 片 / 9 步 / 高亮引用 9 处 / 逐片连通检查 45 片

[PASS] giraffe_01.json: 52 片 / 16 步 / 高亮引用 23 处 / 逐片连通检查 52 片

[PASS] great_wall_01.json: 72 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 72 片

[PASS] greenhouse_01.json: 56 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 56 片

[PASS] greenhouse_dome_01.json: 66 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 66 片

[PASS] hangar_01.json: 74 片 / 14 步 / 高亮引用 23 处 / 逐片连通检查 74 片

[PASS] hanging_garden_01.json: 85 片 / 18 步 / 高亮引用 31 处 / 逐片连通检查 85 片

[PASS] harbor_crane_01.json: 86 片 / 19 步 / 高亮引用 31 处 / 逐片连通检查 86 片

[PASS] harbor_ferry_01.json: 20 片 / 6 步 / 高亮引用 10 处 / 逐片连通检查 20 片

[PASS] hedgehog_01.json: 53 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 53 片

[PASS] helicopter_01.json: 87 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 87 片

[PASS] helicopter_pad_01.json: 71 片 / 17 步 / 高亮引用 30 处 / 逐片连通检查 71 片

[PASS] hex_honeycomb_01.json: 44 片 / 8 步 / 高亮引用 17 处 / 逐片连通检查 44 片

[PASS] horse_stable_01.json: 56 片 / 13 步 / 高亮引用 12 处 / 逐片连通检查 56 片

[PASS] hospital_01.json: 98 片 / 18 步 / 高亮引用 33 处 / 逐片连通检查 98 片

[PASS] hot_air_balloon_01.json: 69 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 69 片

[PASS] ice_cream_truck_01.json: 73 片 / 16 步 / 高亮引用 30 处 / 逐片连通检查 73 片

[PASS] ice_rink_01.json: 84 片 / 19 步 / 高亮引用 28 处 / 逐片连通检查 84 片

[PASS] igloo_01.json: 66 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 66 片

[PASS] kangaroo_01.json: 70 片 / 13 步 / 高亮引用 16 处 / 逐片连通检查 70 片

[PASS] kindergarten_01.json: 61 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 61 片

[PASS] knight_armor_01.json: 56 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 56 片

[PASS] ladybug_01.json: 21 片 / 5 步 / 高亮引用 7 处 / 逐片连通检查 21 片

[PASS] lantern_festival_01.json: 57 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 57 片

[PASS] library_building_01.json: 90 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 90 片

[PASS] lifeguard_tower_01.json: 48 片 / 11 步 / 高亮引用 10 处 / 逐片连通检查 48 片

[PASS] lighthouse_01.json: 77 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 77 片

[PASS] lighthouse_pier_01.json: 72 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 72 片

[PASS] lion_dance_01.json: 75 片 / 14 步 / 高亮引用 14 处 / 逐片连通检查 75 片

[PASS] lunar_lander_01.json: 63 片 / 16 步 / 高亮引用 39 处 / 逐片连通检查 63 片

[PASS] magic_pinwheel_mill_01.json: 21 片 / 6 步 / 高亮引用 7 处 / 逐片连通检查 21 片

[PASS] magic_tree_01.json: 58 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 58 片

[PASS] marble_dash_lane_01.json: 53 片 / 12 步 / 高亮引用 19 处 / 逐片连通检查 53 片

[PASS] marble_grand_cascade_01.json: 123 片 / 32 步 / 高亮引用 42 处 / 逐片连通检查 123 片

[PASS] marble_run_spiral_01.json: 80 片 / 18 步 / 高亮引用 36 处 / 逐片连通检查 80 片

[PASS] marble_splitter_01.json: 40 片 / 10 步 / 高亮引用 15 处 / 逐片连通检查 40 片

[PASS] marble_starter_slope_01.json: 21 片 / 6 步 / 高亮引用 6 处 / 逐片连通检查 21 片

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

[PASS] napkin_holder_01.json: 22 片 / 7 步 / 高亮引用 9 处 / 逐片连通检查 22 片

[PASS] oasis_01.json: 72 片 / 14 步 / 高亮引用 19 处 / 逐片连通检查 72 片

[PASS] observatory_01.json: 53 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 53 片

[PASS] octopus_01.json: 53 片 / 10 步 / 高亮引用 9 处 / 逐片连通检查 53 片

[PASS] open_air_cinema_01.json: 54 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 54 片

[PASS] owl_01.json: 52 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 52 片

[PASS] pagoda_01.json: 73 片 / 16 步 / 高亮引用 27 处 / 逐片连通检查 73 片

[PASS] panda_bamboo_01.json: 65 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 65 片

[PASS] parking_garage_01.json: 82 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 82 片

[PASS] peacock_01.json: 50 片 / 12 步 / 高亮引用 14 处 / 逐片连通检查 50 片

[PASS] pedestrian_overpass_01.json: 65 片 / 13 步 / 高亮引用 18 处 / 逐片连通检查 65 片

[PASS] pencil_cup_01.json: 24 片 / 7 步 / 高亮引用 7 处 / 逐片连通检查 24 片

[PASS] penguin_01.json: 54 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 54 片

[PASS] penguin_pool_01.json: 63 片 / 13 步 / 高亮引用 17 处 / 逐片连通检查 63 片

[PASS] pet_clinic_01.json: 96 片 / 18 步 / 高亮引用 25 处 / 逐片连通检查 96 片

[PASS] phone_cradle_01.json: 20 片 / 6 步 / 高亮引用 8 处 / 逐片连通检查 20 片

[PASS] pinwheel_mosaic_01.json: 21 片 / 5 步 / 高亮引用 7 处 / 逐片连通检查 21 片

[PASS] pirate_ship_01.json: 74 片 / 13 步 / 高亮引用 13 处 / 逐片连通检查 74 片

[PASS] planetarium_01.json: 68 片 / 17 步 / 高亮引用 29 处 / 逐片连通检查 68 片

[PASS] planetarium_02.json: 74 片 / 12 步 / 高亮引用 15 处 / 逐片连通检查 74 片

[PASS] plank_bridge_01.json: 27 片 / 5 步 / 高亮引用 8 处 / 逐片连通检查 27 片

[PASS] plaza_canopy_01.json: 25 片 / 7 步 / 高亮引用 12 处 / 逐片连通检查 25 片

[PASS] police_car_01.json: 53 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 53 片

[PASS] post_office_01.json: 97 片 / 19 步 / 高亮引用 30 处 / 逐片连通检查 97 片

[PASS] pumpkin_lantern_01.json: 62 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 62 片

[PASS] puppet_theater_01.json: 46 片 / 10 步 / 高亮引用 11 处 / 逐片连通检查 46 片

[PASS] pyramid_giza_01.json: 64 片 / 17 步 / 高亮引用 49 处 / 逐片连通检查 64 片

[PASS] race_track_01.json: 82 片 / 18 步 / 高亮引用 30 处 / 逐片连通检查 82 片

[PASS] radio_telescope_01.json: 62 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 62 片

[PASS] railway_crossing_01.json: 62 片 / 13 步 / 高亮引用 22 处 / 逐片连通检查 62 片

[PASS] rainbow_zigzag_wall_01.json: 20 片 / 5 步 / 高亮引用 8 处 / 逐片连通检查 20 片

[PASS] rainforest_canopy_01.json: 90 片 / 18 步 / 高亮引用 26 处 / 逐片连通检查 90 片

[PASS] rehab_park_01.json: 41 片 / 9 步 / 高亮引用 13 处 / 逐片连通检查 41 片

[PASS] rescue_hq_01.json: 101 片 / 18 步 / 高亮引用 69 处 / 逐片连通检查 101 片

[PASS] rhombus_patchwork_01.json: 41 片 / 10 步 / 高亮引用 21 处 / 逐片连通检查 41 片

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

[PASS] royal_citadel_01.json: 124 片 / 28 步 / 高亮引用 33 处 / 逐片连通检查 124 片

[PASS] safari_lodge_01.json: 72 片 / 13 步 / 高亮引用 20 处 / 逐片连通检查 72 片

[PASS] sailboat_01.json: 68 片 / 15 步 / 高亮引用 30 处 / 逐片连通检查 68 片

[PASS] sandbox_park_01.json: 63 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 63 片

[PASS] santa_sleigh_01.json: 47 片 / 10 步 / 高亮引用 10 处 / 逐片连通检查 47 片

[PASS] satellite_dish_01.json: 67 片 / 14 步 / 高亮引用 21 处 / 逐片连通检查 67 片

[PASS] school_bus_01.json: 98 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 98 片

[PASS] sculpture_plaza_01.json: 56 片 / 12 步 / 高亮引用 13 处 / 逐片连通检查 56 片

[PASS] sector_rotunda_01.json: 52 片 / 13 步 / 高亮引用 15 处 / 逐片连通检查 52 片

[PASS] seedling_greenhouse_01.json: 22 片 / 6 步 / 高亮引用 9 处 / 逐片连通检查 22 片

[PASS] sheep_farm_01.json: 74 片 / 15 步 / 高亮引用 19 处 / 逐片连通检查 74 片

[PASS] ski_jump_01.json: 54 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 54 片

[PASS] ski_lodge_01.json: 55 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 55 片

[PASS] skyscraper_01.json: 122 片 / 26 步 / 高亮引用 73 处 / 逐片连通检查 122 片

[PASS] slide_playground_01.json: 67 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 67 片

[PASS] snack_tray_01.json: 21 片 / 6 步 / 高亮引用 9 处 / 逐片连通检查 21 片

[PASS] snowman_01.json: 72 片 / 14 步 / 高亮引用 13 处 / 逐片连通检查 72 片

[PASS] snowplow_01.json: 44 片 / 10 步 / 高亮引用 14 处 / 逐片连通检查 44 片

[PASS] soccer_goal_01.json: 81 片 / 18 步 / 高亮引用 32 处 / 逐片连通检查 81 片

[PASS] solar_farm_01.json: 53 片 / 13 步 / 高亮引用 21 处 / 逐片连通检查 53 片

[PASS] space_elevator_01.json: 72 片 / 12 步 / 高亮引用 12 处 / 逐片连通检查 72 片

[PASS] space_probe_01.json: 23 片 / 6 步 / 高亮引用 8 处 / 逐片连通检查 23 片

[PASS] space_shuttle_01.json: 68 片 / 15 步 / 高亮引用 19 处 / 逐片连通检查 68 片

[PASS] space_station_01.json: 69 片 / 16 步 / 高亮引用 21 处 / 逐片连通检查 69 片

[PASS] spider_bot_01.json: 62 片 / 16 步 / 高亮引用 26 处 / 逐片连通检查 62 片

[PASS] stadium_gate_01.json: 103 片 / 18 步 / 高亮引用 33 处 / 逐片连通检查 103 片

[PASS] steam_locomotive_01.json: 99 片 / 18 步 / 高亮引用 34 处 / 逐片连通检查 99 片

[PASS] stellar_launch_gantry_01.json: 116 片 / 28 步 / 高亮引用 28 处 / 逐片连通检查 116 片

[PASS] stonehenge_01.json: 91 片 / 19 步 / 高亮引用 24 处 / 逐片连通检查 91 片

[PASS] strait_rainbow_bridge_01.json: 110 片 / 25 步 / 高亮引用 34 处 / 逐片连通检查 110 片

[PASS] streetcar_01.json: 48 片 / 9 步 / 高亮引用 16 处 / 逐片连通检查 48 片

[PASS] submarine_01.json: 75 片 / 16 步 / 高亮引用 24 处 / 逐片连通检查 75 片

[PASS] submarine_dock_01.json: 89 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 89 片

[PASS] subway_station_01.json: 87 片 / 18 步 / 高亮引用 30 处 / 逐片连通检查 87 片

[PASS] suspension_bridge_01.json: 74 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 74 片

[PASS] suspension_rail_01.json: 75 片 / 16 步 / 高亮引用 29 处 / 逐片连通检查 75 片

[PASS] swing_set_01.json: 47 片 / 10 步 / 高亮引用 13 处 / 逐片连通检查 47 片

[PASS] switchback_ramp_01.json: 45 片 / 11 步 / 高亮引用 15 处 / 逐片连通检查 45 片

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

[PASS] trapezoid_awning_01.json: 40 片 / 9 步 / 高亮引用 16 处 / 逐片连通检查 40 片

[PASS] trebuchet_01.json: 57 片 / 12 步 / 高亮引用 15 处 / 逐片连通检查 57 片

[PASS] treehouse_01.json: 79 片 / 18 步 / 高亮引用 27 处 / 逐片连通检查 79 片

[PASS] treehouse_02.json: 99 片 / 18 步 / 高亮引用 31 处 / 逐片连通检查 99 片

[PASS] trex_skeleton_01.json: 73 片 / 16 步 / 高亮引用 25 处 / 逐片连通检查 73 片

[PASS] trilithon_ring_01.json: 23 片 / 5 步 / 高亮引用 6 处 / 逐片连通检查 23 片

[PASS] triumphal_arch_01.json: 88 片 / 18 步 / 高亮引用 29 处 / 逐片连通检查 88 片

[PASS] truss_bridge_01.json: 73 片 / 12 步 / 高亮引用 18 处 / 逐片连通检查 73 片

[PASS] turtle_beach_01.json: 48 片 / 8 步 / 高亮引用 8 处 / 逐片连通检查 48 片

[PASS] volcano_base_01.json: 83 片 / 18 步 / 高亮引用 33 处 / 逐片连通检查 83 片

[PASS] warehouse_01.json: 97 片 / 18 步 / 高亮引用 28 处 / 逐片连通检查 97 片

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
   [通过] expansion_orb_01
   [通过] ferry_terminal_01
   [通过] fire_station_01
   [通过] freight_yard_01
   [通过] giant_ferris_wheel_01
   [通过] hanging_garden_01
   [通过] harbor_crane_01
   [通过] helicopter_01
   [通过] hospital_01
   [通过] ice_rink_01
   [通过] library_building_01
   [通过] lighthouse_01
   [通过] marble_grand_cascade_01
   [通过] marble_run_spiral_01
   [通过] parking_garage_01
   [通过] pet_clinic_01
   [通过] post_office_01
   [通过] race_track_01
   [通过] rainforest_canopy_01
   [通过] rescue_hq_01
   [通过] rocket_launchpad_01
   [通过] roman_aqueduct_01
   [通过] royal_citadel_01
   [通过] school_bus_01
   [通过] skyscraper_01
   [通过] soccer_goal_01
   [通过] stadium_gate_01
   [通过] steam_locomotive_01
   [通过] stellar_launch_gantry_01
   [通过] stonehenge_01
   [通过] strait_rainbow_bridge_01
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
   小计: D4+ 共 52 个模型, 通过 52, 失败 0

==============================================================
 strict 巡检结论: 全绿 (strict 零警告审计 + 逐步装配质检均通过;
                  D4+ 抗扰动巡检: 全绿 (52 个 D4+ 模型 x 50 次采样))
[通过] 弱磁严格档全库巡检 (strict)

==============================================================
 门禁关卡 3: L3 实物复核缺口报告 (报告型)
 $ /usr/bin/python3 /tmp/wt-risk-report/magtile-studio/tools/list_physical_pending.py /tmp/wt-risk-report/magtile-studio/data/models
==============================================================
== 实物搭建复核跟踪 (D4+, 规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
扫描 250 个模型, D4+ 共 52 个: 已复核 0, 待复核 52

-- 待复核 (52) --
模型                           难度     片数   步骤
giant_ferris_wheel_01        D5    122   30
marble_grand_cascade_01      D5    123   32
royal_citadel_01             D5    124   28
skyscraper_01                D5    122   26
stellar_launch_gantry_01     D5    116   28
strait_rainbow_bridge_01     D5    110   25
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
expansion_orb_01             D4     78   18
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

待复核数量: 52
[通过] L3 实物复核缺口报告 (报告型)

==============================================================
 发布门禁报告
==============================================================
  PASS   免费层清单对齐核验                  0s
  PASS   弱磁严格档全库巡检 (strict)         43s
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
D4+ 共 52 个 (待复核 52); 免费层 D4+ 0 个; 抽样目标 10 个, 命中 S1=0 S2=6 S3=4

#   模型                       难度    片数   步骤 主题     层      预计 状态
1   royal_citadel_01         D5   124   28 城堡王国   S2  120min 待复核
2   marble_grand_cascade_01  D5   123   32 滚珠乐园   S2  120min 待复核
3   giant_ferris_wheel_01    D5   122   30 游乐园    S2  120min 待复核
4   skyscraper_01            D5   122   26 建筑地标   S2  120min 待复核
5   stellar_launch_gantry_01 D5   116   28 航天探索   S2  120min 待复核
6   strait_rainbow_bridge_01 D5   110   25 工程结构   S2  120min 待复核
7   stadium_gate_01          D4   103   18 城市生活   S3   70min 待复核
8   ferry_terminal_01        D4   100   19 海洋航行   S3   70min 待复核
9   treehouse_02             D4    99   18 自然世界   S3   70min 待复核
10  elephant_01              D4    95   18 动物     S3   70min 待复核

预计总耗时: 1000 分钟 (约 16.7 小时, 难度预算口径见规程第 2 节)

-- 已标注 physical_verified 的模型 (3, 一致性核对) --
  [OK ] castle_foundation_01     D3 2026-08-25 via content_meta (2026-08-25)
  [OK ] great_wall_01            D3 2026-08-25 via content_meta (2026-08-25)
  [OK ] tokyo_tower_01           D3 2026-08-25 via content_meta (2026-08-25)

抽样包缺口: 10 / 10 (存在缺口, --fail-on-missing-sample 生效)
[失败] R6 实物抽样包 V1 复核缺口 (physical_sample_pack) (退出码 1, 日志: /tmp/magtile_v1_readiness_B58RU4/06_R6.log)

==============================================================
 R7 [P0] D4+ 实物复核全集清零 (list_physical_pending)
==============================================================
== 实物搭建复核跟踪 (D4+, 规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
扫描 250 个模型, D4+ 共 52 个: 已复核 0, 待复核 52

-- 待复核 (52) --
模型                           难度     片数   步骤
giant_ferris_wheel_01        D5    122   30
marble_grand_cascade_01      D5    123   32
royal_citadel_01             D5    124   28
skyscraper_01                D5    122   26
stellar_launch_gantry_01     D5    116   28
strait_rainbow_bridge_01     D5    110   25
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
expansion_orb_01             D4     78   18
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

待复核数量: 52 (存在待复核, --fail-on-pending 生效)
[失败] R7 D4+ 实物复核全集清零 (list_physical_pending) (退出码 1, 日志: /tmp/magtile_v1_readiness_B58RU4/07_R7.log)

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
儿童友好文案守卫: 通过 —— 301 个文件 / 8493 段用户可见中文文案, 无恐吓词与催促话术
[通过] R16 儿童友好文案守卫 (check_child_friendly_copy)

==============================================================
 R17 [P1] D4+ 扰动仿真抽检 (validate --jitter 50)
==============================================================
抽样规则: D5 全数优先 + 大体量 D4 补足, 目标 10 个; 每模型 --jitter 50
  [ 1] royal_citadel_01.json        D5  124 片  通过
  [ 2] marble_grand_cascade_01.json D5  123 片  通过
  [ 3] giant_ferris_wheel_01.json   D5  122 片  通过
  [ 4] skyscraper_01.json           D5  122 片  通过
  [ 5] stellar_launch_gantry_01.json D5  116 片  通过
  [ 6] strait_rainbow_bridge_01.json D5  110 片  通过
  [ 7] stadium_gate_01.json         D4  103 片  通过
  [ 8] rescue_hq_01.json            D4  101 片  通过
  [ 9] ferry_terminal_01.json       D4  100 片  通过
  [10] apartment_block_01.json      D4   99 片  通过
[断言通过] D4+ 扰动仿真抽检全绿 (10/10, 每个 50 次扰动; 不豁免 S1/S2 实搭)
[通过] R17 D4+ 扰动仿真抽检 (validate --jitter 50)

==============================================================
 R18 [P1] 内容系列归类机检 (check_content_series --strict)
==============================================================
==============================================================
 内容系列归类机检 (content_meta.series / matrix_bucket)
==============================================================
词表:              /tmp/wt-risk-report/magtile-studio/data/content_series_map.json
                   (13 个矩阵主题 + 11 个矩阵外桶)
模型总数:          250
矩阵内 (series):   211
矩阵外 (bucket):   39
缺失归类:          0
词值非法:          0

主题 × 难度矩阵计数 (现状; 520 目标对照见 CONTENT_GAP_AUDIT.md 第 3 节):
  主题                             D1   D2   D3   D4   D5  合计
  城堡与要塞 castle_fortress        1    0    6    1    1     9
  陆地交通 land_transport           1    6   26    7    0    40
  海空交通 sea_air_transport        1    0   15    8    0    24
  航天器 spacecraft                 1    2   15    1    1    20
  动物世界 animal_world             2    2   24    2    0    30
  建筑地标 landmark_architecture    1    0   10    7    1    19
  桥梁工程 bridge_engineering       1    0    4    1    1     7
  几何艺术 geometric_art            2    3    1    1    0     7
  滚珠乐园 marble_run               1    2    1    2    1     7
  植物花园 plant_garden             2    3    4    3    0    12
  节日限定 holiday_seasonal         1    1    9    0    0    11
  实用功能 practical_utility        6    1    0    0    0     7
  幻想与机械 fantasy_machinery      1    2   14    0    1    18
  矩阵内小计                       21   22  129   33    6   211

矩阵外桶计数:
  城市生活 city_life               15
  运动 sports                       7
  田园 farm                         3
  工程结构 engineering_misc         2
  音乐 music                        1
  自然世界 nature_misc              4
  校园 campus                       0
  游乐园 amusement                  2
  海洋航行 maritime_misc            2
  博物馆 museum                     1
  其他 other                        2
  矩阵外小计                       39

归类齐全且词值全部合法, 无警告
==============================================================
[通过] R18 内容系列归类机检 (check_content_series --strict)

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
  PASS   R4   [P0] E2E 冒烟 (run_e2e_smoke.sh --strict)         35s
  PASS   R5   [P0] 发布门禁快检 (run_release_gate.sh)       43s
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
  PASS   R16  [P0] 儿童友好文案守卫 (check_child_friendly_copy) 1s
  PASS   R17  [P1] D4+ 扰动仿真抽检 (validate --jitter 50)  12s
  PASS   R18  [P1] 内容系列归类机检 (check_content_series --strict) 0s
  SKIP   M1   [P0] Windows/macOS 实机打包验收 + 代码签名/公证 -
  SKIP   M2   [P0] Android 真机验收 + 商店上架资料      -
  SKIP   M3   [P0] 隐私政策法务定稿 + 合规自查单     -
  SKIP   M4   [P0] E2E 矩阵 P0 人工要点打钩与签核记录 -
  SKIP   M5   [P0] 实物抽样实搭签核 (R6/R7 只报告缺口) -
  SKIP   M6   [P0] 软著 / ICP 备案 / 开发者账号 / 运营主体 -
--------------------------------------------------------------
 合计 25 项: 17 PASS / 2 FAIL / 6 SKIP (其中 P0 失败 2 项)
 结论: 存在 2 项 P0 失败 —— 未达上架就绪, 逐项对照清单补齐
 分项日志: /tmp/magtile_v1_readiness_B58RU4

 阻塞项指引 (工程侧已触顶, 见 docs/reports/LAUNCH_BLOCKERS_2026-08-26.md):
   路径 A 实物签核 —— R6/R7: 按 docs/reports/PHYSICAL_REVIEW_QUEUE.md 实搭落盘
   路径 B 配额解冻 —— 已完成 2026-08-26 (D1 20/20, D5 6/6, strict 守卫绿; 维持解冻线即可)
   路径 C Manual P0 —— 行政/实机/沙盒/法务: docs/USER_HANDOFF.md §4

 难度配额快照 (--full 档 strict 守卫口径):
   ==============================================================
    难度配额检查 (D3 冻结硬闸门 —— CONTENT_GAP_AUDIT.md 7.3 节)
   ==============================================================
   主库模型总数:      250  (/tmp/wt-risk-report/magtile-studio/data/models)
     D1 (入门):          21  (8.4%)   解冻线 >= 20, 已达标
     D2 (进阶):          30  (12.0%)
     D3 (熟练):         147  (58.8%)
     D4 (挑战):          46  (18.4%)
     D5 (大师):           6  (2.4%)   解冻线 >= 6, 已达标
   
   D3 冻结状态: 已解冻 (D1 21 >= 20 且 D5 6 >= 6)
   ==============================================================
```

</details>

## 附录 B: run_e2e_smoke.sh --strict 独立跑完整输出 (/tmp/e2e_strict_20260826_batchp.log)

<details>
<summary>点开查看完整日志 (151 行, NO_COLOR=1)</summary>

```text
==============================================================
 MagTile Studio 核心用户路径 E2E 冒烟
 路径矩阵: docs/E2E_TEST_MATRIX.md
 项目根: /tmp/wt-risk-report/magtile-studio
 CLI 构建: /tmp/wt-risk-report/magtile-studio/build / Qt 构建: /tmp/wt-risk-report/magtile-studio/build-qt
 档位: --strict (SKIP 按失败处理)
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

==============================================================
 E2E 冒烟 9: E2E-14a Android JNI 符号断言 (NDK 交叉编译)
==============================================================
  NDK: /opt/android-sdk/ndk/27.2.12479018
-- Configuring done (0.0s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/wt-risk-report/magtile-studio/build-android
ninja: no work to do.
  (符号清单解析自 /tmp/wt-risk-report/.github/workflows/android.yml)
[断言通过] JNI 符号断言通过 (34 个, 与 android.yml 同口径)
[通过] E2E-14a Android JNI 符号断言 (NDK 交叉编译)

==============================================================
 E2E 冒烟报告 (路径矩阵: docs/E2E_TEST_MATRIX.md)
==============================================================
  PASS   E2E-01a CLI 启动冒烟 (catalog 13 片型)         0s
  PASS   E2E-11a 免费层清单对齐 (verify_free_tier)     0s
  PASS   E2E-11b CLI 免费筛选对账 (--free-only)         0s
  PASS   E2E-06a CLI 免费模型教程步进 (beach_hut_01)  1s
  PASS   E2E-17a 跨端存档键契约 (CLI 写 -> sqlite 直读) 0s
  PASS   E2E-QT Qt 无头冒烟 (test_qt_smoke.sh)            14s
  PASS   E2E-12a Qt 进度页深链 (--smoke-open-progress)   5s
  PASS   E2E-04a/09a/11c/12b Qt 按钮级路径冒烟         14s
  PASS   E2E-14a Android JNI 符号断言 (NDK 交叉编译)  1s
--------------------------------------------------------------
 结论: 9 项通过 (0 项跳过), 自动子集全绿
 人工侧: 按 docs/E2E_TEST_MATRIX.md 第 1 节 P0 的 Manual 要点逐条打钩
```

</details>

# V1 上架就绪探测报告 (2026-08-26 刷新, --quick 档)

- 生成时间: 2026-08-26 03:56 UTC (软件侧红项清零波次后刷新; 上一份 --quick 记录 @ `8ee2fc7` 见本文件历史版本, 上一份全量档记录见 `READINESS_FULL_2026-08-25.md` @ `b369bad`, 其 R4 E2E 全量档证据仍有效)
- 基线提交: `9aa146d` (`cursor/magtile-studio-foundation-a95b` —— 自 `8ee2fc7` 以来为路径 B 配额解冻内容批 (D1 ×20 / D5 ×5 入库, B1 置换退役 25 个 D3) 与软件侧红项清零波次 (QA 难度感知片数下限治理 `b925eba`、2 个 D5 扩规模、R9 放置重排、实物三件套刷新至 51 口径); 模型库保持 250, C++ 引擎源码未变更)
- 构建配置: CMake Release, `/tmp/wt-risk-report/magtile-studio` worktree (@ `9aa146d`, 工作区干净) 增量构建, 退出码 0
- 执行命令: `tools/check_v1_readiness.sh --quick` (**--quick 档**: R4 E2E / R5 发布门禁 / R17 扰动抽检三个长跑项按约定记 SKIP; 总耗时约 1s)
- 退出码: **1** (仅 R6/R7 两项 L3 实物复核 P0 失败, 属预期硬闸门, 非软件缺陷)
- 长跑项补充覆盖 (同场同基线): `tools/run_release_gate.sh --full --fail-on-pending` 已在同一 worktree 同一提交单独实跑 (见 `RELEASE_GATE_STATUS.md` 2026-08-26 03:56 UTC 刷新) —— **全量 QA 42 子关卡 0 失败首次全绿** (CTest 556/556, strict 巡检三阶段全绿含 D4+ 抗扰动 51/51 × 50 轮), 是 R5 默认档的超集且覆盖面超出 R17 的 10 模型抽样; 唯一红灯为 L3 实物复核 51 待复核硬闸门。R4 E2E 冒烟本次未跑 (--quick 约定), 全量档证据保持 `READINESS_FULL_2026-08-25.md` §3 (b369bad, 其后无引擎/Qt 界面变更; 模型 JSON 变更已由本场全量 QA 的 250/250 validate + 逐步装配全绿覆盖)

## 1. 结论速览

**合计 25 项: 14 PASS / 2 FAIL / 9 SKIP (P0 失败 2 项, 全部为实物复核硬闸门)。**

工程侧判定: **软件门禁首次在 250 基线上无任何工程侧红项** —— 上一轮 (`b31e933`) 发布门禁暴露的 5 个内容侧真红 (20 个 D1 片数下限冲突 / 2 个 D5 片数区间 / 2 个 D5 抖动失败) 已全部按治理决策 + 内容返工清零 (明细见 `RELEASE_GATE_STATUS.md` §2), 难度配额守卫 strict 档保持绿灯 (D1 20 ≥ 20 且 D5 6 ≥ 6, D3 解冻维持)。唯二失败 R6/R7 为 D4+ 实物复核缺口 (51 个: 45 D4 + 6 D5, 较 8ee2fc7 基线 +5 个新 D5), 按设计须用户实搭清零 (`docs/PHYSICAL_REBUILD_CHECKLIST.md`, 排产单 `docs/reports/PHYSICAL_REVIEW_QUEUE.md`), 不属工程可修复范围。本次运行无任何工程可修复的失败项。

与前次 --quick 运行 (`8ee2fc7`) 的口径差异: 探测项集合不变 (R1~R18 + M1~M6 共 25 项), SKIP 集合不变 (R4/R5/R17 + M1~M6)。数据面变化: ① R6 抽样包命中从 S1=0 S2=1 S3=9 变为 **S1=0 S2=6 S3=4** (6 个 D5 全部进入优先抽样, 预计 1000 分钟 ≈ 16.7 小时, 前次 750 分钟); ② R7 待复核从 46 增至 **51** (+5 新 D5); ③ R18 矩阵内/外从 176/74 变为 **201/49** (D1/D5 新批全部落矩阵内, 系列归类回填); ④ R16 文案段数 8874 → 8571 (B1 退役 25 个 D3 模型文案随之出库); ⑤ 尾部难度配额快照从「冻结生效中 (D1 0/20, D5 1/6)」翻转为「**已解冻 (D1 20 ≥ 20 且 D5 6 ≥ 6)**」—— 阻塞项指引中的路径 B 已完结, 实际剩余路径仅 A (实物) 与 C (Manual P0)。

## 2. 逐项结果

| 检查 | 级别 | 结果 | 耗时 | 说明 |
| --- | --- | --- | --- | --- |
| R1 内容体量 | P0 | **PASS** | 0s | 模型 JSON 250 个 >= 门槛 200 (目标区间 200~250 上限达成) |
| R2 目录/缩略图对账 | P1 | **PASS** | 0s | 模型 250 / 目录登记 250 / 缩略图就绪 250, 三方一致 |
| R3 免费层清单对齐 | P0 | **PASS** | 0s | 免费标签 30 x starter 清单 x core-9 三条断言全过 |
| R4 E2E 冒烟 | P0 | SKIP | - | --quick 约定; 全量档证据见 READINESS_FULL_2026-08-25.md §3 (其后无引擎/界面变更) |
| R5 发布门禁快检 | P0 | SKIP | - | --quick 约定; 同场已单独实跑超集档 `--full --fail-on-pending`, QA 全绿 (见 RELEASE_GATE_STATUS.md) |
| R6 实物抽样包缺口 | P0 | **FAIL** | 0s | 预期失败: 抽样包缺口 10/10, 命中 S1=0 S2=6 S3=4 (详见 §3) |
| R7 D4+ 实物复核清零 | P0 | **FAIL** | 0s | 预期失败: D4+ 51 个待复核 0/51 (详见 §3) |
| R8 隐私合规文档 | P0 | **PASS** | 0s | SECURITY_AND_PRIVACY + PRIVACY_POLICY_DRAFT 在位 |
| R9 桌面打包资产 | P0 | **PASS** | 0s | 打包手册/CPack/WiX/starter 清单/第三方声明/CI 齐备 |
| R10 计费适配层单测 | P1 | **PASS** | 0s | `magtile_billing_test` 实跑通过 (41 断言全绿) |
| R11 Google Play 计费接线 | P0 | **PASS** | 0s | 四项接线证据在位 (沙盒付费验收属人工项 B3) |
| R11W Windows 商店计费接线 | P0 | **PASS** | 0s | 五项接线证据在位 (MSIX 实包验收属人工项 B3/M1) |
| R12 Android 构建链路资产 | P1 | **PASS** | 0s | android.yml + build.gradle.kts + README + JNI 在位 |
| R13 Android release 签名 | P0 | **PASS** | 0s | signingConfigs + keystore.properties.example 齐备 |
| R14 商店上架文档守卫 | P0 | **PASS** | 0s | validate_store_listing 全过 (15+5 章节, 内链全有效) |
| R15 国内合规清单守卫 | P0 | **PASS** | 0s | 51 条 (P0 30 / P1 21) 全带级别与负责方, 交叉引用 5 项就位 |
| R16 儿童友好文案守卫 | P0 | **PASS** | 0s | 301 文件 / 8571 段用户可见中文文案, 零红线 |
| R17 D4+ 扰动仿真抽检 | P1 | SKIP | - | --quick 约定; 同场发布门禁 strict 巡检阶段 3 已对全部 51 个 D4+ 实跑 strict --jitter 50 全绿 (超集, 见 RELEASE_GATE_STATUS.md §2.3) |
| R18 内容系列归类机检 | P1 | **PASS** | 0s | 250 归类齐全: 矩阵内 201 + 矩阵外 49, 缺失/非法 0 |
| M1~M6 人工项 | P0 | SKIP x6 | - | 实机打包/真机验收/法务定稿/矩阵签核/实搭签核/备案 |

## 3. R6/R7 失败详情 (预期硬闸门, 非工程可修复)

- **R6**: 实物抽样包缺口 10/10 —— D4+ 51 个全部待复核, 抽样命中 S1=0 / S2=6 / S3=4: **6 个 D5 全部纳入优先抽样** (royal_citadel_01 / marble_grand_cascade_01 / giant_ferris_wheel_01 / skyscraper_01 / stellar_launch_gantry_01 / strait_rainbow_bridge_01, 各 120min) + 4 个高片数 D4 (stadium_gate_01 / ferry_terminal_01 / treehouse_02 / elephant_01, 各 70min), 预计实搭总耗时约 1000 分钟 (约 16.7 小时)。已标注 `physical_verified` 的 3 个 D3 模型 (castle_foundation_01 / great_wall_01 / tokyo_tower_01) 一致性核对通过。
- **R7**: 扫描 250 模型, D4+ 共 51 个: 已复核 0, 待复核 51 (`--fail-on-pending` 生效)。

两项均为 L3 实物复核硬闸门: 需用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭后回填 `physical_verified` 标记 (族去重排产单见 `docs/reports/PHYSICAL_REVIEW_QUEUE.md`: 必搭 40 ≈ 51.7h + 可缓建 11 ≈ 12.8h; 缩减流程见 `docs/USER_HANDOFF.md` §4.3)。待复核集合较 8ee2fc7 基线 +5 个新 D5 (giant_ferris_wheel_01 / marble_grand_cascade_01 / royal_citadel_01 / stellar_launch_gantry_01 / strait_rainbow_bridge_01), 其中 3 个曾带软件侧红项的模型已于本波次返工完毕并通过 strict --jitter 50 (见 RELEASE_GATE_STATUS.md §2), **全部 51 个均可直接排实搭**。本次运行无任何非预期 / 工程可修复的失败项。

## 4. 下一步

1. 用户侧: 按 `docs/USER_HANDOFF.md` §4 完成实物 (R6/R7 清零, 建议从 §3 抽样包 10 个起步)、行政、实机、沙盒验收; 路径 B 配额解冻已完结 (D1 20/20 + D5 6/6, 快照见附录尾段), 无需再决策
2. 签核档: 上架签核前以全量档复跑 (`tools/check_v1_readiness.sh` 不带 `--quick`, 配 Android NDK 后加 `--strict`), 消除 R4/R5/R17 SKIP 与 E2E-14a SKIP

## 附录: 本次 --quick 档完整输出 (/tmp/readiness_quick_20260826_qagreen.log)

<details>
<summary>点开查看完整日志 (383 行, NO_COLOR=1)</summary>

```text
==============================================================
 MagTile Studio V1 上架就绪自动探测
 对账清单: docs/V1_LAUNCH_CHECKLIST.md
 项目根: /tmp/wt-risk-report/magtile-studio
 档位: --quick (跳过 E2E 冒烟 / 发布门禁 / 扰动抽检)
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

[跳过] R4 [P0] E2E 冒烟 (run_e2e_smoke.sh) —— --quick (签核前必须全量跑)

[跳过] R5 [P0] 发布门禁快检 (run_release_gate.sh) —— --quick (签核前必须全量跑)

==============================================================
 R6 [P0] 实物抽样包 V1 复核缺口 (physical_sample_pack)
==============================================================
== V1 上架 D4+ 实物复核优先抽样包 (规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
D4+ 共 51 个 (待复核 51); 免费层 D4+ 0 个; 抽样目标 10 个, 命中 S1=0 S2=6 S3=4

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
[失败] R6 实物抽样包 V1 复核缺口 (physical_sample_pack) (退出码 1, 日志: /tmp/magtile_v1_readiness_5QnOQo/06_R6.log)

==============================================================
 R7 [P0] D4+ 实物复核全集清零 (list_physical_pending)
==============================================================
== 实物搭建复核跟踪 (D4+, 规程: docs/PHYSICAL_REBUILD_CHECKLIST.md) ==
扫描 250 个模型, D4+ 共 51 个: 已复核 0, 待复核 51

-- 待复核 (51) --
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

待复核数量: 51 (存在待复核, --fail-on-pending 生效)
[失败] R7 D4+ 实物复核全集清零 (list_physical_pending) (退出码 1, 日志: /tmp/magtile_v1_readiness_5QnOQo/07_R7.log)

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
儿童友好文案守卫: 通过 —— 301 个文件 / 8571 段用户可见中文文案, 无恐吓词与催促话术
[通过] R16 儿童友好文案守卫 (check_child_friendly_copy)

[跳过] R17 [P1] D4+ 扰动仿真抽检 (validate --jitter 50) —— --quick (慢项; 签核前必须全量跑, 全量档不允许静默跳过)

==============================================================
 R18 [P1] 内容系列归类机检 (check_content_series --strict)
==============================================================
==============================================================
 内容系列归类机检 (content_meta.series / matrix_bucket)
==============================================================
词表:              /tmp/wt-risk-report/magtile-studio/data/content_series_map.json
                   (13 个矩阵主题 + 11 个矩阵外桶)
模型总数:          250
矩阵内 (series):   201
矩阵外 (bucket):   49
缺失归类:          0
词值非法:          0

主题 × 难度矩阵计数 (现状; 520 目标对照见 CONTENT_GAP_AUDIT.md 第 3 节):
  主题                             D1   D2   D3   D4   D5  合计
  城堡与要塞 castle_fortress        1    0    6    1    1     9
  陆地交通 land_transport           1    5   26    7    0    39
  海空交通 sea_air_transport        1    0   15    8    0    24
  航天器 spacecraft                 1    2   15    1    1    20
  动物世界 animal_world             2    2   24    2    0    30
  建筑地标 landmark_architecture    1    0    9    7    1    18
  桥梁工程 bridge_engineering       1    0    4    1    1     7
  几何艺术 geometric_art            2    1    1    0    0     4
  滚珠乐园 marble_run               1    0    1    2    1     5
  植物花园 plant_garden             2    1    4    3    0    10
  节日限定 holiday_seasonal         1    1    9    0    0    11
  实用功能 practical_utility        5    1    0    0    0     6
  幻想与机械 fantasy_machinery      1    2   14    0    1    18
  矩阵内小计                       20   15  128   32    6   201

矩阵外桶计数:
  城市生活 city_life               18
  运动 sports                      10
  田园 farm                         5
  工程结构 engineering_misc         3
  音乐 music                        1
  自然世界 nature_misc              4
  校园 campus                       1
  游乐园 amusement                  2
  海洋航行 maritime_misc            2
  博物馆 museum                     1
  其他 other                        2
  矩阵外小计                       49

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
  SKIP   R4   [P0] E2E 冒烟 (run_e2e_smoke.sh)                  -
  SKIP   R5   [P0] 发布门禁快检 (run_release_gate.sh)       -
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
  SKIP   R17  [P1] D4+ 扰动仿真抽检 (validate --jitter 50)  -
  PASS   R18  [P1] 内容系列归类机检 (check_content_series --strict) 0s
  SKIP   M1   [P0] Windows/macOS 实机打包验收 + 代码签名/公证 -
  SKIP   M2   [P0] Android 真机验收 + 商店上架资料      -
  SKIP   M3   [P0] 隐私政策法务定稿 + 合规自查单     -
  SKIP   M4   [P0] E2E 矩阵 P0 人工要点打钩与签核记录 -
  SKIP   M5   [P0] 实物抽样实搭签核 (R6/R7 只报告缺口) -
  SKIP   M6   [P0] 软著 / ICP 备案 / 开发者账号 / 运营主体 -
--------------------------------------------------------------
 合计 25 项: 14 PASS / 2 FAIL / 9 SKIP (其中 P0 失败 2 项)
 结论: 存在 2 项 P0 失败 —— 未达上架就绪, 逐项对照清单补齐
 分项日志: /tmp/magtile_v1_readiness_5QnOQo

 阻塞项指引 (工程侧已触顶, 见 docs/reports/LAUNCH_BLOCKERS_2026-08-25.md):
   路径 A 实物签核 —— R6/R7: 按 docs/reports/PHYSICAL_REVIEW_QUEUE.md 实搭落盘
   路径 B 配额解冻 —— G2 红灯②: D1>=20 且 D5>=6 (置换/扩库/豁免, 需你决策)
                        规划: docs/reports/QUOTA_SUBSTITUTION_PLAN_2026-08-25.md
   路径 C Manual P0 —— 行政/实机/沙盒/法务: docs/USER_HANDOFF.md §4

 难度配额快照 (--full 档 strict 守卫口径):
   ==============================================================
    难度配额检查 (D3 冻结硬闸门 —— CONTENT_GAP_AUDIT.md 7.3 节)
   ==============================================================
   主库模型总数:      250  (/tmp/wt-risk-report/magtile-studio/data/models)
     D1 (入门):          20  (8.0%)   解冻线 >= 20, 已达标
     D2 (进阶):          23  (9.2%)
     D3 (熟练):         156  (62.4%)
     D4 (挑战):          45  (18.0%)
     D5 (大师):           6  (2.4%)   解冻线 >= 6, 已达标
   
   D3 冻结状态: 已解冻 (D1 20 >= 20 且 D5 6 >= 6)
   ==============================================================
```

</details>

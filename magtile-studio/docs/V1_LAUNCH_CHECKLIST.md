# V1 上架就绪清单 (Launch Readiness Checklist)

本清单是「完整可上架商业软件」的**单一对账单**: 把 V1 商用上架前的全部
待办 (内容 / 付费 / 打包 / 合规 / 验收 / 实物 / 资质) 汇总为按 P0/P1
分组的可勾选清单, 每项标注自动化程度、执行载体与**当前真实状态**。
与既有文档的分工:

| 问题 | 文档 |
| --- | --- |
| **工程已完成什么、你还需做什么** | **[USER_HANDOFF.md](USER_HANDOFF.md)** |
| 卖给谁、怎么收费、里程碑定义 | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) |
| 用户路径逐条走通 (上架必测) | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) |
| 代码与内容质量关卡 (按提交跑) | [TESTING.md](TESTING.md) |
| 桌面打包怎么做 | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) / [../scripts/package_windows.md](../scripts/package_windows.md) |
| Android 外壳怎么构建与验收 | [../platforms/android/README.md](../platforms/android/README.md) |
| **上架前还差哪些事、差多少** | **本清单** |

## 0. 字段口径与自动探测

- **优先级**: 与 [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §0 同口径 ——
  **P0** = 上架阻断, 任一 P0 未就绪不允许出包上架; **P1** = 重要,
  允许带**已记录**的已知问题上架, 但必须在签核记录中留痕;
- **探测**: **Auto** = 有自动化载体可重复探测; **Auto(部分)** =
  数据链路自动化、真机/视觉/法务侧仍需人工; **Manual** = 纯人工;
- **状态**: ✅ 已就绪 / 🔶 部分就绪 (进行中) / ⬜ 未开始。状态列为
  **2026-08-25 仓库快照**; 标注「探测 Rn」的行以
  `tools/check_v1_readiness.sh` 的实时输出为准 (本清单不替代实跑)。

自动探测一键跑 (Auto 项全部串起来, 输出 PASS/FAIL/SKIP 摘要):

```bash
tools/check_v1_readiness.sh            # 全量: 含 E2E 冒烟 / 发布门禁快检 / 扰动仿真抽检 (数分钟)
tools/check_v1_readiness.sh --quick    # 快检: 跳过三个长跑项 R4/R5/R17 (记 SKIP)
tools/check_v1_readiness.sh --strict   # 签核档: E2E 冒烟用 --strict (SKIP 也算失败)
tools/check_v1_readiness.sh --help     # 完整用法
```

退出码: **0** = 无 P0 失败; **1** = 存在 P0 失败 (2026-08-25 22:03 UTC
`--quick` 实跑为 1: 合计 25 项 **14 PASS / 2 FAIL / 9 SKIP** —— 自动侧
P0 FAIL 仅剩 §8 实物复核缺口 R6/R7 两项, 其余自动项全 PASS (含 R18
系列归类机检首跑即绿); **250 基线后 R6/R7 仍为唯二 P0 FAIL**,
D4+ 待复核 46 个 0/46);
**2** = 环境/参数不满足。**内容库已扩容收官至 250 模型** (`2b2c4ff`,
内容批 F~I 合计 234→250; 收官批全量 QA 38 关卡全过 —— strict 巡检 +
L2 jitter + 免费层对齐全开)。全量档 (QA + L2 + L3 硬闸门) 最新实跑
留痕: [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md)
(**已刷新至治理批后 250 基线**: 2026-08-25 21:53 UTC, 基线 `b369bad`;
软件侧全绿 —— CTest **556/556** + 模型库 250/250 + 唯一性 31125
对 0 警告 + 系列归类 176+74 全合法, L2 抗扰动 46/46 x 50 轮全绿;
`--full --l2` 总退出码 1 来自两道**预期红**: L3 实物 0/46 + 难度配额
strict (D3 冻结 D1 0/20 / D5 1/6), 口径见 §7 G2);
全量就绪探测留痕:
[reports/READINESS_FULL_2026-08-25.md](reports/READINESS_FULL_2026-08-25.md)
(**已刷新至 250 基线** `2b2c4ff` 全量档实跑: 合计 24 项 16 PASS /
2 FAIL 仅 R6/R7 实物硬闸门 / 6 SKIP)。**阻塞项决策单** (三条并行解阻路径):
[reports/LAUNCH_BLOCKERS_2026-08-25.md](reports/LAUNCH_BLOCKERS_2026-08-25.md)。
L2 风险报告与结构族包**已刷新至 250
基线** (`ced770c`, 见 §8); strict 巡检深报告**已刷新至 250 基线**
(基线 `2b2c4ff` 实跑: 249 通过 + 1 白名单豁免, 逐步装配 250/250,
D4+ 46/46 x 50 轮全绿)。

## 1. 内容 (目标 200~250 模型 —— 上限 250 已达成)

体量目标取 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §8 V1 (100+) 与 V2
(250+) 之间的上架决议值 **200~250** (探测门槛默认 200, 可用
`--model-target` 调整); **2026-08-25 内容批 F~I 收官 (`2b2c4ff`) 后
全库 250 模型, 目标区间上限达成**; 质量红线见 [TESTING.md](TESTING.md)
第 7 节。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| C1 | 模型库体量达 200~250 | P0 | Auto (R1) | `data/models/*.json` 计数; [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 产能与主题池 | ✅ 250 个 JSON (最近登记批 `2b2c4ff` 247→250, 内容批 F~I 合计 234→250, 此前批 A~E 合计 209→234; R1 门槛 200 恒过, **200~250 目标区间上限达成**) |
| C2 | 全库质量门禁全绿 (16 关 QA + strict 零未豁免警告) | P0 | Auto (R5) | `tests/run_full_qa.sh` / `tools/run_strict_audit.sh`; 内容批 PR 一键机检 `tools/review_content_batch.sh` (五道阻断关卡: strict 校验 / D3 冻结 / series 归类 / core-9 分层 / 唯一性抽查, 用法 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §4.3); 巡检深报告 [reports/STRICT_AUDIT_2026-08-25.md](reports/STRICT_AUDIT_2026-08-25.md) (**已刷新至 250 基线** `2b2c4ff`: 249 通过 + 1 白名单豁免, 逐步装配 250/250, D4+ 46x50 全绿); 最新全库实跑留痕 [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md) (**已刷新至 250 基线** `9955aaa`: QA + L2 全绿仅 L3 红) | ✅ 全库 250 模型 strict 双档零未豁免警告 (250 收官批 `2b2c4ff` 全量 QA 38 关卡全过: strict 巡检 + L2 jitter + 免费层对齐全开, 唯一性 31125 对 0 警告, core-9 片型分层全绿, 儿童文案守卫全绿; 内容批 F~I 16 个新模型逐个 validate 双档 + strict `--jitter 50` 全绿入库; D4+ 全集 45 → 46 —— 新增批旗舰 `stonehenge_01` D4; 唯一豁免 `suspension_bridge_01` 已文档化) |
| C3 | 模型库目录全量登记 + 缩略图全覆盖 | P0 | Auto (R2) | `tools/update_model_catalog.py` / `tools/generate_thumbnails.py` | ✅ JSON 250 / 目录登记 250 / 缩略图就绪 250 三方对账一致 (`2b2c4ff` 收官重登记; 难度分布 D2 x23 / D3 x181 / D4 x45 / D5 x1) |
| C4 | 免费层 30 对齐 (标签 = starter 清单, 全 core-9) | P0 | Auto (R3) | `tools/verify_free_tier.py`; 决议 [FREE_TIER_MANIFEST.md](FREE_TIER_MANIFEST.md) | ✅ 三条断言常绿 (随发布门禁复跑) |
| C5 | 主题覆盖与难度分布终审 (D1~D4 全覆盖, 系列不断档) | P1 | Auto(部分) (R18 系列归类机检; 矩阵判读与终审签核仍人工) | [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §2; 主题 × 难度矩阵进度快照 [reports/CONTENT_MATRIX_PROGRESS.md](reports/CONTENT_MATRIX_PROGRESS.md) (`tools/update_model_catalog.py --matrix-report` 自动生成, 13 主题 × D1~D5 对照 §2.2 终态 520); 归类机检 `tools/check_content_series.py --strict` (词表 `data/content_series_map.json`; 亦已注册 CTest 硬闸门 `content_series_gate` 随全量回归常跑, 并为 `tests/run_full_qa.sh` 可选关卡 20, `MAGTILE_SERIES_CHECK=1` 开启); 难度配额守卫 `tools/check_difficulty_quota.py` (D1~D5 分布报告 + D3 冻结判定, `tests/run_full_qa.sh` 关卡 21 常开报告型, `MAGTILE_DIFFICULTY_QUOTA=1` 升级 strict 守卫档, 解冻线 D1 >= 20 且 D5 >= 6, 口径 [TESTING.md](TESTING.md) 3.19); `magtile_app library` 分布输出 | 🔶 扩容已收官 (250 上限, 难度分布快照见 C3); series 归类回填收官 **250/250** (R18 机检全绿: 归类齐全、词值零非法), 矩阵进度快照已入库 (矩阵内 176/520 = 34%, 矩阵外聚桶 74 —— 断档格与超编格以快照为准); 上架前对照快照人工终审一次 |

## 2. 付费闭环 (订阅 / IAP)

定价与商品口径见 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2/§3
(订阅为收入主体, 儿童侧零价格信息红线见 [UI_UX_SPEC.md](UI_UX_SPEC.md) §11)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| B1 | 计费适配层 + 假计费闭环 (三档商品 / 购买 / 恢复 / 统一解锁口径) | P0 | Auto (R10) | `src/billing/` + `magtile_billing_test` + `qt_billing_bridge`; [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.2 | ✅ 单测全绿, Qt 订阅页接假计费闭环 |
| B2 | 真实商店计费接入 (Windows 商店 / Google Play `StoreBillingClient`) | P0 | Auto (R11 分平台: Google Play 接线 PASS / Windows 档 R11W 接线 PASS) | Android: `platforms/android/app/.../PlayBillingManager.kt` (Play Billing 6.x 购买/恢复/回执确认 + 启动静默恢复 → 既有 `setSubscriptionActive` 契约键, 与 FakeBilling 同键) + 家长门后订阅页 `SubscriptionActivity.kt` (三档档位卡实时取 Play 价格 + 主 CTA + 恢复购买 + 会话守卫, 对齐桌面 Qt SubscriptionPage; 接线与订阅页说明 [../platforms/android/README.md](../platforms/android/README.md) 第三节); Windows: `src/billing/store_billing_client.cpp` 的 `MAGTILE_BILLING_WINDOWS_STORE` 宏分支 (WinRT `StoreContext` 查商品 / `RequestPurchaseAsync` 收银台购买 / `AddOnLicenses` 许可证恢复 + Qt 壳启动静默恢复 → 同一 `setSubscriptionActive` 契约键; 仅 MSIX 商店包配置 `-DMAGTILE_BILLING_WINDOWS_STORE=ON` 编入, 本地开发档保持 FakeBilling) | 🔶 Google Play 与 Windows 商店两侧代码均已接线, R11/R11W 实跑 PASS (Android: Release 走 Play Billing, Debug 保留模拟订阅; Windows: 商店上下文仅 MSIX 包身份可用, 商品表查到才亮价格卡, 否则退回「即将上线」占位; 商品 id 三端统一 `sub_monthly`/`sub_yearly`/`sub_family_yearly`); Qt 订阅页桌面侧 UI 已收口 —— 商店档真实价格卡 (商品表查到才亮价, 「商店可用 <=> 价格卡真有价」口径随 `qt_gui_smoke --smoke-parent-flow` 终态常态断言) + 「恢复购买」按钮 + `simulatedBilling` 分流标注 (CTA 与购买/恢复成功文案只在假计费档标「开发模拟」, 商店档真实扣费不标; 取消/退款指引商店档指向系统商店订阅管理, 商店暂时联系不上给温和「稍后再试」而非「即将上线」, `qt_billing_bridge` 常态断言); Android 订阅页 UI 已落地 (家长门后 SubscriptionActivity: 三档档位卡价格实时读 Play 后台、查询不可用退温和占位绝不显示空价格卡, 主 CTA 接 purchase + 「恢复购买」接 restore, 会话守卫到期自动退场儿童侧零价格 §11; Debug 档「模拟已订阅」QA 开关同页, assembleDebug 绿 + 文案守卫全绿) —— B3 的购买入口依赖已解除; 剩余: MSIX 商店包出包 (§3 侧) + 双商店后台商品配置与沙盒验收 (B3) |
| B3 | 商店商品配置 + 沙箱付费验收 (真实账号购买 / 恢复 / 退款链路) | P0 | Manual | 商品 id 约定见 `store_billing_client.hpp` 注释; 价格表 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §3.1; Google Play 侧分步验收文档 [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) (内部测试轨 + 许可测试账号 + 购买/恢复/断网宽限期勾选清单; 接线概要 [../platforms/android/README.md](../platforms/android/README.md) 第三节); Windows 商店侧分步验收文档 [WINDOWS_STORE_BILLING_SANDBOX_QA.md](WINDOWS_STORE_BILLING_SANDBOX_QA.md) (Partner Center 附加内容配置 + MSIX 商店包测试安装 + 同构勾选清单; 微软商店无沙盒无时间压缩, 成本控制与上线后回归项口径见文内第四/五节) | ⬜ Google Play 代码侧已就绪 (B2 🔶, 订阅页购买/恢复入口已落地 —— SubscriptionActivity, 前置 P4 已满足) 且分步验收文档已备, 执行仍依赖开发者账号 (L3) 与 Play Console 商品配置; Windows 代码侧已就绪 (B2 🔶) 且分步验收文档已备, 执行依赖 Partner Center 商品配置 (附加内容 id = 三端统一商品 id; 订阅附加内容需微软侧开通账号权限) 与 MSIX 商店包出包 |
| B4 | 首批 3 个一次性内容包上线 | P1 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.3/§8 V1 交付物 | ⬜ 未开始 (订阅先行) |
| B5 | 儿童侧零价格红线复核 (订阅入口必过家长门, 无倒计时/催购) | P0 | Auto(部分) (R16 文案红线守卫 + E2E 家长门流; 视觉/语气终审仍人工) | `qt_gui_smoke --smoke-parent-flow` 自动; 文案红线 `tools/check_child_friendly_copy.py` 全库扫描 (恐吓词/催促稀缺话术, [UI_UX_SPEC.md](UI_UX_SPEC.md) §11 无倒计时/无「即将涨价」等) | 🔶 家长门流随 E2E 常绿 + 文案红线随 R16 常态守卫 (2026-08-25 17:20 实跑 PASS: 260 文件 7751 段用户可见中文文案 0 违规), 上架前视觉与语气人工终审 |

## 3. 桌面 Windows / macOS

打包手册: [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md)
(Qt 商用壳, 含 LGPL 合规清单) 与
[../scripts/package_windows.md](../scripts/package_windows.md) (NSIS/WiX)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| D1 | 打包资产与手册完备 (CPack / WiX / starter 清单 / 第三方声明) | P0 | Auto (R9) | `platforms/windows/packaging/` + 两份打包手册 + CI `windows-release.yml` | ✅ 资产齐备 (探测存在性) |
| D2 | Windows 安装包在真实 runner 出包 (流水线转正) | P0 | Manual | `.github/workflows/windows-release.yml` (**草案, 尚未在真实 runner 上验证**, 见该文件头注) + 触发与首跑签核指南 [../scripts/package_windows.md](../scripts/package_windows.md) §8 (触发命令 / 预期产物 / CI 排查表 / 签核登记表) + 触发前预检清单 [reports/WINDOWS_CI_PREFLIGHT.md](reports/WINDOWS_CI_PREFLIGHT.md) (平台前提 / 仓库状态 / 场次纪律, 本地可验部分已全绿登记) | 🔶 首跑阻塞项已修 (windows-latest 的 Win Server 2025 镜像已移除预装 NSIS → 流水线打包前 Chocolatey 自装) + Linux 可验子集全绿 (actionlint 零告警 / 版本提取步 pwsh 实测 / `smoke_qt_windows.ps1 -DryRun` 自检过 / `smoke_qt_linux_pack.sh` 41 项全绿); 触发与验收路径已落档 §8 —— workflow 已带 `workflow_dispatch` + `model_set` (full/starter) 输入, 验收口径为 full/starter 两场 dispatch 试跑全绿并按 §8.4 登记签核 (注意 dispatch 需 workflow 已在默认分支, 未合入前替代路径见 §8.1); 真实 runner 出包仍待触发, 全绿后按 §8.5 翻 ✅ |
| D3 | Windows 实机验收 (干净 Win10/11, 未装 Qt/VS) | P0 | Manual | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §11 (自动冒烟 `smoke_qt_windows.ps1` + 人工验收单) | ⬜ 无 Windows 实机记录 |
| D4 | macOS 打包 (macdeployqt + DMG) + 签名公证 (Developer ID / notarytool) | P0 | Manual | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §5 macOS 小节 (公证步骤已写明) + §12 验收清单; 人工验收单 (可打印) [reports/MACOS_ACCEPTANCE_CHECKLIST.md](reports/MACOS_ACCEPTANCE_CHECKLIST.md) | ⬜ 无 macOS 实机记录; 人工验收单已备 (36 项勾选表: 安装/启动/教程/家长门/订阅/签名公证, D4 收口须正式档 P0 32 项全过并按其 §9 签核回填) |
| D5 | 代码签名证书 (Windows Authenticode; 依赖运营主体 L4) | P0 | Manual | [../scripts/package_windows.md](../scripts/package_windows.md) 第十一节 (`signtool`, 未签名会被 SmartScreen 拦截) | ⬜ 证书未申请 |
| D6 | LGPL 合规逐项核对 (Qt 随包分发) | P0 | Auto(部分) (可自动化项脚本断言; 人工项出包时打钩) | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §8 清单 (逐项标注 [自动]/[自动·发布档]/[人工]); 自动核对脚本 `scripts/check_lgpl_compliance.sh` (对出包产物: 动态链接非静态链 DT_NEEDED/ldd/静态吸入符号三重断言 + 仅 LGPL 模块白名单·白名单外 Qt 库当场失败 + THIRD_PARTY_NOTICES/EULA/README 必备文件清单, 已挂接 `smoke_qt_linux_pack.sh` 第 6 步随 D7 冒烟常跑); `THIRD_PARTY_NOTICES.md` 已随包 | 🔶 可自动化项已脚本化并实跑通过 (9 项 OK; 发布前追加项 LGPLv3/GPLv3 全文 + Qt 精确版本/download.qt.io 源码地址 3 项 WARN 属预期缺口 §10 待办, 出正式包前跑 `--release` 档缺则硬性失败); 人工项 (未修改源码/可替换性 §4(d)/界面署名/法务终审) 出包时对照 §8 逐项打钩 |
| D7 | Linux 打包冒烟 (无 Win/mac 机器时的链路自证) | P1 | Auto (单独跑) | `scripts/smoke_qt_linux_pack.sh`; [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §9 | ✅ 已实跑全绿 (Ubuntu, Qt 6.4.2 / NSIS 3.10: 三档 TGZ 清单断言 + NSIS 编译冒烟 + offscreen 启动 + LGPL 合规自动核对 `check_lgpl_compliance.sh` (原 ldd 核验扩展, D6 载体), 落档 [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §9); 未纳入常跑 CI, 出包前复跑一次 |
| D8 | 自动更新 (COMMERCIAL_PLAN §8 列为 V1 交付物) | P1 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §8 V1; [ROADMAP.md](ROADMAP.md) 阶段 3 | ⬜ 未实现 —— 上架前须决策: 实现, 或降级 V1.1 并在签核记录留痕 |

## 4. Android

构建与验收手册: [../platforms/android/README.md](../platforms/android/README.md)
(第一节 Gradle 构建 / 第二节纯 NDK / 第五节 CI / 第六节缺口)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| A1 | APK 构建 + 包内容校验 CI 常绿 (原生库 / 数据 / 缩略图) | P0 | Auto | `.github/workflows/android.yml` (assemble-debug + ndk-so 双 job) | ✅ CI 常跑 |
| A2 | JNI 符号与 NDK 交叉编译本地断言 | P0 | Auto (R4 内 E2E-14a) | `tools/run_e2e_smoke.sh` (符号清单解析自 `android.yml`, 口径自动同步) | ✅ 随 E2E 冒烟 |
| A3 | release 签名配置 (signingConfig + 密钥管理; 商店档产物) | P0 | Auto (R13: signingConfigs 块 + `keystore.properties.example` 齐备) | `platforms/android/app/build.gradle.kts` signingConfigs (从不入库的 `keystore.properties` 读取) + [../platforms/android/SIGNING.md](../platforms/android/SIGNING.md) (生成/出包/CI 口径) | 🔶 签名接线与模板/手册已落地 (缺配置时 release 报错指引, debug 不受影响); 真实 keystore 生成与商店档出包属人工 (随 A4/A5) |
| A4 | 真机验收 (arm64 API 26+; E2E-03/14/15 + 触屏手势 + 首启解包) | P0 | Manual (可自动化部分随设备仪器测试) | 勾选表 [reports/QA_ANDROID_DEVICE_CHECKLIST.md](reports/QA_ANDROID_DEVICE_CHECKLIST.md) (§1 自动侧 `platforms/android/run_instrumented_smoke.sh` + §2~§4 人工项 + §5 签核登记); [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §1/§3; [../platforms/android/README.md](../platforms/android/README.md) 第一节走查 | ⬜ 无真机验收记录; 执行载体已备 —— M-01~M-05 可自动化部分入仪器测试 (断点续搭/完成链路+首搭成就/家长门入口/订阅锁可见性/手势事件链路, 设备接入即跑), 纯视觉/手感项 @Ignore 骨架挂人工勾选表 |
| A5 | 商店上架资料 (图标/截图/儿童类目分级问卷; Google Play 亲子政策 / 国内商店资质) | P0 | Auto(部分) (R14/R15 守卫文案与资质清单文档结构; 素材制作与后台填报仍人工) | 文案字段 [STORE_LISTING.md](STORE_LISTING.md) + 资质办理 [CHINA_STORE_COMPLIANCE.md](CHINA_STORE_COMPLIANCE.md); [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2 (优先华为/应用宝) + §6.3 | ⬜ 素材/资质未开始 (国内商店依赖 L1/L2); 两份清单文档已入库, 结构由 R14/R15 常态守卫 |
| A6 | starter 子集包验证 (`-PmagtileAssets=starter` 恰 30 模型) | P1 | Manual | [../platforms/android/README.md](../platforms/android/README.md) 第四节; [FREE_TIER_MANIFEST.md](FREE_TIER_MANIFEST.md) §1 | 🔶 构建选项已落地, 出包前抽验一次 |
| A7 | Android 已知体验缺口盘点留痕 (视口 MSAA / 按需渲染节电 / 家长中心完整功能等) | P1 | Manual | [../platforms/android/README.md](../platforms/android/README.md) 第六节「后续计划」 | 🔶 缺口已文档化, P1 允许带已记录问题上架 |

## 5. 隐私与儿童合规

合规基线: [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md) (数据清单 +
自查单) 与 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §6.3 (COPPA / 中国
《儿童个人信息网络保护规定》/ GDPR-K 策略: 零账号可玩 + 不触发收集)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| V1 | 隐私政策草稿入库并随应用可查阅 | P0 | Auto (R8 存在性) | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) | 🔶 草稿已起草 (家长一页纸 + 正文十节) |
| V2 | 隐私政策法务定稿 (运营主体全称 / 注册地址 / 备案号 / 生效日期) | P0 | Manual | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) 头部「状态: 草稿」标注; 依赖 L4 (影响面见 [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §1.3) | ⬜ 未定稿 |
| V3 | 应用内数据管理入口 (家长中心查阅 / 导出 / 删除) | P0 | Auto(部分) | 数据隐私后端 `progress/data_privacy` (三端同一导出契约) + Qt `privacy_backend` (家长中心「隐私与数据」区) + Android JNI `progressStoreAvailable`/`exportLocalDataJson`/`clearLocalData` (家长门后隐私面板, 与 Qt 同口径: 温和禁用 / 防覆盖原子导出 / 清除后锁家长会话) | 🔶 Qt + Android 双端在位 (同一核心实现同一导出格式); 真机走查随 V4 自查单 |
| V4 | 上架前跑一遍安全与隐私自查单 (三平台逐项) | P0 | Manual | [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md) 合规检查清单 (§3/§4/§5.2/§6/§8/§11) 的可执行签核载体: [reports/PRIVACY_SECURITY_SIGNOFF.md](reports/PRIVACY_SECURITY_SIGNOFF.md) (数据收集 / 家长门 / 导出删除 / 离线 / 第三方 SDK / 计费回执 六组 × Windows/macOS/Android 逐项勾选 + 平台签核栏与总放行判定, 逐组与 [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) 对外承诺互证; Android 计费组复用 [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) 勾选清单只记结论) | 🔶 三平台逐项签核单已入库 (空白模板, 含已知缺口预登记; 其中 Android 备份白名单缺口已关闭 —— manifest 挂 `dataExtractionRules` + `fullBackupContent` 双规则仅含 progress.db, DC7 改为对产物核验); 实际执行须对候选出包产物进行 (随 D2/D4/A4 出包与真机验收、V5 断网复核同批), 归档签核后转 ✅ |
| V5 | 离线承诺断网复核 (断网走安装启动与教程主链路) | P1 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) E2E-20 | ⬜ 随真机验收一并做 |

## 6. E2E 验收

路径矩阵与签核规则: [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) (§1 全部
20 条路径, §3 签核规则)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| E1 | 自动子集全绿: `tools/run_e2e_smoke.sh --strict` (Qt 与 Android 项不允许 SKIP) | P0 | Auto (R4) | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §2/§3 | ✅ 签核档实跑全绿: `--strict` 9 项 0 SKIP (含 Qt 无头/按钮级路径冒烟与 NDK r27 JNI 符号断言, 2026-08-25 实跑), 且已随 CI 每次 push 常态复跑 (`qa.yml` e2e-strict job, FAIL/SKIP 均红灯); 上架签核时按 §10 复跑留痕 |
| E2 | 矩阵 P0 的 Manual / Auto(部分) 人工要点逐条打钩, 归档签核记录 (执行人/日期/设备) | P0 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §1 「人工要点」列 | ⬜ 待真机与实机验收时执行 |
| E3 | P1 路径已知问题留痕 (允许带问题上架但须记录) | P1 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §3 第 3 条 | ⬜ 随 E2 一并归档 |

## 7. 发布门禁 (Release Gate)

门禁定义与时机: [TESTING.md](TESTING.md) 第 5 节; 一键入口
`tools/run_release_gate.sh`; CI 手动流水线 `.github/workflows/release-gate.yml`。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| G1 | 快检档常绿 (免费层对齐 + strict 全库巡检 + 待复核报告) | P0 | Auto (R5) | `tools/run_release_gate.sh`; 最新全量实跑留痕 [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md) | ✅ 探测通过 (报告型 L3 项不阻断); 全量档 QA 41 子关卡 (软件侧 38 过) + L2 抗扰动档全绿 (**治理批后基线实跑** `b369bad`: CTest 556/556, 模型库 250/250, D4+ jitter 46/46) |
| G2 | 出包终防线全绿: `tools/run_release_gate.sh --full --fail-on-pending` | P0 | Auto + 线下 | 同上; `--full` 档四道发布专项全开 (免费层对齐 / strict 巡检 / 系列归类机检 `tools/check_content_series.py --strict` / 难度配额守卫 `tools/check_difficulty_quota.py --strict` = 全量 QA 关卡 10/15/20/21, 口径 [TESTING.md](TESTING.md) 3.19 与第 5 节); D4+ 实物复核清零 (见 §8) 与 D3 解冻 (D1 >= 20 且 D5 >= 6) 是两道并列前置 | ⬜ **双红灯口径 (治理批 `324e1b9` 后)**: `--full --fail-on-pending` 同时被两道硬闸卡红 —— ① L3 实物硬闸门: **250 基线 D4+ 待复核 46 个 0/46** (见 [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md)), §8 实搭清零前红灯; ② 难度配额 strict 守卫 (QA 关卡 21, `tools/check_difficulty_quota.py --strict`): D3 冻结生效 (当前 D1 0/20、D5 1/6), **D1 >= 20 且 D5 >= 6 补齐前红灯** (属预期告警, 不允许占位交差); 两道红灯之外软件侧全绿 —— `b369bad` 基线 `--full --l2` 实跑 QA+L2 全绿, 总退出码 1 仅来自难度配额守卫; 解除路径分别为 §8 缩减集实搭清零与 D1/D5 内容补齐 |

## 8. 实物复核 (L2 三层缩减流程)

**口径升级 (2026-08-25 L2 决议)**: [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md)
的 L2 物理仿真层从规划转入工程实现, 实物验证升级为**三层流程** ——
上一层全绿才进下一层, 人手实搭量随之大幅缩减:

1. **第一层 软件全绿 (Auto, 既有)**: strict 双档零未豁免警告 +
   16 关 QA (§1 C2, 探测 R5);
2. **第二层 虚拟物理验证 (Auto, L2 新增)**: `magtile_app validate
   --jitter N` 蒙特卡洛容差抖动 (逐步注入 ±1.5mm/±2° 位姿扰动,
   D4+ 默认 50 次全绿, 专门捕捉 F08 错位累积失稳,
   [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) §4 失效分类) +
   `tools/physical_risk_report.py` 全库风险评分排序 (JSON/Markdown
   报告, 输出「建议人手验 Top 15」) + [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md)
   §2 触发条件自动标记 (L1 Warning / 高墙链 / 临界重心 / 弱磁承重)
   代码化; 门禁接入 `tools/run_strict_audit.sh` /
   `tools/run_release_gate.sh`, 就绪探测 R17;
3. **第三层 缩减后人手实搭 (Manual)**: 只搭 **risk Top 15 + 结构族
   代表** (`tools/physical_family_pack.py` 结构族聚类, 每族一个代表
   实搭, 同族其余成员由「代表实搭通过 + 第二层全绿」覆盖) ——
   **全库 250 个模型不必全搭, D4+ 也不再逐个人手清零**; 实搭失败经
   `tools/physical_failure_registry.py` 登记入账, 按四步闭环手册
   [PHYSICAL_CALIBRATION_WORKFLOW.md](PHYSICAL_CALIBRATION_WORKFLOW.md)
   提炼为负例夹具, 回灌第二层参数校准。

**红线不变**: 软件与仿真全绿仍**不豁免**人手实搭 —— 第二层只缩减
「搭哪些」, 不放松「怎么搭」; 缩减集内**未实搭严禁标记
`physical_verified`**; 模型结构改动后旧结论作废, 同族代表结论一并
复验。规程: [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md);
抽样报告: [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md);
复核人上手指南 (备料/工时/打印/落盘/照片归档):
[reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md)。

**载体状态注**: L2 工具链已**全部入库** (2026-08-25 L2 批次 10/10
交付): jitter CLI `8b424be` / 风险报告 `41bda4c` (公共入口增补
`6dff7cb`) / 结构族 `b093b6d` (交付时 209 模型 → 154 族; **250 基线
刷新** `ced770c`: 185 族, 多成员 52, 必搭 36 / 可缓建 10 省 21%,
实跑报告 [reports/PHYSICAL_FAMILY_PACK.md](reports/PHYSICAL_FAMILY_PACK.md)) / 失败登记
`08d3018` / R17 探测 `13e6cd9` / 门禁接入 `6acfa54` + `607c0cb` /
夹具与单测 `262ebc3` (ctest 472/472 绿) / 文档口径 `bca88fd` +
`df902b9`; 实跑状态以 `tools/check_v1_readiness.sh` 输出为准。
抖动首巡揪出的 **4 个边缘模型已全部加固入库** (2026-08-25 接力批:
`lego_style_house_01` `24fd0ec` / `ball_run_tower_01` `8d07fe5` /
`marble_run_spiral_01` `114c154` / `rainforest_canopy_01` `2ffc06e`),
D4+ `--jitter 50` 全绿 (234 基线 45/45; **250 基线全集 46** —— 内容批
F~I 旗舰 `stonehenge_01` D4 入列, 250 基线 46x50 全绿见
[reports/STRICT_AUDIT_2026-08-25.md](reports/STRICT_AUDIT_2026-08-25.md)),
`run_release_gate --full --l2` 软件侧 QA+L2 全绿 (L3 + 难度配额两道预期红, 见
[reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md), **已刷新至治理批后 250 基线** `b369bad`)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| S0 | 第二层虚拟物理验证全绿 (D4+ 默认 `--jitter 50` + 风险报告 + 自动标记) | P0 | Auto (R17) | `magtile_app validate --jitter N` (蒙特卡洛 ±1.5mm/±2° 逐步扰动, 失败记 F08 类) + `tools/physical_risk_report.py` + [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) §2 触发条件代码化; 门禁接入 `tools/run_strict_audit.sh` / `tools/run_release_gate.sh`; jitter 夹具与 risk report 单测随 ctest; 就绪探测载体 `tools/check_v1_readiness.sh` R17 (P1 报告档): D4+ 确定性抽检 —— D5 全数优先 + 大体量 D4 按总片数降序补足 (默认 10 个, `--jitter-sample` 可调; 与 `physical_sample_pack.py` 同一风险代理口径), 逐个 `validate --jitter 50`; 慢项 `--quick` 记 SKIP 而**全量签核必跑**: 二进制缺失 / `--jitter` 特性不可用 / 抽样为空一律显式 FAIL 不静默跳过; `physical_risk_report.py` 落地后抽样源可切换其高风险 Top 子集 | ✅ 工具链 + 4 边缘模型加固全部入库; D4+ jitter 全绿 (234 基线 45/45 复验 `3d24d74`; **250 基线 D4+ 全集 46** —— 内容批 F~I 旗舰 `stonehenge_01` D4 入列, 其余 15 个全部 D2/D3, 逐个 `--jitter 50` 全绿入库, 250 基线 46x50 全绿见 [reports/STRICT_AUDIT_2026-08-25.md](reports/STRICT_AUDIT_2026-08-25.md)); `run_release_gate --full --l2` QA+L2 全绿 (实跑留痕 [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md), **已刷新至治理批后 250 基线** `b369bad`) |
| S1 | 缩减人手集实搭签核: **risk Top 15 + 结构族代表** (并集去重, 清单以两份报告实跑输出钉死) | P0 | Auto 报告 (R6 + R17) + Manual 实搭 | `tools/physical_risk_report.py` Top 15 人手建议 (实跑报告 [reports/PHYSICAL_RISK_REPORT.md](reports/PHYSICAL_RISK_REPORT.md), **已刷新至 250 基线** `ced770c`: 250 全扫, L2 标记 163 / l2_required 172, Top3 `skyscraper_01` 63.9 / `suspension_bridge_01` 55.4 / `lighthouse_01` 54.6 与 234 库持平, Top15 清单 ≈ 17.3 小时不变) + `tools/physical_family_pack.py` 结构族代表 (实跑报告 [reports/PHYSICAL_FAMILY_PACK.md](reports/PHYSICAL_FAMILY_PACK.md), **已刷新至 250 基线**: 185 族, 多成员 52, 必搭 36 / 可缓建 10 省 21%); 规程 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md) + 上手指南 [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md) + 工作单 [reports/PHYSICAL_SIGNOFF_WORKSHEET.md](reports/PHYSICAL_SIGNOFF_WORKSHEET.md); 原 V1 抽样包 10 个 ([reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md), `tools/physical_sample_pack.py --fail-on-missing-sample`) 预计与 Top 15 高度重合, 作首批排产兼第二层校准数据 | ⬜ 0 已复核 —— 人手范围由报告钉死, **不必 250 全搭** |
| S2 | D4+ 实物风险全覆盖清零 (缩减集实搭 + 同族代表结论 + 第二层全绿合围) | P0 | Auto 报告 (R7, 覆盖口径随 L2 门禁接入升级) + Manual 实搭 | `tools/list_physical_pending.py --fail-on-pending` + `tools/physical_family_pack.py` 族谱; 落盘口径见 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 5.2 | ⬜ 三层覆盖口径已定 (原「45 个逐个实搭」改为缩减集 + 族代表覆盖); 实搭失败经 `tools/physical_failure_registry.py` 登记整改, 整改后同族复验 |
| S3 | 免费层 D3 抽检 30% (免费层无 D4+, 实物风险由抽检政策覆盖) | P1 | Manual | [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §4.3; [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md) §2 免费层说明 | 🔶 已有 3 个 D3 实物复核落盘 (`content_meta.physical_verified`, R6 报告一致性核对可见) |
| S4 | 实搭结果回灌校准 (实物失败 → 登记账本 → 负例夹具 → 第二层参数校准) | P1 | Auto(部分) (账本完整性 `check` 可门禁) | `tools/physical_failure_registry.py` (失效账本 `data/physical_failures.json`: add 登记 / mark-sunk 关账 / check 完整性门禁) + 四步闭环手册 [PHYSICAL_CALIBRATION_WORKFLOW.md](PHYSICAL_CALIBRATION_WORKFLOW.md) | ⬜ 载体已入库 (账本工具 + 手册, `08d3018`), 执行随缩减集实搭同步 (首批 10 个实搭结果即首轮校准输入) |

## 9. 软著 / 备案 / 商店资质

国内商店上架前置项见 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2 与
§6.3 末条; 逐项**办理动作**、负责方与串行关键路径见
[CHINA_STORE_COMPLIANCE.md](CHINA_STORE_COMPLIANCE.md) (本节是其
状态快照, 两处互为回链); 面向执行人的**分步操作手册** (去哪个网站、
带什么材料、按什么顺序、等多久) 见
[ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) (L1~L5 逐行
挂链见下表)。办理本身为线下法务/行政流程无自动化载体 (就绪探测记
SKIP M6), 建议**最早启动** (周期不受工程进度控制); 该办理清单的
章节/条目/交叉引用完整性由 `tools/check_china_compliance_docs.py`
守卫 (探测 R15, 已接入 `tools/check_v1_readiness.sh`)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| L1 | 软件著作权登记 (国内安卓商店硬前置) | P0 (国内) | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2/§6.3; 办理步骤与材料清单 [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §2 | ⬜ 未启动 (可执行步骤已细化) |
| L2 | App 备案 (工信部 ICP; 隐私政策 §5 承诺境内合规云) | P0 (国内) | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §6.3; [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) §5; 备案流程与前置 [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §3 | ⬜ 未启动 (可执行步骤已细化) |
| L3 | 开发者账号开通 (华为 / 应用宝 / Google Play / Microsoft Store; macOS 走 Developer ID 直分发亦需 Apple 开发者账号) | P0 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2 商店策略; 逐平台开通步骤 [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §4 | ⬜ 未启动 (可执行步骤已细化) |
| L4 | 运营主体信息定稿 (名称 / 地址 / 联系邮箱 → 隐私政策 V2 / 商店资料 A5 / 签名证书 D5 的共同前置) | P0 | Manual | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) §1/§10 占位符; 定稿字段与对隐私政策的影响 [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §1 | ⬜ 未定 (定稿字段清单已细化) |
| L5 | 商标注册与 IP 红线终审 (不用品牌词, 无侵权外观) | P1 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §6.1 (红线已文档化); 启动动作 [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §5 | 🔶 红线自查已内建于内容管线, 注册未启动 |

## 10. 放行规则

1. **自动侧**: `tools/check_v1_readiness.sh --strict` 退出码 0 (即全部
   Auto P0 项 PASS), 其内含并等价于 [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md)
   §3 第 1 条的两道命令口径 (`run_e2e_smoke.sh --strict` +
   `run_release_gate.sh` 系列);
2. **人工侧**: 本清单全部 P0 行状态到 ✅, Manual 项附签核记录
   (执行人 / 日期 / 设备或单据编号); P1 未完成项逐条写明问题与影响面;
3. **维护约定**: 新增上架相关待办**先登记本清单**; 能自动探测的落到
   `tools/check_v1_readiness.sh` 并在「探测」列标注检查号; 状态列
   随每次盘点更新快照日期 (§0), 不允许只改状态不改日期。

# V1 上架就绪清单 (Launch Readiness Checklist)

本清单是「完整可上架商业软件」的**单一对账单**: 把 V1 商用上架前的全部
待办 (内容 / 付费 / 打包 / 合规 / 验收 / 实物 / 资质) 汇总为按 P0/P1
分组的可勾选清单, 每项标注自动化程度、执行载体与**当前真实状态**。
与既有文档的分工:

| 问题 | 文档 |
| --- | --- |
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
tools/check_v1_readiness.sh            # 全量: 含 E2E 冒烟与发布门禁快检 (数分钟)
tools/check_v1_readiness.sh --quick    # 快检: 跳过两个长跑项 (记 SKIP)
tools/check_v1_readiness.sh --strict   # 签核档: E2E 冒烟用 --strict (SKIP 也算失败)
tools/check_v1_readiness.sh --help     # 完整用法
```

退出码: **0** = 无 P0 失败; **1** = 存在 P0 失败 (当前仓库状态下预期
非零 —— 见下文各 ⬜ 项); **2** = 环境/参数不满足。

## 1. 内容 (目标 200~250 模型)

体量目标取 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §8 V1 (100+) 与 V2
(250+) 之间的上架决议值 **200~250** (探测门槛默认 200, 可用
`--model-target` 调整); 质量红线见 [TESTING.md](TESTING.md) 第 7 节。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| C1 | 模型库体量达 200~250 | P0 | Auto (R1) | `data/models/*.json` 计数; [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 产能与主题池 | 🔶 191 个 JSON (目标 200 还差 9, 内容批次仍在推进) |
| C2 | 全库质量门禁全绿 (16 关 QA + strict 零未豁免警告) | P0 | Auto (R5) | `tests/run_full_qa.sh` / `tools/run_strict_audit.sh`; 最近报告 [reports/STRICT_AUDIT_2026-08-25.md](reports/STRICT_AUDIT_2026-08-25.md) | ✅ 全库 strict 双档零未豁免警告 (唯一豁免 `suspension_bridge_01` 已文档化) |
| C3 | 模型库目录全量登记 + 缩略图全覆盖 | P0 | Auto (R2) | `tools/update_model_catalog.py` / `tools/generate_thumbnails.py` | 🔶 目录登记 187 / 缩略图就绪 179 / JSON 191 (在制批次未收口, 以 R2 实时输出为准) |
| C4 | 免费层 30 对齐 (标签 = starter 清单, 全 core-9) | P0 | Auto (R3) | `tools/verify_free_tier.py`; 决议 [FREE_TIER_MANIFEST.md](FREE_TIER_MANIFEST.md) | ✅ 三条断言常绿 (随发布门禁复跑) |
| C5 | 主题覆盖与难度分布终审 (D1~D4 全覆盖, 系列不断档) | P1 | Manual | [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §2; `magtile_app library` 分布输出 | 🔶 主题池持续补批中, 上架前人工终审一次 |

## 2. 付费闭环 (订阅 / IAP)

定价与商品口径见 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2/§3
(订阅为收入主体, 儿童侧零价格信息红线见 [UI_UX_SPEC.md](UI_UX_SPEC.md) §11)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| B1 | 计费适配层 + 假计费闭环 (三档商品 / 购买 / 恢复 / 统一解锁口径) | P0 | Auto (R10) | `src/billing/` + `magtile_billing_test` + `qt_billing_bridge`; [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.2 | ✅ 单测全绿, Qt 订阅页接假计费闭环 |
| B2 | 真实商店计费接入 (Windows 商店 / Google Play `StoreBillingClient`) | P0 | Auto (R11 分平台: Google Play 接线 PASS / Windows 档 R11W SKIP) | Android: `platforms/android/app/.../PlayBillingManager.kt` (Play Billing 6.x 购买/恢复/回执确认 + 启动静默恢复 → 既有 `setSubscriptionActive` 契约键, 与 FakeBilling 同键; 接线说明 [../platforms/android/README.md](../platforms/android/README.md) 第三节); 桌面: `src/billing/store_billing_client.cpp` (跨商店接口缝) | 🔶 Google Play 侧已接线 (Release 走 Play Billing, Debug 保留模拟订阅; 商品 id 三端统一 `sub_monthly`/`sub_yearly`/`sub_family_yearly`); Windows 商店档未接 (MSIX 商店包前接入); Android 订阅页 UI (档位卡 + 恢复购买按钮) 随家长中心落地 |
| B3 | 商店商品配置 + 沙箱付费验收 (真实账号购买 / 恢复 / 退款链路) | P0 | Manual | 商品 id 约定见 `store_billing_client.hpp` 注释; 价格表 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §3.1; Google Play 侧走 Play Console 内部测试轨 + 许可测试账号 ([../platforms/android/README.md](../platforms/android/README.md) 第三节沙盒验收要点) | ⬜ Google Play 代码侧已就绪 (B2 🔶), 仍依赖开发者账号 (L3) 与 Play Console 商品配置; Windows 依赖 B2 Windows 档 |
| B4 | 首批 3 个一次性内容包上线 | P1 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.3/§8 V1 交付物 | ⬜ 未开始 (订阅先行) |
| B5 | 儿童侧零价格红线复核 (订阅入口必过家长门, 无倒计时/催购) | P0 | Auto(部分) | `qt_gui_smoke --smoke-parent-flow` 自动; 文案红线人工按 [UI_UX_SPEC.md](UI_UX_SPEC.md) §11 | 🔶 自动侧随 E2E 常绿, 上架前文案人工终审 |

## 3. 桌面 Windows / macOS

打包手册: [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md)
(Qt 商用壳, 含 LGPL 合规清单) 与
[../scripts/package_windows.md](../scripts/package_windows.md) (NSIS/WiX)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| D1 | 打包资产与手册完备 (CPack / WiX / starter 清单 / 第三方声明) | P0 | Auto (R9) | `platforms/windows/packaging/` + 两份打包手册 + CI `windows-release.yml` | ✅ 资产齐备 (探测存在性) |
| D2 | Windows 安装包在真实 runner 出包 (流水线转正) | P0 | Manual | `.github/workflows/windows-release.yml` (**草案, 尚未在真实 runner 上验证**, 见该文件头注) | ⬜ 草案待首跑 |
| D3 | Windows 实机验收 (干净 Win10/11, 未装 Qt/VS) | P0 | Manual | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §11 (自动冒烟 `smoke_qt_windows.ps1` + 人工验收单) | ⬜ 无 Windows 实机记录 |
| D4 | macOS 打包 (macdeployqt + DMG) + 签名公证 (Developer ID / notarytool) | P0 | Manual | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §5 macOS 小节 (公证步骤已写明) | ⬜ 仅手册, 无 macOS 实机记录 |
| D5 | 代码签名证书 (Windows Authenticode; 依赖运营主体 L5) | P0 | Manual | [../scripts/package_windows.md](../scripts/package_windows.md) 第十一节 (`signtool`, 未签名会被 SmartScreen 拦截) | ⬜ 证书未申请 |
| D6 | LGPL 合规逐项核对 (Qt 随包分发) | P0 | Manual | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §8 清单; `THIRD_PARTY_NOTICES.md` 已随包 | 🔶 清单与声明就绪, 出包时逐项打钩 |
| D7 | Linux 打包冒烟 (无 Win/mac 机器时的链路自证) | P1 | Auto (单独跑) | `scripts/smoke_qt_linux_pack.sh`; [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §9 | 🔶 脚本可跑, 未纳入常跑 CI (出包前手动执行) |
| D8 | 自动更新 (COMMERCIAL_PLAN §8 列为 V1 交付物) | P1 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §8 V1; [ROADMAP.md](ROADMAP.md) 阶段 3 | ⬜ 未实现 —— 上架前须决策: 实现, 或降级 V1.1 并在签核记录留痕 |

## 4. Android

构建与验收手册: [../platforms/android/README.md](../platforms/android/README.md)
(第一节 Gradle 构建 / 第二节纯 NDK / 第五节 CI / 第六节缺口)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| A1 | APK 构建 + 包内容校验 CI 常绿 (原生库 / 数据 / 缩略图) | P0 | Auto | `.github/workflows/android.yml` (assemble-debug + ndk-so 双 job) | ✅ CI 常跑 |
| A2 | JNI 符号与 NDK 交叉编译本地断言 | P0 | Auto (R4 内 E2E-14a) | `tools/run_e2e_smoke.sh` (符号清单解析自 `android.yml`, 口径自动同步) | ✅ 随 E2E 冒烟 |
| A3 | release 签名配置 (signingConfig + 密钥管理; 商店档产物) | P0 | Auto (R13: signingConfigs 块 + `keystore.properties.example` 齐备) | `platforms/android/app/build.gradle.kts` signingConfigs (从不入库的 `keystore.properties` 读取) + [../platforms/android/SIGNING.md](../platforms/android/SIGNING.md) (生成/出包/CI 口径) | 🔶 签名接线与模板/手册已落地 (缺配置时 release 报错指引, debug 不受影响); 真实 keystore 生成与商店档出包属人工 (随 A4/A5) |
| A4 | 真机验收 (arm64 API 26+; E2E-03/14/15 + 触屏手势 + 首启解包) | P0 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §1/§3; [../platforms/android/README.md](../platforms/android/README.md) 第一节走查 | ⬜ 无真机验收记录 |
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
| V2 | 隐私政策法务定稿 (运营主体全称 / 注册地址 / 备案号 / 生效日期) | P0 | Manual | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) 头部「状态: 草稿」标注; 依赖 L5 | ⬜ 未定稿 |
| V3 | 应用内数据管理入口 (家长中心查阅 / 导出 / 删除) | P0 | Auto(部分) | 数据隐私后端 (`progress/data_privacy` + Qt `privacy_backend`, 在制) | 🔶 在制, 未收口 |
| V4 | 上架前跑一遍安全与隐私自查单 (三平台逐项) | P0 | Manual | [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md) 合规检查清单 | ⬜ 待出包前执行并归档 |
| V5 | 离线承诺断网复核 (断网走安装启动与教程主链路) | P1 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) E2E-20 | ⬜ 随真机验收一并做 |

## 6. E2E 验收

路径矩阵与签核规则: [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) (§1 全部
20 条路径, §3 签核规则)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| E1 | 自动子集全绿: `tools/run_e2e_smoke.sh --strict` (Qt 与 Android 项不允许 SKIP) | P0 | Auto (R4) | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §2/§3 | 🔶 默认档常绿; `--strict` 需 Qt6 + NDK 环境齐备后作为签核动作执行 |
| E2 | 矩阵 P0 的 Manual / Auto(部分) 人工要点逐条打钩, 归档签核记录 (执行人/日期/设备) | P0 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §1 「人工要点」列 | ⬜ 待真机与实机验收时执行 |
| E3 | P1 路径已知问题留痕 (允许带问题上架但须记录) | P1 | Manual | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §3 第 3 条 | ⬜ 随 E2 一并归档 |

## 7. 发布门禁 (Release Gate)

门禁定义与时机: [TESTING.md](TESTING.md) 第 5 节; 一键入口
`tools/run_release_gate.sh`; CI 手动流水线 `.github/workflows/release-gate.yml`。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| G1 | 快检档常绿 (免费层对齐 + strict 全库巡检 + 待复核报告) | P0 | Auto (R5) | `tools/run_release_gate.sh` | ✅ 探测通过 (报告型 L3 项不阻断) |
| G2 | 出包终防线全绿: `tools/run_release_gate.sh --full --fail-on-pending` | P0 | Auto + 线下 | 同上; D4+ 实物复核清零是前置 (见 §8) | ⬜ 被 §8 实物复核卡住 (45 个待复核即红灯) |

## 8. 实物抽样复核

软件 strict 全绿**不豁免**实物复核 —— D4+ 逐个实搭是商用上架硬门槛。
规程: [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md);
抽样报告: [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| S1 | V1 优先抽样包 10 个实搭签核 (S2 旗舰 D5 + S3 大体量 D4, 预算约 12.5 小时) | P0 | Auto 报告 (R6) + Manual 实搭 | `tools/physical_sample_pack.py --fail-on-missing-sample` | ⬜ 0/10 已复核 |
| S2 | D4+ 全集清零 (45 个全部实物复核落盘 `physical_verified`) | P0 | Auto 报告 (R7) + Manual 实搭 | `tools/list_physical_pending.py --fail-on-pending`; 落盘口径见 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 5.2 | ⬜ 0/45 已复核 |
| S3 | 免费层 D3 抽检 30% (免费层无 D4+, 实物风险由抽检政策覆盖) | P1 | Manual | [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §4.3; [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md) §2 免费层说明 | 🔶 已有 3 个 D3 实物复核落盘 (`content_meta.physical_verified`, R6 报告一致性核对可见) |

## 9. 软著 / 备案 / 商店资质

国内商店上架前置项见 [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2 与
§6.3 末条; 逐项**办理动作**、负责方与串行关键路径见
[CHINA_STORE_COMPLIANCE.md](CHINA_STORE_COMPLIANCE.md) (本节是其
状态快照, 两处互为回链)。办理本身为线下法务/行政流程无自动化载体,
建议**最早启动** (周期不受工程进度控制); 该办理清单的章节/条目/
交叉引用完整性由 `tools/check_china_compliance_docs.py` 守卫
(探测 R15, 已接入 `tools/check_v1_readiness.sh`)。

| # | 待办 | 优先级 | 探测 | 载体 / 依据 | 状态 (2026-08-25) |
| --- | --- | --- | --- | --- | --- |
| L1 | 软件著作权登记 (国内安卓商店硬前置) | P0 (国内) | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2/§6.3 | ⬜ 未启动 |
| L2 | App 备案 (工信部 ICP; 隐私政策 §5 承诺境内合规云) | P0 (国内) | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §6.3; [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) §5 | ⬜ 未启动 |
| L3 | 开发者账号开通 (华为 / 应用宝 / Google Play / Microsoft Store; macOS 走 Developer ID 直分发亦需 Apple 开发者账号) | P0 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §5.2 商店策略 | ⬜ 未启动 |
| L4 | 运营主体信息定稿 (名称 / 地址 / 联系邮箱 → 隐私政策 V2 / 商店资料 A5 / 签名证书 D5 的共同前置) | P0 | Manual | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) §1/§10 占位符 | ⬜ 未定 |
| L5 | 商标注册与 IP 红线终审 (不用品牌词, 无侵权外观) | P1 | Manual | [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §6.1 (红线已文档化) | 🔶 红线自查已内建于内容管线, 注册未启动 |

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

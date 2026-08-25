# 用户交接单 —— 工程侧与用户侧最终分工 (USER HANDOFF)

> **读者**: 项目所有者 (你)。本单回答两个问题: **工程侧已经把哪些事做完、
> 做到什么程度** (§1~§3), 以及**哪些事只能由你完成、每件怎么做、做完后
> 工程怎么验收** (§4~§5)。
>
> **分支**: `cursor/magtile-studio-foundation-a95b`; 单一对账单仍是
> [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md), 本单不另立口径,
> 只做「工程 vs 你」的分工切面。
>
> **状态快照**: 2026-08-25 19:30 UTC 文档同步 —— 内容库扩容至
> **234 模型** (`3d24d74` 基线, 内容批 A~E 合计 209→234); L2 风险报告
> 与结构族包已刷新至 234 基线 (`50a3f4c`), strict 巡检 / 发布门禁 /
> 全量就绪三报告随并行刷新批复跑。自动探测最近一次 `--quick` 实跑为
> 17:20 UTC (209 模型时点)。
> 工作区多代理并行推进, 状态以 `tools/check_v1_readiness.sh` 实跑与
> 清单最新快照为准; 本单引用的 commit 均已推送 origin (并行工作区
> 偶有变基, 哈希漂移时按提交信息检索)。
>
> **L2 决议 (2026-08-25 16:03 用户指令)**: 实物验证工程 (L2) 全套
> 必做 —— 风险报告 + 蒙特卡洛抖动 + 结构族去重 + 文档/CI 接入,
> 效率可慢、质量优先。实物复核随之升级为**三层流程**, 你的人手
> 实搭量大幅缩减 (§4.3); **L2 批次 10 槽 + 接力批 4 模型加固均已交付** (§2)。

**快照时自动探测实跑** (`tools/check_v1_readiness.sh --quick`,
17:20 UTC / 209 模型时点; 扩容至 234 后 R1/R2 口径已按仓库快照核对 ——
JSON / 目录登记 / 缩略图 234 三方一致, 全量复跑随刷新批):

```
合计 24 项: 13 PASS / 2 FAIL / 9 SKIP (其中 P0 失败 2 项)
```

仅有的 2 项 FAIL 是 **R6/R7 实物复核** —— 唯一无法**完全**由软件代劳
的自动侧 P0 缺口, 但 L2 三层流程已把其中的人手量大幅缩减 (见 §4.3);
9 项 SKIP = 快检刻意跳过的 R4/R5/R17 三个长跑项 (全量档会实跑) +
M1~M6 六个纯人工提醒项 (即 §4 的你的清单, 不参与自动判定)。合计项
23 → 24 系 L2 批次新增 R17 扰动仿真抽检探测所致。

---

## 1. 工程侧已交付 (按 V1 清单章节, 附 commit 依据)

状态口径与 [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) 同源
(✅ 已就绪 / 🔶 部分就绪); 本节只列 ✅/🔶 行, ⬜ 行全部进 §4 你的清单。

### 1.1 §1 内容 (C1~C4 ✅, C5 🔶)

| 项 | 状态 | 交付物 | commit / 依据 |
| --- | --- | --- | --- |
| C1 模型库体量 | ✅ | **234 个模型 JSON** (探测门槛 200, 处于 200~250 目标区间) | 最近登记批 `3d24d74` (229→234; 内容批 A~E 合计 209→234); R1 实跑 PASS |
| C2 全库质量门禁 | ✅ | 全库 234 模型 strict 双档零未豁免警告 (并入批全库 QA 36 关卡全绿: test_all_models 234/234 + 唯一性 27261 对 0 警告; 唯一豁免 `suspension_bridge_01` 已文档化) | 并入批 `3d24d74`; 巡检深报告 [reports/STRICT_AUDIT_2026-08-25.md](reports/STRICT_AUDIT_2026-08-25.md) + 最新全库实跑留痕 [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md) (`5b915a0`/209 基线, 234 刷新批复跑中); R5 实跑 |
| C3 目录 + 缩略图 | ✅ | JSON / 目录登记 / 缩略图 234 三方对账一致 | `3d24d74`; R2 实跑 PASS |
| C4 免费层 30 对齐 | ✅ | 标签 = starter 清单, 全 core-9, 三条断言常绿 | [FREE_TIER_MANIFEST.md](FREE_TIER_MANIFEST.md); R3 实跑 PASS |
| C5 主题/难度终审 | 🔶 | 分布数据可一键输出 (`magtile_app library`), 人工终审留待上架前 | [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) §2 |

### 1.2 §2 付费闭环 (B1 ✅, B2/B5 🔶)

| 项 | 状态 | 交付物 | commit / 依据 |
| --- | --- | --- | --- |
| B1 假计费闭环 | ✅ | 计费适配层 + 三档商品 + 购买/恢复 + 统一解锁口径, 41 断言单测 | `f4bb5c7`; R10 PASS |
| B2 真实商店接线 | 🔶 | **Google Play**: Play Billing 6.x 购买/恢复/回执 + 启动静默恢复 (`a694a17`); **Windows 商店**: WinRT 全链 + MTA 线程模型 (`aa50909`); **Qt 订阅页商店档 UI**: 真实价格卡 + 恢复购买 + `simulatedBilling` 分流 (`aa50909`); **Android 订阅页 UI** (家长门后档位卡 + 恢复购买): `1333f8e` (drawable 先行 `9d9ad0a`) | R11 / R11W 实跑 PASS; 商品 id 三端统一 `sub_monthly`/`sub_yearly`/`sub_family_yearly` |
| B5 儿童零价格红线 | 🔶 | 家长门流随 E2E 常绿 + R16 文案守卫常态扫描 (快照时实跑: 260 文件 7751 段, 0 违规); 视觉/语气人工终审留待上架前 | 守卫 `654d775`/`61b514c`, 违规修复 `a128acd`/`5023313` |

### 1.3 §3 桌面 (D1/D7 ✅, D2/D6 🔶)

| 项 | 状态 | 交付物 | commit / 依据 |
| --- | --- | --- | --- |
| D1 打包资产 | ✅ | CPack/NSIS/WiX 资产 + 双打包手册 + `windows-release.yml` (已迁仓库根) | `9c92aee`; R9 PASS |
| D2 Windows CI 出包 | 🔶 | 首跑阻塞项已修 + Linux 可验子集全绿 + **触发/预期产物/排查/签核四件套指南** | `150a948` → [../scripts/package_windows.md](../scripts/package_windows.md) §8; 真实 runner 首跑见 §4.5 |
| D6 LGPL 合规 | 🔶 | 清单与 `THIRD_PARTY_NOTICES.md` 随包就绪 + 自动核对脚本已入库 (`2605e34`), 出包时逐项打钩 | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §8 |
| D7 Linux 打包冒烟 | ✅ | 三档 TGZ 清单断言 + NSIS 编译 + offscreen 启动 + ldd 核验, Ubuntu 实跑全绿 | 落档 [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §9 |

### 1.4 §4 Android (A1/A2 ✅, A3/A6/A7 🔶)

| 项 | 状态 | 交付物 | commit / 依据 |
| --- | --- | --- | --- |
| A1/A2 构建 CI + JNI 断言 | ✅ | `android.yml` 双 job 常跑 + 34 符号断言随 E2E | R4 内 E2E-14a |
| A3 release 签名 | 🔶 | signingConfigs 接线 + 模板 + 手册 (真实 keystore 属你, §4.6) | `2878ed0` → [../platforms/android/SIGNING.md](../platforms/android/SIGNING.md); R13 PASS |
| A6 starter 子集 | 🔶 | `-PmagtileAssets=starter` 构建选项落地, 出包前抽验 | [../platforms/android/README.md](../platforms/android/README.md) 第四节 |
| A7 体验缺口留痕 | 🔶 | MSAA/节电等缺口已文档化 (P1 允许带记录上架); 仪器测试骨架 M-01~M-05 已入库 | `9d9ad0a`; README 第六节 |

### 1.5 §5 隐私 (V1/V3/V4 🔶)

| 项 | 状态 | 交付物 | commit / 依据 |
| --- | --- | --- | --- |
| V1 隐私政策草稿 | 🔶 | 家长一页纸 + 正文十节 (定稿等 L4 字段, §4.2) | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md); R8 PASS |
| V3 数据管理入口 | 🔶 | Qt + Android 双端「查阅/导出/删除」同一核心实现同一导出契约 | `35042c9` + `20bb90d` |
| V4 自查单载体 | 🔶 | 三平台逐项签核单空白模板 (六组 × 三平台 + 放行判定) | `2750313` → [reports/PRIVACY_SECURITY_SIGNOFF.md](reports/PRIVACY_SECURITY_SIGNOFF.md) |

### 1.6 §6/§7 E2E 与发布门禁 (E1/G1 ✅)

| 项 | 状态 | 交付物 | commit / 依据 |
| --- | --- | --- | --- |
| E1 自动子集 strict 全绿 | ✅ | `run_e2e_smoke.sh --strict` 9 项 0 SKIP + **每次 push CI 常态复跑** (`qa.yml` e2e-strict job) | CI 固化 `15f4e03`; 按钮级路径冒烟 `26032b0` |
| G1 门禁快检常绿 | ✅ | `run_release_gate.sh` 快检档 PASS + 全量档 QA+L2 全绿 (仅 L3 实物硬闸门红 —— G2 被实物复核卡住, 见 §4.3) | R5 实跑; 留痕 [reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md) |
| 整机 QA 报告 | ✅ | Qt 桌面儿童视角全路径实玩 (`86e0b5f`, P1-1 已修 `b16e85e`) + Android 全量静态审查 (`b3c1685`) | [reports/QA_QT_CHILD_PLAYTHROUGH.md](reports/QA_QT_CHILD_PLAYTHROUGH.md) / [reports/QA_ANDROID_CHILD_PLAYTHROUGH.md](reports/QA_ANDROID_CHILD_PLAYTHROUGH.md) |

### 1.7 §8/§9 给你铺路的执行文档 (全部新增)

| 交付物 | 服务哪项 | commit |
| --- | --- | --- |
| [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md) 实物复核上手指南 (备料/工时/打印/落盘/照片) | R6/R7 | `418473d` |
| [reports/PHYSICAL_SIGNOFF_WORKSHEET.md](reports/PHYSICAL_SIGNOFF_WORKSHEET.md) 可打印逐模型工作单 | R6/R7 | 随抽样工具生成 |
| [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) Google Play 沙盒验收分步 | B3 | `5ea1a1b` |
| [WINDOWS_STORE_BILLING_SANDBOX_QA.md](WINDOWS_STORE_BILLING_SANDBOX_QA.md) 微软商店验收分步 (无沙盒, 真钱口径) | B3 | `721a594` |
| [reports/MACOS_ACCEPTANCE_CHECKLIST.md](reports/MACOS_ACCEPTANCE_CHECKLIST.md) macOS 36 项可打印验收单 | D4 | `06e5e9f` |
| [../scripts/package_windows.md](../scripts/package_windows.md) §8 Windows CI 触发与首跑签核指南 | D2 | `150a948` |
| [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) 行政办理执行手册 (去哪办/带什么/什么顺序/等多久) | L1~L5 | `be708d3` |
| [reports/PRIVACY_SECURITY_SIGNOFF.md](reports/PRIVACY_SECURITY_SIGNOFF.md) 三平台隐私安全签核单 | V4 | `2750313` |
| 清单状态列对齐实跑快照 | 全局 | `e5be8d7` |

---

## 2. 工程侧交付快照 (2026-08-25 17:40 UTC: L2 批次 10/10 + 接力批 4/4 全部入库)

16:03 用户决议派发的 **L2 实物验证工程批次已 10/10 全部入库** (三层
流程定义见 §4.3 与 [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §8):

| 槽 | 任务 (L2 批次) | 服务清单项 | 落地状态 |
| --- | --- | --- | --- |
| 1 | `tools/physical_risk_report.py` 全库风险评分 + 「建议人手验 Top 15」(JSON/Markdown 报告) | §8 S0/S1 | **已交付** `41bda4c` (209 模型 3.6s 全扫; 公共入口 `risk_score()` 增补 `6dff7cb`) |
| 2 | `magtile_app validate --jitter N` 蒙特卡洛容差抖动 (C++, ±1.5mm/±2° 逐步扰动, 失败记 F08 类) | §8 S0 | **已交付** `8b424be` (规则号 R9, issue code `placement_jitter_failure`; 全库首巡 208/209 全绿) |
| 3 | `tools/physical_family_pack.py` 结构族聚类 (每族一个代表实搭, 削减重复) | §8 S1/S2 | **已交付** `b093b6d` (交付时 209 模型 → 154 结构族; 与风险分探测链会师 `6dff7cb`); **234 基线刷新** `50a3f4c` (174 族, 多成员 48) |
| 4 | [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) §2 触发条件自动标记代码化 (L1 Warning / 高墙链 / 临界重心 / 弱磁承重) | §8 S0 | **已交付** —— 五条触发条件代码化随槽 1 落地 (`41bda4c`), 验证文档 L2 层「规划 → 已实现」口径收口 `bca88fd` |
| 5 | `run_strict_audit.sh` / `run_release_gate.sh` 门禁接入 | §7 G1/G2 | **已交付** `6acfa54` (挂钩) + `607c0cb` (strict 档 D4+ 首巡结果登记) |
| 6 | jitter 测试夹具 + risk report 单测 (ctest 注册) | §8 S0 | **已交付** `262ebc3` (全量 ctest 472/472 绿, R9 夹具进注册表必备清单) |
| 7 | `tools/physical_failure_registry.py` 实物失败登记与校准工作流 | §8 S4 | **已交付** `08d3018` (失效账本工具 + 四步闭环手册 [PHYSICAL_CALIBRATION_WORKFLOW.md](PHYSICAL_CALIBRATION_WORKFLOW.md)) |
| 8 | `check_v1_readiness.sh` 新增 R17 L2 探测 | §0 | **已交付** `13e6cd9` (探测合计项 23 → 24; `--quick` 记 SKIP, 全量签核必跑) |
| 9 | V1 清单 §8 + 本交接单 L2 流程更新 | 本单 | **已交付** `df902b9` (本次快照刷新即其收尾编辑) |
| 10 | Android B2 订阅页提交收口 | B2 | **已交付** (代码 `1333f8e` + 文档 `5eb27a9`) |

**L2 完成定义达成情况**: risk report 可输出「建议人手验 Top 15」✅;
结构族报告交付时 209 → 154 族 ✅ —— **234 基线刷新** (`50a3f4c`,
[reports/PHYSICAL_RISK_REPORT.md](reports/PHYSICAL_RISK_REPORT.md) +
[reports/PHYSICAL_FAMILY_PACK.md](reports/PHYSICAL_FAMILY_PACK.md)):
234 → 174 族 (多成员 48), 族去重后必搭 35 个 / 可缓建 10 个 (省 22%);
D4+ 默认 `--jitter 50` 全绿 ✅ (`run_strict_audit.sh --jitter-only
--jitter require` 45/45, 基线 `5b915a0`; 扩容至 234 后 D4+ 全集仍为 45,
新增批全部 D2/D3 且逐个 `--jitter 50` 全绿入库)。

**接力批 (已交付): 抖动首巡揪出的 4 个边缘模型内容侧加固** ——
全部入库并复验 50/50 全绿 (`lego_style_house_01` `24fd0ec` 步骤重排;
`ball_run_tower_01` `8d07fe5`/`5b915a0` 门式立柱; `marble_run_spiral_01`
`114c154` 转角斜撑; `rainforest_canopy_01` `2ffc06e` 板根斜撑)。
处置记录 [PHYSICS_RULES.md](PHYSICS_RULES.md) R9 节; 门禁留痕
[reports/RELEASE_GATE_STATUS.md](reports/RELEASE_GATE_STATUS.md)
(QA + L2 全绿, 仅 L3 实物硬闸门红)。

**工程收口标准**: `check_v1_readiness.sh --quick` 只剩 R6/R7 FAIL ——
**当前已达成** (24 项: 13 PASS / 2 FAIL / 9 SKIP); L2 工具链 + 内容加固
全部入库 ✅; `run_release_gate.sh --full --l2` QA+L2 全绿 ✅;
剩余工程侧: 清单 §8 S1/S2 实物复核 (用户侧) + 可选内容扩至 250。

---

## 3. 工程侧下一波可继续做 (不依赖你的资源)

1. **B2 收尾**: 双端订阅页回归复跑 + 清单 B2 状态收敛 (Android 订阅页 UI 已入库 `1333f8e`);
2. **D6 收尾**: 把 LGPL 自动核对脚本 (`2605e34`) 纳入出包流程与手册勾选项;
3. **内容 234 → 250**: 继续按主题池补批; 并输出主题/难度分布报表, 给 C5 人工终审当底稿;
4. **D8 自动更新决策文档**: COMMERCIAL_PLAN §8 列为 V1 交付物但未实现 —— 工程可先出「实现 vs 降级 V1.1」决策文档与最小方案, 决策本身留你签字;
5. **B4 首批一次性内容包**: 内容与打包侧可先做 (P1, 商店后台配置属你);
6. **A7 体验缺口**: Android 视口 MSAA、按需渲染节电等 (P1, 已留痕);
7. **Android 仪器测试 M-01~M-05 实装**: 骨架已入库 (`9d9ad0a`), 用例填充可继续;
8. **商店素材底稿**: 按 [STORE_LISTING.md](STORE_LISTING.md) 规格出桌面/模拟器截图草稿 (**终稿须真机截图**, 归你 §4.6);
9. **D2 试跑标签**: 真实 runner 首跑也可由工程打 `v*` 试跑标签触发 ([../scripts/package_windows.md](../scripts/package_windows.md) §8.1); 你若想自己控制发版节奏, 按 §4.5 执行即可。

---

## 4. 必须由你完成 (工程无法代劳的全部事项)

四要素口径: **做什么 / 准备什么 / 指向文档 / 预估工时**。「动手工时」
指你 (或你请的人) 实际投入; 机构审查等待另列「外部周期」, 可全程并行。
探测编号对照: 实物 = R6/R7 (提醒项 M5; L2 虚拟验证层 = R17);
行政 = L1~L5 (提醒项 M6); 实机/真机 = M1/M2; 法务 = M3; 签核 = M4;
真钱验收 = B3; 证书 = D5。

### 4.1 第 0 步: 运营主体定稿 (L4, 阻塞全部行政与法务)

| 做什么 | 准备什么 | 文档 | 预估工时 |
| --- | --- | --- | --- |
| 定稿 7 字段 (公司全称/注册地址/法人与备案负责人/对公账户/官网域名/企业邮箱/儿童个人信息保护专员), 落《定稿单》归档, 注册域名 + 开 `support@`/`security@` 邮箱, 回填 [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) 与 [STORE_LISTING.md](STORE_LISTING.md) 占位 | 营业执照 (无公司先设立, 经营范围覆盖软件开发/销售) + 对公银行账户 | [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §1 | **0.5~1 个工作日** (公司设立另计) |

主体一经办理不可轻易变更 (软著/备案/商店账号/签名证书五处必须同一
主体), 所以它是第 0 步、此后冻结。

### 4.2 行政批 (L1/L2/L3/L5 + 证书 D5, 主体定稿当周并行启动)

| # | 做什么 | 准备什么 | 文档 | 动手工时 | 外部周期 |
| --- | --- | --- | --- | --- | --- |
| L1 软著登记 | CPCC 官网企业实名 → 在线申请表 → 上传鉴别材料 → 跟踪补正 | 源程序前后 30 页 (排除 `third_party/`) + 操作手册 60 页 + 营业执照扫描件 | [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §2 | 4~8 小时备料提交 | **30~40 工作日 (全清单关键路径, 最先启动)** |
| L2 App + 网站备案 | 云平台主体备案 → App 备案 (包名 + 签名特征) + 网站备案; 30 日内补公安备案 | 域名 (实名=主体) + 境内云服务器 + **release 签名包** (A3, §4.6 先做) + 负责人手机盯核验 | [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §3 | 2~4 小时 (分两次) | 初审 1~2 工作日 + 管局最长约 20 工作日 |
| L3 开发者账号 | 华为/应用宝 (国内优先) + Google Play (先办邓白氏) + Microsoft Partner Center + Apple Developer; 全部用公司主体实名 | 对公账户盯打款验证; Google $25 一次性 + 国际信用卡; MS 约 US$99 一次性; Apple US$99/年 | [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §4 | 每家 1~2 小时, 合计约 1 个工作日 | 华为最快 30 分钟; **邓白氏最长约 30 天** (与软著同批启动) |
| L5 商标 (P1) | 「MagTile Studio」近似检索 + 中国 9/28/41 类 + 美国同步提交 (可代理) | 定稿名称与图形 | [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §5 | 2~4 小时 | 以年计, **不阻塞 V1** |
| D5 代码签名证书 | 以公司主体向 CA 申请 Windows Authenticode (OV/EV); macOS 签名用 Apple Developer ID (含在 L3 Apple 账号内) | 营业执照 + 邓白氏/电话核验材料 (CA 要求) | [../scripts/package_windows.md](../scripts/package_windows.md) 第十一节 | 1~2 小时申请 | CA 验证数天 (未签名会被 SmartScreen 拦截) |

### 4.3 实物复核 (R6/R7, **随时可开工, 不依赖行政**; L2 三层流程已大幅缩减人手量)

**新口径 (2026-08-25 L2 决议)**: 你**不必把全库 234 个模型全搭一遍,
也不再逐个搭完 45 个 D4+ 全集**。实物验证升级为三层流程 (对账口径
[V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §8): 第一层软件全绿
(strict 双档, 既有) 与第二层虚拟物理验证 (`magtile_app validate
--jitter N` 蒙特卡洛抖动 + 全库风险评分 + 自动标记, 探测 R17) 全部由
软件自动跑; 你只需人手实搭第三层**缩减集 = risk Top 15 + 结构族代表**
(并集去重, 清单由工具实跑输出钉死, 不靠拍脑袋):

```bash
python3 tools/physical_risk_report.py    # 全库风险评分排序 + 「建议人手验 Top 15」(JSON/Markdown)
python3 tools/physical_family_pack.py    # 结构族聚类: 每族一个代表, 同族其余由代表结论覆盖
```

(两工具与 `--jitter` 均为 L2 批次交付物, **已全部入库** —— 逐槽
哈希见 §2; 具体旗标以各自 `--help` 为准。)

| # | 做什么 | 准备什么 | 文档 | 预估工时 |
| --- | --- | --- | --- | --- |
| R6 首批: 抽样包 10 个实搭签核 (预计与 risk Top 15 高度重合, 结果兼作第二层首轮校准数据) | 逐模型: strict (+ `--jitter`) 预检 → 只看教程实搭 → 敲击/提起/拆解重搭 → 拍照 → 通过则落盘 `physical_verified` 三字段; 失败按失效编码经 `tools/physical_failure_registry.py` 登记 (回灌负例夹具) | 官方基准品牌磁力片按**单模型最大需求**备料 (最多 122 片; 颜色瓶颈: 灰方 65 / 蓝方 43 / 橙方 34); 平整硬桌面 + 秒表 + 录像 + 打印工作单 | [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md) + [reports/PHYSICAL_SIGNOFF_WORKSHEET.md](reports/PHYSICAL_SIGNOFF_WORKSHEET.md) + 规程 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md) | **约 12.5 小时** (D5 旗舰 120 分钟单独一场 + 9×D4 各 70 分钟) |
| R7 缩减集清零: risk Top 15 + 结构族代表 (扣除与抽样包重合部分) | 同上; **非代表模型不用搭** —— 由「同族代表实搭通过 + 第二层 jitter 全绿」覆盖; 可多人按模型切分 (每模型一人走完全程) | 同上 | 同上 §1/§6 | **以两份报告实跑清单为准 (已刷新至 234 基线 `50a3f4c`): 族去重后必搭 35 个 ≈ 2500 分钟 (约 41.7 小时), 可缓建 10 个 ≈ 700 分钟 (约 11.7 小时, 省 22%)** (原全集口径 45 个 ≈ 53 小时; 缓建采纳与否是策展/QA 政策决定, 见 [reports/PHYSICAL_FAMILY_PACK.md](reports/PHYSICAL_FAMILY_PACK.md)) |

红线: 缩减是「搭哪些」的缩减, 不是「怎么搭」的放松 —— 缩减集内
**未实搭严禁标记通过**, 固定动作 (敲击/提起/拆解重搭) 与落盘纪律不变;
模型结构改动后旧结论作废 (三字段一并清除), 同族代表结论一并复验;
实搭失败的模型整改后从规程第 0 节重走, 同族全员重新覆盖。

### 4.4 法务批 (M3: 隐私政策定稿 V2, 依赖 L4)

| 做什么 | 准备什么 | 文档 | 预估工时 |
| --- | --- | --- | --- |
| 隐私政策法务过稿定稿 (主体全称/地址/备案号/生效日期落款) + 《儿童个人信息保护声明》独立成文 + 网页版发布到 `/privacy` 与 `/children-privacy` (托管在已备案域名) | L4 定稿单 + 法务顾问 + 已备案官网 (L2 事项 B) | [PRIVACY_POLICY_DRAFT.md](PRIVACY_POLICY_DRAFT.md) 头部「法务定稿项」 + [ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §1.3 | 0.5~1 个工作日协调 (律师工时另计) |

### 4.5 桌面实机批 (M1: D2 确认 / D3 / D4)

| # | 做什么 | 准备什么 | 文档 | 预估工时 |
| --- | --- | --- | --- | --- |
| D2 Windows CI 首跑 | 触发 `windows-release` (dispatch 或 `v*` 试跑标签), full/starter 两场全绿后按 §8.4 登记、§8.5 翻 ✅ | GitHub 仓库操作权限 | [../scripts/package_windows.md](../scripts/package_windows.md) §8 | 1 小时 + CI 等待 (约 1 小时/场) |
| D3 Windows 干净机验收 | 干净 Win10/11 (未装 Qt/VS) 装包 → `smoke_qt_windows.ps1` 自动冒烟 + 人工验收单 | 实机或干净虚拟机; 正式档需 D5 证书 (内测可先 ad-hoc) | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §11 | 2~4 小时 |
| D4 macOS 打包 + 公证 + 验收 | macdeployqt + DMG → Developer ID 签名 → notarytool 公证 → stapler 装订 → 36 项验收单 (P0 32 项全过签核) | Mac 实机 + Apple Developer 付费账号 (L3) | [../scripts/package_qt_desktop.md](../scripts/package_qt_desktop.md) §5/§12 + [reports/MACOS_ACCEPTANCE_CHECKLIST.md](reports/MACOS_ACCEPTANCE_CHECKLIST.md) | 0.5~1 个工作日 |

### 4.6 Android 真机批 (M2: A3 keystore / A4 / A5)

| # | 做什么 | 准备什么 | 文档 | 预估工时 |
| --- | --- | --- | --- | --- |
| A3 正式 keystore | 生成 release keystore (**从不入库**, 丢失即无法更新应用) → 出一版 release 包 → 导出签名特征给 L2 备案 | 密钥口令入密码库, 至少两人可恢复 | [../platforms/android/SIGNING.md](../platforms/android/SIGNING.md) | 1 小时 |
| A4 真机验收 | arm64 API 26+ 真机走 E2E-03/14/15 + 触屏手势 + 首启解包 + 断网复核 (V5 顺带) | 真机 1~2 台 (建议一台低端机) | [../platforms/android/README.md](../platforms/android/README.md) 第一节 + [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §1/§3 | 半天 |
| A5 商店上架资料 | 图标/真机截图/儿童类目分级问卷/各商店后台填报 (国内商店等 L1/L2 取证后提审) | A4 的真机 (截图必须真实界面不得合成) + 软著证书 + 备案号 + 隐私 URL | [STORE_LISTING.md](STORE_LISTING.md) + [CHINA_STORE_COMPLIANCE.md](CHINA_STORE_COMPLIANCE.md) §8 | 1~2 个工作日 |

### 4.7 真钱/沙盒付费验收 (B3, 依赖 L3 账号 + B2 收尾)

| 平台 | 做什么 | 准备什么 | 文档 | 预估工时 |
| --- | --- | --- | --- | --- |
| Google Play | Play Console 配三档订阅商品 (id 与代码**逐字符一致**) → 内部测试轨上传 release AAB → 许可测试账号跑 购买/恢复/断网宽限期 三组勾选清单 | L3 Google 账号 + A3 keystore + 真机 (经测试轨安装, 不可侧载); 测试卡不真扣费, 沙盒时间压缩 (月续 5 分钟) | [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) | 2~4 小时 (不含商店审核等待) |
| Microsoft Store | Partner Center 配订阅附加内容 (**注意不可逆项**: 周期发布后不可改、价格只降不升) → MSIX 商店包测试安装 → 同构三组勾选清单 | L3 微软账号 (订阅附加内容需微软侧开通权限) + MSIX 商店包 (工程侧配合出包); **微软商店无沙盒** —— 用月度档实购 + 立即取消控成本 (预算约一个月订阅费) | [WINDOWS_STORE_BILLING_SANDBOX_QA.md](WINDOWS_STORE_BILLING_SANDBOX_QA.md) | 2~4 小时 |

### 4.8 签核归档 (M4 + V4, 随 §4.5/§4.6 同批做)

| 做什么 | 文档 | 预估工时 |
| --- | --- | --- |
| E2E 矩阵 P0 行「人工要点」逐条打钩, 归档执行人/日期/设备 | [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) §1/§3 | 随批执行 + 1~2 小时归档 |
| 三平台隐私安全自查单对**候选出包产物**逐项签核 | [reports/PRIVACY_SECURITY_SIGNOFF.md](reports/PRIVACY_SECURITY_SIGNOFF.md) | 每平台 1~2 小时 |
| V1 清单全部 Manual 行回填状态 + 签核记录 | [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §10 | 1 小时 |

**工时汇总** (单人动手, 可多人并行压缩): 实物缩减集必搭 35 个
≈ 41.7 小时 (234 基线族包实跑 `50a3f4c`; 可缓建 10 个再省约 11.7
小时; 原全集口径 45 个 ≈ 53 小时) + 实机/真机/签核约 3~4 个工作日 +
行政动手约 2~3 个工作日 + 付费验收约 1 个工作日 + 法务协调约 1 个
工作日 ≈ **12~14 个工作日量级** (缓建全部采纳则 ≈ 11~13; 原全集口径
≈ 15); 外部等待关键路径 = 软著 30~40 个工作日, 与全部动手项并行。

---

## 5. 你完成后, 工程如何验收

每完成一批, 在仓库跑对应命令; 预期输出对不上就把输出发回工程侧排查。

### 5.1 实物复核落盘后 (§4.3)

开工前先用 L2 报告拿实搭清单, 完成后跑验收:

```bash
python3 tools/physical_risk_report.py
# 开工前: 输出全库风险评分排序与「建议人手验 Top 15」(JSON/Markdown)
python3 tools/physical_family_pack.py
# 开工前: 输出结构族与每族代表清单 (与 Top 15 取并集 = 你的实搭范围)
python3 tools/physical_sample_pack.py --fail-on-missing-sample
# 预期: 抽样包 10/10 已复核, 退出码 0
python3 tools/list_physical_pending.py data/models --fail-on-pending
# 预期: 待复核清单为空, 退出码 0 (覆盖口径 = 缩减集实搭 + 同族代表
# 结论 + 第二层全绿, 随 L2 门禁接入落地, 以工具实跑输出为准)
tools/check_v1_readiness.sh --quick
# 预期: R6/R7 与 L2 探测 R17 全部 PASS, 摘要零 FAIL, 退出码 0
tools/run_release_gate.sh --full --fail-on-pending
# 预期: 全绿 —— G2 出包终防线解锁
```

实搭中任何失败: 按失效编码经 `tools/physical_failure_registry.py`
登记 (照片 + 模型 id + 步骤号; 四步闭环见
[PHYSICAL_CALIBRATION_WORKFLOW.md](PHYSICAL_CALIBRATION_WORKFLOW.md)),
工程侧据此整改并回灌第二层负例夹具 (§4.3 红线: 整改后同族全员重新覆盖)。

### 5.2 Android keystore 就位后 (§4.6 A3)

```bash
cd platforms/android && ./gradlew bundleRelease
# 预期: BUILD SUCCESSFUL, 产物 app/build/outputs/bundle/release/*.aab
# (缺 keystore.properties 时构建报错并指引, 属预期防呆)
```

签名特征 (公钥/MD5) 按 [../platforms/android/SIGNING.md](../platforms/android/SIGNING.md)
导出, 交 L2 备案表单。

### 5.3 Windows CI 首跑后 (§4.5 D2)

```bash
gh run list --workflow windows-release.yml --limit 3
# 预期: full 与 starter 两场 conclusion=success;
# Artifacts 含 安装包 .exe + 便携 .zip 双产物 (下载后 sha256sum 核验)
```

随后按 [../scripts/package_windows.md](../scripts/package_windows.md)
§8.4 登记签核、§8.5 一次性翻状态 (D2 → ✅)。

### 5.4 macOS 公证后 (§4.5 D4)

```bash
xcrun notarytool history ...   # 预期: status Accepted
xcrun stapler validate MagTileStudio.dmg   # 预期: The validate action worked!
spctl --assess --type execute "MagTile Studio.app"   # 预期: accepted, Developer ID
```

外加 [reports/MACOS_ACCEPTANCE_CHECKLIST.md](reports/MACOS_ACCEPTANCE_CHECKLIST.md)
P0 32 项全过并回填其 §9 签核栏。

### 5.5 付费验收后 (§4.7 B3)

两份沙盒验收文档的 A (购买) / B (恢复) / C (断网宽限期) 三组勾选清单
全过并回填文内验收登记表; 桌边核验契约键 —— 家长中心导出 JSON, 确认
`subscription_active` 与商店侧订阅状态一致 (购买后 true / 退款收回后
false, 「宁可锁」口径)。

### 5.6 行政取证后 (§4.2)

- 证书/备案号/账号 ID 登记 [CHINA_STORE_COMPLIANCE.md](CHINA_STORE_COMPLIANCE.md)
  §9 总控清单; 勾掉对应 checkbox;
- 回填 [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §9 状态列
  (随手更新快照日期, 其 §10 维护约定);
- 备案取号后**通知工程侧**: 「应用内展示备案号」是取号后的工程项
  ([ADMIN_LAUNCH_CHECKLIST.md](ADMIN_LAUNCH_CHECKLIST.md) §3.4), 工程落
  「家长中心 → 关于」页后你复核;
- `tools/check_v1_readiness.sh --quick` 保持全绿 (R14/R15 文档守卫)。

### 5.7 最终放行 (全部完成后)

```bash
tools/check_v1_readiness.sh --strict
# 预期: 退出码 0 —— R1~R16 (含 R11W) 全 PASS;
# M1~M6 恒 SKIP (人工提醒项, 以你的签核记录为准, 不参与自动判定)
tools/run_e2e_smoke.sh --strict
# 预期: 9 项全 PASS, 0 SKIP
tools/run_release_gate.sh --full --fail-on-pending
# 预期: 全绿
```

人工侧同时满足 [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §10
放行规则: 全部 P0 行 ✅ + Manual 项附签核记录 (执行人/日期/设备或单据
编号); P1 未完成项逐条留痕。三道命令 + 清单人工侧全过 = **可提交商店审核**。

---

## 6. 一句话分工

| 谁 | 负责什么 |
| --- | --- |
| **工程 (Agent)** | 代码、内容、测试、CI、打包脚本、全部执行文档脚手架、L2 虚拟物理验证工具链 (jitter / 风险报告 / 结构族 / 失败登记); 自动探测除 R6/R7 外全绿并保持 |
| **你** | 磁力片实搭**缩减集** (risk Top 15 + 结构族代表, R6/R7 —— 不必 234 全搭)、运营主体与行政五件 (L1~L5)、证书 (D5)、实机真机验收 (M1/M2/M4)、法务定稿 (M3)、真钱付费验收 (B3)、商店素材终稿与提审 |

工程侧收口后, 你手上是**一套按步骤可执行、可验收的清单**, 每一项都有
对应文档、命令与预期输出 —— 而不是一堆半成品代码。

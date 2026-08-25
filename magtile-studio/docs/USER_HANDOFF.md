# MagTile Studio — 用户交接单 (USER HANDOFF)

> **工程侧目标**：把能自动验证的全部做到绿，只把**必须你本人到场/到场决策/花真钱/办行政**的事项留给你。
>
> **分支**：`cursor/magtile-studio-foundation-a95b`  
> **对账单**：[`V1_LAUNCH_CHECKLIST.md`](V1_LAUNCH_CHECKLIST.md) + `tools/check_v1_readiness.sh`

---

## 1. 工程侧已交付（你现在就有的）

| 领域 | 状态 | 依据 |
| --- | --- | --- |
| 内容库 209 模型 + 免费层 30 | ✅ | R1–R3 PASS |
| Qt 桌面完整儿童向 UI + QA 报告 | ✅ | `QA_QT_CHILD_PLAYTHROUGH.md` |
| Android 外壳 + GLES 3D 教程 | ✅ | `assembleDebug` 绿、CI `android.yml` |
| 双端计费接线（假计费 + Play + Win Store） | ✅ | R10/R11/R11W PASS |
| E2E strict 9/9 + CI 每次 push 阻断 | ✅ | `e2e-strict` job |
| 儿童文案守卫 R16 | ✅ | 全库扫描 0 违规 |
| 隐私双端导出/删除（Qt + Android） | ✅ | V3 🔶→工程就位 |
| 打包手册 + Linux 冒烟全绿 | ✅ | D7 ✅ |
| Win release 触发指南 | ✅ | `package_windows.md` §8 |
| Play / Win 沙盒验收分步文档 | ✅ | `PLAY_BILLING_SANDBOX_QA.md` / `WINDOWS_STORE_BILLING_SANDBOX_QA.md` |
| 实物签核工作单 + 用户准备指南 | ✅ | `PHYSICAL_SIGNOFF_WORKSHEET.md` / `PHYSICAL_REVIEW_USER_GUIDE.md` |
| 行政办理手册 | ✅ | `ADMIN_LAUNCH_CHECKLIST.md` |
| macOS / 隐私安全签核模板 | ✅ | `MACOS_ACCEPTANCE_CHECKLIST.md` / `PRIVACY_SECURITY_SIGNOFF.md` |

**自动探测当前**：`13 PASS / 2 FAIL / 8 SKIP` —— 唯一工程无法消除的 FAIL 是 **R6/R7 实物复核**。

---

## 2. 工程侧正在收口（子代理 10 槽满负荷）

- Android 订阅页 UI（B2）—— `SubscriptionActivity` 已实现，`assembleDebug` 绿，待提交
- Qt 订阅页商店档 UI（B2）—— 部分已推送
- D6 LGPL 出包自动核对、Android 仪器测试扩展、商店素材规格单等

**工程完美收口标准**：readiness 只剩 R6/R7 FAIL；B2 双端 UI ✅；清单工程项无 ⬜。

---

## 3. 必须由你完成（按推荐顺序）

### 第 0 步：定运营主体（阻塞一切行政与法务）

| 做什么 | 准备什么 | 文档 | 工时 |
| --- | --- | --- | --- |
| 确定公司全称、注册地址、联系邮箱 | 营业执照或个体户信息 | [`ADMIN_LAUNCH_CHECKLIST.md`](ADMIN_LAUNCH_CHECKLIST.md) §1 | 1–3 天决策 |

→ 定稿后填入 `PRIVACY_POLICY_DRAFT.md` → 隐私政策 V2。

---

### 第 1 批：可并行启动（行政 + 账号）

| # | 做什么 | 准备什么 | 文档 | 外部周期 |
| --- | --- | --- | --- | --- |
| L1 | 软件著作权登记 | 源代码前后 30 页、说明书、营业执照 | ADMIN §2 | ~30–40 工作日 |
| L2 | ICP 备案 | 域名、云服务器、主体证件 | ADMIN §3 | ~20 工作日 |
| L3 | 开发者账号 | 对公账户、邓白氏（Google） | ADMIN §4 | 华为快；Google 邓白氏最长 ~30 天 |
| D5 | 代码签名证书 | 运营主体、Authenticode 购买 | `package_windows.md` §11 | 数天 |

---

### 第 2 批：实物复核（工程最大硬门槛）

| 做什么 | 准备什么 | 文档 | 工时 |
| --- | --- | --- | --- |
| 抽样 10 个模型实搭签核 | 磁力片按最大需求备料（最多 122 片/场）；打印工作单 | [`PHYSICAL_REVIEW_USER_GUIDE.md`](reports/PHYSICAL_REVIEW_USER_GUIDE.md) + [`PHYSICAL_SIGNOFF_WORKSHEET.md`](reports/PHYSICAL_SIGNOFF_WORKSHEET.md) | **~12.5 小时** |
| D4+ 全集 45 个清零 | 同上，可多人按模型切分 | 同上 §1.2 | **~53 小时** |

落盘后运行：

```bash
tools/list_physical_pending.py --fail-on-pending   # 期望：待复核 0
tools/check_v1_readiness.sh --quick                  # 期望：R6/R7 PASS
tools/run_release_gate.sh --full --fail-on-pending   # 期望：全绿
```

---

### 第 3 批：真机 / 实机 / 真钱验收

| # | 做什么 | 设备/账号 | 文档 | 工时 |
| --- | --- | --- | --- | --- |
| A4 | Android 真机走查 | arm64 API 26+ 手机 | `platforms/android/README.md` + `QA_ANDROID_DEVICE_CHECKLIST` | 半天 |
| D3 | Windows 干净机验收 | Win10/11 未装 Qt/VS | `package_qt_desktop.md` §11 | 2–3 小时 |
| D4 | macOS 打包 + 公证 | Mac + Apple Developer ID | `MACOS_ACCEPTANCE_CHECKLIST.md` | 半天 |
| B3 | 沙盒/商店真钱购买验收 | Play 内部测试轨 / Partner Center MSIX | `PLAY_BILLING_SANDBOX_QA.md` / `WINDOWS_STORE_BILLING_SANDBOX_QA.md` | 各 2–4 小时 |
| D2 | Windows CI 真实 runner 出包 | 推 `v*` 标签或合入 main 后 dispatch | `package_windows.md` §8 | 1 小时触发 + 等待 CI |
| A5 | 商店截图/图标/分级问卷 | 真机截图素材 | `STORE_LISTING.md` + `STORE_ASSETS_SPEC.md`（生成中） | 1–2 天 |

---

### 第 4 批：签核归档

| 做什么 | 文档 |
| --- | --- |
| E2E 人工要点打钩 | `E2E_TEST_MATRIX.md` §1 + §3 |
| 隐私安全三平台自查 | `PRIVACY_SECURITY_SIGNOFF.md` |
| V1 清单 P0 全 ✅ 签核 | `V1_LAUNCH_CHECKLIST.md` |

---

## 4. 你怎么判断「可以上架了」

全部满足才可提交商店审核：

```bash
cd magtile-studio
tools/check_v1_readiness.sh              # 0 项 P0 FAIL（含 R6/R7）
tools/run_e2e_smoke.sh --strict          # 9/9 PASS
tools/run_release_gate.sh --full --fail-on-pending
```

外加：`V1_LAUNCH_CHECKLIST.md` 全部 P0 行 ✅ 或签核记录豁免；B3 真钱链路走通；L1/L2（国内）或 L3（海外）账号就绪。

---

## 5. 一句话分工

| 谁 | 负责什么 |
| --- | --- |
| **工程（Agent）** | 代码、内容、测试、CI、文档脚手架、自动探测全绿（除实物） |
| **你** | 磁力片实搭、真机实机、证书与行政、运营主体、真钱沙盒、商店素材拍摄 |

**工程侧做到「完美」后，你手上会是一份按步骤可执行的清单，而不是一堆半成品代码。**

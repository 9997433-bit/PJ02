# MagTile Studio — Windows 商店 (Microsoft Store) 计费沙盒验收步骤 (清单 §2 B3 Windows 侧)

本文档是 Windows 商店侧订阅计费**沙盒验收**的单一说明源, 对应上架
清单 [`V1_LAUNCH_CHECKLIST.md`](V1_LAUNCH_CHECKLIST.md) §2 B3
(探测口径 Manual —— 涉及 Partner Center 后台与实机收银台, 无法自动化;
代码侧就绪度由 B2 的 R11W 自动探测常绿保证)。接线实现与设计取舍见
`include/magtile/billing/store_billing_client.hpp` 头注与
`src/billing/store_billing_client.cpp` 的 `MAGTILE_BILLING_WINDOWS_STORE`
宏分支; Google Play 侧姊妹篇见
[PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md)。

**验收范围** (三条链路, 与 Play 侧同构):

1. **购买**: 家长门后发起订阅 → 商店收银台 (`RequestPurchaseAsync`) →
   契约键落盘 → 免费层锁解除;
2. **恢复**: 清数据 / 卸载重装 / 换机后, 启动静默恢复与「恢复购买」
   入口把权益找回来 (`StoreAppLicense.AddOnLicenses`, 商店账户即回执);
3. **断网宽限期**: 无网启动不锁已购内容 (App 侧本地凭证,
   [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §4.4), 且权益真实失效后
   联网启动会收回 (宁可锁)。

> **与 Play 侧的机制差异, 验收前先读** (决定了本文档若干口径与
> Play 姊妹篇不同, 不是漏写):
>
> 1. **微软商店没有沙盒**: 无许可测试账号、无「一律批准」测试卡、
>    无时间压缩 —— 全部验收发生在**真实商店环境**, 购买正式档位是
>    **真实扣费** (成本控制策略见第四节);
> 2. **App 侧「断网宽限期」** = 商店查询失败时保留本地契约键继续
>    解锁, 是我们自己的离线优先策略, 与 Play 侧同口径;
> 3. **商店侧没有宽限期 (grace period)**: 微软官方明示订阅计费不提供
>    宽限期 —— 扣款失败进入 **dunning (补扣) 状态**: 当前计费期内
>    订阅仍有效并周期性重试扣款 (最长约两周), 计费期结束仍失败则
>    订阅直接取消。第五节 C 组按 dunning 模型设计, 没有 Play 侧的
>    「宽限期 + 账号保留」两段。

## 一、前置条件

| # | 条件 | 依据 |
| --- | --- | --- |
| P1 | Microsoft Store 开发者账号 (Partner Center) 可用, 应用已预留名称并取得包身份 (Package Identity) | 清单 §9 L3 (开发者账号) |
| P2 | **订阅附加内容权限**: Partner Center 新建附加内容时「产品类型 = 订阅 (Subscription)」可选 —— 微软官方注明订阅附加内容**并非对所有开发者账号开放** (需微软侧开通); 若不可选, 先经开发者支持申请, 期间勿用 Durable 附加内容顶替上线 (无自动续订, 属商务决策, 见第六节排查表) | learn.microsoft.com「Enable subscription add-ons」系列文档的账号开通注记 |
| P3 | **MSIX 商店包**: 以 `-DMAGTILE_BUILD_QT=ON -DMAGTILE_BILLING_WINDOWS_STORE=ON` 构建的 Qt 壳打成 MSIX, Identity 与 Partner Center 一致 (第三节)。NSIS/ZIP/MSI 直分发包**没有包身份**, 拿不到商店上下文, 不能用于本验收 | 根 `CMakeLists.txt` 选项注释; [`../scripts/package_windows.md`](../scripts/package_windows.md) |
| P4 | 测试机 Windows 10/11 + Microsoft Store 可用 + 登录测试用 Microsoft 账号; **应用必须先从商店安装过一次** (取得商店许可) —— `Windows.Services.Store` 无模拟器, 未经商店安装时商品查询与收银台不可用 | 官方测试口径: 商店许可缓存于账号 + 设备, 装过一次后同 Identity 的本地构建可继续联调 |
| P5 | 只验**商店档构建**: 桌面开发档 (宏 OFF) 走 FakeBillingClient「模拟已订阅」链路, 一切入口显示「即将上线」占位属预期, 与商店验收互不相干 | `apps/desktop_qt/src/billing_backend.cpp` 编译期分流 |
| P6 | 订阅页 UI 已就绪: Qt 侧三档档位卡 + 恢复购买按钮已落地 (家长门后, `SubscriptionPage.qml`), Windows 侧**无 UI 缺口** (与 Android 侧 B2 剩余缺口不同) | 清单 §2 B2 状态列 |

## 二、Partner Center 商品配置 (一次性)

1. Partner Center → 对应应用 → 「附加内容 (Add-ons)」, 创建 **3 个**
   订阅附加内容。**「产品 ID (Product ID)」即代码读到的
   `InAppOfferToken`**, 必须与三端统一商品 id **逐字符一致**
   (`include/magtile/billing/store_billing_client.hpp` 注释,
   `store_billing_client.cpp` 的 `kKnownSubscriptions` 表):

   | 商品 id (产品 ID) | 档位 | 订阅周期 | 定价 (COMMERCIAL_PLAN §3.1) |
   | --- | --- | --- | --- |
   | `sub_monthly` | 订阅 · 月度 | 1 个月 | ¥28/月 ($4.99) |
   | `sub_yearly` | 订阅 · 年度 (主推) | 1 年 | ¥198/年 ($34.99) |
   | `sub_family_yearly` | 订阅 · 家庭年度 | 1 年 | ¥268/年 ($44.99) |

2. **不可逆项, 提交前逐字核对**: 订阅周期发布后**不可更改**; 价格
   发布后**只能降不能升**, 且 Partner Center 新建附加内容默认价格是
   **Free** —— 一旦以 Free 误发布, 该商品 id 永远无法涨回正价。
3. **免费试用期不配置** (可选项为 1 周 / 1 个月, 发布后同样不可
   增删改): V1 定价口径明确不做「免费试用自动扣费」
   ([COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §3.2, 儿童产品口碑雷区)。
4. 标题/描述填中文本地化文案。价格文案经 `queryProducts` 由商店后台
   下发 (`StorePrice.FormattedPrice`), 客户端不内置任何价格文本 ——
   儿童侧零价格红线 ([UI_UX_SPEC.md](UI_UX_SPEC.md) §11) 的实现前提;
   档位名与一句话说明是客户端本地文案 (`kKnownSubscriptions`),
   Partner Center 的 Title 面向商店页, 两者不冲突。
5. 附加内容须随一次**应用提交**发布并通过认证才对客户端可见;
   新建/改动有分钟级到小时级传播延迟, 商品查询空先等一等再排查。

## 三、MSIX 商店包与测试安装

1. Partner Center → 应用 → 「产品身份 (Product identity)」页取
   Package Identity (Name / Publisher / Publisher Display Name),
   MSIX 清单的 `<Identity>` 必须与之一致, 否则商店关联失败。
2. Windows 实机构建 (VS2022 + Windows SDK, 构建前置见
   [`../scripts/package_windows.md`](../scripts/package_windows.md) 第一节):

   ```bat
   cmake -S . -B build-store -G "Visual Studio 17 2022" -A x64 ^
       -DMAGTILE_BUILD_QT=ON ^
       -DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64 ^
       -DMAGTILE_BILLING_WINDOWS_STORE=ON
   cmake --build build-store --config Release --parallel
   ctest --test-dir build-store -C Release --output-on-failure
   ```

   要点: 该选项默认 OFF 且非 Windows 平台开启会配置期 FATAL_ERROR;
   开启后 `magtile_core` 编入 WinRT `StoreContext` 接线并链接
   `windowsapp`; `magtile_billing_test` 第 5 节在商店宏下有同名守卫,
   ctest 全绿再继续。
3. 打 MSIX: 仓库现有打包路径 (NSIS / ZIP / MSI,
   [`../scripts/package_windows.md`](../scripts/package_windows.md))
   **不产出 MSIX**; 首次商店出包需补 MSIX 装配 —— windeployqt 收
   Qt 运行库到安装布局 → `makeappx pack` (或 MSIX Packaging Tool /
   WapProj), Identity 用第 1 步的值。此项即清单 B2 状态列的
   「MSIX 商店包出包」剩余工作, 落地后回填
   [`../scripts/package_windows.md`](../scripts/package_windows.md)
   与 [`../scripts/package_qt_desktop.md`](../scripts/package_qt_desktop.md)
   商店渠道待办 (含 LGPL 可替换性法务评估, 见其第八节)。
4. 提交 Partner Center 并控制可见性: 首选 **私密受众 (Private
   audience)** —— 用已知用户组 (known user group) 圈定测试 Microsoft
   账号, 商店里只有名单内账号可见可装; 已公开发布过的应用退而用
   **包航班 (Package flights)** 给测试组发测试包。提交须通过商店
   认证后测试账号才能安装。
5. 测试账号在测试机 Microsoft Store 登录 → 从商店页安装。
   **从商店装过一次后**, 商店许可缓存在账号 + 设备上, 同 Identity
   的本地开发构建可继续联调, 不必每轮改动都重新过审; 重传商店的
   每一版 MSIX 版本号须递增。

## 四、测试账号与成本控制 (无沙盒的现实口径)

1. 没有许可测试账号 / 测试卡机制, 购买正式档位是**真实扣费**。
   控制成本的建议: 主链路 (第五节 A/B/C 组) 用最低价月度档
   `sub_monthly` (¥28) 实购验收; `sub_yearly` / `sub_family_yearly`
   验到「价格卡正确显示 + 收银台能拉起」即可 (拉起后合上, A6 口径),
   不必每档实购。
2. 实购后立即到 **account.microsoft.com/services** (微软账户的
   「服务与订阅」页) 取消自动续订 —— 取消后**当期仍有效, 期末失效,
   无部分退款**, 正好作为 C5 失效收回的免费素材。
3. 同一账号对同一订阅**取消后短期内不能重购**; 需要重复验购买流时
   准备 **≥ 2 个测试 Microsoft 账号** (私密受众名单里都要加上)。
4. **无时间压缩**: 月度档自然计费周期就是 1 个月 —— C 组中依赖
   续订点/到期的项 (C4/C5) 无法当天闭环, 首轮验收按第五节标注
   登记为**上线后回归项**, 不阻塞其余勾选。有服务端条件时可用
   微软商店购买 REST API (Get subscriptions for a user / Change the
   billing state: cancel / extend / disable autorenew) 加速失效场景,
   但该 API 同样要求账号已开通订阅权限 (前置条件 P2), V1 无服务端,
   不作硬依赖。
5. 退款: 无开发者自助退款通道, 误购经微软账户订单页 / 微软支持
   申诉处理。

## 五、验收清单 (实机逐项勾选)

前置状态: 私密受众渠道从商店安装的商店档 MSIX + 测试账号, 首启完成
(进度存档建档), 未订阅。Qt 壳无 logcat 类日志通道, 结果以界面文案 +
C6 契约键导出核验为准。

### A. 购买

- [ ] A1 未订阅态基线: 非免费模型详情弹窗显示温和「🔒 订阅解锁」
      提示 (无价格无催促), 免费层模型「🧲 开始搭建」照常。
- [ ] A2 订阅页 (家长门后) 三档档位卡价格文案来自商店后台
      (`FormattedPrice` 本地化价格, 与第二节配置一致); 商品查询
      不可用时整页 CTA 退「🌱 订阅即将上线」占位, **绝不出现空价格
      卡**; 价格在家长门外任何界面不出现 (§11 红线)。
- [ ] A3 CTA 文案核验: 商店档按钮为「🌱 开通订阅」, **不得**出现
      「开发模拟, 不产生扣费」字样 (`simulatedBilling` 分流 ——
      商店档真实扣费, 误标即 P0 文案缺陷)。
- [ ] A4 购买 `sub_monthly` (成本控制, 第四节): 商店收银台弹出且
      挂接在应用窗口上 → 完成支付 → 界面提示
      「订阅已开通 —— 全库已解锁」。
- [ ] A5 解锁生效: 回到模型库, 原被锁模型的详情弹窗订阅提示退场,
      「🧲 开始搭建」出现并可进入分步教程 (免费层锁读同一契约键,
      零额外接线)。
- [ ] A6 合上收银台 (不支付): 界面温和收场「已取消, 随时可以再来」
      (`NotPurchased` → 中性 Cancelled, 不弹「失败」), 订阅状态
      不翻转、不解锁。
- [ ] A7 重启保持: 杀进程重启 → 仍解锁 (契约键落盘 + 构造期本地
      凭证载入 + 启动静默恢复校准, 三重口径一致)。

### B. 恢复

- [ ] B1 应用内清数据恢复: 家长门 → 隐私与数据 → 「清除本地数据」
      (二次确认; 契约键随存档一并清空, 详情弹窗回到锁定态, 家长
      会话一并收回) → 重启 → 启动静默恢复 (`AddOnLicenses` 读商店
      许可) 自动找回权益, 无需任何点击。
- [ ] B2 卸载重装恢复: 系统卸载 → 从商店重装 → 首启后自动解锁
      (商店账户即回执, 换机场景同口径)。
- [ ] B3 「恢复购买」按钮 (订阅页): 已购账号点按 →
      「已恢复订阅 —— 全库重新解锁」; 换一个**无订阅**的测试账号 →
      「这个账户下暂时没有可恢复的订阅」中性提示 (不是报错), 且
      本地凭证被清空 (商店明确无订阅 → 宁可锁)。

### C. 断网宽限期与失效收回

- [ ] C1 无网启动不锁: 已订阅解锁态 → 断网 (拔网线/关 Wi-Fi) →
      杀进程重启 → 仍解锁。两种实现路径都算通过:
      (a) `AddOnLicenses` 读系统**本地缓存**的许可证, 断网也查询
      成功 → 静默恢复 Restored; (b) 许可查询不可用 → Unavailable
      **不动本地契约键** (离线宽限期凭证, COMMERCIAL_PLAN §4.4)。
- [ ] C2 无网期间体验完整: 断网下浏览/搭建/进度落盘照常 (离线优先,
      §4.4), 无任何联网报错弹窗。
- [ ] C3 恢复联网重启: 订阅仍有效 → 保持解锁, 无「先锁再开」抖动
      (启动静默恢复校准不闪锁)。
- [ ] C4 商店侧扣款失败 (dunning, **上线后回归项**): 移除/替换为
      失效支付方式 → 等下一个续订点 (月度档 1 个月, 无时间压缩) →
      dunning 期内重启 App **仍解锁** (当期内 `IsActive` 仍 true,
      商店周期性重试扣款最长约两周); 当期结束扣款仍失败 → 订阅
      取消 → 联网重启 **回到锁定态** (查询成功但无有效订阅 →
      契约键清空, 宁可锁)。注意: 商店侧**无宽限期**, 不要按 Play
      侧「宽限期 + 账号保留」两段口径验。
- [ ] C5 取消/到期收回 (**上线后回归项**, 依赖自然计费期):
      account.microsoft.com/services 取消自动续订 (第四节 2) →
      当期结束订阅失效 → 联网重启 → 详情弹窗回到「🔒 订阅解锁」,
      免费层照常可玩。
- [ ] C6 (可选) 契约键落盘核验: 家长门 → 隐私与数据 →
      「导出进度 (JSON)」, 导出文件 settings 段中
      `subscription_active` / `subscription_product_id` 与当前界面
      锁定状态一致 (与 FakeBilling / Google Play 同键同口径,
      跨端互认)。

## 六、常见问题排查

| 症状 | 常见原因 (按概率排查) |
| --- | --- |
| 订阅页退「订阅即将上线」占位 / 商品查询为空 | 非商店包身份 (本地裸 exe, `StoreContext::GetDefault()` 返回 null); 应用未从商店安装过 (无商店许可, 前置条件 P4); 附加内容未随应用提交发布 / 传播延迟未过; 产品 ID 与代码商品 id 不一致 (逐字符核对第二节表); 构建没开 `MAGTILE_BILLING_WINDOWS_STORE` (开发档宏 OFF 属预期, 前置条件 P5) |
| 收银台拉不起来 / 弹窗没有宿主 | Win32 桌面窗口挂接 (`IInitializeWithWindow`) 取的是当前活动窗口 —— 应用最小化或被遮挡时先点回应用窗口再发起购买 |
| 点购买返回温和占位 (「订阅功能正在准备中…」) | 未知商品 id (客户端拒绝口径, 与 FakeBilling/Play 一致); 商店 `NetworkError` / `ServerError`; 商品未在 Partner Center 配置 |
| Partner Center 建不了「订阅」类型附加内容 | 开发者账号未被微软开通订阅附加内容权限 (前置条件 P2) → 经开发者支持申请; 评估 Durable 过渡属商务决策 (无自动续订, `queryProducts` 虽同时查 Durable/Subscription 两类, 但续费模型完全不同, 勿悄悄替换) |
| 已购账号「恢复购买」返回「暂时没有可恢复的订阅」 | 许可证缓存未刷新 (商店 App 里核对该账号订阅状态后重试); 测试机登录账号与购买账号不一致; 订阅已过当期失效 (C5 口径, 属预期) |
| 取消后无法立即重购同一订阅 | 平台限制 (同一账号短期内不能重购) → 换第二个测试账号 (第四节 3) |
| 桌面开发档一切「即将上线」/ 出现「开发模拟」标注 | 符合预期: 宏 OFF 走 FakeBillingClient (前置条件 P5), QA 用「模拟已订阅」开关; 商店验收必须用商店档 MSIX |

## 七、验收登记

通过后在下表登记并回填清单 B3 状态位
([V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §2):

| 项 | 记录 |
| --- | --- |
| 执行日期 / 执行人 | ⬜ |
| 构建 (MSIX 版本号 / 提交时间 / 渠道 = 私密受众或包航班) | ⬜ |
| 测试机 / Windows 版本 | ⬜ |
| 测试账号 (脱敏, 含第二账号) | ⬜ |
| A 购买 (A1~A7) | ⬜ |
| B 恢复 (B1~B3) | ⬜ |
| C 断网宽限期与失效收回 (C1~C6; C4/C5 可登记为上线后回归项, C6 可选) | ⬜ |
| 实购订单与取消/退款处置记录 | ⬜ |
| 遗留问题 / 备注 | ⬜ |

## 相关文档

- [`../scripts/package_windows.md`](../scripts/package_windows.md) —
  Windows 构建与打包手册 (NSIS/ZIP/MSI 路径; MSIX 商店包装配待补,
  见本文第三节)。
- [`../scripts/package_qt_desktop.md`](../scripts/package_qt_desktop.md)
  — Qt 打包手册与商店渠道待办 (MSIX 条目、LGPL 可替换性法务评估)。
- [`../platforms/windows/README.md`](../platforms/windows/README.md) —
  Windows 平台构建与安装包总览。
- `include/magtile/billing/store_billing_client.hpp` /
  `src/billing/store_billing_client.cpp` — Windows 商店接线实现
  (WinRT StoreContext / 购买 / 恢复 / 契约键落盘) 与商品 id 约定。
- [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.2 / §3.1 / §4.4 —
  订阅承诺项、价格表、离线优先与宽限期本地凭证策略。
- [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §2 B2/B3 —
  就绪度总览 (B2 接线 🔶 自动探测 R11W, B3 本验收 Manual)。
- [UI_UX_SPEC.md](UI_UX_SPEC.md) §11 — 儿童侧零价格红线
  (价格文案只允许出现在家长门后)。
- [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) —
  Google Play 侧姊妹篇 (内部测试轨 + 许可测试账号 + 时间压缩沙盒,
  机制与本文差异见文首对照)。

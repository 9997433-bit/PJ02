# MagTile Studio — Google Play Billing 沙盒验收步骤 (清单 §2 B3)

本文档是 Google Play 侧订阅计费**沙盒验收**的单一说明源, 对应上架
清单 [`V1_LAUNCH_CHECKLIST.md`](V1_LAUNCH_CHECKLIST.md) §2 B3
(探测口径 Manual —— 涉及 Play Console 后台与真机收银台, 无法自动化;
代码侧就绪度由 B2 的 R11 自动探测常绿保证)。接线实现与设计取舍见
[`../platforms/android/README.md`](../platforms/android/README.md)
第三节「订阅与计费」与
`platforms/android/app/src/main/kotlin/com/magtile/studio/PlayBillingManager.kt`
头注。

**验收范围** (三条链路, 全部走 Play 沙盒零真实扣费):

1. **购买**: 家长门后发起订阅 → Play 收银台 → 回执确认 → 契约键
   落盘 → 免费层锁解除;
2. **恢复**: 清数据 / 卸载重装 / 换机后, 启动静默恢复与「恢复购买」
   入口把权益找回来;
3. **断网宽限期**: 无网启动不锁已购内容 (App 侧本地凭证,
   [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §4.4), 且权益真实失效后
   联网启动会收回 (宁可锁)。

> 术语区分, 验收时不要混淆:
> **App 侧「断网宽限期」** = 商店查询失败 (无网 / Play 不可用) 时
> 保留本地契约键继续解锁, 是我们自己的离线优先策略;
> **Play 侧「宽限期 (grace period)」** = 用户扣款失败后 Play 给的
> 补救期, 期间 `queryPurchasesAsync` 仍返回有效订阅 —— 两者在
> 第五节 C 组分别有勾选项。

## 一、前置条件

| # | 条件 | 依据 |
| --- | --- | --- |
| P1 | Google Play 开发者账号可用, 应用已创建 (包名 `com.magtile.studio`) | 清单 §9 L3 (法务与账号) |
| P2 | release 签名链路就绪 (`keystore.properties` + `bundleRelease` 出签名 AAB) | [`../platforms/android/SIGNING.md`](../platforms/android/SIGNING.md); 建议接受 Play App Signing (Google 托管分发签名) |
| P3 | 测试机 = arm64-v8a 真机, 装有 Play 商店且登录测试账号; **App 必须经 Play 内部测试轨安装, 不可侧载** (侧载包与 Play 分发签名/许可校验不匹配, 商品查询与收银台会拒绝) | 首发 ABI 只出 arm64 (README 第一节) |
| P4 | ✅ 已满足 —— 家长门后的订阅页 UI 已落地 (`SubscriptionActivity`: 三档档位卡 + 主 CTA + 恢复购买按钮, 接 `PlayBillingManager.queryProducts` / `purchase` / `restore`), 这是唯一的购买/恢复触发入口; 入口路径: 标题栏年龄段入口 → 家长门 → 年龄段对话框「订阅」键 | README 第三节; 订阅是应用内商品, 无入口则购买链路无法发起 —— 本前置已随 B2 订阅页收口满足 |
| P5 | 只验 **Release 构建**: Debug 档 Play Billing 全部入口温和短路, 「模拟已订阅」QA 开关是 Debug 专属链路, 与沙盒验收互不相干 | `PlayBillingManager.enabled = !BuildConfig.DEBUG` |

## 二、Play Console 商品配置 (一次性)

1. Play Console → 对应应用 → 「创收」→ 「订阅」, 创建 **3 个**
   订阅商品, 商品 id 必须与代码**逐字符一致** (三端统一约定,
   `PlayBillingManager.PRODUCT_IDS` /
   `include/magtile/billing/store_billing_client.hpp` 注释):

   | 商品 id | 档位 | 定价 (COMMERCIAL_PLAN §3.1) |
   | --- | --- | --- |
   | `sub_monthly` | 订阅 · 月度 | ¥28/月 ($4.99) |
   | `sub_yearly` | 订阅 · 年度 (主推) | ¥198/年 ($34.99) |
   | `sub_family_yearly` | 订阅 · 家庭年度 | ¥268/年 ($44.99) |

2. 每个商品至少配置 1 个**自动续订基础方案** (base plan);
   客户端购买流取第一个 offerToken, 验收期不配叠加优惠。
3. 标题/描述填中文本地化文案 (价格与文案经 `queryProducts` 由
   Play 后台下发, 客户端不内置任何价格文本 —— 儿童侧零价格红线
   [UI_UX_SPEC.md](UI_UX_SPEC.md) §11 的实现前提)。
4. 在订阅设置中开启 **宽限期 (grace period)** —— 第五节 C4 要验
   扣款失败补救期内不锁内容。
5. 三个商品全部 **激活 (Activate)**。新建/改动商品对测试轨生效
   可能有分钟级到小时级传播延迟, 商品查询空先等一等再排查。

## 三、内部测试轨 (Internal testing)

1. 出签名 AAB: `./gradlew :app:bundleRelease`
   (产物 `app/build/outputs/bundle/release/app-release.aab`,
   流程与核验见 [`../platforms/android/SIGNING.md`](../platforms/android/SIGNING.md))。
2. Play Console → 「测试与发布」→ 「内部测试」→ 新建 release →
   上传 AAB → 保存并发布 (内部测试轨免审核, 分钟级可装)。
3. 「测试人员」页签添加测试邮件列表 (内部测试轨上限 100 人),
   复制 **opt-in 链接**。
4. 测试机上用测试账号打开 opt-in 链接 → 「成为测试人员」→
   从 Play 商店页安装。
5. 后续每轮回归重传 AAB 须递增 `versionCode`
   (`app/build.gradle.kts` defaultConfig); 测试机从 Play 更新,
   不要 adb 覆盖安装。

## 四、许可测试账号 (License testing)

1. Play Console **账号级**页面 (非单应用) → 「设置」→
   「许可测试」→ 把测试 Gmail 加入名单 (改动生效可能要几分钟到
   几小时; 同一账号也必须在第三节的测试人员列表里, 且是测试机
   Play 商店的登录账号)。
2. 许可测试账号的收银台会出现**测试支付方式**:
   「测试卡, 一律批准」/「测试卡, 一律拒绝」以及两种延迟支付
   测试卡 (几分钟后自动完成/自动取消, 用于验 PENDING 待付款链路),
   全程零真实扣费; 沙盒订单在 Play Console 订单页可见并可退款。
3. 测试订阅的时间轴被**压缩** (验收时按此表安排等待时间):

   | 生产口径 | 沙盒口径 |
   | --- | --- |
   | 月度续订 (`sub_monthly`) | 每 **5 分钟** 续订一次 |
   | 年度续订 (`sub_yearly` / `sub_family_yearly`) | 每 **30 分钟** 续订一次 |
   | 扣款失败宽限期 (grace period) | **5 分钟** |
   | 账号保留 (account hold) | **10 分钟** |
   | 回执确认窗口 (acknowledge, 逾期 Play 自动退款) | **5 分钟** (生产为 3 天) |

   测试订阅最多自动续订 **6 次**后自动取消 —— 到期失效是免费的
   负向素材, 第五节 C5 直接利用它。
4. 可选工具: Google 官方 **Play Billing Lab** App (测试机安装,
   用许可测试账号登录) 可模拟 Billing 响应码、切换商店国家/地区,
   排查 UNAVAILABLE 类温和降级分支时比物理断网更可控。

## 五、验收清单 (真机逐项勾选)

前置状态: 内部测试轨安装的 Release 包 + 许可测试账号, 首启完成
(资产解包 + 进度存档建档), 未订阅。观察 logcat 用
`adb logcat -s MagTileBilling` (回执/落盘每步都有中文日志)。

### A. 购买

- [ ] A1 未订阅态基线: 非免费模型详情弹窗显示温和「🔒 订阅解锁」
      提示 (无价格无催促), 免费层 30 模型「🧲 开始搭建」照常。
- [ ] A2 订阅页 (家长门后) 三档档位卡的价格文案来自 Play 后台
      (`queryProducts` 下发的本地化价格, 与第二节配置一致);
      价格在家长门外任何界面**不出现** (§11 红线)。
- [ ] A3 购买主推档 `sub_yearly`: 选「测试卡, 一律批准」→ 收银台
      完成 → 界面温和确认; logcat 出现
      `订阅状态已落盘: active=true product=sub_yearly`。
- [ ] A4 解锁生效: 回到模型库, 原被锁模型的详情弹窗订阅提示退场,
      「🧲 开始搭建」出现并可进入分步教程 (免费层锁读同一契约键,
      零额外接线)。
- [ ] A5 回执确认生效: 等 **6 分钟以上** (沙盒确认窗口 5 分钟),
      Play 商店订阅管理页里该订阅仍为有效、未被自动退款
      (说明 acknowledge 已随购买完成)。
- [ ] A6 取消收银台 (返回键收起): 界面温和收场 (CANCELLED 中性
      结果, 不弹「失败」), 订阅状态不翻转、不解锁。
- [ ] A7 待付款 (PENDING): 换延迟支付测试卡购买 → 本次不解锁
      (温和收场); 几分钟后测试卡自动完成付款 → **重启 App** →
      启动静默恢复补发权益, 解锁生效 (A4 口径)。

### B. 恢复

- [ ] B1 应用内清数据恢复: 家长门 → 隐私面板 → 「清除本地数据」
      (订阅状态随契约键一并清空, 详情弹窗回到锁定态) → 杀进程
      重启 → 启动静默恢复自动找回权益 (无需任何点击; 首启开档
      为异步, 落盘有 2 秒退避重试, 数秒内解锁即为通过)。
- [ ] B2 卸载重装恢复: 系统卸载 → 经 Play 重装 (不可侧载) →
      首启后自动解锁 (换机场景同此口径)。
- [ ] B3 「恢复购买」按钮 (订阅页): 已购账号点按 → RESTORED,
      解锁生效; 换一个**无订阅**的测试账号 → NOTHING_TO_RESTORE,
      界面给中性提示 (「没有找到可恢复的订阅」类措辞, 不是报错)。

### C. 断网宽限期与失效收回

- [ ] C1 无网启动不锁: 已订阅解锁态 → 开飞行模式 → 杀进程重启 →
      仍解锁 (查询失败不动本地凭证; logcat 出现
      `Play Billing 连接失败, 保留本地订阅凭证 (离线宽限期)` 或
      `订阅查询失败, 保留本地凭证`)。
- [ ] C2 无网期间体验完整: 飞行模式下浏览/搭建/进度落盘照常
      (离线优先, §4.4), 无任何联网报错弹窗。
- [ ] C3 恢复联网重启: 订阅仍有效 → 保持解锁, 契约键无抖动
      (logcat 无 active=false 落盘)。
- [ ] C4 Play 侧扣款失败宽限期: Play 商店把该订阅支付方式改为
      「测试卡, 一律拒绝」→ 等下一个续订点 (月度 5 分钟) 进入
      宽限期 (沙盒 5 分钟) → 期间重启 App **仍解锁**
      (Play 在宽限期内仍返回有效订阅); 宽限期过后进入账号保留
      (沙盒 10 分钟) → 重启 App **回到锁定态** (查询成功但无有效
      订阅 → 契约键清空, 宁可锁)。
- [ ] C5 到期/退款收回: 等测试订阅自动取消到期 (最多 6 次续订,
      月度约半小时) **或** 在 Play Console 订单页对该订单执行
      「退款并撤销权益」→ 联网重启 → 详情弹窗回到「🔒 订阅解锁」,
      logcat 出现 `订阅状态已落盘: active=false`。
- [ ] C6 (可选) 契约键落盘核验: 家长门 → 隐私面板 → 「导出进度
      (JSON)」, 导出文件 settings 段中 `subscription_active` /
      `subscription_product_id` 与当前界面锁定状态一致
      (与桌面 FakeBilling 同键同口径, 跨端互认)。

## 六、常见问题排查

| 症状 | 常见原因 (按概率排查) |
| --- | --- |
| 商品查询为空 / 订阅页退「即将上线」占位 | 商品未激活; 商品 id 与代码不一致; AAB 未发布到测试轨; 配置传播延迟未过; Play 商店缓存 (系统设置里清 Play 商店缓存后重试) |
| 收银台报「无法购买你要的商品」 | 侧载安装 (签名不匹配, 必须经 opt-in 链接从 Play 装); 测试机登录账号不在测试人员名单; 安装包 versionCode 落后于测试轨在线版本 |
| 购买成功但几分钟后被退款 | 回执确认失败 (沙盒 5 分钟窗口): 查 logcat `回执确认失败`; 静默恢复会补确认, 若仍复现须排查网络/Play 服务 |
| 收银台不出现测试卡 | 账号不在**账号级**许可测试名单 (与应用级测试人员名单是两处配置), 或名单改动尚未传播 |
| Debug 包上一切「不可用」 | 符合预期: Debug 档全部入口温和短路 (前置条件 P5), QA 用「模拟已订阅」开关, 沙盒验收必须用测试轨 Release 包 |

## 七、验收登记

通过后在下表登记并回填清单 B3 状态位
([V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §2):

| 项 | 记录 |
| --- | --- |
| 执行日期 / 执行人 | ⬜ |
| 构建 (versionCode / versionName / AAB 上传时间) | ⬜ |
| 测试机型 / Android 版本 | ⬜ |
| 测试账号 (脱敏) | ⬜ |
| A 购买 (A1~A7) | ⬜ |
| B 恢复 (B1~B3) | ⬜ |
| C 断网宽限期与失效收回 (C1~C6, C6 可选) | ⬜ |
| 遗留问题 / 备注 | ⬜ |

## 相关文档

- [`../platforms/android/README.md`](../platforms/android/README.md)
  第三节 — Play Billing 接线设计 (启动静默恢复 / 购买 / 恢复 /
  回执确认 / Debug 分流) 与 JNI 契约键口径。
- [`../platforms/android/SIGNING.md`](../platforms/android/SIGNING.md)
  — release 签名与 AAB 出包 (本验收的安装包来源)。
- [COMMERCIAL_PLAN.md](COMMERCIAL_PLAN.md) §2.2 / §3.1 / §4.4 —
  订阅承诺项、价格表、离线优先与宽限期本地凭证策略。
- [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §2 B2/B3 —
  就绪度总览 (B2 接线 🔶 自动探测 R11, B3 本验收 Manual)。
- [UI_UX_SPEC.md](UI_UX_SPEC.md) §11 — 儿童侧零价格红线
  (价格文案只允许出现在家长门后)。
- [WINDOWS_STORE_BILLING_SANDBOX_QA.md](WINDOWS_STORE_BILLING_SANDBOX_QA.md)
  — Windows 商店侧姊妹篇 (Partner Center 配置 + MSIX 测试安装 +
  同构勾选清单; 微软商店无沙盒/无时间压缩, 机制差异见其文首对照)。

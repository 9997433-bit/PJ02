# MagTile Studio — Android Debug / Release QA 手册

本文档是 Android 端 **QA 视角的单页入口**: 回答「Debug 包和
Release 包到底差在哪、仪器测试怎么跑、release 签名怎么配、
内部测试轨怎么走」四个高频问题, 并把两条验收载体
([真机验收勾选表](reports/QA_ANDROID_DEVICE_CHECKLIST.md) 与
[Play 沙盒验收](PLAY_BILLING_SANDBOX_QA.md)) 按构建档位对号入座。

> 单一说明源约定: 本页只做 QA 视角的收口与索引, **不承载实现
> 细节的第二份维护拷贝** —— 签名/出包的权威流程在
> [`platforms/android/SIGNING.md`](../platforms/android/SIGNING.md),
> 计费沙盒验收的权威步骤在
> [`PLAY_BILLING_SANDBOX_QA.md`](PLAY_BILLING_SANDBOX_QA.md),
> 工程与测试套件全貌在
> [`platforms/android/README.md`](../platforms/android/README.md)
> (第一/五节)。两边如有出入, 以上述单一说明源为准并回修本页。

---

## 一、Debug vs Release 构建差异 (QA 必读)

同一份代码, 两个构建档位的行为差异**全部**收敛在下表 —— QA 拿到
一个 APK, 先确认档位, 再决定套哪份验收载体:

| 维度 | Debug (`assembleDebug`) | Release (`assembleRelease` / `bundleRelease`) |
| --- | --- | --- |
| **计费 (billing)** | `PlayBillingManager` 全部入口**温和短路** (`enabled = !BuildConfig.DEBUG`, 编译期常量): 不连 Play、购买/恢复返回 UNAVAILABLE。QA 走订阅页内「**模拟已订阅**」开关 (家长门后, 模拟档位 `sub_yearly`, 零真实扣费), 与桌面 FakeBillingClient 同角色 | 走**真实 Google Play Billing**: 启动静默恢复 + 订阅页购买/恢复/回执确认, 成功后写 `progress/subscription_settings` 契约键; 「模拟已订阅」开关**不可见亦不可达** |
| **签名 (signing)** | AGP 默认 debug keystore 自动签名, 零配置, `adb install` 直装 | 必须配置 `keystore.properties` (见第三节); 缺配置时 release 任务**执行期以中文指引报错**, 绝不产出未签名包 |
| **混淆 (ProGuard / R8)** | 不混淆 (构建系统默认) | `isMinifyEnabled = false` —— 当前**刻意关闭**, 出包即真机验收口径, 两档字节码行为一致; `app/proguard-rules.pro` 已预置 JNI keep 规则 (Kotlin `external fun` 与 `Java_com_magtile_studio_*` 符号), 日后开启 minify 时 JNI 链路不会被改名/裁剪破坏 (细节见 [SIGNING.md](../platforms/android/SIGNING.md) 第四节) |
| **安装方式** | `adb install` 侧载 | 计费沙盒验收**必须经 Play 内部测试轨安装, 不可侧载** (侧载包与 Play 分发签名/许可校验不匹配, 商品查询与收银台会拒绝); 非计费类回归可侧载已签名 APK |
| **CI 覆盖** | `assemble-debug` 任务常绿 (打包 + APK 内容校验) | CI **刻意不做** release 构建 (runner 无密钥); 出包在可接触密钥的受信环境手工执行 |
| **QA 验收载体** | [QA_ANDROID_DEVICE_CHECKLIST.md](reports/QA_ANDROID_DEVICE_CHECKLIST.md) (真机勾选表, §2/§4 依赖「模拟已订阅」开关) | [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) (购买/恢复/断网宽限期三条链路, 全程沙盒零扣费) |

两档共同点 (QA 不必重复验): 订阅解锁读同一契约键
(`subscription_active` / `subscription_product_id`, 与桌面同键同
口径), 免费层锁零分叉; 数据资产打包、JNI 链路、`minSdk 26` /
`arm64-v8a` 首发 ABI 完全一致。

> 快速判档: 进家长门后的订阅页 —— 有「模拟已订阅」开关行 =
> Debug; 没有且价格来自 Play 后台 = Release。

## 二、仪器测试 (instrumented tests) 怎么跑

仪器测试只在 **Debug 变体**执行 (`connectedDebugAndroidTest`);
androidTest 依赖不进产品 APK。套件五个测试类的覆盖明细见
[`platforms/android/README.md`](../platforms/android/README.md)
第五节, 对应勾选表 [§1 自动侧](reports/QA_ANDROID_DEVICE_CHECKLIST.md)。

**有设备** (真机/模拟器, 必须支持 arm64-v8a):

```bash
cd platforms/android
./run_instrumented_smoke.sh
# 真机流水线 (无设备要报错而非跳过):
MAGTILE_REQUIRE_DEVICE=1 ./run_instrumented_smoke.sh
# 报告: app/build/reports/androidTests/connected/
```

脚本自动定位 adb (PATH / ANDROID_HOME / local.properties)、逐台
校验 ABI、唤醒屏幕并解锁 keyguard (Espresso 点击需要窗口焦点),
然后交给 Gradle 一条龙: 构建 → 安装 → 执行 → 卸载。等价直跑:
`./gradlew :app:connectedDebugAndroidTest`。

**无设备** (CI 编译门, 只编译测试 APK 不执行):

```bash
cd platforms/android
./gradlew :app:assembleDebugAndroidTest
```

执行要点:

- 各测试 `@Before` 删除 `progress.db` 回到首启状态 (默认 7-9 档 /
  未订阅 / 库存未登记), 结果不受上次运行残留影响;
- `DeviceManualQaTest` 的 3 个 `@Ignore` 项在报告中应显示为
  **skipped 而非 failed** —— 那是 M-01~M-03 人工项的常驻提醒,
  按勾选表 §2 人眼签核;
- 全绿后勾选表 §1 整节即勾过, 再走 §2~§4 人工项。

## 三、Release keystore 配置 (一次性)

权威流程 (含备份纪律、Play App Signing 取舍、CI 口径) 见
[`platforms/android/SIGNING.md`](../platforms/android/SIGNING.md);
QA / 出包同学的最短路径:

```bash
cd platforms/android

# 1. 生成 release keystore (仅首次; 生成后立即离线双备份 ——
#    密钥丢失 = 永久失去该包名的更新能力)
keytool -genkeypair -v -keystore release.keystore \
    -alias magtile-release -keyalg RSA -keysize 4096 -validity 10000

# 2. 从模板建配置并填入四个键 (storeFile / storePassword /
#    keyAlias / keyPassword, 全部必填)
cp keystore.properties.example keystore.properties

# 3. 出包
./gradlew :app:assembleRelease   # APK: 国内商店直传 / 侧载验收
./gradlew :app:bundleRelease     # AAB: Google Play 要求 App Bundle

# 4. 核验签名
apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk
```

安全红线: `keystore.properties` 与 `*.keystore` / `*.jks` 已被
`.gitignore` 排除, **真实口令与密钥绝不入库**; 仓库只保留占位模板
`keystore.properties.example`。缺配置直接跑 release 任务会得到
中文指引报错 (复制模板 → 生成 keystore → 填键 → 重跑), debug
构建不受任何影响。对应上架清单
[V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) §4 A3
(自动探测 R13)。

## 四、Play Console 内部测试轨 (Internal testing)

计费沙盒验收的前置分发通道 (完整版含商品配置、许可测试账号、
沙盒时间压缩表与逐项勾选清单, 见
[PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md)
第二~五节):

1. 出签名 AAB: `./gradlew :app:bundleRelease`
   (产物 `app/build/outputs/bundle/release/app-release.aab`);
2. Play Console → 「测试与发布」→ 「内部测试」→ 新建 release →
   上传 AAB → 保存并发布 (内部测试轨免审核, 分钟级可装);
3. 「测试人员」页签添加测试邮件列表 (上限 100 人), 复制
   **opt-in 链接**;
4. 测试机用测试账号打开 opt-in 链接 → 「成为测试人员」→
   从 Play 商店页安装 (**不可 adb 侧载**, 见第一节安装方式行);
5. 每轮回归重传 AAB 须递增 `versionCode`
   (`app/build.gradle.kts` defaultConfig), 测试机从 Play 更新;
6. 验计费还需: Play Console 配置三个订阅商品 (`sub_monthly` /
   `sub_yearly` / `sub_family_yearly`, 与代码逐字符一致) +
   测试账号加入**许可测试** (License testing) 名单 —— 收银台出现
   测试支付方式, 全程零真实扣费。

常见坑速查:

| 现象 | 原因与处置 |
| --- | --- |
| release 包装不上 (签名冲突) | 设备上残留 debug 包 (两档签名不同): 先卸载 `com.magtile.studio` 再装 |
| 订阅页商品查询空 | 商品新建/改动对测试轨有分钟级到小时级传播延迟, 先等再排查; 确认三个商品已激活 |
| 收银台拒绝 / 商品不可用 | 包是侧载的而非内部测试轨安装; 或测试账号不在测试人员 + 许可测试双名单 |
| 「模拟已订阅」开关找不到 | 拿到的是 Release 包 —— 该开关是 Debug 专属 (第一节), Release 验订阅走真实沙盒购买 |

## 五、验收载体对号入座

| 验什么 | 用哪个档位 | 执行载体 |
| --- | --- | --- |
| 真机功能验收 (3D 视口/手势/教程/家长门/跨端互通, V1 清单 §4 A4) | Debug (`adb install`) | [reports/QA_ANDROID_DEVICE_CHECKLIST.md](reports/QA_ANDROID_DEVICE_CHECKLIST.md): §1 仪器测试一键跑 (本文档第二节) + §2~§4 人工项 + §5 登记 |
| 订阅计费沙盒验收 (购买/恢复/断网宽限期, V1 清单 §2 B3) | Release (内部测试轨安装) | [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md): 第五节 A/B/C 三组逐项勾选 |
| 无设备 CI 门 | Debug | `assembleDebug` (打包校验) + `assembleDebugAndroidTest` (测试编译门), `.github/workflows/android.yml` |

## 相关文档

- [`platforms/android/README.md`](../platforms/android/README.md) —
  Android 工程全貌: 构建 (第一节) / JNI (第三节) / 数据资产
  (第四节) / CI 与仪器测试套件明细 (第五节)。
- [`platforms/android/SIGNING.md`](../platforms/android/SIGNING.md) —
  release 签名与出包的单一说明源 (本文档第三节是其 QA 摘要)。
- [PLAY_BILLING_SANDBOX_QA.md](PLAY_BILLING_SANDBOX_QA.md) —
  Play 计费沙盒验收的单一说明源 (本文档第四节是其分发通道摘要)。
- [reports/QA_ANDROID_DEVICE_CHECKLIST.md](reports/QA_ANDROID_DEVICE_CHECKLIST.md) —
  Debug 档真机验收勾选表 (V1 清单 §4 A4 执行载体)。
- [E2E_TEST_MATRIX.md](E2E_TEST_MATRIX.md) — 跨端 E2E 矩阵
  (Android 侧条目 E2E-03/08/11/14/15 与签核规则)。
- [V1_LAUNCH_CHECKLIST.md](V1_LAUNCH_CHECKLIST.md) — 上架清单
  (§2 B2/B3 计费, §4 A3 签名 / A4 真机验收)。

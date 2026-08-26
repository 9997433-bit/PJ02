# MagTile Studio — Android Release 签名与出包

本文档是 Android release 签名的单一说明源, 对应上架清单
[`docs/V1_LAUNCH_CHECKLIST.md`](../../docs/V1_LAUNCH_CHECKLIST.md)
§4 A3, 自动探测为 `tools/check_v1_readiness.sh` 的 R13
(口径: 本目录存在 `keystore.properties.example` 模板 +
`app/build.gradle.kts` 含 `signingConfigs` 块)。

## 设计要点

- **密钥绝不入库**: 真实 keystore (`*.keystore` / `*.jks`) 与口令文件
  `keystore.properties` 均已被本目录 `.gitignore` 排除, 仓库只保留
  占位模板 `keystore.properties.example`。
- **debug 链路零影响**: `keystore.properties` 不存在时,
  `assembleDebug` (本地与 CI) 照常构建, 行为与接线前完全一致。
- **release 缺配置时清晰报错**: 无 `keystore.properties` 时执行
  `assembleRelease` / `bundleRelease` / `installRelease` 会在执行期
  以中文指引失败 (复制模板 → 生成 keystore → 填键 → 重跑),
  而不是默默产出无法上架的未签名 APK。

## 一、生成 release keystore (一次性)

```bash
cd platforms/android
keytool -genkeypair -v -keystore release.keystore \
    -alias magtile-release -keyalg RSA -keysize 4096 -validity 10000
```

- `-validity 10000` (约 27 年): 商店要求签名密钥覆盖应用全生命周期。
- 证书主体 (CN/O 等) 填运营主体信息 (依赖清单 §9 L4 定稿)。
- **立即离线备份** keystore 与口令 (密码管理器 + 离线介质双份):
  密钥丢失 = 永久失去该包名的更新能力, 无法找回。
- 上 Google Play 可选启用 Play App Signing (Google 托管应用签名密钥,
  本地密钥降级为上传密钥, 丢失可申请重置); 国内商店 (华为/应用宝,
  `docs/COMMERCIAL_PLAN.md` §5.2) 均为自持密钥, 备份纪律同上。

## 二、配置 keystore.properties

```bash
cd platforms/android
cp keystore.properties.example keystore.properties
# 编辑填入四个键: storeFile / storePassword / keyAlias / keyPassword
```

四个键全部必填, 任一缺失或留空, release 构建会报错并指回模板。
`storeFile` 相对本目录解析 (也接受绝对路径)。

## 三、出包 (assembleRelease / bundleRelease)

```bash
cd platforms/android

# APK (国内商店直传 / 侧载验收)
./gradlew :app:assembleRelease
# 产物: app/build/outputs/apk/release/app-release.apk (已签名)

# AAB (Google Play 要求 App Bundle)
./gradlew :app:bundleRelease
# 产物: app/build/outputs/bundle/release/app-release.aab (已签名)

# 出包后核验签名 (任选其一)
apksigner verify --print-certs app/build/outputs/apk/release/app-release.apk
keytool -printcert -jarfile   app/build/outputs/apk/release/app-release.apk
```

数据资产档位与 debug 同一套开关: 追加 `-PmagtileAssets=starter`
只打 30 个入门模型 (README 第四节), 默认全库。

接线实现见 `app/build.gradle.kts`「Release 签名」一节:
`signingConfigs.release` 从 `keystore.properties` 读取四元组,
`buildTypes.release.signingConfig` 仅在该文件存在时生效。

## 四、ProGuard / R8 与 JNI

release 当前**不开启**混淆/裁剪 (`isMinifyEnabled = false`, 全部
Kotlin 代码与 JNI 绑定原样保留, 出包即真机验收口径)。
`app/proguard-rules.pro` 已随本次接线预置最小 keep 规则并挂接进
release 档 —— 日后开启 `isMinifyEnabled = true` 时, JNI 链路
(Kotlin `external fun` 与原生导出符号 `Java_com_magtile_studio_*`
按「类全名 + 方法名」静态匹配) 不会被改名/裁剪破坏; 原生侧无
FindClass 反射回调 Kotlin, 无需额外 keep。

## 五、CI 口径

CI (`.github/workflows/android.yml`) **刻意不做 release 构建**:
runner 上没有也不应该有真实密钥, `assemble-debug` 任务保持常绿即可
(清单 §4 A1)。release 出包在可接触密钥的受信环境手工执行 (本文档
第三节), 真机验收与商店提审属人工项 (清单 §4 A4/A5, 探测侧 M2)。
若日后要在 CI 出 release 包, 密钥经 CI Secret 注入并在 workflow 内
落地为临时 `keystore.properties`, 本接线无需改动。

## 相关文档

- `README.md` 第一节 — debug 构建与安装 (release 出包即本文档)。
- `docs/V1_LAUNCH_CHECKLIST.md` §4 A3 — 上架清单条目与放行规则。
- `docs/COMMERCIAL_PLAN.md` §5.2 — 商店分发策略 (华为/应用宝优先)。

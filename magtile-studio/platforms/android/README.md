# MagTile Studio — Android 平台外壳

本目录是 Android 端的完整 Gradle 工程 (从脚手架推进到「可安装最小
体验」): `magtile_core` (C++20, 无桌面依赖) 通过 Android NDK 交叉
编译为 `libmagtile_core.so`, 由 JNI 包装层暴露给 Kotlin; APK 内置
`data/` 子集与全部缩略图, 首启解包后即可浏览 **全库模型库**
(缩略图卡片 + 难度/主题/免费/核心 9 片/「我能搭的」筛选), 登记家里的
磁力片库存 (SQLite, 与桌面同一 schema), 并对任意模型按需执行完整
物理校验 (R1~R8)。

> 状态: **可安装最小体验**。已落地: Gradle 工程 (含 wrapper)、JNI
> 链路 (目录加载 / 模型库列表含 core-9 与「我能搭的」判定 / 物理校验 /
> 教程步骤数 / 进度存档打开 / 库存读写 / 缺片清单)、RecyclerView 模型
> 卡片列表 (缩略图 / 中文名 / 主题 / 难度星 / 片数·步数 / 「需要
> 扩展装」角标)、筛选栏 (难度星级 / 主题 / 「只看免费」 /
> 「只用核心 9 片」 / 「我能搭的」, 口径与桌面 GL/Qt 一致)、磁力片
> 库存录入屏 (片型 +
> 数量步进器, 对齐桌面 InventoryPage)、数据资产打包与首启解包。
> 尚未落地: 渲染循环 (GLES3 / Vulkan)、分步教程交互 UI (卡片详情当前
> 为「教程即将上线」占位), 计划见下文与 `docs/ROADMAP.md`。

## 目录结构

```
platforms/android/
├── README.md                 本文档
├── CMakeLists.txt            JNI 共享库构建脚本 (双入口: 仓库根 / Gradle)
├── jni/
│   └── magtile_jni.cpp       JNI 包装层 (9 个入口, 见下表)
├── settings.gradle.kts       Gradle 工程入口 (工程根 = 本目录)
├── build.gradle.kts          插件版本 (AGP 8.7.3 / Kotlin 2.0.21)
├── gradle.properties         AndroidX / 配置缓存
├── gradlew / gradle/         Gradle Wrapper (8.13)
└── app/
    ├── build.gradle.kts      externalNativeBuild + assets 打包接线
    │                         (-PmagtileAssets=starter 打入门子集, 见第四节)
    └── src/main/
        ├── AndroidManifest.xml
        ├── kotlin/com/magtile/studio/
        │   ├── MainActivity.kt        模型库列表 + 筛选栏 + 详情弹窗 + 按需校验
        │   ├── InventoryActivity.kt   磁力片库存录入屏 (片型 + 数量步进器)
        │   ├── MagTileNative.kt       进度存档/库存 JNI 桥 (进程级单例)
        │   ├── ModelCard.kt           卡片元数据 (listModels JSON 解析)
        │   ├── ModelCardAdapter.kt    RecyclerView 适配器 (缩略图 + 角标)
        │   ├── ThumbnailLoader.kt     assets/thumbnails 异步解码 + LruCache
        │   └── DataAssetInstaller.kt  assets/data -> filesDir/data 解包
        └── res/                       布局 / 主题 / 自适应启动图标
```

## 一、构建 APK (Gradle, 推荐)

前置条件:

- JDK **17+** (AGP 8.7 要求; JDK 21 亦可)
- Android SDK: `platforms;android-35`、`build-tools;35.0.0`、
  `ndk;27.2.12479018` (r27c)、`cmake;3.22.1`
  (缺失组件在 SDK 许可已接受时由 AGP 自动补装)

```bash
cd platforms/android
# 指定 SDK 位置 (二选一): export ANDROID_HOME=~/Android/Sdk
# 或写 local.properties: echo "sdk.dir=$HOME/Android/Sdk" > local.properties

./gradlew :app:assembleDebug
# 产物: app/build/outputs/apk/debug/app-debug.apk (全库约 12.5 MB, arm64-v8a;
#        追加 -PmagtileAssets=starter 只打 30 个入门模型, 见第四节)

adb install app/build/outputs/apk/debug/app-debug.apk
```

安装启动后: 首次启动解包数据资产 (秒级) → 状态栏显示
「N / N 个模型 · 13 种磁力片形状」(N = 全库模型数, 当前 139+) →
滚动缩略图模型卡片列表;
筛选栏可按难度星级 / 主题过滤, 勾选「只看免费」只看免费层 30 模型
(目录「免费」标签, 非免费详情弹窗以温和订阅提示替换教程占位),
勾选「只用核心 9 片」只看基础套装
能搭的模型 (用到扩展片型的卡片带琥珀「需要扩展装」角标); 「我能搭的」
只看家里磁力片库存足够搭建的模型 —— 未登记库存时该开关禁用, 由
「去登记 ▶」引导进库存录入屏 (片型 + 数量步进器, 长按连加, 支持
直接输入; 「保存, 看看我能搭什么 ▶」保存后直接勾上筛选), 已登记后
入口变为「改库存」。点击卡片弹出简介 + 套装说明 + 库存对照 (够搭 /
还差几片, 「缺什么片?」展开清单) 与「教程即将上线」占位, 「物理校验」
按钮按需加载模型并展示 R1~R8 中文校验摘要与教程步骤数。

要点:

- `app/build.gradle.kts` 的 `externalNativeBuild` 指向本目录
  `CMakeLists.txt` (双入口设计, 会 `add_subdirectory` 仓库根拉起
  `magtile_core`; 桌面 GL/Qt/CTest 在 Android 下自动强制关闭)。
- 首发只出 `arm64-v8a`; 模拟器调试可在 `abiFilters` 临时追加 `x86_64`。
- `minSdk 26` (Android 8.0): NDK libc++ 的 `std::filesystem` 自
  android-26 起完整可用, `magtile_core` 的 JSON 加载依赖它。

## 二、纯 NDK 交叉编译 .so (不需要 Gradle / SDK)

适合 CI 与本地快速验证。前置条件: Android NDK **r26+** (自带
Clang 17+, 完整支持 C++20)、CMake ≥ 3.22、Ninja。

```bash
# ANDROID_NDK 指向 NDK 根目录, 例如 ~/Android/Sdk/ndk/27.2.12479018
cmake -S . -B build-android -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE=$ANDROID_NDK/build/cmake/android.toolchain.cmake \
    -DANDROID_ABI=arm64-v8a \
    -DANDROID_PLATFORM=android-26 \
    -DCMAKE_BUILD_TYPE=Release
cmake --build build-android
# 产物: build-android/platforms/android/libmagtile_core.so
```

其他 ABI 依次替换 `ANDROID_ABI`: `armeabi-v7a`、`x86_64`。

## 三、JNI 接口与链接方式

`platforms/android/CMakeLists.txt` 将仓库根的 **静态库** `magtile_core`
与 `jni/magtile_jni.cpp` 一起链接为 **一个** 共享库, 产物命名为
`libmagtile_core.so` (Kotlin 侧 `System.loadLibrary("magtile_core")`)。
单 .so 方案下 STL 使用默认的 `c++_static` 即可; 若日后拆分多个原生库,
需统一切换 `-DANDROID_STL=c++_shared`。

JNI 接口一览 —— 模型库链路绑定 `com.magtile.studio.MainActivity`:

| Kotlin 声明 | 说明 |
| --- | --- |
| `loadCatalog(catalogPath: String): Int` | 加载 `tile_catalog.json`, 返回形状数量, 失败 -1 |
| `listModels(dataDir: String): String` | 模型库目录 JSON: `{"inventory_configured":bool,"models":[{id/name/name_en/description/difficulty/total_pieces/step_count/theme/file/bom_known/core9_only/can_build/missing_total/free},...]}`, 失败 `{"error":"..."}`; 卡片元数据外逐模型加载 BOM 判定「只用核心 9 片」(`core::isCoreTile` 共享口径, 目录 tier 优先) 与库存已登记时的「我能搭的」(`can_build` / 共缺几片 `missing_total`); `free` = 免费层判定 (`core::isFreeTierModel`, 目录 tags 含「免费」, 与桌面 CLI/GL/Qt 同口径); 模型文件有问题按 `bom_known=false` 降级, 139 模型后台线程百毫秒完成 |
| `validateModel(jsonPath: String): String` | 加载模型并跑完整物理校验 (R1~R8), 返回中文摘要 |
| `getTutorialStepCount(): Int` | 最近一次成功加载模型的教程步骤数, 未加载 -1 |

进度存档 / 磁力片库存链路绑定 `com.magtile.studio.MagTileNative`
(直接复用核心库 `progress::ProgressStore` —— 与桌面 CLI
`inventory set` / GL / Qt 录入界面同一份 SQLite schema
(`tile_inventory` 表), 存档文件互相兼容; Android 端存档在
`filesDir/progress.db`):

| Kotlin 声明 | 说明 |
| --- | --- |
| `openProgressStore(dbPath: String): Boolean` | 打开 (不存在则创建) 进度存档数据库; 失败 false 并降级 (库存功能不可用, 模型库照常) |
| `inventoryRows(): String` | 库存录入界面数据源: `{"configured":bool,"total":N,"shapes":[{id/name_zh/expansion/count},...]}`, 全部片型按核心 9 片在前的枚举顺序, 中文名与 core/expansion 分层以 `tile_catalog.json` 为准 |
| `saveInventory(countsJson: String): Boolean` | 保存库存快照 (`{"square":12,...}` upsert): 数量夹到 [0,999], 未知片型跳过; count=0 也保留「明确没有」 |
| `canBuildModel(jsonPath: String): Int` | 库存是否足够搭建: 1 够搭 / 0 缺片 / -1 无法判定 (未登记库存或模型文件有问题) |
| `missingPiecesJson(jsonPath: String): String` | 缺片清单: `{"configured","can_build","missing_total","missing":[{id/name_zh/count}],"text":"缺 2 片正方形、…"}` (措辞与桌面 Qt `missingText` 一致), 失败 `{"error":"..."}` |

筛选在 Kotlin 侧完成 (`MainActivity.applyFilters`), 口径与桌面
GL/Qt 模型库一致: 难度星级精确匹配、规范主题 (目录 `theme` 字段)、
「只看免费」要求 `free` (非免费照常可浏览, 详情弹窗以温和订阅提示
替换教程占位)、「只用核心 9 片」要求 `bom_known && core9_only`
(BOM 未知不进核心筛选)、「我能搭的」要求 `can_build` (库存未登记时
开关禁用并引导录入, 不显示全空列表); 「需要扩展装」角标 =
`bom_known && !core9_only`。

## 四、数据资产策略

- 构建期: `app/build.gradle.kts` 的 `stageMagTileAssets` 任务 (Sync)
  把仓库根 `data/` 的**子集**同步进 APK assets, 分两个目录:
  - `assets/data/`: `tile_catalog.json` + `model_catalog.json` +
    `models/*.json` (约 3.3 MB), 供原生层读取;
  - `assets/thumbnails/`: 全库卡片缩略图 (320x240 PNG, 约 30 KB/张,
    全库约 4 MB), 只被 Kotlin UI 消费。

  数据单一来源是仓库根 `data/`, 不做第二份拷贝。
- **starter 子集 (可选)**: `./gradlew :app:assembleDebug -PmagtileAssets=starter`
  只打 30 个精选入门模型及其缩略图 (清单
  `platforms/windows/packaging/starter_models.txt`, 与免费层选品一致,
  三端对齐决议见 `docs/FREE_TIER_MANIFEST.md`); `stageStarterCatalog`
  任务把 `model_catalog.json` 过滤到同一子集, 目录不会列出 APK 里
  不存在的模型。默认与 CI 均为全库 (`-PmagtileAssets=full`), 行为不变。
- 运行期: `magtile_core` 走 `std::filesystem` 读真实文件路径, 不能直接
  读 assets 流, 故 `DataAssetInstaller` 在首次启动 (或 APK 更新后, 以
  `lastUpdateTime` 版本戳判断) 把 assets/data 解包到 `filesDir/data`;
  版本戳一致时零拷贝, 日常启动无 IO 开销。
- 缩略图**不解包**: 刻意放在 `assets/data/` 之外, `ThumbnailLoader`
  按 `thumbnails/<模型 id>.png` 约定 (与核心库 `findThumbnail` 的
  `data/thumbnails/<id>.png` 约定一致) 直接流式读 assets + 后台线程
  解码 + `LruCache` (进程内存 1/8 上限), 不占用 `filesDir` 空间;
  asset 缺失时卡片显示占位底色, 并记入负缓存避免滚动时反复尝试 IO。
- 进度存档 (磁力片库存 / 教程进度 / 收藏) 是运行期数据, 不在 assets
  范围: `filesDir/progress.db` (SQLite, 随 `allowBackup` 自动备份),
  schema 与桌面完全一致 (同一份 `progress_store.cpp` 编译进 .so)。

## 五、CI

`.github/workflows/android.yml` (仓库根) 包含两个任务:

- `ndk-so`: 纯 NDK 交叉编译 `libmagtile_core.so` 并断言 9 个 JNI
  符号齐全 (模型库 4 个 + 进度存档/库存 5 个) —— 持续保证
  `magtile_core` 无平台依赖。
- `assemble-debug`: Gradle 全量打包 debug APK, 校验 APK 内容
  (原生库 / 数据资产 / 缩略图已打包; 缩略图数量落后于模型数量时
  只告警 —— 内容制作期新模型缩略图可能滞后生成, 缺图卡片显示占位)
  并上传为构建产物。

## 六、后续计划

- 渲染: 复用 `include/magtile/render/renderer.hpp` 抽象接口, Android 端
  实现 GLES3 / Vulkan 后端 (桌面 GLFW+GL4.1 后端不上移动端)。
- 教程交互: `TutorialEngine` 已与 UI 解耦, Kotlin 侧仅做手势与 HUD;
  卡片详情的「教程即将上线」占位替换为分步教程页。
- 模型库增强: 搜索框、「只看收藏」筛选 (「我能搭的」与库存录入
  已落地, 对齐桌面 GL 模型库全量筛选器还差收藏/完成状态维度)。
- 进度存档: `progress_store` (SQLite) 已开箱接入 (库存链路), 待接
  完成状态 / 收藏 / 「继续上次」到列表 UI。

## 相关文档

- `docs/PLATFORM_ARCHITECTURE.md` — 跨平台技术架构总纲 (共享 C++ 核心 +
  平台外壳、渲染后端矩阵、CI 矩阵); 本目录即其第 8 节规划的
  `platforms/android/` 落地。
- `docs/ARCHITECTURE.md` — 核心分层与模块职责。
- `docs/PHYSICS_RULES.md` — validateModel 执行的 R1~R8 物理规则。
- `platforms/windows/README.md` — Windows 端构建与安装包规划。

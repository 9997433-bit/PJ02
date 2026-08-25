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
> 教程步骤数 / 进度存档打开 / 库存读写 / 缺片清单 / 年龄段设置读写 /
> 进度页与成就墙数据源 / 教程步骤数据与进度读写 / 家长门
> 出题·校验·会话 / 3D 场景加载·设步·相机手势·渲染循环)、
> RecyclerView 模型卡片列表 (缩略图 / 中文名 / 主题 / 难度星 /
> 片数·步数 / 「需要扩展装」角标)、筛选栏 (难度星级 / 主题 /
> 「只看免费」 / 「只用核心 9 片」 / 「我能搭的」, 口径与桌面
> GL/Qt 一致)、订阅状态与免费层锁 (解锁 = 免费层或订阅有效,
> 与桌面 `billing::isContentUnlocked` / DetailPage 锁同口径; 订阅
> 状态经 `progress/subscription_settings` 契约键与桌面同键落
> settings 表, Debug 档带「模拟已订阅」QA 开关, 不接真实商店
> SDK)、分龄 UI 三档 (4-6 超大卡片只留主题筛选 / 7-9
> 难度+主题+免费 / 10+ 全量筛选, 与桌面 Qt LibraryPage 同一口径,
> 年龄段与桌面 settings 同键)、磁力片库存录入屏 (片型 +
> 数量步进器, 对齐桌面 InventoryPage)、进度页「我的作品」与成就墙
> (统计 + 进行中/已完成/收藏列表 + 徽章墙, 对齐桌面 Qt
> ProgressPage/AchievementsPage 口径; 作品行直达教程 —— 进行中
> 「继续搭建」断点续搭 / 已完成「再搭一次」从头开始 / 收藏直达
> 详情, 与桌面 startBuild 同口径)、分步教程页 (**3D 教程视口**
> GLES3 渲染循环, 复用与桌面 GL/Qt 同一份 `GlSceneRenderer`: 单指
> 旋转 / 双指捏合缩放 / 双指平移, 当前步新增片橙色描边呼吸 + 未放
> 片 ghost 轮廓; 下方步骤列表 + 上一步/下一步 + 断点续搭 + 当前步
> 写进度存档)、家长门 (年龄段切换与库存录入入口上锁,
> UI_UX_SPEC.md §9: 算术题 + 中文大写数字软键盘 + 冷却 +
> 15 分钟内存会话, 复用 `core::ParentGate` 共享状态机)、
> 数据资产打包与首启解包。
> 尚未落地 (3D 视口剩余缺口见第六节): 视口 MSAA 抗锯齿与按需渲染
> 节电 (当前连续重绘驱动呼吸动画)、「转一转视角」引导态 (第 0 步)
> 与视角重置按钮, 计划见下文与 `docs/ROADMAP.md`。

## 目录结构

```
platforms/android/
├── README.md                 本文档
├── SIGNING.md                release 签名与出包手册 (清单 §4 A3 / 探测 R13)
├── keystore.properties.example  release 签名配置模板 (真实密钥不入库)
├── CMakeLists.txt            JNI 共享库构建脚本 (双入口: 仓库根 / Gradle)
├── jni/
│   ├── magtile_jni.cpp       JNI 包装层 (模型库/存档/教程/家长门/隐私/订阅 23 个入口, 见下表)
│   └── magtile_scene_jni.cpp 3D 教程视口 JNI 桥 (场景/相机/渲染循环 8 个入口, 见下表)
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
        │   ├── MainActivity.kt        模型库列表 + 分龄筛选栏 + 详情弹窗 + 按需校验
        │   ├── ParentGateDialog.kt    家长门对话框 (算术题 + 中文大写数字软键盘)
        │   ├── InventoryActivity.kt   磁力片库存录入屏 (片型 + 数量步进器)
        │   ├── ProgressActivity.kt    进度页「我的作品」(统计 + 作品列表)
        │   ├── AchievementsActivity.kt 成就墙全览 (徽章两列网格)
        │   ├── TutorialActivity.kt    分步教程页 (3D 视口 + 步骤列表 + 上一步/下一步 + 进度落盘)
        │   ├── TutorialSceneView.kt   3D 教程视口 (GLSurfaceView/GLES3 + 触屏轨道相机手势)
        │   ├── TutorialSceneNative.kt 3D 视口 JNI 桥 (场景加载/设步/手势/渲染循环)
        │   ├── TutorialStepAdapter.kt 教程步骤行适配器 (已完成/当前/待搭三态)
        │   ├── MagTileNative.kt       进度存档/库存/年龄段/进度页/教程 JNI 桥 (进程级单例)
        │   ├── ModelCard.kt           卡片元数据 (listModels JSON 解析)
        │   ├── ModelCardAdapter.kt    RecyclerView 适配器 (标准/启蒙双卡片布局)
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

Release 出包 (`assembleRelease` / `bundleRelease`): 签名从工程根
`keystore.properties` 读取 (不入库, 模板 `keystore.properties.example`),
生成密钥 / 配置 / 出包 / 核验的完整流程见 [SIGNING.md](SIGNING.md)
(对应上架清单 `docs/V1_LAUNCH_CHECKLIST.md` §4 A3, 自动探测 R13)。

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
入口变为「改库存」。点击卡片弹出简介 + 预计用时「🕒 大约 N 分钟」
(原生层 `core::estimateBuildMinutes` 与桌面 Qt 详情页同一纯函数档位
估算, 步数未知时隐藏, 4-6 岁更大字, 与缺片/订阅状态无关照常显示)
+ 套装说明 + 库存对照 (够搭 /
还差几片, 「缺什么片?」展开清单), 已解锁模型 (免费层或订阅生效,
`billing::isContentUnlocked` 与桌面同口径) 带「🧲 开始搭建」大按钮
直达分步教程页; 未订阅的非免费模型只锁这个入口 —— 浏览/校验照常,
以温和的「🔒 订阅解锁」提示替代 (无价格无催促, 措辞对齐桌面 Qt
DetailPage 订阅横幅), 订阅生效后提示退场全库直达教程; 「物理校验」
按钮按需加载模型并展示 R1~R8 中文校验摘要与教程步骤数。

订阅状态持久化与桌面完全同键同口径 (`progress/subscription_settings`
契约键 `subscription_active` / `subscription_product_id`, 落同一份
SQLite settings 表, 缺键/脏值一律按未订阅兜底宁可锁); **Debug 构建**
在家长门后的年龄段对话框带「🧪 模拟订阅: 开/关」QA 开关 (与桌面
订阅页 `devControlsEnabled` 开发开关同角色, 模拟档位同为年度主推
`sub_yearly`, 零真实扣费), `BuildConfig.DEBUG` 为编译期常量,
Release 档不可见亦不可达。当前不接任何真实商店 SDK。

分步教程页 (3D 教程视口 + 文字分步, 措辞对齐桌面 GL/Qt 教程 HUD):
进度头「第 x/y 步 · 已放 n/m 片」+ 进度条, 页顶为**可交互 3D 教程
视口** (GLSurfaceView + GLES3, 复用与桌面 GLFW/ImGui、Qt FBO 视口
完全同一份场景渲染器 `render::GlSceneRenderer` —— 着色器版本头按
上下文自动切 300 es, 绘制实现三端同一份): 当前步新增片橙色描边 +
呼吸动画引导放置, 未放片为淡化 ghost 轮廓提示最终形态, 参照片琥珀
描边, 地面网格 + 半透明彩色薄板与桌面完全同观感; 触屏手势与 Qt
教程视口同一口径 —— 单指拖动旋转 (0.32°/dp)、双指捏合缩放 (指距
比经对数换算, 12%/格, 与桌面滚轮同缩放曲线)、双指同向滑动平移,
断点续搭时视口直接停在上次的当前步。下方步骤列表逐行显示序号圆徽
+ 中文说明 + 小提示 (💡) + 片数增量 (+N 片), 当前步主色高亮并自动
滚动定位, 已完成步换 ✓ 绿徽; 底部「◀ 上一步 / 下一步 ▶」大按钮
(末步变「完成 🎉」), 步骤导航同步驱动 3D 场景设步。进度写档口径
对齐桌面 Qt TutorialViewport: 会话开始即建档 (模型库/进度页立刻
显示进行中), 每次步骤导航把当前步与增量游玩时长写进
`model_progress` 表 (与桌面同一份 SQLite schema, 断点续搭跨端互通),
走完最后一步记完成 + 解锁首搭成就 first_model_completed (进度页/
成就墙即时可见); 存档写入失败只降级不打断搭建, 3D 场景加载失败也
只温和降级为文字分步 (视口画地面网格, 不报错不锁功能, P3 零挫败)。

标题栏右侧是年龄段模式入口 (三档单选, UI_UX_SPEC.md §2): 年龄段
切换是家长操作 (§9), 点击先过**家长门** —— 中文数字乘法题 (如
「叁 × 柒 = ?」) + 中文大写数字软键盘 (56dp 键帽, 不依赖输入法),
答对开启 15 分钟家长会话 (只存内存, 重启即失效), 会话内再点免重复
验证; 连续 3 次答错温和提示「休息一下」并 60 秒冷却 (题目/校验/
冷却/会话与桌面 GL/Qt 同一 `core::ParentGate` 状态机)。过门后弹
三档单选, 切换立即生效并落盘 (settings 表 `age_mode` 键, 与桌面
GL/Qt/CLI 同键):

- **4-6 岁 · 启蒙**: 超大卡片 (大缩略图竖排 + 大字号, 副标题只留
  主题, 不显示英文名与「需要扩展装」角标), 筛选只留主题;
- **7-9 岁 · 标准** (默认档): 标准卡片, 难度 + 主题 + 只看免费
  (库存录入入口保留, 点击过家长门);
- **10-12 岁 · 进阶**: 全量筛选 (难度 / 主题 / 只看免费 /
  只用核心 9 片 / 我能搭的)。

筛选栏的库存录入入口 (「去登记 ▶」/「改库存」) 同为家长操作,
过同一扇家长门 (同一会话守卫, 15 分钟内免重复验证)。

被收起的筛选维度切档时同步清零 —— 看不见的筛选绝不悄悄过滤列表
(与桌面 Qt LibraryPage `collapseHiddenFilters` 同一策略)。

标题栏的「🏆 我的进度」进进度页「我的作品」(儿童可达无家长门 §5.3,
对齐桌面 Qt ProgressPage/AchievementsPage 口径): 三格温和统计
(已完成 / 进行中 / 收藏) + 成就墙条带 (已点亮枚数 + 「看看全部
徽章 ▶」进全览) + 进行中列表 (进度条 + 第 x/y 步 + 用时) + 已完成
列表 (完成日期 + 用时 + 片数) + 我的收藏; 没有作品时温和空态引导
去模型库 (§4.3 只报喜不催促, 不显示分数排名)。成就墙全览为徽章
两列网格: 已点亮 = 完成绿卡 + ✓ + 解锁日期, 未点亮 = 灰色剪影 +
一句话达成条件 (不显示进度百分比, §7.1 防焦虑); 徽章只与搭建行为
挂钩 (按完成模型数 1/3/10/30 分档, §4.5)。进度页作品行直达教程
(整行可点 + 行尾动作标签, 路由口径与桌面 Qt
`StudioBackend::startBuild` 一致): 进行中「继续搭建 ▶」进
TutorialActivity 断点续搭 (教程页自读存档当前步, 3D 视口停在上次
的当前步); 已完成「再搭一次 ▶」带 `EXTRA_RESTART` 从头开始 ——
已完成的存档值为总步数, 不从头会直接落在末步完成态 (与桌面同
理由; 完成时刻存储层只记首次, 重搭不丢 ✓ 已完成徽标); 收藏行与
桌面同为「点击直达详情」—— 带模型 id 收屏返回模型库, 由详情弹窗
接力 (免费判定/订阅提示留在详情一处)。进度页本身保持儿童可达无
家长门 (§5.3), 教程页返回后自动重拉总览; 行对应模型已下架时教程
页/模型库侧都只温和提示不崩溃, 空态引导保持不变。

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
与 `magtile_render_scene` (无窗口 GL 场景渲染器, 与桌面 GLFW/ImGui、
Qt FBO 教程视口同一份 3D 绘制实现, 根 CMakeLists 在 Android 下也
构建该目标)、`jni/magtile_jni.cpp`、`jni/magtile_scene_jni.cpp` 一起
链接为 **一个** 共享库并挂上系统 `libGLESv3` (GLES3 核心入口经
`dlsym` 运行时解析, 与 GLFW `glfwGetProcAddress` / Qt
`getProcAddress` 同一角色), 产物命名为 `libmagtile_core.so`
(Kotlin 侧 `System.loadLibrary("magtile_core")`)。
单 .so 方案下 STL 使用默认的 `c++_static` 即可; 若日后拆分多个原生库,
需统一切换 `-DANDROID_STL=c++_shared`。

JNI 接口一览 —— 模型库链路绑定 `com.magtile.studio.MainActivity`:

| Kotlin 声明 | 说明 |
| --- | --- |
| `loadCatalog(catalogPath: String): Int` | 加载 `tile_catalog.json`, 返回形状数量, 失败 -1 |
| `listModels(dataDir: String): String` | 模型库目录 JSON: `{"inventory_configured":bool,"models":[{id/name/name_en/description/difficulty/total_pieces/step_count/theme/file/bom_known/core9_only/can_build/missing_total/free/estimated_minutes},...]}`, 失败 `{"error":"..."}`; 卡片元数据外逐模型加载 BOM 判定「只用核心 9 片」(`core::isCoreTile` 共享口径, 目录 tier 优先) 与库存已登记时的「我能搭的」(`can_build` / 共缺几片 `missing_total`); `free` = 免费层判定 (`core::isFreeTierModel`, 目录 tags 含「免费」, 与桌面 CLI/GL/Qt 同口径); `estimated_minutes` = 预计用时档位 (§5.4, `core::estimateBuildMinutes` 与桌面 Qt 详情页同一纯函数, 5/10/15/20/30/45 分钟六档, 0 = 步数未知时界面隐藏); 模型文件有问题按 `bom_known=false` 降级, 139 模型后台线程百毫秒完成 |
| `validateModel(jsonPath: String): String` | 加载模型并跑完整物理校验 (R1~R8), 返回中文摘要 |
| `getTutorialStepCount(): Int` | 最近一次成功加载模型的教程步骤数, 未加载 -1 |

进度存档 / 磁力片库存 / 年龄段设置 / 进度页与成就墙 / 分步教程
链路绑定 `com.magtile.studio.MagTileNative` (直接复用核心库
`progress::ProgressStore` —— 与桌面 CLI `inventory set` / GL / Qt
录入界面同一份 SQLite schema (`tile_inventory` 表 + `settings` 表),
存档文件互相兼容; Android 端存档在 `filesDir/progress.db`):

| Kotlin 声明 | 说明 |
| --- | --- |
| `openProgressStore(dbPath: String): Boolean` | 打开 (不存在则创建) 进度存档数据库; 失败 false 并降级 (库存功能不可用, 模型库照常) |
| `inventoryRows(): String` | 库存录入界面数据源: `{"configured":bool,"total":N,"shapes":[{id/name_zh/expansion/count},...]}`, 全部片型按核心 9 片在前的枚举顺序, 中文名与 core/expansion 分层以 `tile_catalog.json` 为准 |
| `saveInventory(countsJson: String): Boolean` | 保存库存快照 (`{"square":12,...}` upsert): 数量夹到 [0,999], 未知片型跳过; count=0 也保留「明确没有」 |
| `canBuildModel(jsonPath: String): Int` | 库存是否足够搭建: 1 够搭 / 0 缺片 / -1 无法判定 (未登记库存或模型文件有问题) |
| `missingPiecesJson(jsonPath: String): String` | 缺片清单: `{"configured","can_build","missing_total","missing":[{id/name_zh/count}],"text":"缺 2 片正方形、…"}` (措辞与桌面 Qt `missingText` 一致), 失败 `{"error":"..."}` |
| `ageModeId(): String` | 年龄段模式标识 (`settings` 表 `age_mode` 键, 与桌面 GL/Qt/CLI `settings set-age` 同键): `"age_4_6"` / `"age_7_9"` / `"age_10_12"`; 存档未打开 / 从未设置 / 存量脏值一律返回默认档 `"age_7_9"` (`progress::getAgeMode` 自带兜底), 调用方无需判空 |
| `setAgeModeId(modeId: String): Boolean` | 保存年龄段模式 (立即落盘): 未知标识返回 false 并忽略 (与桌面 SettingsBackend 一致); 存档未打开 / 落盘失败仍返回 true —— 本次运行内生效, 重启后回读不到 (温和降级) |
| `progressOverviewJson(dataDir: String): String` | 进度页「我的作品」/ 成就墙数据源 (口径与桌面 Qt StudioBackend 的 `inProgressList`/`completedList`/`favoritesList`/`achievementsList` 一致): `{"store_ready","completed_count","in_progress_count","favorite_count","achievement_count","in_progress":[{id/name/current_step/step_count/play_text}],"completed":[{id/name/pieces/meta_text}],"favorites":[{id/name}],"achievements":[{id/name/condition/unlocked/unlocked_text}]}`, 失败 `{"error":"..."}`; 只统计仍在目录中的模型, 进行中要求已真正开动 (current_step > 0); 徽章按完成数 1/3/10/30 分档 (存档 achievements 表已解锁或达到阈值即点亮, 未点亮带一句话达成条件, 不下发进度百分比 §7.1), 存档中额外成就以通用徽章补列; "用时 23 分钟"/"解锁于 8月20日" 等措辞与桌面一致; 徽章 emoji 由 Kotlin 侧按 id 映射 (增补平面字符不过 `NewStringUTF`); 存档不可用时 `store_ready=false`, 列表为空、徽章全未点亮, 页面照常可看 |
| `getTutorialSteps(dataDir: String, modelId: String): String` | 分步教程步骤数据源 (modelId 经模型库目录解析到模型 JSON, 与进度页"只认仍在库中的模型"同一口径): `{"model_id","name","step_count","total_pieces","steps":[{step_number/description/tip/pieces_added/pieces_total},...]}`, 失败 `{"error":"..."}`; `pieces_added` = 本步骤新增片数 (片数增量), `pieces_total` = 累计已放片数 (末步 = 模型总片数) |
| `savedTutorialStep(modelId: String): Int` | 存档中该模型的当前步 (断点续搭): 无记录 / 存档不可用一律 0 (从头开始, 温和降级); 已完成模型返回总步数 (完成链路推到最后一步), 调用方据此进入完成态 |
| `saveTutorialStep(modelId: String, step: Int, stepCount: Int, playSeconds: Long): Boolean` | 写教程进度 (口径与桌面 Qt TutorialViewport 的 `flushProgress`/`applyStepChange` 一致, 同一份 `model_progress` 表): step = 已完成到第几步, playSeconds = 本次新增游玩秒数 (存储层累加只增不减); step >= stepCount 时记完成 (首次完成时刻不覆盖) + 解锁首搭成就 `first_model_completed`; 存档未打开 / 写入失败返回 false (调用方不打断搭建, P3 零挫败) |

家长门链路同样绑定 `com.magtile.studio.MagTileNative` (直接复用
`core::ParentGate` —— 与桌面 GL/Qt 完全同一状态机: 乘法题生成 /
中文大写数字验证 / 3 次答错 60 秒冷却 / 15 分钟内存会话; 会话与
冷却只存内存永不落盘, 防重启绕过, 与 ProgressStore 无关):

| Kotlin 声明 | 说明 |
| --- | --- |
| `parentGateOpenJson(): String` | 进门出新题 (每次进门新题防背题, 与桌面 ParentGateBackend::openGate 同口径): `{"question":"叁 × 柒 = ?","attempts_remaining":N,"cooldown_seconds":N,"session_active":bool}`; 仍在上一轮冷却期时 `cooldown_seconds > 0`, 界面据此直接进温和的「休息一下」倒计时 |
| `parentGateSubmitJson(answer: String): String` | 提交答案 (中文大写数字如 `贰拾壹`, 接受 `壹拾贰`/`拾贰` 变体): `{"result":"passed"/"wrong"/"cooling","attempts_remaining":N,"cooldown_seconds":N,"session_active":bool}`; passed = 15 分钟家长会话已开启, wrong/cooling 由界面给温和提示 (「再试一次吧」/「休息一下」) |
| `parentGateSessionActive(): Boolean` | 家长会话是否仍有效: true = 守卫期内免重复验证 (时长读 `core::ParentGate::kDefaultSessionDuration`, 与桌面 Qt 会话守卫同策略) |

家长门入口 (`ParentGateDialog.requireParent`): 标题栏年龄段切换与
筛选栏库存录入都先过门, 会话内免重复; 「我的进度」保持儿童可达
无门 (§5.3)。

隐私与数据链路同样绑定 `com.magtile.studio.MagTileNative`
(SECURITY_AND_PRIVACY.md §3 / §4 C4/Z8: 家长可查看、导出、删除
全部本地数据; 直接复用核心库 `progress::exportLocalDataJson` /
`ProgressStore::clearAllData` —— 与桌面 Qt 家长中心「隐私与数据」
区**同一实现与导出格式**, 三端导出文件互认):

| Kotlin 声明 | 说明 |
| --- | --- |
| `exportLocalDataJson(): String` | 导出全部本地数据 (进度/成就/磁力片库存/设置 —— 应用在本机的全部用户数据) 为家长可读 JSON 文本 (缩进 2 空格, 顶层 `format`/`format_version`/`exported_at`, 与桌面同格式); 写文件由 Kotlin 侧完成 (应用专属外部目录 `getExternalFilesDir`, 零权限, 家长可用文件管理器取走; 不可用时退回 `filesDir`), 文件名带时间戳互不覆盖; 存档未打开/读库失败返回 `{"error":"..."}` (界面温和提示) |
| `clearLocalData(): Boolean` | 清除全部本地数据: 进度/成就/库存/设置四张表**单事务原子清空** (要么全清要么不动), 表结构与 schema 版本保留, 清完等价首次启动空档; 成功 true, 存档未打开/失败 false (温和提示不弹「失败」) |

隐私与数据入口: 年龄段对话框 (已在家长门后) 的中性键「隐私与
数据」进隐私面板 —— 展示「我们收集什么 / 数据存在哪 (存档完整
路径) / 隐私政策草稿文档路径 `docs/PRIVACY_POLICY_DRAFT.md`」,
文案口径与桌面 Qt 家长中心一致; 「导出进度 (JSON)」直接导出,
「清除本地数据」再过一道二次确认 (说清删什么 + 不可恢复 + 引导
先导出, 「先不清除」为安全默认), 清除成功后年龄段回默认档、
订阅状态回未订阅、模型库重拉 (库存回未登记引导态) —— 温和回到
首次启动状态。

订阅状态链路同样绑定 `com.magtile.studio.MagTileNative`
(COMMERCIAL_PLAN §2.2: 直接复用 `progress/subscription_settings`
契约键 —— 与桌面 Qt BillingBackend / FakeBillingClient **同键**
(`subscription_active` / `subscription_product_id`) **同口径**
(缺键/脏值/存档不可用一律按未订阅兜底, 宁可锁不放行), 落同一份
SQLite settings 表, 存档文件跨端互认; 不接任何真实商店 SDK):

| Kotlin 声明 | 说明 |
| --- | --- |
| `subscriptionActive(): Boolean` | 订阅当前是否有效 (免费层锁的读取口径, 与桌面 DetailPage 锁 / `billing::isContentUnlocked` 同一判定源): 存档未打开 / 缺键 / 脏值一律 false (未订阅兜底宁可锁 —— 与免费层 `is_free` 缺数据宁可放行的方向相反, 守的是付费权益) |
| `subscriptionProductId(): String` | 生效中的订阅商品档位 id (如 `sub_yearly`, 三端统一档位约定); 未订阅 / 从未写入 / 存档不可用返回空串 |
| `setSubscriptionActive(active: Boolean, productId: String): Boolean` | 写订阅状态 (立即落盘, `progress::setSubscriptionActive` 同一实现: `active=false` 时清空档位记录); 成功 true, 存档未打开 / 落盘失败 false —— 调用方不得在 false 时翻转界面解锁状态 (订阅权益以落盘为准, 与年龄段"内存态即真相"的温和降级刻意不同)。当前唯一调用方是 Debug 档「模拟已订阅」QA 开关 |

**后续接真实商店 (Google Play Billing) 的路径**: 界面与免费层锁
只面向订阅状态读取口径, 不感知商店 SDK —— 接入时在 Kotlin 侧引入
Play Billing Library (购买流 / 恢复购买 / 回执校验), 购买或恢复
成功后经 `setSubscriptionActive` 写同一契约键即可, 免费层锁零改动;
商品 id 沿用三端统一约定 (`sub_monthly` / `sub_yearly` /
`sub_family_yearly`, `COMMERCIAL_PLAN.md` §3.1), 原生侧对应
`billing::StoreBillingClient` 骨架 (各商店接法与回执口径文档见
`include/magtile/billing/store_billing_client.hpp`; 空实现档全部
Unavailable 绝不误报已订阅)。届时 Debug 档「模拟已订阅」QA 开关
保持仅 Debug 可见, 与真实购买链路互不干扰。

3D 教程视口链路绑定 `com.magtile.studio.TutorialSceneNative`
(实现在 `jni/magtile_scene_jni.cpp`; 场景绘制复用
`render::GlSceneRenderer`, 步骤语义复用 `tutorial::TutorialEngine`,
相机为共享 `render::OrbitCamera` —— 手势常量单一来源在原生层,
与桌面完全同口径)。线程约定: `surfaceCreated` / `drawFrame` 只在
GLSurfaceView 渲染线程调用 (GL 资源属于该线程的 EGL 上下文), 其余
入口主线程 / 工作线程均可 (会话状态由原生互斥锁保护):

| Kotlin 声明 | 说明 |
| --- | --- |
| `loadScene(dataDir: String, modelId: String, resumeStep: Int): Int` | 加载教程场景 (modelId 经模型库目录解析, 与 `getTutorialSteps` 同口径): 片型目录 + 模型 + 教程引擎 + 按最终成品包围盒取景 + 跳到断点步 (0 = 从头 -> 第 1 步, 越界夹取); 返回步骤数, 失败 -1 (步骤一致性问题与桌面同策略不进 3D 教程, 视口温和降级为只画地面网格, 文字分步照常) |
| `setStep(step: Int)` | 跳到指定步 (1..stepCount, "当前展示步" 语义: 该步新增片描边 + 呼吸, 之后的片 ghost); 越界夹取, 未加载空操作 |
| `releaseScene()` | 释放场景会话 (引擎/相机/片快照); GL 资源随 EGL 上下文由系统回收 |
| `dragRotate(dxDp: Double, dyDp: Double)` | 单指拖动 = 轨道旋转: dp 位移, 原生按 0.32°/px 换算 (与桌面鼠标左键 / Qt 触屏单指同一手感) |
| `pinchZoom(spreadRatio: Double)` | 双指捏合 = 缩放: 指距比经对数换算成等效滚轮格数 (`OrbitCamera::kZoomStepFactor` 12%/格, 与桌面滚轮 / Qt 捏合同一缩放口径) |
| `pan(dxPx: Double, dyPx: Double, viewportHeightPx: Int)` | 双指同向滑动 = 平移 (物理像素对视口高换算世界距离, 与桌面右键拖动 / Qt 双指平移同口径) |
| `surfaceCreated()` | 表面创建 / EGL 上下文重建 (仅 GL 线程): 重建 `GlSceneRenderer` GL 资源; 初始化失败只写 logcat 温和降级 |
| `drawFrame(width: Int, height: Int, timeSeconds: Double)` | 绘制一帧 (仅 GL 线程): timeSeconds 驱动本步新增片呼吸动画; 场景未加载时画清屏 + 地面网格 |

筛选在 Kotlin 侧完成 (`MainActivity.applyFilters`), 口径与桌面
GL/Qt 模型库一致: 难度星级精确匹配、规范主题 (目录 `theme` 字段)、
「只看免费」要求 `free` (非免费照常可浏览, 详情弹窗以温和订阅提示
替换教程占位)、「只用核心 9 片」要求 `bom_known && core9_only`
(BOM 未知不进核心筛选)、「我能搭的」要求 `can_build` (库存未登记时
开关禁用并引导录入, 不显示全空列表); 「需要扩展装」角标 =
`bom_known && !core9_only`。

筛选控件按年龄段收放 (`MainActivity.applyAgeMode`, 三档口径与桌面
Qt LibraryPage 一致): 4-6 只留主题 (难度 / 免费 / 核心 9 片 /
我能搭的 / 库存入口收起), 换用超大卡片布局 `item_model_card_junior`;
7-9 难度 + 主题 + 只看免费 (库存入口保留, 点击过家长门); 10+ 全量。
被收起的维度
切档时同步清零, 库存录入屏「保存, 看看我能搭什么 ▶」也只在 10+ 档
自动勾上「我能搭的」(其他档位该筛选不可见, 不悄悄开启)。

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

- `ndk-so`: 纯 NDK 交叉编译 `libmagtile_core.so` 并断言 31 个 JNI
  符号齐全 (模型库 4 个 + 进度存档/库存/年龄段/进度页 8 个 +
  分步教程 3 个 + 家长门 3 个 + 隐私与数据 2 个 + 订阅状态 3 个 +
  3D 教程视口 8 个) —— 持续保证 `magtile_core` 无平台依赖。
- `assemble-debug`: Gradle 全量打包 debug APK, 校验 APK 内容
  (原生库 / 数据资产 / 缩略图已打包; 缩略图数量落后于模型数量时
  只告警 —— 内容制作期新模型缩略图可能滞后生成, 缺图卡片显示占位)
  并上传为构建产物。

## 六、后续计划

- 3D 教程视口 (骨架已落地, 剩余缺口):
  - **已落地**: GLES3 渲染循环 (GLSurfaceView) + 与桌面 GL/Qt 完全
    同一份场景渲染器 (`magtile_render_scene`, 地面网格 / 半透明彩色
    薄板 / 当前步橙色描边呼吸 / ghost 轮廓 / 参照片琥珀描边) +
    触屏轨道相机 (单指旋转 / 双指捏合缩放 / 双指平移, 与 Qt 触屏
    同口径) + 断点续搭设步 + 上下文丢失恢复;
  - **缺口**: 视口 MSAA 抗锯齿 (桌面 4x, Android 当前用默认
    EGLConfig, 边缘有锯齿; 需自定义 EGLConfigChooser + 降级链);
    按需渲染节电 (当前 RENDERMODE_CONTINUOUSLY 连续重绘驱动呼吸
    动画, 后续可改脏帧模式 + 呼吸期定频重绘); 「转一转视角」
    引导态 (第 0 步空场景) 与视角重置按钮; 「减少动态效果」开关
    联动 (桌面 §4.7 已有, Android 待 ui_settings 链路接通)。
- 模型库增强: 搜索框、「只看收藏」筛选 (「我能搭的」与库存录入
  已落地, 对齐桌面 GL 模型库全量筛选器还差收藏/完成状态维度)。
- 进度存档: `progress_store` (SQLite) 已开箱接入 (库存 + 年龄段 +
  进度页/成就墙 + 教程进度链路), 进度页作品行「继续搭建 /
  再搭一次」直达教程页已落地 (进行中断点续搭 / 已完成从头再搭 /
  收藏直达详情, 与桌面 startBuild 同口径); 模型卡片上的完成/
  进行中徽标、收藏切换与「继续上次」大卡片待接入模型库列表 UI。
- 家长门: 年龄段切换与库存录入入口已上锁 (对齐 UI_UX_SPEC.md §9,
  复用 `core::ParentGate` 共享状态机, 15 分钟会话守卫); 后续随
  桌面 M3 推进可选 4 位 PIN 与家长中心完整功能 (订阅/数据管理)。
- 订阅与计费: 订阅状态读写与免费层锁已对齐桌面 (`progress/
  subscription_settings` 同键同口径, Debug 档「模拟已订阅」QA
  开关); 尚未接真实 Google Play Billing SDK —— 接入路径见第三节
  「后续接真实商店」(Kotlin 侧 Play Billing Library 购买/恢复成功
  后经 `setSubscriptionActive` 写同一契约键, 免费层锁零改动, 原生
  侧对应 `billing::StoreBillingClient` 骨架); 家长门后的订阅页
  (三档档位卡 + 恢复购买, 对齐桌面 Qt SubscriptionPage) 待家长
  中心落地时一并接入。

## 相关文档

- `docs/PLATFORM_ARCHITECTURE.md` — 跨平台技术架构总纲 (共享 C++ 核心 +
  平台外壳、渲染后端矩阵、CI 矩阵); 本目录即其第 8 节规划的
  `platforms/android/` 落地。
- `docs/ARCHITECTURE.md` — 核心分层与模块职责。
- `docs/PHYSICS_RULES.md` — validateModel 执行的 R1~R8 物理规则。
- `platforms/windows/README.md` — Windows 端构建与安装包规划。

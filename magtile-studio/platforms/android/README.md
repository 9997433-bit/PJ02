# MagTile Studio — Android 平台外壳 (脚手架)

本目录是 Android 端的最小脚手架, 用于证明跨平台路径成立:
`magtile_core` (C++20, 无桌面依赖) 通过 Android NDK 交叉编译为
`libmagtile_core.so`, 由 JNI 包装层暴露给 Kotlin 调用。

> 状态: **脚手架**。JNI 链路 (目录加载 / 模型物理校验 / 教程步骤数)
> 已可用; 渲染循环 (GLSurfaceView / Vulkan)、教程交互 UI、完整
> Gradle 工程尚未落地, 计划见下文与 `docs/ROADMAP.md`。

## 目录结构

```
platforms/android/
├── README.md                 本文档
├── CMakeLists.txt            JNI 共享库构建脚本 (双入口: 仓库根 / Gradle)
├── jni/
│   └── magtile_jni.cpp       JNI 包装层: loadCatalog / validateModel / getTutorialStepCount
└── app/src/main/kotlin/com/magtile/studio/
    └── MainActivity.kt       最小 Kotlin 壳 (System.loadLibrary + 冒烟验证)
```

## 一、纯 NDK 交叉编译 .so (不需要 Gradle)

适合 CI 与本地快速验证。前置条件:

- Android NDK **r26 及以上** (自带 Clang 17+, 完整支持 C++20)
- CMake ≥ 3.22, Ninja

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

要点:

- NDK 工具链文件会定义 `ANDROID`, 仓库根 `CMakeLists.txt` 据此:
  强制关闭桌面 GL 后端 (GLFW/ImGui) 与 CTest, 跳过命令行应用,
  只构建 `magtile_core` 静态库 + 本目录的 JNI 共享库。
- `ANDROID_PLATFORM=android-26` (Android 8.0) 起 `std::filesystem`
  在 NDK libc++ 中可完整使用; `magtile_core` 的 JSON 加载依赖它。
- 其他 ABI 依次替换 `ANDROID_ABI`: `armeabi-v7a`、`x86_64`。

## 二、magtile_core 的链接方式

`platforms/android/CMakeLists.txt` 将仓库根的 **静态库** `magtile_core`
与 `jni/magtile_jni.cpp` 一起链接为 **一个** 共享库, 并把产物命名为
`libmagtile_core.so` (Kotlin 侧 `System.loadLibrary("magtile_core")`)。
单 .so 方案下 STL 使用默认的 `c++_static` 即可; 若日后拆分多个原生库,
需统一切换 `-DANDROID_STL=c++_shared`。

JNI 接口一览 (符号绑定到 `com.magtile.studio.MainActivity`):

| Kotlin 声明 | 说明 |
| --- | --- |
| `loadCatalog(catalogPath: String): Int` | 加载 `tile_catalog.json`, 返回形状数量, 失败 -1 |
| `validateModel(jsonPath: String): String` | 加载模型并跑完整物理校验 (R1~R8), 返回中文摘要 |
| `getTutorialStepCount(): Int` | 最近一次成功加载模型的教程步骤数, 未加载 -1 |

## 三、Gradle 工程接入 (计划, 尚未提交)

为保持脚手架轻量, 本目录暂不包含 Gradle Wrapper 与构建脚本;
新建 Gradle 工程时按以下要点接入即可:

1. `app/build.gradle.kts` 中指向本目录的 CMake 入口:

```kotlin
android {
    namespace = "com.magtile.studio"
    compileSdk = 35
    defaultConfig {
        minSdk = 26          // std::filesystem 需要 android-26+
        externalNativeBuild {
            cmake { arguments += listOf("-DANDROID_PLATFORM=android-26") }
        }
        ndk { abiFilters += listOf("arm64-v8a") }
    }
    externalNativeBuild {
        cmake {
            path = file("../CMakeLists.txt")   // platforms/android/CMakeLists.txt
            version = "3.22.1"
        }
    }
}
```

   该 CMakeLists 是双入口设计: 被 Gradle 直接调用时会自动
   `add_subdirectory` 仓库根目录, 拉起 `magtile_core`。

2. **数据资产**: 把仓库根 `data/` (形状目录 + 模型库) 打进 APK assets
   (`sourceSets` 里追加 `assets.srcDirs += "../../../data"` 或用
   Gradle copy 任务), 首次启动时解包到 `filesDir/data` 再把路径传给
   JNI —— `MainActivity.kt` 的冒烟验证即按此约定读取。
3. `MainActivity.kt` 刻意只依赖 `android.app.Activity` (无 AndroidX),
   可直接作为最小可编译起点。

## 四、后续计划

- 渲染: 复用 `include/magtile/render/renderer.hpp` 抽象接口, Android 端
  实现 GLES3 / Vulkan 后端 (桌面 GLFW+GL4.1 后端不上移动端)。
- 教程交互: `TutorialEngine` 已与 UI 解耦, Kotlin 侧仅做手势与 HUD。
- CI: 在桌面构建旁增加 NDK 交叉编译任务, 保证 `magtile_core`
  持续保持无平台依赖。

## 相关文档

- `docs/PLATFORM_ARCHITECTURE.md` — 跨平台技术架构总纲 (共享 C++ 核心 +
  平台外壳、渲染后端矩阵、CI 矩阵); 本目录即其第 8 节规划的
  `platforms/android/` 落地脚手架。
- `docs/ARCHITECTURE.md` — 核心分层与模块职责。
- `docs/PHYSICS_RULES.md` — validateModel 执行的 R1~R8 物理规则。
- `platforms/windows/README.md` — Windows 端构建与安装包规划。

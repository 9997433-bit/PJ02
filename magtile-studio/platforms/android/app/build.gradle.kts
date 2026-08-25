// =============================================================
// MagTile Studio - Android app 模块
//
// 三条与常规工程不同的接线 (均回引仓库根, 保持单一数据源):
//   1. externalNativeBuild 指向 ../CMakeLists.txt (双入口设计, 会
//      add_subdirectory 仓库根, 交叉编译 magtile_core + JNI 为
//      libmagtile_core.so; 桌面 GL/Qt/CTest 在 Android 下自动关闭)。
//   2. stageMagTileAssets 任务把仓库根 data/ 的子集同步进
//      build/magtile-assets/, 作为额外 assets 目录打进 APK:
//        assets/data/       形状目录 + 模型库目录 + 全部模型 JSON
//                           (约 3.3 MB), 首启由 DataAssetInstaller
//                           解包到 filesDir/data 供原生层读取;
//        assets/thumbnails/ 全库卡片缩略图 (320x240 PNG, 约 4 MB),
//                           只被 Kotlin UI 消费, 经 ThumbnailLoader
//                           直接流式读 assets, 不落盘 (刻意放在
//                           data/ 之外避免解包)。
//   3. minSdk 26: NDK libc++ 的 std::filesystem 自 android-26 起完整
//      可用, magtile_core 的 JSON 加载依赖它。
// =============================================================

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.magtile.studio"
    compileSdk = 35
    // 与 CI 及 README 保持一致的 NDK 版本 (r27c, Clang 18, 完整 C++20)
    ndkVersion = "27.2.12479018"

    defaultConfig {
        applicationId = "com.magtile.studio"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        externalNativeBuild {
            cmake {
                arguments += listOf("-DANDROID_PLATFORM=android-26")
            }
        }
        // 首发只出 arm64 (实机全覆盖); 模拟器调试可临时追加 x86_64
        ndk { abiFilters += listOf("arm64-v8a") }
    }

    externalNativeBuild {
        cmake {
            path = file("../CMakeLists.txt")   // platforms/android/CMakeLists.txt
            version = "3.22.1"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    sourceSets {
        getByName("main") {
            // stageMagTileAssets 的输出目录 (内容为 data/...)
            assets.srcDir(layout.buildDirectory.dir("magtile-assets"))
        }
    }
}

// 把仓库根 data/ 的子集同步进 build 目录作为 APK assets。
// 用 Sync (而非 Copy) 保证删除模型/缩略图后旧文件不会残留在 APK 里。
// 缩略图刻意放到 assets/thumbnails/ (data/ 之外): DataAssetInstaller
// 只解包 assets/data, 缩略图由 Kotlin 直接流式读 assets, 不落盘。
val stageMagTileAssets = tasks.register<Sync>("stageMagTileAssets") {
    description = "同步仓库根 data/ 子集 (tile_catalog + model_catalog + models/ + thumbnails/) 到 APK assets"
    into(layout.buildDirectory.dir("magtile-assets"))
    from(rootProject.layout.projectDirectory.dir("../../data")) {
        include("tile_catalog.json", "model_catalog.json", "models/**")
        into("data")
    }
    from(rootProject.layout.projectDirectory.dir("../../data/thumbnails")) {
        include("*.png")
        into("thumbnails")
    }
}
tasks.named("preBuild") { dependsOn(stageMagTileAssets) }

dependencies {
    // 模型卡片列表; 刻意不引 appcompat/material, 保持依赖面最小
    implementation("androidx.recyclerview:recyclerview:1.3.2")
}

// =============================================================
// MagTile Studio - Android app 模块
//
// 四条与常规工程不同的接线 (均回引仓库根/工程根, 保持单一数据源):
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
//   4. release 签名从工程根 keystore.properties 读取 (不入库, 模板
//      keystore.properties.example, 流程 ../SIGNING.md): 文件不存在时
//      debug 照常, release 任务执行期给中文指引报错 (见文内守卫)。
// =============================================================

// 顶层 import: 脚本体内 `java` 标识符被 Java 插件扩展遮蔽, 不能就地全限定
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// ---- Release 签名 (密钥不入库; 生成/配置/出包流程见 ../SIGNING.md) ----
// keystore.properties (工程根 platforms/android/, .gitignore 已排除,
// 模板 keystore.properties.example) 存在时读取签名四元组; 不存在时
// assembleDebug 照常, release 任务在执行期给出中文指引报错 (见下方
// 守卫) —— 刻意不在配置期失败, 否则连 debug 构建/IDE 同步都会被拖垮。
val keystorePropsFile = rootProject.file("keystore.properties")
val keystoreProps: Properties? =
    if (keystorePropsFile.isFile) {
        Properties().apply { keystorePropsFile.inputStream().use { load(it) } }
    } else {
        null
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

    signingConfigs {
        // 仅在 keystore.properties 就位时注册 (V1 清单 §4 A3, 探测 R13);
        // 四个键全部必填, 缺失/留空立刻报错指回模板, 不带病出包
        if (keystoreProps != null) {
            create("release") {
                fun prop(key: String): String =
                    keystoreProps.getProperty(key)?.trim()?.takeIf { it.isNotEmpty() }
                        ?: throw GradleException(
                            "keystore.properties 缺少 $key (四个键都必填, " +
                                "模板见 keystore.properties.example, 流程见 SIGNING.md)"
                        )
                storeFile = rootProject.file(prop("storeFile"))
                storePassword = prop("storePassword")
                keyAlias = prop("keyAlias")
                keyPassword = prop("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            // 混淆当前关闭 (出包即真机验收口径); proguard-rules.pro 已
            // 预置 JNI keep 规则, 日后开启 minify 不会破坏 external fun
            // 与 Java_com_magtile_studio_* 符号的静态匹配 (SIGNING.md 第四节)
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.findByName("release")
        }
    }

    buildFeatures {
        // BuildConfig.DEBUG 门控「模拟已订阅」QA 开关 (MainActivity.
        // toggleDevBilling, 仅 Debug 档可见; AGP 8 起默认不生成需显式开)
        buildConfig = true
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

// ---- Release 出包守卫: 无签名配置时给清晰错误, 不产未签名包 ----------
// 用 doFirst 而非 taskGraph.whenReady —— 后者与配置缓存不兼容
// (gradle.properties 已开启 org.gradle.configuration-cache)。
// preReleaseBuild 是 release 变体一切构建路径的最早前置, 挂它实现
// 快速失败 (报错在编译/原生构建之前); 三个生命周期任务兜底。
if (keystoreProps == null) {
    val guardedReleaseTasks =
        setOf("preReleaseBuild", "assembleRelease", "bundleRelease", "installRelease")
    tasks.configureEach {
        if (name in guardedReleaseTasks) {
            doFirst {
                throw GradleException(
                    """
                    Release 签名未配置: 缺少 platforms/android/keystore.properties (密钥不入库)。
                      1. 复制模板: cp keystore.properties.example keystore.properties
                      2. 按 SIGNING.md 生成 release keystore 并填入四个键
                         (storeFile / storePassword / keyAlias / keyPassword)
                      3. 重跑 ./gradlew :app:assembleRelease (或 :app:bundleRelease)
                    debug 构建不受影响: ./gradlew :app:assembleDebug 照常可用。
                    """.trimIndent()
                )
            }
        }
    }
}

// ---- 数据资产打包 (默认全库; -PmagtileAssets=starter 打入门子集) ------
//
// starter 模式 (可选, 面向轻量分发验证): 只打 30 个精选入门模型
// (platforms/windows/packaging/starter_models.txt, 与免费层选品一致,
// 详见 docs/FREE_TIER_MANIFEST.md) 及其缩略图, model_catalog.json 由
// stageStarterCatalog 任务过滤到同一子集 (否则目录会列出 APK 里
// 不存在的模型文件)。默认与 CI 均为全库, 行为不变。
val magtileAssetsMode = (project.findProperty("magtileAssets") as String?) ?: "full"
require(magtileAssetsMode == "full" || magtileAssetsMode == "starter") {
    "magtileAssets 只支持 full / starter, 收到: $magtileAssetsMode"
}
val starterModelIds: Set<String> =
    if (magtileAssetsMode == "starter") {
        rootProject.file("../windows/packaging/starter_models.txt").readLines()
            .map { it.trim() }
            .filter { it.isNotEmpty() && !it.startsWith("#") }
            .toSet()
    } else {
        emptySet()
    }

// starter 模式: 过滤 model_catalog.json 到入门子集 (保留 schema_version
// 等根字段与条目顺序; 非 starter 模式无人依赖此任务, 不会执行)。
val stageStarterCatalog = tasks.register("stageStarterCatalog") {
    description = "过滤 model_catalog.json 到 starter 入门模型子集"
    val source = rootProject.file("../../data/model_catalog.json")
    val output = layout.buildDirectory.file("magtile-starter/model_catalog.json")
    val ids = starterModelIds
    inputs.file(source)
    outputs.file(output)
    doLast {
        @Suppress("UNCHECKED_CAST")
        val root = groovy.json.JsonSlurper().parse(source) as MutableMap<String, Any?>
        @Suppress("UNCHECKED_CAST")
        val models = root["models"] as List<Map<String, Any?>>
        root["models"] = models.filter { (it["id"] as? String) in ids }
        val outFile = output.get().asFile
        outFile.parentFile.mkdirs()
        outFile.writeText(groovy.json.JsonOutput.toJson(root))
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
        if (magtileAssetsMode == "starter") {
            include("tile_catalog.json")
            starterModelIds.forEach { include("models/$it.json") }
        } else {
            include("tile_catalog.json", "model_catalog.json", "models/**")
        }
        into("data")
    }
    from(rootProject.layout.projectDirectory.dir("../../data/thumbnails")) {
        if (magtileAssetsMode == "starter") {
            starterModelIds.forEach { include("$it.png") }
        } else {
            include("*.png")
        }
        into("thumbnails")
    }
    if (magtileAssetsMode == "starter") {
        dependsOn(stageStarterCatalog)
        from(layout.buildDirectory.file("magtile-starter/model_catalog.json")) {
            into("data")
        }
    }
}
tasks.named("preBuild") { dependsOn(stageMagTileAssets) }

dependencies {
    // 模型卡片列表; 刻意不引 appcompat/material, 保持依赖面最小
    implementation("androidx.recyclerview:recyclerview:1.3.2")
}

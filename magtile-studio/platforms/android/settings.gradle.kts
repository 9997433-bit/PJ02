// =============================================================
// MagTile Studio - Android Gradle 工程入口
//
// 工程根目录即 platforms/android (不是仓库根): Android 构建自包含,
// 只通过 app 模块的 externalNativeBuild 与 assets 拷贝任务回引仓库根
// 的 C++ 核心与 data/ 资产。构建步骤见同目录 README.md。
// =============================================================

pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "magtile-studio-android"
include(":app")

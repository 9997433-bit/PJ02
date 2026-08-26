// 顶层构建脚本: 只声明插件版本, 具体配置在 app/build.gradle.kts。
// AGP 8.7 要求 Gradle >= 8.9 (wrapper 已固定 8.13) 与 JDK 17+。
plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
}

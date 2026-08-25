# =============================================================
# MagTile Studio - R8/ProGuard 最小 keep 规则
#
# release 当前未开启混淆 (build.gradle.kts isMinifyEnabled = false),
# 本文件已预先挂接进 release 档, 仅在日后开启时生效。
# 唯一的硬约束是 JNI: Kotlin 侧 external fun 与原生导出符号
# Java_com_magtile_studio_* 按「类全名 + 方法名」静态匹配
# (MainActivity / MagTileNative / TutorialSceneNative 三条链路,
# 符号全集见 .github/workflows/android.yml 的 ndk-so 断言),
# 任一侧被改名/裁剪都会在运行时抛 UnsatisfiedLinkError。
# 原生侧无 FindClass 反射回调 Kotlin, 无需额外 keep。
# =============================================================

# 保留全部含 native 方法的类 (类名参与 JNI 符号) 及其 native 方法
-keepclasseswithmembers class com.magtile.studio.** {
    native <methods>;
}

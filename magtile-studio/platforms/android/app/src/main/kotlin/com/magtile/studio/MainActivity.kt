package com.magtile.studio

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.widget.TextView

/**
 * MagTile Studio Android 壳 (脚手架)。
 *
 * 当前只做一件事: 打通 Kotlin -> JNI -> magtile_core 链路 —— 加载磁力片
 * 目录、跑一遍模型物理校验、读取教程步骤数, 并把结果显示在屏幕上。
 * 正式版将在此接入 GLSurfaceView / Vulkan 渲染循环与分步教程 UI。
 *
 * 依赖说明: 刻意只用 android.app.Activity (不引 AndroidX), 使本文件在
 * Gradle 工程搭好之前就能作为最小可编译的参考实现。Gradle 工程结构与
 * externalNativeBuild 配置见同目录 README.md。
 */
class MainActivity : Activity() {

    // ---- JNI 接口 (实现见 jni/magtile_jni.cpp) ----------------------
    /** 加载磁力片形状目录, 返回形状数量; 失败返回 -1。 */
    external fun loadCatalog(catalogPath: String): Int

    /** 加载模型 JSON 并执行完整物理校验, 返回中文校验摘要。 */
    external fun validateModel(jsonPath: String): String

    /** 最近一次成功加载模型的教程步骤数; 尚未加载返回 -1。 */
    external fun getTutorialStepCount(): Int

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 脚手架冒烟验证: data/ 资产需先由 assets 解包到 filesDir
        // (Gradle 工程接好后由启动逻辑完成, 见 README "数据资产" 一节)。
        val dataDir = filesDir.resolve("data")
        val text = try {
            val shapeCount = loadCatalog(
                dataDir.resolve("tile_catalog.json").absolutePath)
            val summary = validateModel(
                dataDir.resolve("models/castle_foundation_01.json").absolutePath)
            val stepCount = getTutorialStepCount()
            "磁力片形状数: $shapeCount\n$summary\n教程步骤数: $stepCount"
        } catch (t: Throwable) {
            Log.e(TAG, "原生层冒烟验证失败", t)
            "原生层调用失败: ${t.message}"
        }

        setContentView(TextView(this).apply { this.text = text })
    }

    companion object {
        private const val TAG = "MagTileMain"

        init {
            // 对应 platforms/android/CMakeLists.txt 产出的 libmagtile_core.so
            System.loadLibrary("magtile_core")
        }
    }
}

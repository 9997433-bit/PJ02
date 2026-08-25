package com.magtile.studio

import android.app.Activity
import android.app.AlertDialog
import android.os.Bundle
import android.util.Log
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import java.util.concurrent.Executors

/**
 * MagTile Studio Android 主界面: 模型库列表。
 *
 * 启动流程 (工作线程, 完成后回主线程刷新):
 *   1. DataAssetInstaller 把 APK assets/data 解包到 filesDir/data
 *      (版本戳一致时零拷贝);
 *   2. JNI loadCatalog() 加载磁力片形状目录;
 *   3. JNI listModels() 读取模型库目录, 解析为 ModelCard 列表。
 *
 * 点击卡片弹出详情: 简介 + 「教程即将上线」占位; 「物理校验」按钮按需
 * 加载模型并跑完整 R1~R8 校验, 展示中文摘要与教程步骤数。
 * 渲染循环 (GLSurfaceView / Vulkan) 与分步教程 UI 后续在此接入。
 */
class MainActivity : Activity() {

    // ---- JNI 接口 (实现见 jni/magtile_jni.cpp) ----------------------
    /** 加载磁力片形状目录, 返回形状数量; 失败返回 -1。 */
    external fun loadCatalog(catalogPath: String): Int

    /** 模型库目录 JSON: {"models":[...]} 或 {"error":"..."}。 */
    external fun listModels(dataDir: String): String

    /** 加载模型 JSON 并执行完整物理校验, 返回中文校验摘要。 */
    external fun validateModel(jsonPath: String): String

    /** 最近一次成功加载模型的教程步骤数; 尚未加载返回 -1。 */
    external fun getTutorialStepCount(): Int

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private lateinit var statusView: TextView
    private lateinit var adapter: ModelCardAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusView = findViewById(R.id.status)
        adapter = ModelCardAdapter(::showModelDialog)
        findViewById<RecyclerView>(R.id.model_list).apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = this@MainActivity.adapter
        }

        loadLibraryAsync()
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()
    }

    /** 解包资产 + 加载形状目录 + 拉取模型库, 全程不阻塞主线程。 */
    private fun loadLibraryAsync() {
        backgroundExecutor.execute {
            try {
                val dataDir = DataAssetInstaller.ensureInstalled(this)
                val shapeCount = loadCatalog(
                    dataDir.resolve("tile_catalog.json").absolutePath)
                check(shapeCount > 0) { "磁力片形状目录加载失败 (详见 logcat)" }
                val cards = ModelCard.listFromJson(
                    listModels(dataDir.absolutePath))

                runOnUiThread {
                    statusView.text =
                        getString(R.string.library_summary, cards.size, shapeCount)
                    adapter.submit(cards)
                }
            } catch (t: Throwable) {
                Log.e(TAG, "模型库加载失败", t)
                runOnUiThread {
                    statusView.text =
                        getString(R.string.library_load_failed, t.message ?: t.toString())
                }
            }
        }
    }

    /** 卡片详情: 简介 + 教程占位 + 按需物理校验入口。 */
    private fun showModelDialog(card: ModelCard) {
        val message = buildString {
            append(card.difficultyStars)
            append("  ")
            append(getString(R.string.card_pieces_steps, card.totalPieces, card.stepCount))
            if (card.theme.isNotBlank()) append("\n主题: ").append(card.theme)
            if (card.description.isNotBlank()) append("\n\n").append(card.description)
            append("\n\n").append(getString(R.string.dialog_tutorial_coming))
        }
        AlertDialog.Builder(this)
            .setTitle(card.name)
            .setMessage(message)
            .setPositiveButton(R.string.dialog_validate) { _, _ -> runValidation(card) }
            .setNegativeButton(R.string.dialog_close, null)
            .show()
    }

    /** 按需加载模型并跑完整物理校验 (R1~R8), 结果以对话框展示。 */
    private fun runValidation(card: ModelCard) {
        val progress = AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_validate_title, card.name))
            .setMessage(R.string.dialog_validating)
            .setCancelable(false)
            .show()

        backgroundExecutor.execute {
            val summary = try {
                val report = validateModel(card.filePath)
                val stepCount = getTutorialStepCount()
                if (stepCount >= 0) {
                    "$report\n\n${getString(R.string.dialog_step_count, stepCount)}"
                } else {
                    report
                }
            } catch (t: Throwable) {
                Log.e(TAG, "物理校验失败: ${card.id}", t)
                "校验失败: ${t.message}"
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                progress.dismiss()
                AlertDialog.Builder(this)
                    .setTitle(getString(R.string.dialog_validate_title, card.name))
                    .setMessage(summary)
                    .setPositiveButton(R.string.dialog_close, null)
                    .show()
            }
        }
    }

    companion object {
        private const val TAG = "MagTileMain"

        init {
            // 对应 platforms/android/CMakeLists.txt 产出的 libmagtile_core.so
            System.loadLibrary("magtile_core")
        }
    }
}

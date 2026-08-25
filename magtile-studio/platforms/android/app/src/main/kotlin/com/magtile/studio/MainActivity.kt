package com.magtile.studio

import android.app.Activity
import android.app.AlertDialog
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.CheckBox
import android.widget.Spinner
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import java.util.concurrent.Executors

/**
 * MagTile Studio Android 主界面: 模型库列表 + 筛选。
 *
 * 启动流程 (工作线程, 完成后回主线程刷新):
 *   1. DataAssetInstaller 把 APK assets/data 解包到 filesDir/data
 *      (版本戳一致时零拷贝; 缩略图在 assets/thumbnails, 不解包);
 *   2. JNI loadCatalog() 加载磁力片形状目录;
 *   3. JNI listModels() 读取模型库目录 (含逐模型 core-9 判定),
 *      解析为 ModelCard 列表。
 *
 * 筛选栏与桌面 GL/Qt 模型库同一套口径:
 *   - 难度: 星级精确匹配 (全部 / ★ ~ ★★★★★);
 *   - 主题: 规范主题 (目录 theme 字段, 缺省第一个标签/未分类);
 *   - 只用核心 9 片: 原生层 core::isCoreTile 共享判定 (目录 tier 优先),
 *     BOM 未知 (模型文件有问题) 的模型不进核心筛选。
 *
 * 点击卡片弹出详情: 简介 + 套装说明 + 「教程即将上线」占位; 「物理校验」
 * 按钮按需加载模型并跑完整 R1~R8 校验, 展示中文摘要与教程步骤数。
 * 渲染循环 (GLSurfaceView / Vulkan) 与分步教程 UI 后续在此接入。
 */
class MainActivity : Activity() {

    // ---- JNI 接口 (实现见 jni/magtile_jni.cpp) ----------------------
    /** 加载磁力片形状目录, 返回形状数量; 失败返回 -1。 */
    external fun loadCatalog(catalogPath: String): Int

    /** 模型库目录 JSON (含 core-9 判定): {"models":[...]} 或 {"error":"..."}。 */
    external fun listModels(dataDir: String): String

    /** 加载模型 JSON 并执行完整物理校验, 返回中文校验摘要。 */
    external fun validateModel(jsonPath: String): String

    /** 最近一次成功加载模型的教程步骤数; 尚未加载返回 -1。 */
    external fun getTutorialStepCount(): Int

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private lateinit var statusView: TextView
    private lateinit var emptyHint: TextView
    private lateinit var filterBar: View
    private lateinit var difficultySpinner: Spinner
    private lateinit var themeSpinner: Spinner
    private lateinit var core9CheckBox: CheckBox
    private lateinit var adapter: ModelCardAdapter

    /** 全量模型列表 (筛选不改动源数据)。 */
    private var allCards: List<ModelCard> = emptyList()
    private var shapeCount = 0

    // ---- 筛选状态 (口径与桌面 GL 一致) -------------------------------
    /** 0 = 全部难度, 1~5 = 星级精确匹配。 */
    private var difficultyFilter = 0
    /** 空 = 全部主题, 否则匹配卡片规范主题。 */
    private var themeFilter = ""
    /** 只显示 BOM 已知且只用核心 9 片型的模型。 */
    private var core9Filter = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusView = findViewById(R.id.status)
        emptyHint = findViewById(R.id.empty_hint)
        filterBar = findViewById(R.id.filter_bar)
        difficultySpinner = findViewById(R.id.filter_difficulty)
        themeSpinner = findViewById(R.id.filter_theme)
        core9CheckBox = findViewById(R.id.filter_core9)

        adapter = ModelCardAdapter(::showModelDialog)
        findViewById<RecyclerView>(R.id.model_list).apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = this@MainActivity.adapter
        }

        setUpFilterBar()
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
                val loadedShapes = loadCatalog(
                    dataDir.resolve("tile_catalog.json").absolutePath)
                check(loadedShapes > 0) { "磁力片形状目录加载失败 (详见 logcat)" }
                val cards = ModelCard.listFromJson(
                    listModels(dataDir.absolutePath))

                runOnUiThread {
                    shapeCount = loadedShapes
                    allCards = cards
                    populateThemeSpinner(cards)
                    filterBar.visibility = View.VISIBLE
                    applyFilters()
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

    // ---- 筛选 --------------------------------------------------------

    /** 难度下拉 (静态项) + core-9 勾选; 主题下拉在数据加载完成后填充。 */
    private fun setUpFilterBar() {
        val difficultyItems =
            listOf(getString(R.string.filter_all_difficulties),
                   "★", "★★", "★★★", "★★★★", "★★★★★")
        difficultySpinner.adapter = spinnerAdapter(difficultyItems)
        difficultySpinner.onItemSelectedListener = onSelected { position ->
            difficultyFilter = position   // 位置即星级 (0 = 全部)
            applyFilters()
        }

        core9CheckBox.setOnCheckedChangeListener { _, checked ->
            core9Filter = checked
            applyFilters()
        }
    }

    /** 主题候选: 规范主题按出现顺序去重 (与桌面 GL 候选构造方式一致)。 */
    private fun populateThemeSpinner(cards: List<ModelCard>) {
        val themes = cards.map { it.theme }.filter { it.isNotBlank() }.distinct()
        themeSpinner.adapter =
            spinnerAdapter(listOf(getString(R.string.filter_all_themes)) + themes)
        themeSpinner.onItemSelectedListener = onSelected { position ->
            themeFilter = if (position == 0) "" else themes[position - 1]
            applyFilters()
        }
    }

    /** 按当前筛选状态刷新列表、计数状态行与空态提示。 */
    private fun applyFilters() {
        if (allCards.isEmpty()) return  // 数据未加载完成 (spinner 初始回调)

        val filtered = allCards.filter { card ->
            (difficultyFilter == 0 || card.difficulty == difficultyFilter) &&
                (themeFilter.isEmpty() || card.theme == themeFilter) &&
                // BOM 未知的模型不进核心筛选 (与桌面 GL 同一降级策略)
                (!core9Filter || (card.bomKnown && card.core9Only))
        }
        adapter.submit(filtered)
        statusView.text = getString(
            R.string.library_summary, filtered.size, allCards.size, shapeCount)
        emptyHint.visibility = if (filtered.isEmpty()) View.VISIBLE else View.GONE
    }

    private fun spinnerAdapter(items: List<String>) =
        ArrayAdapter(this, android.R.layout.simple_spinner_item, items).apply {
            setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        }

    private fun onSelected(handler: (position: Int) -> Unit) =
        object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: AdapterView<*>?, view: View?, position: Int, id: Long) {
                handler(position)
            }
            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }

    // ---- 卡片详情与物理校验 -------------------------------------------

    /** 卡片详情: 简介 + 套装说明 + 教程占位 + 按需物理校验入口。 */
    private fun showModelDialog(card: ModelCard) {
        val message = buildString {
            append(card.difficultyStars)
            append("  ")
            append(getString(R.string.card_pieces_steps, card.totalPieces, card.stepCount))
            if (card.theme.isNotBlank()) append("\n主题: ").append(card.theme)
            // 套装说明 (BOM 未知时不显示, 与卡片角标同一口径)
            if (card.bomKnown) {
                append("\n")
                append(getString(
                    if (card.core9Only) R.string.dialog_core9_note
                    else R.string.dialog_expansion_note))
            }
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

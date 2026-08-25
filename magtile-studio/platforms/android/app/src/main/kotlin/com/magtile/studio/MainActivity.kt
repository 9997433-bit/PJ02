package com.magtile.studio

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
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
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

/**
 * MagTile Studio Android 主界面: 模型库列表 + 筛选。
 *
 * 启动流程 (工作线程, 完成后回主线程刷新):
 *   1. DataAssetInstaller 把 APK assets/data 解包到 filesDir/data
 *      (版本戳一致时零拷贝; 缩略图在 assets/thumbnails, 不解包);
 *   2. JNI loadCatalog() 加载磁力片形状目录;
 *   3. MagTileNative.openProgressStore() 打开进度存档
 *      (filesDir/progress.db, 与桌面同一 SQLite schema);
 *   4. JNI listModels() 读取模型库目录 (含逐模型 core-9 判定与
 *      库存已登记时的「我能搭的」判定), 解析为 ModelCard 列表。
 *
 * 筛选栏与桌面 GL/Qt 模型库同一套口径:
 *   - 难度: 星级精确匹配 (全部 / ★ ~ ★★★★★);
 *   - 主题: 规范主题 (目录 theme 字段, 缺省第一个标签/未分类);
 *   - 只用核心 9 片: 原生层 core::isCoreTile 共享判定 (目录 tier 优先),
 *     BOM 未知 (模型文件有问题) 的模型不进核心筛选;
 *   - 我能搭的: 库存对照 BOM (原生层 tile_inventory 表快照); 未登记
 *     库存时禁用并以「去登记 ▶」引导进 InventoryActivity 录入
 *     (引导而非报错, 不显示全空列表 —— 与桌面 GL 同策略)。
 *
 * 点击卡片弹出详情: 简介 + 套装说明 + 库存对照 (够搭 / 还差几片,
 * 「缺什么片?」按需展开清单) + 「教程即将上线」占位; 「物理校验」
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
    private lateinit var buildableCheckBox: CheckBox
    private lateinit var inventoryButton: TextView
    private lateinit var adapter: ModelCardAdapter

    /** 全量模型列表 (筛选不改动源数据)。 */
    private var allCards: List<ModelCard> = emptyList()
    private var shapeCount = 0
    /** 磁力片库存是否已登记 (含 0 数量的 "明确没有"; 未登记时
     *  「我能搭的」筛选禁用并引导录入)。 */
    private var inventoryConfigured = false

    // ---- 筛选状态 (口径与桌面 GL 一致) -------------------------------
    /** 0 = 全部难度, 1~5 = 星级精确匹配。 */
    private var difficultyFilter = 0
    /** 空 = 全部主题, 否则匹配卡片规范主题。 */
    private var themeFilter = ""
    /** 只显示 BOM 已知且只用核心 9 片型的模型。 */
    private var core9Filter = false
    /** 只显示库存足够搭建的模型 (库存未登记时恒 false)。 */
    private var buildableFilter = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusView = findViewById(R.id.status)
        emptyHint = findViewById(R.id.empty_hint)
        filterBar = findViewById(R.id.filter_bar)
        difficultySpinner = findViewById(R.id.filter_difficulty)
        themeSpinner = findViewById(R.id.filter_theme)
        core9CheckBox = findViewById(R.id.filter_core9)
        buildableCheckBox = findViewById(R.id.filter_buildable)
        inventoryButton = findViewById(R.id.filter_inventory)

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

    /** 解包资产 + 加载形状目录 + 打开进度存档 + 拉取模型库, 全程不阻塞主线程。 */
    private fun loadLibraryAsync() {
        backgroundExecutor.execute {
            try {
                val dataDir = DataAssetInstaller.ensureInstalled(this)
                val loadedShapes = loadCatalog(
                    dataDir.resolve("tile_catalog.json").absolutePath)
                check(loadedShapes > 0) { "磁力片形状目录加载失败 (详见 logcat)" }
                // 进度存档 (SQLite): 打开失败只降级 —— 库存/「我能搭的」
                // 不可用, 模型库照常可浏览 (P3 零挫败, 与桌面同策略)
                if (!MagTileNative.openProgressStore(
                        File(filesDir, PROGRESS_DB_NAME).absolutePath)) {
                    Log.w(TAG, "进度存档打开失败, 库存功能降级 (详见 logcat)")
                }
                val library = ModelCard.libraryFromJson(
                    listModels(dataDir.absolutePath))

                runOnUiThread {
                    shapeCount = loadedShapes
                    allCards = library.cards
                    inventoryConfigured = library.inventoryConfigured
                    populateThemeSpinner(library.cards)
                    updateInventoryUi()
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

    /**
     * 库存保存后的轻量刷新: 只重拉 listModels (重算 can_build),
     * 不重建主题下拉, 保留难度/主题/core-9 筛选状态。
     * @param enableBuildable true = 「保存, 看看我能搭什么」, 刷新后
     *        直接勾上「我能搭的」(与桌面录入页同一直达路径)。
     */
    private fun refreshLibraryAsync(enableBuildable: Boolean) {
        backgroundExecutor.execute {
            try {
                val dataDir = DataAssetInstaller.ensureInstalled(this)  // 版本戳一致零拷贝
                val library = ModelCard.libraryFromJson(
                    listModels(dataDir.absolutePath))
                runOnUiThread {
                    allCards = library.cards
                    inventoryConfigured = library.inventoryConfigured
                    updateInventoryUi()
                    if (enableBuildable && inventoryConfigured) {
                        buildableCheckBox.isChecked = true  // 监听器随之 applyFilters
                    }
                    applyFilters()
                }
            } catch (t: Throwable) {
                Log.e(TAG, "模型库刷新失败", t)
            }
        }
    }

    /** 库存录入屏返回: 保存成功 (RESULT_OK) 时刷新「我能搭的」数据。 */
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_INVENTORY && resultCode == RESULT_OK) {
            refreshLibraryAsync(enableBuildable = data?.getBooleanExtra(
                InventoryActivity.EXTRA_LOOK_WHAT_I_CAN_BUILD, false) == true)
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

        // "我能搭的": 依据磁力片库存过滤 BOM 满足的模型; 可用性由
        // updateInventoryUi() 按库存是否已登记切换 (未登记时禁用引导)
        buildableCheckBox.setOnCheckedChangeListener { _, checked ->
            buildableFilter = checked
            applyFilters()
        }
        inventoryButton.setOnClickListener {
            startActivityForResult(
                Intent(this, InventoryActivity::class.java), REQUEST_INVENTORY)
        }
    }

    /**
     * 「我能搭的」筛选可用性 (与桌面 GL 同策略): 库存已登记时可勾选,
     * 录入入口显示「改库存」; 未登记时禁用 (不显示全空列表), 入口
     * 显示「去登记 ▶」引导先录入。
     */
    private fun updateInventoryUi() {
        buildableCheckBox.isEnabled = inventoryConfigured
        if (!inventoryConfigured) {
            buildableCheckBox.isChecked = false  // 监听器将 buildableFilter 归 false
        }
        inventoryButton.text = getString(
            if (inventoryConfigured) R.string.filter_edit_inventory
            else R.string.filter_go_inventory)
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
                (!core9Filter || (card.bomKnown && card.core9Only)) &&
                // 「我能搭的」: 库存对照 BOM (BOM 未知的不进筛选)
                (!buildableFilter || card.canBuild)
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

    /** 卡片详情: 简介 + 套装说明 + 库存对照 + 教程占位 + 按需物理校验入口。 */
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
                // 库存对照 (登记过库存才显示; 未登记不提 "缺片", 引导在筛选栏)
                if (inventoryConfigured) {
                    append("\n")
                    append(getString(
                        if (card.canBuild) R.string.dialog_can_build
                        else R.string.dialog_missing_summary, card.missingTotal))
                }
            }
            if (card.description.isNotBlank()) append("\n\n").append(card.description)
            append("\n\n").append(getString(R.string.dialog_tutorial_coming))
        }
        val builder = AlertDialog.Builder(this)
            .setTitle(card.name)
            .setMessage(message)
            .setPositiveButton(R.string.dialog_validate) { _, _ -> runValidation(card) }
            .setNegativeButton(R.string.dialog_close, null)
        if (inventoryConfigured && card.bomKnown && !card.canBuild) {
            builder.setNeutralButton(R.string.dialog_whats_missing) { _, _ ->
                showMissingPieces(card)
            }
        }
        builder.show()
    }

    /** 缺片清单: JNI missingPiecesJson 按需加载 BOM 与库存对照。 */
    private fun showMissingPieces(card: ModelCard) {
        backgroundExecutor.execute {
            val text = try {
                val root = JSONObject(MagTileNative.missingPiecesJson(card.filePath))
                when {
                    root.has("error") -> root.getString("error")
                    root.optBoolean("can_build") ->
                        getString(R.string.dialog_can_build)
                    // 与桌面 Qt missingText 同一措辞: "缺 2 片正方形、1 片菱形"
                    else -> root.getString("text")
                }
            } catch (t: Throwable) {
                Log.e(TAG, "缺片清单加载失败: ${card.id}", t)
                getString(R.string.dialog_missing_failed)
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                AlertDialog.Builder(this)
                    .setTitle(getString(R.string.dialog_missing_title, card.name))
                    .setMessage(text)
                    .setPositiveButton(R.string.dialog_close, null)
                    .show()
            }
        }
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
        private const val REQUEST_INVENTORY = 1001

        /** 进度存档文件名 (filesDir 下; 与桌面同一 SQLite schema)。 */
        const val PROGRESS_DB_NAME = "progress.db"

        init {
            // 对应 platforms/android/CMakeLists.txt 产出的 libmagtile_core.so
            System.loadLibrary("magtile_core")
        }
    }
}

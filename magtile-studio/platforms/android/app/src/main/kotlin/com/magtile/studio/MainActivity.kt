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
 *   - 只看免费: 免费层模型 (原生层 core::isFreeTierModel 共享判定,
 *     目录 tags 含「免费」); 非免费模型照常可浏览, 详情弹窗以温和
 *     订阅提示替换「教程即将上线」占位 (不锁内容不催促);
 *   - 只用核心 9 片: 原生层 core::isCoreTile 共享判定 (目录 tier 优先),
 *     BOM 未知 (模型文件有问题) 的模型不进核心筛选;
 *   - 我能搭的: 库存对照 BOM (原生层 tile_inventory 表快照); 未登记
 *     库存时禁用并以「去登记 ▶」引导进 InventoryActivity 录入
 *     (引导而非报错, 不显示全空列表 —— 与桌面 GL 同策略)。
 *
 * 分龄 UI (UI_UX_SPEC.md §2, 与桌面 Qt LibraryPage 同一口径; 年龄段
 * 经 MagTileNative.ageModeId() 读进度存档 settings 表 age_mode 键,
 * 与桌面 GL/Qt/CLI 同键):
 *   4-6 启蒙  超大卡片 (大缩略图竖排 + 少文字), 只留主题筛选;
 *   7-9 标准  标准卡片, 难度 + 主题 + 只看免费 (库存录入入口保留);
 *   10+ 进阶  全量筛选 (难度/主题/免费/核心 9 片/我能搭的)。
 * 被收起的筛选维度同步清零 (applyAgeMode) —— 看不见的筛选绝不能
 * 悄悄过滤列表 (与 Qt collapseHiddenFilters 同一策略)。标题栏入口
 * 可切换档位, 立即生效并经 setAgeModeId 落盘。
 *
 * 家长门 (UI_UX_SPEC.md §9): 年龄段切换与库存录入都是家长操作,
 * 入口先过 ParentGateDialog (算术题 + 冷却, 复用 core::ParentGate
 * 共享状态机), 15 分钟会话守卫期内免重复验证; 「我的进度」保持
 * 儿童可达无门 (§5.3)。
 *
 * 点击卡片弹出详情: 简介 + 套装说明 + 库存对照 (够搭 / 还差几片,
 * 「缺什么片?」按需展开清单) + 免费模型「开始搭建」直达
 * TutorialActivity 分步教程 (非免费为温和订阅提示); 「物理校验」
 * 按钮按需加载模型并跑完整 R1~R8 校验, 展示中文摘要与教程步骤数。
 * 渲染循环 (GLSurfaceView / Vulkan) 与 3D 教程视口后续在此接入。
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
    private lateinit var freeCheckBox: CheckBox
    private lateinit var core9CheckBox: CheckBox
    private lateinit var buildableCheckBox: CheckBox
    private lateinit var inventoryButton: TextView
    private lateinit var ageModeButton: TextView
    private lateinit var adapter: ModelCardAdapter

    /** 全量模型列表 (筛选不改动源数据)。 */
    private var allCards: List<ModelCard> = emptyList()
    private var shapeCount = 0
    /** 磁力片库存是否已登记 (含 0 数量的 "明确没有"; 未登记时
     *  「我能搭的」筛选禁用并引导录入)。 */
    private var inventoryConfigured = false

    /** 进度页收藏行带回的待弹详情模型 id (列表加载完成后补弹)。 */
    private var pendingDetailModelId: String? = null

    // ---- 年龄段模式 (UI_UX_SPEC.md §2, 与桌面 settings 同键) ----------
    /** 当前年龄段模式标识 (启动时经 JNI 从进度存档读取, 默认 7-9 标准档)。 */
    private var ageModeId = AGE_7_9
    /** 4-6 启蒙模式: 超大卡片, 只留主题筛选。 */
    private val bandJunior get() = ageModeId == AGE_4_6
    /** 10+ 进阶模式: 全量筛选 (核心 9 片 / 我能搭的 仅此档可见)。 */
    private val bandFull get() = ageModeId == AGE_10_12

    // ---- 筛选状态 (口径与桌面 GL 一致) -------------------------------
    /** 0 = 全部难度, 1~5 = 星级精确匹配。 */
    private var difficultyFilter = 0
    /** 空 = 全部主题, 否则匹配卡片规范主题。 */
    private var themeFilter = ""
    /** 只显示免费层模型 (目录「免费」标签)。 */
    private var freeFilter = false
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
        freeCheckBox = findViewById(R.id.filter_free)
        core9CheckBox = findViewById(R.id.filter_core9)
        buildableCheckBox = findViewById(R.id.filter_buildable)
        inventoryButton = findViewById(R.id.filter_inventory)
        ageModeButton = findViewById(R.id.age_mode_button)
        // 年龄段切换是家长操作 (UI_UX_SPEC.md §9): 先过家长门 (算术题 +
        // 冷却, core::ParentGate 共享状态机), 通过后才弹三档选择;
        // 15 分钟会话守卫期内免重复验证 (与桌面 Qt 会话守卫同策略)
        ageModeButton.setOnClickListener {
            ParentGateDialog.requireParent(this) { showAgeModeDialog() }
        }

        // 进度页「我的作品」入口 (统计 + 作品列表 + 成就墙; 纯只读看板,
        // 返回后无需刷新模型库): 带 result 启动 —— 收藏行「点击直达
        // 详情」时进度页带模型 id 收屏返回, 本屏接力弹详情弹窗
        // (与桌面 Qt ProgressPage openModel 同路由, 免费判定/订阅
        // 提示留在详情一处)
        findViewById<TextView>(R.id.progress_button).setOnClickListener {
            startActivityForResult(
                Intent(this, ProgressActivity::class.java), REQUEST_PROGRESS)
        }

        adapter = ModelCardAdapter(::showModelDialog)
        findViewById<RecyclerView>(R.id.model_list).apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = this@MainActivity.adapter
        }

        setUpFilterBar()
        applyAgeMode()  // 先按默认档渲染标题栏入口, 存档档位读到后再套用
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
                // 年龄段 (settings 表 age_mode 键, 与桌面同键):
                // 存档打开失败 / 从未设置时原生层兜底返回默认档 7-9
                val storedAgeMode = MagTileNative.ageModeId()
                val library = ModelCard.libraryFromJson(
                    listModels(dataDir.absolutePath))

                runOnUiThread {
                    shapeCount = loadedShapes
                    allCards = library.cards
                    inventoryConfigured = library.inventoryConfigured
                    populateThemeSpinner(library.cards)
                    updateInventoryUi()
                    ageModeId = storedAgeMode
                    applyAgeMode()
                    filterBar.visibility = View.VISIBLE
                    applyFilters()
                    // 进度页收藏行的详情请求先于数据到达时在此补弹
                    pendingDetailModelId?.let {
                        pendingDetailModelId = null
                        openModelDetailById(it)
                    }
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
                    // 「我能搭的」筛选仅 10+ 进阶档可见: 其他档位不悄悄
                    // 开启被收起的筛选 (与 Qt collapseHiddenFilters 等效)
                    if (enableBuildable && inventoryConfigured && bandFull) {
                        buildableCheckBox.isChecked = true  // 监听器随之 applyFilters
                    }
                    applyFilters()
                }
            } catch (t: Throwable) {
                Log.e(TAG, "模型库刷新失败", t)
            }
        }
    }

    /** 库存录入屏返回: 保存成功 (RESULT_OK) 时刷新「我能搭的」数据;
     *  进度页返回: 收藏行带回模型 id 时接力弹详情弹窗。 */
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_INVENTORY && resultCode == RESULT_OK) {
            refreshLibraryAsync(enableBuildable = data?.getBooleanExtra(
                InventoryActivity.EXTRA_LOOK_WHAT_I_CAN_BUILD, false) == true)
        }
        if (requestCode == REQUEST_PROGRESS && resultCode == RESULT_OK) {
            data?.getStringExtra(ProgressActivity.RESULT_EXTRA_MODEL_ID)
                ?.takeIf { it.isNotBlank() }
                ?.let { openModelDetailById(it) }
        }
    }

    /**
     * 按模型 id 弹详情弹窗 (进度页收藏行「点击直达详情」的落点):
     * 列表尚未加载完 (进程重建后 result 先于数据到达) 先记下, 加载
     * 完成后补弹; 模型已下架 (不在当前目录中) 温和提示不崩溃。
     */
    private fun openModelDetailById(modelId: String) {
        if (allCards.isEmpty()) {
            pendingDetailModelId = modelId
            return
        }
        val card = allCards.find { it.id == modelId }
        if (card != null) {
            showModelDialog(card)
        } else {
            android.widget.Toast.makeText(
                this, R.string.progress_model_unavailable,
                android.widget.Toast.LENGTH_LONG).show()
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

        freeCheckBox.setOnCheckedChangeListener { _, checked ->
            freeFilter = checked
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
        // 库存录入同为家长操作 (登记家里的磁力片属数据维护, §9):
        // 入口过同一扇家长门, 会话守卫期内免重复验证
        inventoryButton.setOnClickListener {
            ParentGateDialog.requireParent(this) {
                startActivityForResult(
                    Intent(this, InventoryActivity::class.java), REQUEST_INVENTORY)
            }
        }
    }

    // ---- 分龄 UI (UI_UX_SPEC.md §2, 与桌面 Qt LibraryPage 同一口径) ---

    /**
     * 按当前年龄段收放筛选控件并切换卡片密度:
     *   4-6 启蒙  只留主题筛选 (难度/免费/核心 9 片/我能搭的/库存
     *             入口收起), 超大卡片;
     *   7-9 标准  难度 + 主题 + 只看免费 (库存录入入口保留,
     *             点击过家长门 §9), 标准卡片;
     *   10+ 进阶  全量筛选。
     * 被收起的筛选维度同步清零: 看不见的筛选绝不能悄悄过滤列表
     * (否则孩子面对被过滤的列表却没有任何入口能解除筛选,
     * 与 Qt collapseHiddenFilters 同一策略)。
     */
    private fun applyAgeMode() {
        ageModeButton.text = getString(when (ageModeId) {
            AGE_4_6 -> R.string.age_mode_badge_4_6
            AGE_10_12 -> R.string.age_mode_badge_10_12
            else -> R.string.age_mode_badge_7_9
        })
        difficultySpinner.visibility = if (bandJunior) View.GONE else View.VISIBLE
        freeCheckBox.visibility = if (bandJunior) View.GONE else View.VISIBLE
        core9CheckBox.visibility = if (bandFull) View.VISIBLE else View.GONE
        buildableCheckBox.visibility = if (bandFull) View.VISIBLE else View.GONE
        inventoryButton.visibility = if (bandJunior) View.GONE else View.VISIBLE

        // 被收起的维度清零 (直接归零筛选变量; 控件同步复位, 值未变时
        // 监听器不触发, 变了触发 applyFilters 也幂等)
        if (bandJunior) {
            if (difficultyFilter != 0) {
                difficultyFilter = 0
                difficultySpinner.setSelection(0)
            }
            freeFilter = false
            freeCheckBox.isChecked = false
        }
        if (!bandFull) {
            core9Filter = false
            core9CheckBox.isChecked = false
            buildableFilter = false
            buildableCheckBox.isChecked = false
        }
        adapter.junior = bandJunior
    }

    /** 三档单选对话框 (展示名对齐 core::displayNameZh); 家长门通过
     *  后由标题栏入口调起 (ParentGateDialog.requireParent)。 */
    private fun showAgeModeDialog() {
        val ids = listOf(AGE_4_6, AGE_7_9, AGE_10_12)
        val labels = arrayOf(
            getString(R.string.age_mode_4_6),
            getString(R.string.age_mode_7_9),
            getString(R.string.age_mode_10_12))
        AlertDialog.Builder(this)
            .setTitle(R.string.age_mode_dialog_title)
            .setSingleChoiceItems(labels, ids.indexOf(ageModeId)) { dialog, which ->
                dialog.dismiss()
                switchAgeMode(ids[which])
            }
            .setNegativeButton(R.string.dialog_close, null)
            .show()
    }

    /** 切换年龄段: 立即生效 (收放筛选 + 换卡片密度), 工作线程落盘。 */
    private fun switchAgeMode(newModeId: String) {
        if (newModeId == ageModeId) return
        ageModeId = newModeId
        applyAgeMode()
        applyFilters()
        // 落盘 (SQLite IO) 放工作线程; 失败只影响下次启动回读,
        // 本次运行已生效 (与桌面 SettingsBackend 同一温和降级)
        backgroundExecutor.execute { MagTileNative.setAgeModeId(newModeId) }
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
                // 「只看免费」: 免费层判定与桌面 CLI/GL/Qt 同一口径
                (!freeFilter || card.isFree) &&
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

    /** 卡片详情: 简介 + 套装说明 + 库存对照 + 「开始搭建」直达分步
     *  教程 (免费模型; 非免费为温和订阅提示) + 按需物理校验入口。 */
    private fun showModelDialog(card: ModelCard) {
        // 免费且有步骤数据 -> 「开始搭建」大按钮直达 TutorialActivity
        // (占位文案退场); 非免费保持温和订阅提示 (教程随订阅上线,
        // 浏览/校验不受限); 免费但无步骤 (数据缺失) 退回教程占位。
        val startable = card.isFree && card.stepCount > 0
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
            if (!startable) {
                append("\n\n").append(getString(
                    if (card.isFree) R.string.dialog_tutorial_coming
                    else R.string.dialog_subscription_note))
            }
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
        if (!startable) {
            builder.show()
            return
        }
        // 「开始搭建」以自定义视图挂在消息下方 (弹窗三个按钮位留给
        // 物理校验 / 缺什么片? / 关闭, 功能不减, 主行动更醒目)
        val startView = layoutInflater.inflate(R.layout.dialog_start_build, null)
        builder.setView(startView)
        val dialog = builder.show()
        startView.findViewById<View>(R.id.dialog_start_build).setOnClickListener {
            dialog.dismiss()
            startActivity(Intent(this, TutorialActivity::class.java)
                .putExtra(TutorialActivity.EXTRA_MODEL_ID, card.id)
                .putExtra(TutorialActivity.EXTRA_MODEL_NAME, card.name))
        }
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
        private const val REQUEST_PROGRESS = 1002

        /** 进度存档文件名 (filesDir 下; 与桌面同一 SQLite schema)。 */
        const val PROGRESS_DB_NAME = "progress.db"

        // 年龄段持久化标识 (与 core::AgeMode toString 一致, 持久化契约)
        private const val AGE_4_6 = "age_4_6"
        private const val AGE_7_9 = "age_7_9"
        private const val AGE_10_12 = "age_10_12"

        init {
            // 对应 platforms/android/CMakeLists.txt 产出的 libmagtile_core.so
            System.loadLibrary("magtile_core")
        }
    }
}

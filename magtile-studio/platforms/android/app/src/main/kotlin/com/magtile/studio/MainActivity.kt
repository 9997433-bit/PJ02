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
 *   10+ 进阶  紧凑卡片 + 全量筛选 (难度/主题/免费/核心 9 片/我能搭的)。
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
 * 「缺什么片?」按需展开清单) + 「开始搭建」直达 TutorialActivity
 * 分步教程; 「物理校验」按钮按需加载模型并跑完整 R1~R8 校验,
 * 展示中文摘要与教程步骤数。
 * 渲染循环 (GLSurfaceView / Vulkan) 与 3D 教程视口后续在此接入。
 *
 * 订阅与免费层锁 (COMMERCIAL_PLAN §2.1/§2.2, 与桌面 Qt DetailPage
 * 完全同口径): 解锁 = 模型属免费层 (is_free) 或 订阅有效
 * (billing::isContentUnlocked 单一判定); 未订阅的非免费模型只锁
 * 「开始搭建」入口 —— 简介/物理校验/浏览照常, 详情弹窗给温和的
 * 「订阅解锁」提示 (无价格无催促, 儿童侧零价格信息 §12.2); 订阅
 * 生效后全库直达教程。订阅状态经 MagTileNative.subscriptionActive()
 * 读进度存档 settings 表 (progress/subscription_settings 契约键,
 * 与桌面 BillingBackend 同键, 缺键/脏值按未订阅兜底宁可锁)。
 * Debug 构建另有「模拟已订阅」QA 开关 (家长门后的年龄段对话框内,
 * BuildConfig.DEBUG 恒 false 的 Release 档不可见), 与桌面订阅页
 * devControlsEnabled 开发开关同角色; 不接任何真实商店 SDK。
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
    private lateinit var libraryEmptyCard: View
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

    /** 订阅是否有效 (免费层锁口径, 与桌面 DetailPage 锁同源: 启动时
     *  经 JNI 读 progress/subscription_settings 契约键; 缺键/脏值/
     *  存档不可用一律 false —— 未订阅兜底, 宁可锁)。 */
    private var subscriptionActive = false

    /** 进度页收藏行带回的待弹详情模型 id (列表加载完成后补弹)。 */
    private var pendingDetailModelId: String? = null

    /** 减少动效 (§4.7, 系统动画设置联动): 列表点按反馈退为静态
     *  按压色、列表切换不做条目动画 (见 MotionPrefs)。 */
    private var reduceMotion = false

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

        reduceMotion = MotionPrefs.reduceMotion(this)

        statusView = findViewById(R.id.status)
        emptyHint = findViewById(R.id.empty_hint)
        libraryEmptyCard = findViewById(R.id.library_empty_card)
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
        adapter.reduceMotion = reduceMotion
        findViewById<RecyclerView>(R.id.model_list).apply {
            layoutManager = LinearLayoutManager(this@MainActivity)
            adapter = this@MainActivity.adapter
            // 减少动效: 列表全量替换/切档时不做条目淡入淡出 (§4.7)
            if (reduceMotion) itemAnimator = null
        }

        // 加载失败 / 空目录的温和空态「再试一次」(与桌面 Qt
        // studio.reload 同角色, 幂等可反复点)
        findViewById<View>(R.id.library_retry).setOnClickListener {
            retryLoadLibrary()
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
                // 订阅状态 (settings 表 subscription_active 键, 与桌面
                // BillingBackend 同键): 缺键/脏值/存档不可用按未订阅兜底
                val storedSubscription = MagTileNative.subscriptionActive()
                val library = ModelCard.libraryFromJson(
                    listModels(dataDir.absolutePath))

                runOnUiThread {
                    shapeCount = loadedShapes
                    allCards = library.cards
                    inventoryConfigured = library.inventoryConfigured
                    subscriptionActive = storedSubscription
                    // 目录打开但一个模型都没有 (数据资产异常): 0 个模型
                    // 不自称"已就绪", 走同一张温和空态卡 + 「再试一次」
                    // (与桌面 Qt 模型库空态同口径)
                    if (allCards.isEmpty()) {
                        statusView.text = getString(R.string.library_empty_catalog)
                        libraryEmptyCard.visibility = View.VISIBLE
                        return@runOnUiThread
                    }
                    libraryEmptyCard.visibility = View.GONE
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
                // 技术细节 (路径/异常) 只进 logcat 给家长/开发者;
                // 儿童侧是温和文案 + 「再试一次」大按钮 (§4.3 零挫败)
                Log.e(TAG, "模型库加载失败", t)
                runOnUiThread {
                    statusView.text = getString(R.string.library_soft_fail_status)
                    libraryEmptyCard.visibility = View.VISIBLE
                }
            }
        }
    }

    /** 空态「再试一次」: 收起空态卡回到加载中, 重跑整条启动链路
     *  (解包/开档/建目录均幂等, 反复点无副作用 —— 与桌面 Qt
     *  studio.reload 同角色)。 */
    private fun retryLoadLibrary() {
        libraryEmptyCard.visibility = View.GONE
        statusView.text = getString(R.string.library_loading)
        loadLibraryAsync()
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
        // 分龄卡片密度三档 (与 Qt LibraryPage 2 列超大 / 3~4 列标准 /
        // 4~5 列紧凑同一密度梯度): 4-6 超大 / 7-9 标准 / 10+ 紧凑
        adapter.density = when {
            bandJunior -> ModelCardAdapter.DENSITY_JUNIOR
            bandFull -> ModelCardAdapter.DENSITY_COMPACT
            else -> ModelCardAdapter.DENSITY_STANDARD
        }
    }

    /** 三档单选对话框 (展示名对齐 core::displayNameZh); 家长门通过
     *  后由标题栏入口调起 (ParentGateDialog.requireParent)。中性键
     *  「隐私与数据」进隐私面板 (同在家长门后, 与桌面家长中心一致);
     *  Debug 构建的正键为「模拟已订阅」QA 开关 (见 toggleDevBilling)。 */
    private fun showAgeModeDialog() {
        val ids = listOf(AGE_4_6, AGE_7_9, AGE_10_12)
        val labels = arrayOf(
            getString(R.string.age_mode_4_6),
            getString(R.string.age_mode_7_9),
            getString(R.string.age_mode_10_12))
        val builder = AlertDialog.Builder(this)
            .setTitle(R.string.age_mode_dialog_title)
            .setSingleChoiceItems(labels, ids.indexOf(ageModeId)) { dialog, which ->
                dialog.dismiss()
                switchAgeMode(ids[which])
            }
            .setNeutralButton(R.string.privacy_entry) { _, _ -> showPrivacyDialog() }
            .setNegativeButton(R.string.dialog_close, null)
        if (BuildConfig.DEBUG) {
            // 「模拟已订阅」QA 开关 (仅 Debug 构建; BuildConfig.DEBUG 为
            // 编译期常量, Release 档此分支不可达 —— 与桌面订阅页
            // devControlsEnabled 开发开关同角色同位置策略: 家长门后)。
            // 按钮标签描述将要执行的动作 (当前未订阅 -> 「开」)。
            builder.setPositiveButton(
                getString(if (subscriptionActive) R.string.dev_billing_turn_off
                          else R.string.dev_billing_turn_on)) { _, _ ->
                toggleDevBilling()
            }
        }
        builder.show()
    }

    /**
     * Debug 档「模拟已订阅」切换 (QA 用, 与桌面 FakeBillingClient::
     * devSetSubscribed 同口径): 打开时以年度主推档 sub_yearly 为模拟
     * 档位, 经 JNI 写 progress/subscription_settings 契约键落盘 ——
     * 与桌面同键, 存档跨端互认; 落盘失败不翻转界面解锁状态 (订阅
     * 权益以落盘为准), 只温和提示。不产生任何真实扣费。
     */
    private fun toggleDevBilling() {
        if (!BuildConfig.DEBUG) return  // Release 档误接线也改不了订阅状态
        val target = !subscriptionActive
        backgroundExecutor.execute {
            val persisted = try {
                MagTileNative.setSubscriptionActive(
                    target, if (target) DEV_BILLING_PRODUCT_ID else "")
            } catch (t: Throwable) {
                Log.e(TAG, "模拟订阅切换失败", t)
                false
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (persisted) {
                    subscriptionActive = target
                }
                android.widget.Toast.makeText(
                    this,
                    getString(when {
                        !persisted -> R.string.dev_billing_soft_fail
                        target -> R.string.dev_billing_on_toast
                        else -> R.string.dev_billing_off_toast
                    }),
                    android.widget.Toast.LENGTH_LONG).show()
            }
        }
    }

    // ---- 隐私与数据 (SECURITY_AND_PRIVACY.md §3/§4 C4/Z8, 家长门后;
    //      文案口径与桌面 Qt 家长中心「隐私与数据」区一致) ---------------

    /** 隐私面板: 我们收集什么 / 数据存在哪 (存档路径) / 隐私政策文档
     *  路径 + 「导出进度 (JSON)」与「清除本地数据」(带二次确认)。 */
    private fun showPrivacyDialog() {
        val dbPath = File(filesDir, PROGRESS_DB_NAME).absolutePath
        AlertDialog.Builder(this)
            .setTitle(R.string.privacy_dialog_title)
            .setMessage(getString(R.string.privacy_summary, dbPath))
            .setPositiveButton(R.string.privacy_export) { _, _ -> exportLocalData() }
            .setNeutralButton(R.string.privacy_clear) { _, _ -> confirmClearLocalData() }
            .setNegativeButton(R.string.dialog_close, null)
            .show()
    }

    /** 导出全部本地数据为 JSON 文件 (复用核心库导出, 与桌面同格式):
     *  写入应用专属外部目录 (无需任何权限, 家长可用文件管理器取走;
     *  外部存储不可用时退回 filesDir), 文件名带时间戳互不覆盖。 */
    private fun exportLocalData() {
        backgroundExecutor.execute {
            val result = try {
                val payload = MagTileNative.exportLocalDataJson()
                if (payload.startsWith("{\"error\"")) {
                    null
                } else {
                    val stamp = java.text.SimpleDateFormat(
                        "yyyyMMdd_HHmmss", java.util.Locale.US).format(java.util.Date())
                    val dir = getExternalFilesDir(null) ?: filesDir
                    File(dir, "magtile_export_$stamp.json").apply { writeText(payload) }
                }
            } catch (t: Throwable) {
                Log.e(TAG, "本地数据导出失败", t)
                null
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                android.widget.Toast.makeText(
                    this,
                    if (result != null) getString(R.string.privacy_export_done, result.absolutePath)
                    else getString(R.string.privacy_export_soft_fail),
                    android.widget.Toast.LENGTH_LONG).show()
            }
        }
    }

    /** 清除本地数据的二次确认 (入口已在家长门后, §6.1 数据操作):
     *  说清删什么 + 不可恢复 + 引导先导出; 「先不清除」为安全默认。 */
    private fun confirmClearLocalData() {
        AlertDialog.Builder(this)
            .setTitle(R.string.privacy_clear_confirm_title)
            .setMessage(R.string.privacy_clear_confirm_text)
            .setPositiveButton(R.string.privacy_clear_confirm_no, null)
            .setNegativeButton(R.string.privacy_clear_confirm_yes) { _, _ -> clearLocalData() }
            .show()
    }

    /** 执行清除 (单事务原子清空) 并温和回到首次状态: 年龄段回默认档、
     *  重拉模型库 (库存回未登记引导态), 只报结果不弹「失败」。 */
    private fun clearLocalData() {
        backgroundExecutor.execute {
            val cleared = try {
                MagTileNative.clearLocalData()
            } catch (t: Throwable) {
                Log.e(TAG, "本地数据清除失败", t)
                false
            }
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (cleared) {
                    // 温和回到首次状态: settings 已清空, 界面同步回默认档;
                    // 订阅状态同键被清 -> 回未订阅 (免费层锁恢复, 宁可锁)
                    ageModeId = AGE_7_9
                    subscriptionActive = false
                    applyAgeMode()
                    refreshLibraryAsync(enableBuildable = false)
                }
                android.widget.Toast.makeText(
                    this,
                    getString(if (cleared) R.string.privacy_clear_done
                              else R.string.privacy_clear_soft_fail),
                    android.widget.Toast.LENGTH_LONG).show()
            }
        }
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

    /** 卡片详情: 简介 + 预计用时 (§5.4, 步数未知隐藏) + 套装说明 +
     *  库存对照 + 「开始搭建」直达分步教程 (免费或订阅生效; 未订阅
     *  的非免费为温和订阅解锁提示) + 按需物理校验入口。 */
    private fun showModelDialog(card: ModelCard) {
        // 解锁口径与桌面 billing::isContentUnlocked / DetailPage 锁
        // 完全一致: 免费层 或 订阅有效 即解锁。已解锁且有步骤数据 ->
        // 「开始搭建」大按钮直达 TutorialActivity; 未订阅的非免费只锁
        // 这个入口 (浏览/校验不受限), 给温和的「订阅解锁」提示 (无
        // 价格无催促 §12.2); 已解锁但无步骤 (数据缺失) 退回教程占位。
        val unlocked = card.isFree || subscriptionActive
        val startable = unlocked && card.stepCount > 0
        // 预计用时 (UI_UX_SPEC §5.4, 与桌面 Qt DetailPage 同口径):
        // 原生层 core::estimateBuildMinutes 档位估算随 listModels 下发
        // (每步 1.5 分钟 + 每片 0.1 分钟归整到 5/10/15/20/30/45 分钟
        // 六档), 只说「大约 N 分钟」不假精确; 0 = 步数未知时整行隐藏;
        // 用时是信息不是门槛 —— 与缺片/订阅锁无关照常显示
        val estimateLine = if (card.estimatedMinutes > 0) {
            getString(R.string.dialog_estimated_minutes, card.estimatedMinutes)
        } else {
            ""
        }
        val message = buildString {
            append(card.difficultyStars)
            append("  ")
            append(getString(R.string.card_pieces_steps, card.totalPieces, card.stepCount))
            if (estimateLine.isNotEmpty()) append("\n").append(estimateLine)
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
                    if (unlocked) R.string.dialog_tutorial_coming
                    else R.string.dialog_subscription_note))
            }
        }
        // 预计用时行加粗 (与桌面 Qt font.bold 一致); 4-6 岁启蒙模式
        // 更大字 (分龄可读 §2, 对齐 Qt bandJunior 换 fontButton 大字号)
        val styledMessage: CharSequence = if (estimateLine.isEmpty()) message else {
            android.text.SpannableString(message).apply {
                val start = message.indexOf(estimateLine)
                val end = start + estimateLine.length
                setSpan(android.text.style.StyleSpan(android.graphics.Typeface.BOLD),
                        start, end, android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                if (bandJunior) {
                    setSpan(android.text.style.RelativeSizeSpan(1.4f),
                            start, end, android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
                }
            }
        }
        val builder = AlertDialog.Builder(this)
            .setTitle(card.name)
            .setMessage(styledMessage)
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

        /** Debug 档「模拟已订阅」写档的模拟档位: 年度主推 (与桌面
         *  FakeBillingClient::devSetSubscribed 同一档位约定)。 */
        private const val DEV_BILLING_PRODUCT_ID = "sub_yearly"

        init {
            // 对应 platforms/android/CMakeLists.txt 产出的 libmagtile_core.so
            System.loadLibrary("magtile_core")
        }
    }
}

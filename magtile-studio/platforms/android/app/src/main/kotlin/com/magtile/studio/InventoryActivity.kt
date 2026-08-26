package com.magtile.studio

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

/**
 * 磁力片库存录入屏 (对齐桌面 InventoryPage.qml 的字段与交互):
 * 全部片型中文名 + − / + 步进器 (48dp 触控目标, 长按连加) + 数量
 * 直接输入, 按 基础套装 (核心 9 片型) / 扩展包 分组; 「我的套装」
 * 多选胶囊 + 「填入数量」按盒装 BOM 预填 (UI_UX_SPEC §10.2)。
 *
 * 数据经 MagTileNative (JNI) 读写核心库 ProgressStore 的
 * tile_inventory 表 —— 与桌面 CLI / GL / Qt 同一份 SQLite schema,
 * 存档在 filesDir/progress.db。编辑副本只存界面, 「返回」不落盘
 * (温和, 不弹确认); 数量为 0 的片型也会记住「明确没有」。
 *
 * 保存成功后 setResult(RESULT_OK): MainActivity 据此刷新
 * 「我能搭的」筛选数据; 「保存, 看看我能搭什么」额外带
 * EXTRA_LOOK_WHAT_I_CAN_BUILD, 由 MainActivity 直接勾上该筛选。
 */
class InventoryActivity : Activity() {

    private val backgroundExecutor = Executors.newSingleThreadExecutor()
    private lateinit var totalBadge: TextView
    private lateinit var coreRows: LinearLayout
    private lateinit var expansionRows: LinearLayout
    private lateinit var setChips: LinearLayout
    private lateinit var applySetsButton: Button

    /** 片型 id -> 该行的数量输入框 (界面即编辑副本, 保存才落盘)。 */
    private val countInputs = LinkedHashMap<String, EditText>()

    /** 套装 id -> 多选胶囊 (勾选态 = 用户家里拥有该盒装)。 */
    private val setCheckboxes = LinkedHashMap<String, CheckBox>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_inventory)

        totalBadge = findViewById(R.id.inventory_total)
        coreRows = findViewById(R.id.inventory_core_rows)
        expansionRows = findViewById(R.id.inventory_expansion_rows)
        setChips = findViewById(R.id.inventory_set_chips)
        applySetsButton = findViewById(R.id.inventory_apply_sets)

        findViewById<TextView>(R.id.inventory_back).setOnClickListener { finish() }
        findViewById<Button>(R.id.inventory_save).setOnClickListener {
            saveAll(lookWhatICanBuild = false)
        }
        findViewById<Button>(R.id.inventory_save_match).setOnClickListener {
            saveAll(lookWhatICanBuild = true)
        }
        applySetsButton.setOnClickListener { applySelectedSets() }

        loadRowsAsync()
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()
    }

    /** 打开存档 + 拉取片型清单与套装目录 (工作线程), 回主线程搭建 UI。 */
    private fun loadRowsAsync() {
        backgroundExecutor.execute {
            // 独立打开存档: 即使从进程重建直达本屏 (未经 MainActivity
            // 启动流程) 也能读写; 原生上下文是进程级单例, 重复打开无害。
            MagTileNative.openProgressStore(
                File(filesDir, MainActivity.PROGRESS_DB_NAME).absolutePath)
            val dataDir = DataAssetInstaller.ensureInstalled(this).absolutePath
            val payload = MagTileNative.inventoryRows()
            val setsPayload = MagTileNative.physicalSetRows(dataDir)
            val ownedPayload = MagTileNative.ownedPhysicalSetsJson()
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                buildRows(payload)
                buildSetChips(setsPayload, ownedPayload)
            }
        }
    }

    /** 按 inventoryRows() JSON 逐片型建行, 核心 9 片在前 (枚举顺序)。 */
    private fun buildRows(payload: String) {
        val shapes = JSONObject(payload).getJSONArray("shapes")
        val inflater = LayoutInflater.from(this)
        for (index in 0 until shapes.length()) {
            val shape = shapes.getJSONObject(index)
            val expansion = shape.getBoolean("expansion")
            val container = if (expansion) expansionRows else coreRows
            val row = inflater.inflate(R.layout.item_inventory_row, container, false)

            row.findViewById<TextView>(R.id.shape_name).text = shape.getString("name_zh")
            val input = row.findViewById<EditText>(R.id.count_input)
            input.setText(shape.getInt("count").toString())
            input.setOnFocusChangeListener { _, hasFocus ->
                if (!hasFocus) applyCount(input, currentCount(input))  // 失焦夹到 0..999
            }

            setUpStepper(row.findViewById(R.id.count_minus)) {
                applyCount(input, currentCount(input) - 1)
            }
            setUpStepper(row.findViewById(R.id.count_plus)) {
                applyCount(input, currentCount(input) + 1)
            }

            countInputs[shape.getString("id")] = input
            container.addView(row)
        }
        refreshTotal()
    }

    /** 搭建「我的套装」多选胶囊, 恢复上次勾选的拥有清单。 */
    private fun buildSetChips(setsPayload: String, ownedPayload: String) {
        setChips.removeAllViews()
        setCheckboxes.clear()

        val setsRoot = JSONObject(setsPayload)
        if (setsRoot.has("error")) {
            // 套装目录不可用: 隐藏整块, 不影响逐片型录入 (P3 零挫败)
            setChips.visibility = View.GONE
            applySetsButton.visibility = View.GONE
            return
        }

        val ownedIds = mutableSetOf<String>()
        val ownedRoot = JSONObject(ownedPayload)
        val ownedArray = ownedRoot.optJSONArray("ids") ?: JSONArray()
        for (i in 0 until ownedArray.length()) {
            ownedIds.add(ownedArray.getString(i))
        }

        val sets = setsRoot.getJSONArray("sets")
        if (sets.length() == 0) {
            setChips.visibility = View.GONE
            applySetsButton.visibility = View.GONE
            return
        }

        val chipMargin = resources.getDimensionPixelSize(R.dimen.spacing_small)
        for (index in 0 until sets.length()) {
            val set = sets.getJSONObject(index)
            val setId = set.getString("id")
            val label = set.optString(
                "ui_preset_label_zh",
                set.optString("name_zh", setId))
            val chip = CheckBox(this).apply {
                text = label
                isChecked = ownedIds.contains(setId)
                minHeight = resources.getDimensionPixelSize(R.dimen.touch_target)
                minWidth = resources.getDimensionPixelSize(R.dimen.touch_target)
                setTextColor(resources.getColorStateList(R.color.set_chip_text, theme))
                buttonDrawable = null  // 纯胶囊外观, 不用系统勾选框
                background = resources.getDrawable(R.drawable.bg_set_chip, theme)
                setPadding(
                    resources.getDimensionPixelSize(R.dimen.spacing),
                    resources.getDimensionPixelSize(R.dimen.spacing_small),
                    resources.getDimensionPixelSize(R.dimen.spacing),
                    resources.getDimensionPixelSize(R.dimen.spacing_small))
                setOnCheckedChangeListener { button, checked ->
                    button.background = resources.getDrawable(
                        if (checked) R.drawable.bg_set_chip_checked
                        else R.drawable.bg_set_chip,
                        theme)
                }
                // 初始选中态背景
                background = resources.getDrawable(
                    if (isChecked) R.drawable.bg_set_chip_checked
                    else R.drawable.bg_set_chip,
                    theme)
            }
            val params = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT)
            if (index > 0) params.marginStart = chipMargin
            setChips.addView(chip, params)
            setCheckboxes[setId] = chip
        }
    }

    /** 合并选中套装 BOM, 预填片型计数 (不自动 saveInventory)。 */
    private fun applySelectedSets() {
        val selectedIds = JSONArray()
        setCheckboxes.forEach { (setId, chip) ->
            if (chip.isChecked) selectedIds.put(setId)
        }

        applySetsButton.isEnabled = false
        backgroundExecutor.execute {
            val dataDir = DataAssetInstaller.ensureInstalled(this).absolutePath
            val result = MagTileNative.applyPhysicalSets(dataDir, selectedIds.toString())
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                applySetsButton.isEnabled = true
                val root = JSONObject(result)
                if (root.has("error")) {
                    Toast.makeText(
                        this, R.string.inventory_sets_soft_fail, Toast.LENGTH_LONG).show()
                    return@runOnUiThread
                }
                val counts = root.getJSONObject("counts")
                counts.keys().forEach { shapeId ->
                    countInputs[shapeId]?.let { input ->
                        applyCount(input, counts.getInt(shapeId))
                    }
                }
                refreshTotal()
                Toast.makeText(
                    this, R.string.inventory_sets_applied_toast, Toast.LENGTH_SHORT).show()
            }
        }
    }

    // ---- 计数编辑 ------------------------------------------------------

    private fun currentCount(input: EditText): Int =
        input.text.toString().toIntOrNull() ?: 0

    private fun applyCount(input: EditText, value: Int) {
        input.setText(value.coerceIn(0, COUNT_MAX).toString())
        refreshTotal()
    }

    private fun refreshTotal() {
        val total = countInputs.values.sumOf { currentCount(it) }
        totalBadge.text = getString(R.string.inventory_total_badge, total)
    }

    /**
     * 步进器: 单击 ±1, 长按连加/连减 (80ms 间隔, 与桌面 autoRepeat
     * 节奏一致), 抬手/取消即停。
     */
    @SuppressLint("ClickableViewAccessibility")  // onTouch 只旁路停止连加, 点击语义不变
    private fun setUpStepper(button: Button, step: () -> Unit) {
        var repeater: Runnable? = null
        button.setOnClickListener { step() }
        button.setOnLongClickListener {
            val runnable = object : Runnable {
                override fun run() {
                    step()
                    button.postDelayed(this, STEPPER_REPEAT_MS)
                }
            }
            repeater = runnable
            button.postDelayed(runnable, STEPPER_REPEAT_MS)
            true
        }
        button.setOnTouchListener { view, event ->
            if (event.actionMasked == MotionEvent.ACTION_UP ||
                event.actionMasked == MotionEvent.ACTION_CANCEL
            ) {
                repeater?.let(view::removeCallbacks)
                repeater = null
            }
            false  // 不消费事件, 点击/长按照常分发
        }
    }

    // ---- 保存 ----------------------------------------------------------

    /** 收集完整快照 (含 0 数量) 落盘; 成功回传结果并关屏。 */
    private fun saveAll(lookWhatICanBuild: Boolean) {
        val counts = JSONObject()
        countInputs.forEach { (shapeId, input) ->
            counts.put(shapeId, currentCount(input).coerceIn(0, COUNT_MAX))
        }
        val total = countInputs.values.sumOf { currentCount(it) }

        backgroundExecutor.execute {
            val saved = MagTileNative.saveInventory(counts.toString())
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                if (!saved) {
                    // P3 零挫败: 存档暂不可用时温和提示, 不弹 "失败"
                    Toast.makeText(
                        this, R.string.inventory_save_soft_fail, Toast.LENGTH_LONG).show()
                    return@runOnUiThread
                }
                Toast.makeText(
                    this,
                    getString(R.string.inventory_saved_toast, total),
                    Toast.LENGTH_SHORT).show()
                setResult(RESULT_OK, Intent().putExtra(
                    EXTRA_LOOK_WHAT_I_CAN_BUILD, lookWhatICanBuild))
                finish()
            }
        }
    }

    companion object {
        /** 结果附加项: true = 「保存, 看看我能搭什么」(直接勾上筛选)。 */
        const val EXTRA_LOOK_WHAT_I_CAN_BUILD = "look_what_i_can_build"

        /** 与桌面录入界面一致的数量上限 (存储层只校验 >= 0)。 */
        private const val COUNT_MAX = 999
        private const val STEPPER_REPEAT_MS = 80L
    }
}

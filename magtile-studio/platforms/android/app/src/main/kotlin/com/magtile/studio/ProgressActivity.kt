package com.magtile.studio

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

/**
 * 进度页「我的作品」(对齐桌面 Qt ProgressPage 的信息层级与口径):
 * 三格温和统计 (已完成/进行中/收藏) + 成就墙条带 (点亮数 + 全览入口)
 * + 进行中列表 (进度条 + 第 x/y 步 + 用时) + 已完成列表 (完成日期
 * 与用时 + 片数) + 我的收藏; 空态温和引导去模型库 (§4.3: 只有正向
 * 与中性反馈, 没有分数没有排名)。
 *
 * 数据经 MagTileNative.progressOverviewJson (JNI) 读核心库
 * ProgressStore —— 与桌面 CLI `progress list` / GL / Qt 同一份
 * SQLite 存档 (filesDir/progress.db)。本屏纯只读不写档。
 *
 * 作品行路由 (对齐桌面 Qt StudioBackend::startBuild 口径):
 *   - 进行中「继续搭建」直达 TutorialActivity 断点续搭 (教程页自读
 *     savedTutorialStep, 视口停在上次的当前步);
 *   - 已完成「再搭一次」带 EXTRA_RESTART 从头开始 —— 已完成的存档值
 *     为总步数, 不从头会直接落在末步完成态 (桌面同理由); 完成时刻
 *     存储层只记首次, 重搭不丢已完成徽标;
 *   - 收藏与桌面同为「点击直达详情」: 详情弹窗在模型库 (MainActivity),
 *     经 activity result 带模型 id 返回并弹出 —— 免费判定/订阅提示
 *     留在详情一处, 本屏保持儿童可达无家长门 (§5.3)。
 * 教程页返回后 onResume 重拉总览 (进度条/统计即时跟上新进度)。
 * 行对应模型已下架时: 教程页温和提示 (不崩溃), 详情路由由模型库
 * 侧温和提示; 空态引导保持不变。
 */
class ProgressActivity : Activity() {

    private val backgroundExecutor = Executors.newSingleThreadExecutor()

    /** 首次 onResume 跳过重拉 (onCreate 已加载)。 */
    private var firstResume = true

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_progress)

        findViewById<TextView>(R.id.progress_back).setOnClickListener { finish() }
        findViewById<View>(R.id.badge_strip).setOnClickListener {
            startActivity(Intent(this, AchievementsActivity::class.java))
        }
        // 「去模型库挑一个」: 模型库即主界面, 关屏即回 (温和引导 §4.3)
        findViewById<Button>(R.id.empty_go_library).setOnClickListener { finish() }

        loadOverviewAsync()
    }

    /** 从教程页返回时重拉总览 (进度条/统计即时跟上新进度); 首次
     *  onResume 紧跟 onCreate 的加载, 跳过避免重复 IO。 */
    override fun onResume() {
        super.onResume()
        if (firstResume) {
            firstResume = false
            return
        }
        loadOverviewAsync()
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()
    }

    /** 打开存档 + 拉取进度总览 (工作线程), 回主线程渲染。 */
    private fun loadOverviewAsync() {
        backgroundExecutor.execute {
            try {
                // 独立打开存档: 即使从进程重建直达本屏 (未经 MainActivity
                // 启动流程) 也能读; 原生上下文是进程级单例, 重复打开无害。
                MagTileNative.openProgressStore(
                    File(filesDir, MainActivity.PROGRESS_DB_NAME).absolutePath)
                val dataDir = DataAssetInstaller.ensureInstalled(this)  // 版本戳一致零拷贝
                val root = JSONObject(
                    MagTileNative.progressOverviewJson(dataDir.absolutePath))
                check(!root.has("error")) { root.getString("error") }
                runOnUiThread {
                    if (isFinishing || isDestroyed) return@runOnUiThread
                    render(root)
                }
            } catch (t: Throwable) {
                Log.e(TAG, "进度看板加载失败", t)
                runOnUiThread {
                    if (isFinishing || isDestroyed) return@runOnUiThread
                    findViewById<TextView>(R.id.progress_status).text =
                        getString(R.string.progress_load_failed, t.message ?: t.toString())
                }
            }
        }
    }

    // ---- 渲染 ----------------------------------------------------------

    private fun render(root: JSONObject) {
        // 状态行: 正常时隐藏; 存档不可用时温和提示 (页面照常可看, P3)
        findViewById<TextView>(R.id.progress_status).apply {
            if (root.optBoolean("store_ready", false)) {
                visibility = View.GONE
            } else {
                text = getString(R.string.progress_store_unavailable)
            }
        }

        // 三格温和统计 (图形 + 数字 + 文字三重编码 §4.7)
        findViewById<TextView>(R.id.stat_completed).text =
            getString(R.string.progress_stat_completed, root.optInt("completed_count"))
        findViewById<TextView>(R.id.stat_in_progress).text =
            getString(R.string.progress_stat_in_progress, root.optInt("in_progress_count"))
        findViewById<TextView>(R.id.stat_favorites).text =
            getString(R.string.progress_stat_favorites, root.optInt("favorite_count"))

        // 成就墙条带: 只报喜不催促 (§4.3, 0 枚时不显示 "0" 这类扫兴数字)
        val badgeCount = root.optInt("achievement_count")
        findViewById<TextView>(R.id.badge_strip_summary).text =
            if (badgeCount > 0) getString(R.string.progress_badge_strip_some, badgeCount)
            else getString(R.string.progress_badge_strip_none)

        val inProgress = root.getJSONArray("in_progress")
        val completed = root.getJSONArray("completed")
        val favorites = root.getJSONArray("favorites")

        // 温和空态: 进行中与已完成都为空时显示引导 (收藏不算作品)
        findViewById<View>(R.id.empty_card).visibility =
            if (inProgress.length() == 0 && completed.length() == 0) View.VISIBLE
            else View.GONE

        bindSection(R.id.section_in_progress,
                    R.string.progress_section_in_progress, inProgress.length())
        bindSection(R.id.section_completed,
                    R.string.progress_section_completed, completed.length())
        bindSection(R.id.section_favorites,
                    R.string.progress_section_favorites, favorites.length())

        renderRows(inProgress, R.id.rows_in_progress) { item, row ->
            row.findViewById<TextView>(R.id.row_icon).apply {
                text = "▶"
                setTextColor(getColor(R.color.magtile_primary))
            }
            // 进度条: 图形 + "第 x/y 步" 文字双编码 (§4.7)
            val currentStep = item.getInt("current_step")
            val stepCount = item.getInt("step_count")
            row.findViewById<ProgressBar>(R.id.row_progress).apply {
                visibility = View.VISIBLE
                max = maxOf(stepCount, 1)
                progress = currentStep.coerceIn(0, max)
            }
            setMeta(row, listOf(
                getString(R.string.progress_step_of, currentStep, stepCount),
                item.optString("play_text")))
            // 断点续搭: 教程页自读 savedTutorialStep, 视口停在上次当前步
            setAction(row, R.string.progress_row_continue, R.color.magtile_primary)
            row.setOnClickListener {
                openTutorial(item, restartFromBeginning = false)
            }
        }

        renderRows(completed, R.id.rows_completed) { item, row ->
            row.findViewById<TextView>(R.id.row_icon).apply {
                text = "✓"
                setTextColor(getColor(R.color.magtile_success))
            }
            // "8月20日 完成 · 用时 23 分钟 · 75 片" (meta 措辞来自原生层,
            // 与桌面 completedList 一致; 片数与 Qt 进度页同样补在行尾)
            val pieces = item.optInt("pieces")
            setMeta(row, listOf(
                item.optString("meta_text"),
                if (pieces > 0) getString(R.string.progress_pieces, pieces) else ""))
            // 「再搭一次」从头开始 (桌面 Qt startBuild 同口径: 已完成的
            // 存档值为总步数, 不从头会直接落在末步完成态; 完成时刻存储层
            // 只记首次, 重搭不丢 ✓ 已完成徽标)
            setAction(row, R.string.progress_row_rebuild, R.color.magtile_success)
            row.setOnClickListener {
                openTutorial(item, restartFromBeginning = true)
            }
        }

        renderRows(favorites, R.id.rows_favorites) { item, row ->
            row.findViewById<TextView>(R.id.row_icon).apply {
                text = "⭐"
                setTextColor(getColor(R.color.magtile_warning))
            }
            // 收藏与桌面同为「点击直达详情」(免费判定/订阅提示留在详情):
            // 详情弹窗在模型库, 带模型 id 收屏返回, MainActivity 接力弹出
            row.setOnClickListener {
                val modelId = item.optString("id")
                if (modelId.isBlank()) return@setOnClickListener
                setResult(RESULT_OK,
                          Intent().putExtra(RESULT_EXTRA_MODEL_ID, modelId))
                finish()
            }
        }

        findViewById<View>(R.id.progress_body).visibility = View.VISIBLE
    }

    /** 分区标题: 有内容才显示 "▶ 进行中 (N)" 式标题行。 */
    private fun bindSection(viewId: Int, template: Int, count: Int) {
        findViewById<TextView>(viewId).apply {
            visibility = if (count > 0) View.VISIBLE else View.GONE
            text = getString(template, count)
        }
    }

    /** 逐条 inflate 列表行: 模型名统一绑定, 其余交给 bind 定制。 */
    private fun renderRows(
        items: JSONArray, containerId: Int, bind: (JSONObject, View) -> Unit) {
        val container = findViewById<LinearLayout>(containerId)
        container.removeAllViews()
        val inflater = LayoutInflater.from(this)
        for (index in 0 until items.length()) {
            val item = items.getJSONObject(index)
            val row = inflater.inflate(R.layout.item_progress_row, container, false)
            row.findViewById<TextView>(R.id.row_name).text = item.getString("name")
            bind(item, row)
            container.addView(row)
        }
    }

    /** 元信息行: 空片段跳过, " · " 相接; 全空则整行隐藏 (不显示空壳)。 */
    private fun setMeta(row: View, parts: List<String>) {
        val text = parts.filter { it.isNotBlank() }.joinToString(" · ")
        row.findViewById<TextView>(R.id.row_meta).apply {
            visibility = if (text.isEmpty()) View.GONE else View.VISIBLE
            this.text = text
        }
    }

    /** 行尾动作标签 ("继续搭建 ▶" 主色 / "再搭一次 ▶" 完成绿, 与桌面
     *  Qt ProgressPage 行尾同款; 整行可点, 标签只作视觉引导)。 */
    private fun setAction(row: View, template: Int, colorRes: Int) {
        row.findViewById<TextView>(R.id.row_action).apply {
            visibility = View.VISIBLE
            text = getString(template)
            setTextColor(getColor(colorRes))
        }
    }

    /** 作品行直达教程 (id 为空的脏数据行只当展示, 不响应)。 */
    private fun openTutorial(item: JSONObject, restartFromBeginning: Boolean) {
        val modelId = item.optString("id")
        if (modelId.isBlank()) return
        startActivity(Intent(this, TutorialActivity::class.java)
            .putExtra(TutorialActivity.EXTRA_MODEL_ID, modelId)
            .putExtra(TutorialActivity.EXTRA_MODEL_NAME, item.optString("name"))
            .putExtra(TutorialActivity.EXTRA_RESTART, restartFromBeginning))
    }

    companion object {
        private const val TAG = "MagTileProgress"

        /** activity result 附加项: 请模型库弹出该模型的详情弹窗
         *  (收藏行点击直达详情, 与桌面 Qt ProgressPage openModel 同路由)。 */
        const val RESULT_EXTRA_MODEL_ID = "open_model_id"
    }
}

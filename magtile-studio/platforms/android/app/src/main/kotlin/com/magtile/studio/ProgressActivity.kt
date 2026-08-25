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
 * SQLite 存档 (filesDir/progress.db)。本屏纯只读不写档; 行目前仅作
 * 展示, 「继续搭建/再搭一次」直达教程待分步教程 UI 落地后接入
 * (与卡片详情「教程即将上线」同一占位口径)。
 */
class ProgressActivity : Activity() {

    private val backgroundExecutor = Executors.newSingleThreadExecutor()

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
        }

        renderRows(favorites, R.id.rows_favorites) { item, row ->
            row.findViewById<TextView>(R.id.row_icon).apply {
                text = "⭐"
                setTextColor(getColor(R.color.magtile_warning))
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

    companion object {
        private const val TAG = "MagTileProgress"
    }
}

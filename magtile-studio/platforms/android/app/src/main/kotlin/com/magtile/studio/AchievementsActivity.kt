package com.magtile.studio

import android.app.Activity
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.widget.LinearLayout
import android.widget.Space
import android.widget.TextView
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

/**
 * 成就墙全览 (对齐桌面 Qt AchievementsPage, UI_UX_SPEC.md §7.1):
 * 徽章卡片两列网格 —— 已点亮 = 完成绿卡 + ✓ + 解锁日期; 未点亮 =
 * 灰色剪影 + 一句话达成条件 (不显示进度百分比, 防焦虑)。成就只与
 * 搭建行为挂钩 (§4.5, 按完成模型数 1/3/10/30 分档), 页脚只报喜
 * 不催促 (§4.3)。
 *
 * 数据与进度页同一个 JNI 入口 (MagTileNative.progressOverviewJson,
 * 口径与桌面 studio.achievementsList() 一致); 存档不可用时徽章全部
 * 未点亮但页面照常可看 (P3 零挫败)。
 */
class AchievementsActivity : Activity() {

    private val backgroundExecutor = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_achievements)

        findViewById<TextView>(R.id.achievements_back).setOnClickListener { finish() }
        loadBadgesAsync()
    }

    override fun onDestroy() {
        super.onDestroy()
        backgroundExecutor.shutdown()
    }

    /** 打开存档 + 拉取徽章墙 (工作线程), 回主线程搭建网格。 */
    private fun loadBadgesAsync() {
        backgroundExecutor.execute {
            try {
                // 独立打开存档: 直达本屏也能读 (进程级单例, 重复打开无害)
                MagTileNative.openProgressStore(
                    File(filesDir, MainActivity.PROGRESS_DB_NAME).absolutePath)
                val dataDir = DataAssetInstaller.ensureInstalled(this)
                val root = JSONObject(
                    MagTileNative.progressOverviewJson(dataDir.absolutePath))
                check(!root.has("error")) { root.getString("error") }
                runOnUiThread {
                    if (isFinishing || isDestroyed) return@runOnUiThread
                    render(root)
                }
            } catch (t: Throwable) {
                Log.e(TAG, "成就墙加载失败", t)
                runOnUiThread {
                    if (isFinishing || isDestroyed) return@runOnUiThread
                    findViewById<TextView>(R.id.achievements_footer).text =
                        getString(R.string.progress_load_failed, t.message ?: t.toString())
                }
            }
        }
    }

    // ---- 渲染 ----------------------------------------------------------

    private fun render(root: JSONObject) {
        val badges = root.getJSONArray("achievements")
        val rows = findViewById<LinearLayout>(R.id.badge_rows)
        rows.removeAllViews()
        val inflater = LayoutInflater.from(this)

        var currentRow: LinearLayout? = null
        for (index in 0 until badges.length()) {
            if (index % COLUMNS == 0) {
                currentRow = LinearLayout(this).apply {
                    orientation = LinearLayout.HORIZONTAL
                    layoutParams = LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                    ).apply { topMargin = dp(8) }
                }
                rows.addView(currentRow)
            }
            val badge = badges.getJSONObject(index)
            val unlocked = badge.getBoolean("unlocked")

            val card = inflater.inflate(R.layout.item_badge_card, currentRow, false)
            card.layoutParams = cellParams(index % COLUMNS)
            card.setBackgroundResource(
                if (unlocked) R.drawable.bg_badge_unlocked else R.drawable.bg_badge_locked)
            // 徽章图形: 未点亮时灰色剪影 (低透明度, §7.1)
            card.findViewById<TextView>(R.id.badge_emoji).apply {
                text = badgeEmoji(badge.getString("id"))
                alpha = if (unlocked) 1f else 0.3f
            }
            // 名称: 点亮附 ✓ (图形+文字双编码, 不单靠颜色 §4.7)
            card.findViewById<TextView>(R.id.badge_name).apply {
                text = badge.getString("name") + if (unlocked) " ✓" else ""
                setTextColor(getColor(
                    if (unlocked) R.color.magtile_text_primary
                    else R.color.magtile_text_secondary))
            }
            // 已点亮: 解锁日期; 未点亮: 一句话达成条件
            card.findViewById<TextView>(R.id.badge_sub).apply {
                text = if (unlocked) badge.optString("unlocked_text")
                       else badge.optString("condition")
                setTextColor(getColor(
                    if (unlocked) R.color.magtile_success
                    else R.color.magtile_text_secondary))
            }
            currentRow?.addView(card)
        }
        // 末行奇数枚: 补一个同宽占位, 保持网格对齐
        if (badges.length() % COLUMNS != 0) {
            currentRow?.addView(Space(this), cellParams(badges.length() % COLUMNS))
        }

        // 页脚只报喜不催促 (§4.3)
        val badgeCount = root.optInt("achievement_count")
        findViewById<TextView>(R.id.achievements_footer).text =
            if (badgeCount > 0) getString(R.string.achievements_footer_some, badgeCount)
            else getString(R.string.achievements_footer_none)
    }

    /** 网格单元参数: 等宽两列, 非行首列带左间距。 */
    private fun cellParams(column: Int) =
        LinearLayout.LayoutParams(0, dp(150), 1f).apply {
            if (column > 0) marginStart = dp(8)
        }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    companion object {
        private const val TAG = "MagTileAchievements"
        private const val COLUMNS = 2

        /**
         * 徽章 emoji 按成就 id 映射 —— 与桌面 Qt kAchievementDefs 同一套
         * 图形。emoji 为增补平面字符, 不经 JNI NewStringUTF 下发 (只接受
         * Modified UTF-8), 故在 Kotlin 侧收口; 存档中未来新增的成就
         * 回退通用徽章 🏅 (与桌面同策略, 永不缺席)。
         */
        private val BADGE_EMOJI = mapOf(
            "first_model_completed" to "🏗️",
            "three_models_completed" to "🏘️",
            "ten_models_completed" to "🏰",
            "thirty_models_completed" to "🌟",
        )

        private fun badgeEmoji(achievementId: String): String =
            BADGE_EMOJI[achievementId] ?: "🏅"
    }
}

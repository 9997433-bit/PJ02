package com.magtile.studio

import android.graphics.Typeface
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import org.json.JSONArray

/**
 * 教程中的一个搭建步骤 (JNI getTutorialSteps() 返回的 JSON 条目;
 * 与核心库 core::BuildStep 字段一一对应, 只含文字分步浏览所需数据)。
 */
data class TutorialStep(
    val stepNumber: Int,
    /** 中文步骤说明 (面向孩子)。 */
    val description: String,
    /** 可选的中文小提示; 空串 = 本步骤没有提示。 */
    val tip: String,
    /** 本步骤新增磁力片数 (片数增量)。 */
    val piecesAdded: Int,
    /** 截至本步骤累计已放片数 (末步 = 模型总片数)。 */
    val piecesTotal: Int,
) {
    companion object {
        /** 解析 getTutorialSteps() 里的 steps 数组。 */
        fun listFromJson(steps: JSONArray): List<TutorialStep> =
            List(steps.length()) { index ->
                val obj = steps.getJSONObject(index)
                TutorialStep(
                    stepNumber = obj.getInt("step_number"),
                    description = obj.optString("description"),
                    tip = obj.optString("tip"),
                    piecesAdded = obj.optInt("pieces_added"),
                    piecesTotal = obj.optInt("pieces_total"),
                )
            }
    }
}

/**
 * 教程步骤列表适配器: 序号圆徽 + 中文说明 + 可选小提示 + 片数增量。
 * 行分三态 (状态不单靠颜色表达 §4.7 —— 徽内符号/加粗/整行底色多重编码):
 *   已完成  绿徽 ✓ + 整行淡出 (回看时按「上一步」回退即恢复当前态);
 *   当前步  主色浅底高亮 + 说明加粗 (TutorialActivity 同步滚动定位);
 *   待搭建  常规白卡。
 */
class TutorialStepAdapter : RecyclerView.Adapter<TutorialStepAdapter.StepHolder>() {

    private val steps = mutableListOf<TutorialStep>()

    /** 已完成步数 (0..stepCount): 前 N 行完成态, 第 N+1 行为当前步。 */
    private var doneCount = 0

    fun submit(newSteps: List<TutorialStep>, done: Int) {
        steps.clear()
        steps.addAll(newSteps)
        doneCount = done
        @Suppress("NotifyDataSetChanged")  // 全量替换一次, 无增量更新场景
        notifyDataSetChanged()
    }

    /** 步骤导航后刷新三态 (步数量级几十行, 整表重绑足够轻)。 */
    fun updateDoneCount(done: Int) {
        if (doneCount == done) return
        doneCount = done
        @Suppress("NotifyDataSetChanged")  // 三态整体前移/后移, 无增量更新场景
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): StepHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_tutorial_step, parent, false)
        return StepHolder(view)
    }

    override fun getItemCount(): Int = steps.size

    override fun onBindViewHolder(holder: StepHolder, position: Int) {
        holder.bind(steps[position])
    }

    inner class StepHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val badge: TextView = itemView.findViewById(R.id.step_badge)
        private val description: TextView = itemView.findViewById(R.id.step_description)
        private val tip: TextView = itemView.findViewById(R.id.step_tip)
        private val pieces: TextView = itemView.findViewById(R.id.step_pieces)

        fun bind(step: TutorialStep) {
            val done = step.stepNumber <= doneCount
            val active = step.stepNumber == doneCount + 1

            description.text = step.description
            description.setTypeface(
                null, if (active) Typeface.BOLD else Typeface.NORMAL)
            if (step.tip.isBlank()) {
                tip.visibility = View.GONE
            } else {
                tip.visibility = View.VISIBLE
                tip.text = itemView.context.getString(R.string.tutorial_step_tip, step.tip)
            }
            pieces.text = itemView.context.getString(
                R.string.tutorial_step_pieces, step.piecesAdded)

            if (done) {
                badge.text = "✓"
                badge.setTextColor(itemView.context.getColor(R.color.magtile_success))
                badge.setBackgroundResource(R.drawable.bg_step_badge_done)
            } else {
                badge.text = step.stepNumber.toString()
                badge.setTextColor(itemView.context.getColor(R.color.magtile_text_primary))
                badge.setBackgroundResource(R.drawable.bg_step_badge)
            }
            // shape 背景不带 padding, 切换背景不影响布局内边距
            itemView.setBackgroundResource(
                if (active) R.drawable.bg_tutorial_step_active
                else R.drawable.bg_progress_card)
            itemView.alpha = if (done) 0.6f else 1.0f
        }
    }
}

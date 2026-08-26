package com.magtile.studio

import android.app.Activity
import android.app.AlertDialog
import android.graphics.Typeface
import android.os.Handler
import android.os.Looper
import android.util.TypedValue
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.widget.GridLayout
import android.widget.TextView
import org.json.JSONObject

/**
 * 家长门对话框 (UI_UX_SPEC.md §9): 年龄段切换 / 库存录入等家长操作
 * 前的强制关卡。题目生成 / 中文大写数字验证 / 3 次答错 60 秒冷却 /
 * 15 分钟家长会话全部由共享状态机 core::ParentGate 负责 (JNI 桥
 * MagTileNative.parentGate*, 与桌面 GL/Qt 完全同一模块); 本类只做
 * 界面: 题面 + 中文大写数字软键盘 (56dp 键帽大号触控, 不依赖物理
 * 键盘/输入法) + 温和的答错/冷却提示。
 *
 * 措辞对齐桌面门界面 (P3 零挫败): 答错是琥珀色「再试一次吧」,
 * 冷却是「休息一下, N 秒后可以再试一次」—— 儿童侧不出现
 * 「验证失败」类苛责语, 不用红色; 门界面无任何商品/价格信息。
 *
 * 会话守卫与桌面 Qt 同策略: 答对后 15 分钟内 (时长读 core::ParentGate
 * 现有常量 kDefaultSessionDuration) 再点家长入口免重复验证; 会话只存
 * 内存, 重启即失效 (「已通过」标记永不落盘, 防重启绕过)。
 */
object ParentGateDialog {

    /** 软键盘数字键位 (与桌面 GL/Qt 门界面同一键位表; 第 12 键为退格)。 */
    private val KEYS =
        listOf("壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖", "零", "拾")

    /** 答案最长 4 字 (标准答案最多 3 字, 留 1 字余量, 与 Qt 版一致)。 */
    private const val MAX_ANSWER_LENGTH = 4

    /**
     * 家长操作统一入口: 15 分钟会话守卫期内直接放行 (免重复验证,
     * 与桌面 Qt 会话守卫同策略), 否则先过家长门, 答对后回调 onPassed。
     */
    fun requireParent(activity: Activity, onPassed: () -> Unit) {
        if (MagTileNative.parentGateSessionActive()) {
            onPassed()
            return
        }
        val view =
            LayoutInflater.from(activity).inflate(R.layout.dialog_parent_gate, null)
        val dialog = AlertDialog.Builder(activity).setView(view).create()
        Controller(activity, view, dialog, onPassed)
        dialog.show()
    }

    /** 单次开门的界面状态机: 答题态 <-> 冷却态 (温和的「休息一下」)。 */
    private class Controller(
        private val activity: Activity,
        view: View,
        private val dialog: AlertDialog,
        private val onPassed: () -> Unit,
    ) {
        private val questionGroup: View = view.findViewById(R.id.gate_question_group)
        private val cooldownGroup: View = view.findViewById(R.id.gate_cooldown_group)
        private val questionView: TextView = view.findViewById(R.id.gate_question)
        private val answerView: TextView = view.findViewById(R.id.gate_answer)
        private val wrongHint: TextView = view.findViewById(R.id.gate_wrong_hint)
        private val submitButton: TextView = view.findViewById(R.id.gate_submit)
        private val cooldownText: TextView = view.findViewById(R.id.gate_cooldown_text)

        private val handler = Handler(Looper.getMainLooper())
        /** 软键盘输入缓冲 (中文大写数字, 键盘只产生 BMP 单码元汉字)。 */
        private var answer = ""
        private var cooldownRemaining = 0

        /** 冷却倒计时心跳 (1s): 走到 0 出新题回到答题态。 */
        private val cooldownTick = object : Runnable {
            override fun run() {
                cooldownRemaining -= 1
                if (cooldownRemaining <= 0) {
                    openGate()
                } else {
                    cooldownText.text = activity.getString(
                        R.string.gate_cooldown_text, cooldownRemaining)
                    handler.postDelayed(this, 1000L)
                }
            }
        }

        init {
            buildKeyboard(view.findViewById(R.id.gate_keys))
            submitButton.setOnClickListener { submit() }
            view.findViewById<TextView>(R.id.gate_cancel)
                .setOnClickListener { dialog.dismiss() }
            view.findViewById<TextView>(R.id.gate_cooldown_back)
                .setOnClickListener { dialog.dismiss() }
            dialog.setOnDismissListener { handler.removeCallbacksAndMessages(null) }
            openGate()
        }

        /** 进门: 出一道新题 (防背题), 复位输入与答错提示; 仍在上一轮
         *  冷却期时直接进「休息一下」倒计时 (与桌面 openGate 同口径)。 */
        private fun openGate() {
            val state = JSONObject(MagTileNative.parentGateOpenJson())
            questionView.text = state.optString("question")
            answer = ""
            renderAnswer()
            wrongHint.visibility = View.GONE
            val cooldown = state.optInt("cooldown_seconds", 0)
            if (cooldown > 0) enterCooldown(cooldown) else showQuestionState()
        }

        /** 提交答案: 答对关门放行; 答错温和提示; 连续答错进冷却。 */
        private fun submit() {
            if (answer.isEmpty()) return
            val result = JSONObject(MagTileNative.parentGateSubmitJson(answer))
            answer = ""
            renderAnswer()
            when (result.optString("result")) {
                "passed" -> {
                    dialog.dismiss()
                    onPassed()
                }
                "cooling" -> enterCooldown(result.optInt("cooldown_seconds", 1))
                else -> {
                    wrongHint.text = activity.getString(
                        R.string.gate_wrong_hint,
                        result.optInt("attempts_remaining", 0))
                    wrongHint.visibility = View.VISIBLE
                }
            }
        }

        private fun showQuestionState() {
            questionGroup.visibility = View.VISIBLE
            cooldownGroup.visibility = View.GONE
        }

        /** 冷却态: 温和的「休息一下」+ 秒级倒计时, 无惩罚文案。 */
        private fun enterCooldown(seconds: Int) {
            cooldownRemaining = seconds
            questionGroup.visibility = View.GONE
            cooldownGroup.visibility = View.VISIBLE
            cooldownText.text =
                activity.getString(R.string.gate_cooldown_text, cooldownRemaining)
            handler.removeCallbacksAndMessages(null)
            handler.postDelayed(cooldownTick, 1000L)
        }

        private fun renderAnswer() {
            if (answer.isEmpty()) {
                answerView.text = activity.getString(R.string.gate_input_placeholder)
                answerView.setTextColor(
                    activity.getColor(R.color.magtile_text_secondary))
                answerView.setTypeface(null, Typeface.NORMAL)
            } else {
                answerView.text = answer
                answerView.setTextColor(
                    activity.getColor(R.color.magtile_text_primary))
                answerView.setTypeface(null, Typeface.BOLD)
            }
            // 空输入不可提交 (半透明表达不可用, 与桌面确认键一致)
            submitButton.isEnabled = answer.isNotEmpty()
            submitButton.alpha = if (answer.isEmpty()) 0.45f else 1f
        }

        /** 软键盘: 4 行 x 3 列, 键帽 56dp (大号触控目标), 3 列等宽。 */
        private fun buildKeyboard(grid: GridLayout) {
            val backspace = activity.getString(R.string.gate_key_backspace)
            (KEYS + backspace).forEach { key ->
                val keyView = TextView(activity).apply {
                    text = key
                    gravity = Gravity.CENTER
                    setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
                    setTextColor(activity.getColor(R.color.magtile_text_primary))
                    setTypeface(null, Typeface.BOLD)
                    background = activity.getDrawable(R.drawable.bg_gate_key)
                    setOnClickListener { pressKey(key, backspace) }
                }
                val params = GridLayout.LayoutParams(
                    GridLayout.spec(GridLayout.UNDEFINED),
                    GridLayout.spec(GridLayout.UNDEFINED, 1f))
                params.width = 0
                params.height = dp(56)
                params.setMargins(dp(4), dp(4), dp(4), dp(4))
                grid.addView(keyView, params)
            }
        }

        private fun pressKey(key: String, backspace: String) {
            answer = when {
                key == backspace -> answer.dropLast(1)  // 按字删除 (BMP 单码元)
                answer.length < MAX_ANSWER_LENGTH -> answer + key
                else -> answer
            }
            renderAnswer()
        }

        private fun dp(value: Int): Int = TypedValue.applyDimension(
            TypedValue.COMPLEX_UNIT_DIP, value.toFloat(),
            activity.resources.displayMetrics).toInt()
    }
}

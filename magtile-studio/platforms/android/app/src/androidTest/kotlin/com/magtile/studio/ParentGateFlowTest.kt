package com.magtile.studio

import android.content.Context
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.doesNotExist
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.RootMatchers.isDialog
import androidx.test.espresso.matcher.ViewMatchers.isDescendantOfA
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withSubstring
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.hamcrest.CoreMatchers.allOf
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * 家长门入口仪器测试 (E2E-08 Android 侧可自动化部分; UI_UX_SPEC §9):
 *
 *   1. 年龄段切换入口先过家长门 (会话未开启时点击必出门);
 *   2. 题面为中文数字乘法 (贰~玖 两个个位数, core::ParentGate 共享
 *      状态机), 测试解析题面并经软键盘作答 —— 门拦截的对象是儿童
 *      而非自动化 (与桌面 expectedAnswer 冒烟同一立场);
 *   3. 答错一次: 琥珀温和提示在场 (无「失败」苛责语), 门不放行;
 *   4. 正确作答: 放行进年龄段对话框, 15 分钟家长会话开启;
 *   5. 会话守卫: 再点家长入口免重复验证 (直接年龄段对话框, 无题面)。
 *
 * 冷却路径 (3 次答错 60 秒) 刻意不在此走查: 状态机有 parent_gate
 * CTest 单测全覆盖, 仪器侧不为它长时间等待; 冷却倒计时的真机表现
 * 属人工项 (docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md §3 M-09)。
 *
 * 运行方式同 MainActivitySmokeTest (需 arm64 设备, 无设备 CI 只编译)。
 */
@RunWith(AndroidJUnit4::class)
class ParentGateFlowTest {

    private val context: Context
        get() = ApplicationProvider.getApplicationContext()

    @Before
    fun resetProgressStoreAndGateSession() {
        TestSupport.deleteProgressStore(context)
        // 家长会话只存内存且进程级单例: 收回上一个测试可能开着的会话,
        // 保证本测试从「门必须出现」的状态开始 (幂等)
        MagTileNative.parentGateLockSession()
    }

    @Test
    fun ageModeEntry_gateBlocks_wrongIsGentle_correctPasses_sessionGuards() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            TestSupport.waitUntil(
                "模型库列表加载出至少 1 张卡片", TestSupport.FIRST_LOAD_TIMEOUT_MS) {
                modelCount(scenario) > 0
            }
            assertFalse("测试起点应无家长会话", MagTileNative.parentGateSessionActive())

            // ---- 1. 家长入口出门 ---------------------------------------
            onView(withId(R.id.age_mode_button)).perform(click())
            onView(withText(R.string.gate_title)).inRoot(isDialog())
                .check(matches(isDisplayed()))

            // 读题面 (如「叁 × 柒 = ?」) 并解出标准答案
            var question = ""
            onView(withId(R.id.gate_question)).inRoot(isDialog())
                .check { view, _ -> question = (view as TextView).text.toString() }
            val answer = expectedAnswerFor(question)

            // ---- 2. 答错一次: 温和提示, 门不放行 -----------------------
            // 「壹」(=1) 恒错: 题目是贰~玖 两个个位数相乘, 积最小为 4
            pressGateKey("壹")
            onView(withId(R.id.gate_submit)).inRoot(isDialog()).perform(click())
            onView(withId(R.id.gate_wrong_hint)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            onView(withId(R.id.gate_wrong_hint)).inRoot(isDialog())
                .check(matches(withSubstring("再试一次")))
            assertFalse("答错后不应开启家长会话",
                MagTileNative.parentGateSessionActive())

            // ---- 3. 正确作答: 放行 + 会话开启 --------------------------
            answer.forEach { pressGateKey(it.toString()) }
            onView(withId(R.id.gate_submit)).inRoot(isDialog()).perform(click())
            onView(withText(R.string.age_mode_dialog_title)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            assertTrue("答对后应开启 15 分钟家长会话",
                MagTileNative.parentGateSessionActive())
            onView(withText(R.string.dialog_close)).inRoot(isDialog()).perform(click())

            // ---- 4. 会话守卫: 再点免重复验证 ---------------------------
            onView(withId(R.id.age_mode_button)).perform(click())
            onView(withText(R.string.age_mode_dialog_title)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            onView(withId(R.id.gate_question)).check(doesNotExist())
            onView(withText(R.string.dialog_close)).inRoot(isDialog()).perform(click())
        }
    }

    // ---- 私有工具 ------------------------------------------------------

    /** 点击软键盘键帽 (键帽是 gate_keys 网格里以字符为文本的视图)。 */
    private fun pressGateKey(label: String) {
        onView(allOf(withText(label), isDescendantOfA(withId(R.id.gate_keys))))
            .inRoot(isDialog()).perform(click())
    }

    /** 解析题面里的两个中文数字并给出标准答案 (中文大写数字)。 */
    private fun expectedAnswerFor(question: String): String {
        val factors = question.mapNotNull { ch ->
            UPPERCASE_DIGITS.indexOf(ch.toString()).takeIf { it >= 0 }
        }
        check(factors.size == 2) { "题面不是两个中文数字相乘: $question" }
        return toChineseUppercase(factors[0] * factors[1])
    }

    /** 整数 -> 规范中文大写数字 (与 core::ParentGate::toChineseUppercase
     *  同规则, 覆盖乘法积域 [4, 81]): 21 -> 贰拾壹, 10 -> 壹拾。 */
    private fun toChineseUppercase(value: Int): String {
        check(value in 0..99) { "超出中文大写数字工具范围: $value" }
        if (value < 10) return UPPERCASE_DIGITS[value]
        val tens = value / 10
        val units = value % 10
        return UPPERCASE_DIGITS[tens] + "拾" +
            (if (units > 0) UPPERCASE_DIGITS[units] else "")
    }

    private fun modelCount(scenario: ActivityScenario<MainActivity>): Int {
        var count = 0
        scenario.onActivity { activity ->
            count = activity.findViewById<RecyclerView>(R.id.model_list)
                .adapter?.itemCount ?: 0
        }
        return count
    }

    private companion object {
        val UPPERCASE_DIGITS =
            listOf("零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖")
    }
}

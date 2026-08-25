package com.magtile.studio

import android.content.Context
import android.os.SystemClock
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.RootMatchers.isDialog
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/**
 * Android 主路径仪器冒烟 (androidTest 骨架, 对齐桌面 GL/Qt 冒烟口径):
 *
 *   1. MainActivity 启动 (解包数据资产 + JNI 加载目录 + 打开进度存档);
 *   2. 模型库列表非空 (RecyclerView 适配器至少 1 张卡片);
 *   3. 勾选「只看免费」后点击首张免费卡 (免费层判定与桌面
 *      core::isFreeTierModel 同口径, 筛选后首张即"首张免费卡");
 *   4. 详情弹窗出现: 弹窗标题 = 卡片中文名, 「物理校验」按钮在场,
 *      免费卡带「🧲 开始搭建」大按钮 (免费层无订阅锁)。
 *
 * 运行方式 (需要真机/模拟器, APK 只出 arm64-v8a):
 *   ../run_instrumented_smoke.sh            # 有设备跑, 无设备温和跳过
 *   ./gradlew :app:connectedDebugAndroidTest # 等价的 Gradle 直跑
 * 无设备的 CI 用 :app:assembleDebugAndroidTest 只编译测试 APK 作编译门。
 *
 * 稳定性设计:
 *   - 启动链路在工作线程 (非 AsyncTask, Espresso 不会自动等待), 故用
 *     轮询等待列表就绪 (首启含资产解包, 上限放宽到 120 秒);
 *   - @Before 删除 progress.db 回到首启状态: 年龄段回默认 7-9 档
 *     (「只看免费」勾选可见)、订阅回未订阅、库存回未登记 —— 断言
 *     不受上一次运行残留影响 (资产解包版本戳不在此文件, 不受影响);
 *   - 不引 espresso-contrib: 条目点击直接经 ViewHolder.performClick
 *     (主线程), 依赖面与产品侧同样保持最小。
 */
@RunWith(AndroidJUnit4::class)
class MainActivitySmokeTest {

    @Before
    fun resetProgressStore() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        File(context.filesDir, MainActivity.PROGRESS_DB_NAME).delete()
    }

    @Test
    fun mainPath_launch_listNonEmpty_clickFirstFreeCard_detailDialogShown() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            // ---- 1+2. 启动后模型库列表非空 (首启含资产解包, 放宽等待) --
            waitUntil("模型库列表加载出至少 1 张卡片", FIRST_LOAD_TIMEOUT_MS) {
                modelCount(scenario) > 0
            }
            assertTrue("模型库列表应非空", modelCount(scenario) > 0)

            // ---- 3. 勾选「只看免费」-> 列表只剩免费层模型 --------------
            // (默认 7-9 标准档该勾选可见; 免费层 30 模型三端对齐,
            //  docs/FREE_TIER_MANIFEST.md, 筛选后列表不该为空)
            onView(withId(R.id.filter_free)).perform(click())
            waitUntil("「只看免费」筛选后列表非空", UI_TIMEOUT_MS) {
                modelCount(scenario) > 0
            }

            // 首张免费卡完成布局后读卡面中文名 (弹窗标题断言用),
            // notifyDataSetChanged 后 ViewHolder 要等下一帧布局, 故轮询
            var firstFreeName = ""
            waitUntil("首张免费卡完成布局", UI_TIMEOUT_MS) {
                scenario.onActivity { activity ->
                    firstFreeName = activity
                        .findViewById<RecyclerView>(R.id.model_list)
                        .findViewHolderForAdapterPosition(0)?.itemView
                        ?.findViewById<TextView>(R.id.model_name)
                        ?.text?.toString().orEmpty()
                }
                firstFreeName.isNotEmpty()
            }

            // 点击首张免费卡 (主线程直接 performClick, 免引 espresso-contrib)
            scenario.onActivity { activity ->
                val clicked = activity
                    .findViewById<RecyclerView>(R.id.model_list)
                    .findViewHolderForAdapterPosition(0)!!
                    .itemView.performClick()
                check(clicked) { "首张免费卡点击未被消费" }
            }

            // ---- 4. 详情弹窗出现 --------------------------------------
            // 标题 = 卡片中文名 (isDialog 根匹配把断言限制在弹窗窗口,
            // 不会误中列表里的同名卡片)
            onView(withText(firstFreeName)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            // 「物理校验」按钮在场 (详情弹窗固定入口)
            onView(withText(R.string.dialog_validate)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            // 免费卡无订阅锁: 「🧲 开始搭建」大按钮在场 (与桌面
            // billing::isContentUnlocked / DetailPage 锁同口径)
            onView(withId(R.id.dialog_start_build)).inRoot(isDialog())
                .check(matches(isDisplayed()))
        }
    }

    /** 当前列表条目数 (RecyclerView 适配器口径, 主线程同步读取)。 */
    private fun modelCount(scenario: ActivityScenario<MainActivity>): Int {
        var count = 0
        scenario.onActivity { activity ->
            count = activity.findViewById<RecyclerView>(R.id.model_list)
                .adapter?.itemCount ?: 0
        }
        return count
    }

    /** 轮询等待条件成立, 超时 fail 并带出等待目标 (中文可读)。 */
    private fun waitUntil(what: String, timeoutMs: Long, condition: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + timeoutMs
        while (SystemClock.elapsedRealtime() < deadline) {
            if (condition()) return
            SystemClock.sleep(POLL_INTERVAL_MS)
        }
        fail("等待超时 (${timeoutMs}ms): $what")
    }

    private companion object {
        /** 首启加载上限: 含 assets/data 解包 + JNI 目录加载 (慢设备兜底)。 */
        const val FIRST_LOAD_TIMEOUT_MS = 120_000L
        /** 纯 UI 状态变化 (筛选刷新 / 下一帧布局) 的等待上限。 */
        const val UI_TIMEOUT_MS = 10_000L
        const val POLL_INTERVAL_MS = 100L
    }
}

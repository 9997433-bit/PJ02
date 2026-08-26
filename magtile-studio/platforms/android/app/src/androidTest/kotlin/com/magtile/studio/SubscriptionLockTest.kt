package com.magtile.studio

import android.content.Context
import androidx.recyclerview.widget.RecyclerView
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.click
import androidx.test.espresso.assertion.ViewAssertions.doesNotExist
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.RootMatchers.isDialog
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withSubstring
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * 订阅锁可见性仪器测试 (E2E-11 Android 侧可自动化部分; 解锁口径与
 * 桌面 billing::isContentUnlocked / Qt DetailPage 锁完全一致):
 *
 *   1. 未订阅 + 非免费模型: 详情弹窗给温和「订阅解锁」提示 (无价格
 *      无催促 §12.2), 只锁「🧲 开始搭建」入口 —— 「物理校验」照常
 *      在场 (浏览/校验不受限, 不锁内容);
 *   2. 订阅生效 (经 setSubscriptionActive 写 progress/
 *      subscription_settings 契约键, 与 Debug 档「模拟已订阅」QA
 *      开关 / Release 档 PlayBillingManager 同一写入口): 同一张
 *      非免费卡「开始搭建」解锁, 订阅提示退场。
 *
 * 测试直接经 JNI 写契约键 (而非点 Debug 开关): 断言的是「免费层锁
 * 随订阅状态读取口径翻转」这条产品逻辑, 与写入方无关; Debug 开关
 * 本身的可见性属真机人工项 (docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md)。
 *
 * 运行方式同 MainActivitySmokeTest (需 arm64 设备, 无设备 CI 只编译)。
 */
@RunWith(AndroidJUnit4::class)
class SubscriptionLockTest {

    private val context: Context
        get() = ApplicationProvider.getApplicationContext()

    @Before
    fun resetProgressStore() {
        // 首启状态: 未订阅 (缺键按未订阅兜底, 宁可锁)
        TestSupport.deleteProgressStore(context)
    }

    @After
    fun clearSubscription() {
        // 不让模拟订阅泄漏到同进程的后续测试 (各测试 @Before 也会删档)
        runCatching { MagTileNative.setSubscriptionActive(false, "") }
    }

    @Test
    fun lockedNonFreeCard_showsGentleNote_locksOnlyStartBuild() {
        val model = TestSupport.firstNonFreeModel(context)
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            waitListLoaded(scenario)
            clickCardAt(scenario, model.position)

            // 详情弹窗在场 (标题 = 模型中文名)
            onView(withText(model.name)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            // 温和订阅提示 (dialog_subscription_note 尾句) 在弹窗消息里
            onView(withSubstring("完整分步教程订阅后解锁")).inRoot(isDialog())
                .check(matches(isDisplayed()))
            // 只锁「开始搭建」入口: 大按钮不在场
            onView(withId(R.id.dialog_start_build)).check(doesNotExist())
            // 浏览/校验不受限: 「物理校验」按钮照常在场
            onView(withText(R.string.dialog_validate)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            onView(withText(R.string.dialog_close)).inRoot(isDialog()).perform(click())
        }
    }

    @Test
    fun subscriptionActive_unlocksStartBuild_noteRetires() {
        val model = TestSupport.firstNonFreeModel(context)
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            waitListLoaded(scenario)  // 启动链路已打开进度存档
            // 写订阅契约键 (与桌面 FakeBilling / Play 接线同键同口径;
            // 模拟档位与 Debug 开关同为年度主推 sub_yearly)
            assertTrue("订阅契约键应落盘成功",
                MagTileNative.setSubscriptionActive(true, "sub_yearly"))
            // 重建 Activity: 启动链路重读 subscriptionActive (与真实
            // 冷启动同一读取口径)
            scenario.recreate()
            waitListLoaded(scenario)
            clickCardAt(scenario, model.position)

            // 同一张非免费卡: 「开始搭建」解锁, 订阅提示退场
            onView(withText(model.name)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            onView(withId(R.id.dialog_start_build)).inRoot(isDialog())
                .check(matches(isDisplayed()))
            onView(withSubstring("完整分步教程订阅后解锁")).check(doesNotExist())
            onView(withText(R.string.dialog_close)).inRoot(isDialog()).perform(click())
        }
    }

    // ---- 私有工具 ------------------------------------------------------

    private fun waitListLoaded(scenario: ActivityScenario<MainActivity>) {
        TestSupport.waitUntil(
            "模型库列表加载出至少 1 张卡片", TestSupport.FIRST_LOAD_TIMEOUT_MS) {
            var count = 0
            scenario.onActivity { activity ->
                count = activity.findViewById<RecyclerView>(R.id.model_list)
                    .adapter?.itemCount ?: 0
            }
            count > 0
        }
    }

    /** 滚动到目录序 position 的卡片并点击 (无筛选时列表序 = 目录序;
     *  条目点击经 ViewHolder.performClick, 与 MainActivitySmokeTest
     *  同策略免引 espresso-contrib)。 */
    private fun clickCardAt(scenario: ActivityScenario<MainActivity>, position: Int) {
        scenario.onActivity { activity ->
            activity.findViewById<RecyclerView>(R.id.model_list)
                .scrollToPosition(position)
        }
        var clicked = false
        TestSupport.waitUntil(
            "第 ${position + 1} 张卡片完成布局并点击", TestSupport.UI_TIMEOUT_MS) {
            scenario.onActivity { activity ->
                val holder = activity.findViewById<RecyclerView>(R.id.model_list)
                    .findViewHolderForAdapterPosition(position)
                if (holder != null && !clicked) {
                    clicked = holder.itemView.performClick()
                }
            }
            clicked
        }
    }
}

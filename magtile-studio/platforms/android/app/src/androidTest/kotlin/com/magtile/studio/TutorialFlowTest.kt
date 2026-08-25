package com.magtile.studio

import android.content.Context
import android.content.Intent
import android.opengl.GLSurfaceView
import android.os.SystemClock
import android.view.InputDevice
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withId
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/**
 * 分步教程仪器测试 (E2E-15 可自动化部分; 对应真机 QA 报告
 * docs/reports/QA_ANDROID_CHILD_PLAYTHROUGH.md 的 P0 项 M-04/M-05
 * 与 M-01~M-03 的可自动化外围):
 *
 *   - M-04 断点续搭: 走 3 步 -> 退出 -> 重进, 断言进度头回到第 4 步
 *     (进度头文案与存档当前步双向对账);
 *   - M-05 完成链路: 「下一步」走完全程 -> 完成横幅 + 进度头完成文案
 *     + 存档记完成 + 首搭成就 first_model_completed 点亮
 *     (progressOverviewJson 与桌面 StudioBackend 同口径);
 *   - 已完成档回读: 不带 EXTRA_RESTART 直接落末步完成态, 带
 *     EXTRA_RESTART (进度页「再搭一次」) 从头开始;
 *   - M-01/M-02/M-03 可自动化外围: 3D 视口在场 + 渲染模式与减少
 *     动效档位对应 (常规连续重绘驱动呼吸 / 减动效脏帧定格) + 触屏
 *     手势事件链路 (单指拖动 / 双指捏合 / 双指平移合成事件全部被
 *     视口消费且不崩溃)。画面正确性 / 手感 / 呼吸动画的视觉核验
 *     无法自动化, 见 DeviceManualQaTest (@Ignore) 与人工勾选表
 *     docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md §2。
 *
 * 运行方式与 MainActivitySmokeTest 相同 (需 arm64 真机/模拟器):
 *   ../run_instrumented_smoke.sh  (无设备温和跳过)
 * 无设备 CI 用 :app:assembleDebugAndroidTest 只编译作编译门。
 *
 * 模型选取: 运行期从解包目录挑「步数最少的免费模型」(免费层直达
 * 教程无订阅锁, 步数最少让完成链路走查最快), 不硬编码模型 id ——
 * 内容库增删不影响本测试。
 */
@RunWith(AndroidJUnit4::class)
class TutorialFlowTest {

    private val context: Context
        get() = ApplicationProvider.getApplicationContext()

    @Before
    fun resetProgressStore() {
        TestSupport.deleteProgressStore(context)
    }

    // ---- M-04 断点续搭 (数据链路) --------------------------------------

    @Test
    fun m04_resume_walkThreeSteps_relaunch_resumesAtStepFour() {
        val model = TestSupport.smallestFreeModel(context)
        val stepsJson = tutorialStepsJson(model.id)
        val stepCount = stepsJson.getInt("step_count")
        val totalPieces = stepsJson.getInt("total_pieces")

        // 第一次会话: 走 3 步后离开 (存档在每次导航与 onPause 落盘)
        launchTutorial(model.id).use { scenario ->
            waitLoaded(scenario)
            clickNext(scenario, times = 3)
            TestSupport.waitUntil("当前步落盘 (= 3)", TestSupport.SAVE_TIMEOUT_MS) {
                MagTileNative.savedTutorialStep(model.id) == 3
            }
        }

        // 第二次会话 (不带 EXTRA_RESTART): 断点续搭, 进度头回到第 4 步
        launchTutorial(model.id).use { scenario ->
            waitLoaded(scenario)
            // 已放片数 = 第 3 步的累计片数 (steps[2].pieces_total)
            val placedPieces =
                stepsJson.getJSONArray("steps").getJSONObject(2).getInt("pieces_total")
            onView(withId(R.id.tutorial_step_label)).check(matches(withText(
                context.getString(
                    R.string.tutorial_step_of, 4, stepCount, placedPieces, totalPieces))))
            scenario.onActivity { activity ->
                assertTrue("断点续搭后「上一步」应可用",
                    activity.findViewById<Button>(R.id.tutorial_prev_button).isEnabled)
            }
        }
    }

    // ---- M-05 完成链路 (完成记录 + 首搭成就) ---------------------------

    @Test
    fun m05_complete_walkAllSteps_recordsCompletion_andFirstBuildAchievement() {
        val model = TestSupport.smallestFreeModel(context)
        val stepsJson = tutorialStepsJson(model.id)
        val stepCount = stepsJson.getInt("step_count")
        val totalPieces = stepsJson.getInt("total_pieces")

        launchTutorial(model.id).use { scenario ->
            waitLoaded(scenario)
            // 「下一步」走完全程 (末步按钮变「完成 🎉」, 完成后禁用)
            repeat(stepCount) { clickNext(scenario, times = 1) }

            // 完成态: 横幅 + 进度头完成文案 + 下一步禁用/上一步可回看
            onView(withId(R.id.tutorial_finished)).check(matches(isDisplayed()))
            onView(withId(R.id.tutorial_step_label)).check(matches(withText(
                context.getString(
                    R.string.tutorial_finished_label, stepCount, totalPieces))))
            scenario.onActivity { activity ->
                assertFalse("完成后「下一步」应禁用",
                    activity.findViewById<Button>(R.id.tutorial_next_button).isEnabled)
                assertTrue("完成后「上一步」应可回看",
                    activity.findViewById<Button>(R.id.tutorial_prev_button).isEnabled)
            }

            // 存档: 完成记录 (当前步 = 总步数) —— 写档在单线程执行器,
            // 该值就位即代表同一原生调用里的完成时刻/成就也已写入
            TestSupport.waitUntil("完成记录落盘", TestSupport.SAVE_TIMEOUT_MS) {
                MagTileNative.savedTutorialStep(model.id) == stepCount
            }

            // 进度页数据源对账 (与桌面 StudioBackend 同口径): 已完成
            // 列表含本模型 + 首搭成就 first_model_completed 点亮
            val dataDir = DataAssetInstaller.ensureInstalled(context)
            val overview =
                JSONObject(MagTileNative.progressOverviewJson(dataDir.absolutePath))
            assertTrue("progressOverviewJson 应可用", overview.optBoolean("store_ready"))
            val completed = overview.getJSONArray("completed")
            val completedIds = (0 until completed.length())
                .map { completed.getJSONObject(it).getString("id") }
            assertTrue("已完成列表应含 ${model.id}", model.id in completedIds)
            val achievements = overview.getJSONArray("achievements")
            val firstBuild = (0 until achievements.length())
                .map { achievements.getJSONObject(it) }
                .firstOrNull { it.getString("id") == "first_model_completed" }
            assertTrue("首搭成就 first_model_completed 应点亮",
                firstBuild != null && firstBuild.getBoolean("unlocked"))
        }
    }

    // ---- 已完成档回读: 直接落完成态 / 「再搭一次」从头开始 --------------

    @Test
    fun completedArchive_reopensAtFinishedState_andRestartBeginsFromStepOne() {
        val model = TestSupport.smallestFreeModel(context)
        val stepsJson = tutorialStepsJson(model.id)
        val stepCount = stepsJson.getInt("step_count")
        val totalPieces = stepsJson.getInt("total_pieces")

        // 经同一 JNI 写入口直接造「已完成」档 (与教程页写档同一实现)
        assertTrue(MagTileNative.openProgressStore(
            File(context.filesDir, MainActivity.PROGRESS_DB_NAME).absolutePath))
        assertTrue(MagTileNative.saveTutorialStep(model.id, stepCount, stepCount, 0))

        // 不带 EXTRA_RESTART: 已完成档直接落末步完成态 (桌面同口径)
        launchTutorial(model.id).use { scenario ->
            waitLoaded(scenario)
            onView(withId(R.id.tutorial_finished)).check(matches(isDisplayed()))
            scenario.onActivity { activity ->
                assertFalse(activity.findViewById<Button>(R.id.tutorial_next_button).isEnabled)
            }
        }

        // 带 EXTRA_RESTART (进度页「再搭一次」): 忽略断点从头开始
        launchTutorial(model.id, restart = true).use { scenario ->
            waitLoaded(scenario)
            onView(withId(R.id.tutorial_step_label)).check(matches(withText(
                context.getString(R.string.tutorial_step_of, 1, stepCount, 0, totalPieces))))
            scenario.onActivity { activity ->
                assertFalse("从头开始时「上一步」应禁用",
                    activity.findViewById<Button>(R.id.tutorial_prev_button).isEnabled)
                assertEquals(View.GONE,
                    activity.findViewById<View>(R.id.tutorial_finished).visibility)
            }
        }
    }

    // ---- M-01/M-02/M-03 可自动化外围: 视口在场 + 渲染模式 + 手势链路 ---

    @Test
    fun scene_viewportPresent_renderModeMatchesMotionPrefs_gesturesConsumed() {
        val model = TestSupport.smallestFreeModel(context)
        launchTutorial(model.id).use { scenario ->
            waitLoaded(scenario)
            // 视口在场 (M-01 外围; 画面正确性属人工 M-01)
            onView(withId(R.id.tutorial_scene)).check(matches(isDisplayed()))
            scenario.onActivity { activity ->
                val scene = activity.findViewById<TutorialSceneView>(R.id.tutorial_scene)
                // 呼吸动画载体 (M-03 外围): 常规档连续重绘驱动 1.2Hz
                // 呼吸; 减少动效档 (随设备系统动画设置) 切脏帧定格
                assertEquals(
                    if (scene.reduceMotion) GLSurfaceView.RENDERMODE_WHEN_DIRTY
                    else GLSurfaceView.RENDERMODE_CONTINUOUSLY,
                    scene.renderMode)
                // 手势事件链路 (M-02 外围): 合成触摸事件全部被视口消费,
                // 原生相机入口 (dragRotate/pinchZoom/pan) 不崩溃; 旋转
                // 灵敏度/缩放曲线等手感属人工 M-02
                dispatchSingleFingerDrag(scene)
                dispatchTwoFingerPinchAndPan(scene)
            }
            // 手势后页面仍存活 (视口仍在场)
            onView(withId(R.id.tutorial_scene)).check(matches(isDisplayed()))
        }
    }

    // ---- 私有工具 ------------------------------------------------------

    private fun launchTutorial(
        modelId: String, restart: Boolean = false,
    ): ActivityScenario<TutorialActivity> {
        val intent = Intent(context, TutorialActivity::class.java)
            .putExtra(TutorialActivity.EXTRA_MODEL_ID, modelId)
        if (restart) intent.putExtra(TutorialActivity.EXTRA_RESTART, true)
        return ActivityScenario.launch(intent)
    }

    /** 等待步骤数据加载完成 (加载在工作线程, tutorial_body 就绪即完成)。 */
    private fun waitLoaded(scenario: ActivityScenario<TutorialActivity>) {
        TestSupport.waitUntil(
            "分步教程数据加载完成", TestSupport.FIRST_LOAD_TIMEOUT_MS) {
            var loaded = false
            scenario.onActivity { activity ->
                loaded = activity
                    .findViewById<View>(R.id.tutorial_body).visibility == View.VISIBLE
            }
            loaded
        }
    }

    /** 主线程直接 performClick「下一步」(导航是同步的主线程状态变更)。 */
    private fun clickNext(scenario: ActivityScenario<TutorialActivity>, times: Int) {
        repeat(times) {
            scenario.onActivity { activity ->
                val next = activity.findViewById<Button>(R.id.tutorial_next_button)
                check(next.isEnabled) { "「下一步」按钮被禁用, 无法继续步进" }
                check(next.performClick()) { "「下一步」点击未被消费" }
            }
        }
    }

    /** 教程步骤数据源 (与 TutorialActivity 同一 JNI, 供期望值对账)。 */
    private fun tutorialStepsJson(modelId: String): JSONObject {
        val dataDir = DataAssetInstaller.ensureInstalled(context)
        val root = JSONObject(
            MagTileNative.getTutorialSteps(dataDir.absolutePath, modelId))
        check(!root.has("error")) { "教程步骤数据源报错: ${root.getString("error")}" }
        return root
    }

    /** 单指拖动 (轨道旋转) 合成事件: DOWN -> MOVE -> UP, 全程应被消费。 */
    private fun dispatchSingleFingerDrag(view: View) {
        val downTime = SystemClock.uptimeMillis()
        var eventTime = downTime
        val cx = (view.width / 2f).coerceAtLeast(1f)
        val cy = (view.height / 2f).coerceAtLeast(1f)
        fun send(action: Int, x: Float, y: Float) {
            val event = MotionEvent.obtain(downTime, eventTime, action, x, y, 0)
            event.source = InputDevice.SOURCE_TOUCHSCREEN
            check(view.dispatchTouchEvent(event)) { "单指手势事件未被视口消费" }
            event.recycle()
            eventTime += 16
        }
        send(MotionEvent.ACTION_DOWN, cx, cy)
        send(MotionEvent.ACTION_MOVE, cx + 40f, cy + 24f)
        send(MotionEvent.ACTION_UP, cx + 40f, cy + 24f)
    }

    /** 双指捏合 (缩放) + 双指同向滑动 (平移) 合成事件序列。 */
    private fun dispatchTwoFingerPinchAndPan(view: View) {
        val downTime = SystemClock.uptimeMillis()
        var eventTime = downTime
        val cx = (view.width / 2f).coerceAtLeast(120f)
        val cy = (view.height / 2f).coerceAtLeast(120f)

        fun obtain(action: Int, points: List<Pair<Float, Float>>): MotionEvent {
            val properties = Array(points.size) { index ->
                MotionEvent.PointerProperties().apply {
                    id = index
                    toolType = MotionEvent.TOOL_TYPE_FINGER
                }
            }
            val coords = Array(points.size) { index ->
                MotionEvent.PointerCoords().apply {
                    x = points[index].first
                    y = points[index].second
                    pressure = 1f
                    size = 1f
                }
            }
            return MotionEvent.obtain(
                downTime, eventTime, action, points.size, properties, coords,
                0, 0, 1f, 1f, 0, 0, InputDevice.SOURCE_TOUCHSCREEN, 0)
                .also { eventTime += 16 }
        }

        fun send(event: MotionEvent) {
            check(view.dispatchTouchEvent(event)) { "双指手势事件未被视口消费" }
            event.recycle()
        }

        val pointerDown1 = MotionEvent.ACTION_POINTER_DOWN or
            (1 shl MotionEvent.ACTION_POINTER_INDEX_SHIFT)
        val pointerUp1 = MotionEvent.ACTION_POINTER_UP or
            (1 shl MotionEvent.ACTION_POINTER_INDEX_SHIFT)

        send(obtain(MotionEvent.ACTION_DOWN, listOf(cx - 60f to cy)))
        send(obtain(pointerDown1, listOf(cx - 60f to cy, cx + 60f to cy)))
        // 捏合放大 (指距 120 -> 200; 首帧只重定基准, 第二帧起产生缩放)
        send(obtain(MotionEvent.ACTION_MOVE, listOf(cx - 100f to cy, cx + 100f to cy)))
        // 双指同向滑动 = 平移 (中点位移)
        send(obtain(MotionEvent.ACTION_MOVE,
            listOf(cx - 100f to (cy + 30f), cx + 100f to (cy + 30f))))
        send(obtain(pointerUp1,
            listOf(cx - 100f to (cy + 30f), cx + 100f to (cy + 30f))))
        send(obtain(MotionEvent.ACTION_UP, listOf(cx - 100f to (cy + 30f))))
    }
}

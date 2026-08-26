package com.magtile.studio

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.fail
import org.junit.Ignore
import org.junit.Test
import org.junit.runner.RunWith

/**
 * 真机人工验收占位骨架 (@Ignore, 刻意不参与自动执行):
 *
 * QA 报告 docs/reports/QA_ANDROID_CHILD_PLAYTHROUGH.md 的 P0 项
 * M-01~M-03 是**视觉正确性与手感判断**, 断言主体是人眼与手指,
 * Espresso 无法替代 —— 本类把它们登记为测试报告里的 skipped 项,
 * 作为「真机 QA 还有人工项未做」的常驻提醒; 执行载体是人工勾选表
 * [docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md] §2 (含步骤/期望/
 * 签核登记)。
 *
 * 同为 M-01~M-03 的**可自动化外围** (视口在场 / 渲染模式对应减少
 * 动效档位 / 手势事件链路被消费不崩溃) 已在 TutorialFlowTest 随
 * connectedDebugAndroidTest 自动执行, 不在此重复。
 *
 * 维护约定: 人工核验方式一旦可自动化 (如截图比对基线落地), 把对应
 * 方法移出本类改为真实断言, 并同步勾选表与 E2E_TEST_MATRIX。
 */
@RunWith(AndroidJUnit4::class)
class DeviceManualQaTest {

    /**
     * M-01 3D 渲染正确性 (P0): 片型模型 / 颜色 / 当前步橙色描边 /
     * 未放片 ghost 轮廓 / 参照片琥珀描边, 与桌面 GL/Qt 视口同观感
     * (三端同一份 GlSceneRenderer)。人工步骤: 真机打开任一免费模型
     * 教程, 逐步对照桌面 Qt 视口截图核验画面 (勾选表 §2 M-01)。
     */
    @Test
    @Ignore("人工项 M-01: 3D 渲染正确性需真机人眼核验 (截图对照桌面视口), " +
        "按 docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md §2 M-01 执行并签核")
    fun m01_sceneRenderingCorrectness_requiresHumanOnDevice() {
        fail("人工项, 不应被自动执行: 见 QA_ANDROID_DEVICE_CHECKLIST.md §2 M-01")
    }

    /**
     * M-02 触屏手势手感 (P0): 单指旋转灵敏度 (0.32°/dp) / 双指捏合
     * 缩放曲线 (12%/格对数换算) / 双指平移阻尼, 与桌面鼠标及 Qt
     * 触屏同手感。事件链路已由 TutorialFlowTest 自动覆盖; 手感判断
     * 人工 (勾选表 §2 M-02)。
     */
    @Test
    @Ignore("人工项 M-02: 触屏手势手感需真机上手判断 (旋转/缩放/平移), " +
        "按 docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md §2 M-02 执行并签核")
    fun m02_touchGestureFeel_requiresHumanOnDevice() {
        fail("人工项, 不应被自动执行: 见 QA_ANDROID_DEVICE_CHECKLIST.md §2 M-02")
    }

    /**
     * M-03 呼吸动画 (P0): 当前步新增片橙色描边 1.2Hz 正弦明暗呼吸;
     * 减少动效档定格最亮帧恒定不闪。渲染模式档位已由 TutorialFlowTest
     * 自动断言; 动画节奏与定格亮度的视觉核验人工 (勾选表 §2 M-03)。
     */
    @Test
    @Ignore("人工项 M-03: 呼吸动画 (1.2Hz 明暗) 与减少动效定格需真机人眼核验, " +
        "按 docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md §2 M-03 执行并签核")
    fun m03_pulseAnimation_requiresHumanOnDevice() {
        fail("人工项, 不应被自动执行: 见 QA_ANDROID_DEVICE_CHECKLIST.md §2 M-03")
    }
}

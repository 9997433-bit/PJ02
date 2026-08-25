package com.magtile.studio

import android.content.Context
import android.provider.Settings

/**
 * 减少动效偏好 (UI_UX_SPEC.md §4.7, 与桌面 Qt Theme.reduceMotion 同
 * 语义): Android 侧低成本读**系统动画设置** —— 家长在系统「无障碍 >
 * 移除动画」或开发者选项里把动画时长/过渡缩放调到 0 时视为开启,
 * 无需新增应用内开关与 JNI 链路 (应用内共享 reduce_motion 设置键的
 * 接通见 README 后续计划)。
 *
 * 开启后的降级 (信息一点不少, 只去掉运动):
 *   - 列表滚动定位: smoothScroll 换瞬时 scrollToPosition;
 *   - 点按反馈: 水波纹扩散退为静态按压色 (bg_model_card_calm /
 *     bg_row_pressed_flat);
 *   - 3D 教程视口: 呼吸描边定格最亮帧且不自驱重绘 (与桌面
 *     kFrozenPulseSeconds 同口径, 见 TutorialSceneView)。
 *
 * 每屏 onCreate 读一次 (两次 Settings.Global 查询, 亚毫秒级);
 * 会话中途改系统设置下次进屏生效, 与桌面切开关即时生效相比是
 * 可接受的低成本折衷。
 */
object MotionPrefs {

    /** 系统动画是否被关闭 (动画时长或过渡缩放为 0 即视为减少动效)。 */
    fun reduceMotion(context: Context): Boolean {
        val resolver = context.contentResolver
        val animator = Settings.Global.getFloat(
            resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
        val transition = Settings.Global.getFloat(
            resolver, Settings.Global.TRANSITION_ANIMATION_SCALE, 1f)
        return animator == 0f || transition == 0f
    }
}

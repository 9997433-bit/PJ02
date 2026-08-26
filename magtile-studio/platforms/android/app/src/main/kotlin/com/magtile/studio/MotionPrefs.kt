package com.magtile.studio

import android.content.Context
import android.provider.Settings

/**
 * 减少动效偏好 (UI_UX_SPEC.md §4.7, 与桌面 Qt Theme.reduceMotion 同
 * 语义), 双通道任一命中即开启:
 *   1. 应用内共享 reduce_motion 设置键 (settings 表, 桌面 GL/Qt
 *      设置页开关同键同一份 SQLite 存档, 经 MagTileNative JNI 读取;
 *      存档尚未打开时原生层返回 false 温和降级, 由通道 2 兜底 ——
 *      MainActivity 冷启动开档后会复读一次);
 *   2. 系统动画设置 —— 家长在系统「无障碍 > 移除动画」或开发者
 *      选项里把动画时长/过渡缩放调到 0 时视为开启。
 *
 * 开启后的降级 (信息一点不少, 只去掉运动):
 *   - 列表滚动定位: smoothScroll 换瞬时 scrollToPosition;
 *   - 点按反馈: 水波纹扩散退为静态按压色 (bg_model_card_calm /
 *     bg_row_pressed_flat);
 *   - 3D 教程视口: 呼吸描边定格最亮帧且不自驱重绘 (与桌面
 *     kFrozenPulseSeconds 同口径, 见 TutorialSceneView)。
 *
 * 每屏 onCreate 读一次 (一次 JNI 键读取 + 两次 Settings.Global
 * 查询, 均亚毫秒级); 会话中途改设置下次进屏生效, 与桌面切开关
 * 即时生效相比是可接受的低成本折衷。
 */
object MotionPrefs {

    /** 减少动效是否开启 (应用内共享设置键 或 系统动画被关闭)。 */
    fun reduceMotion(context: Context): Boolean {
        // 通道 1: 共享 reduce_motion 键 (对齐桌面 GL/Qt, §16.2 P1 收口)
        if (MagTileNative.reduceMotion()) return true
        // 通道 2: 系统动画时长或过渡缩放为 0 即视为减少动效
        val resolver = context.contentResolver
        val animator = Settings.Global.getFloat(
            resolver, Settings.Global.ANIMATOR_DURATION_SCALE, 1f)
        val transition = Settings.Global.getFloat(
            resolver, Settings.Global.TRANSITION_ANIMATION_SCALE, 1f)
        return animator == 0f || transition == 0f
    }
}

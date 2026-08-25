package com.magtile.studio

import android.annotation.SuppressLint
import android.content.Context
import android.opengl.GLSurfaceView
import android.os.SystemClock
import android.util.AttributeSet
import android.view.MotionEvent
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10
import kotlin.math.hypot

/**
 * 3D 教程视口 (GLSurfaceView + GLES3): 渲染循环与触屏手势的 Android
 * 外壳, 绘制本体在原生层 (TutorialSceneNative -> GlSceneRenderer,
 * 与桌面 GLFW/ImGui、Qt FBO 视口同一份场景渲染器)。
 *
 * 触屏手势与 Qt 教程视口 (tutorial_viewport.cpp touchEvent) 同一
 * 口径: 单指拖动 = 轨道旋转 (0.32°/dp), 双指捏合 = 缩放 (指距比经
 * 对数换算, 12%/格), 双指同向滑动 = 平移 (中点位移)。手指数变化
 * (落下/抬起第二指) 的当帧只重定基准 —— 基准点语义随手指数切换
 * (单指位置 <-> 双指中点), 跨口径求差会跳变。
 *
 * 渲染模式为连续重绘: 本步新增片的呼吸描边动画由帧时间驱动 (与
 * 桌面同一实现); 视口离屏时由宿主 Activity 转发 onPause 停帧,
 * 不在后台空转。场景很小 (数百片薄板), 单帧 GPU 开销可忽略。
 */
class TutorialSceneView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : GLSurfaceView(context, attrs) {

    private val density = resources.displayMetrics.density

    // 手势基准: 单指 = 触点位置, 双指 = 两指中点 + 指距
    private var touchPointCount = 0
    private var anchorX = 0f
    private var anchorY = 0f
    private var lastSpread = 0f

    init {
        setEGLContextClientVersion(3)
        setRenderer(SceneRenderer())
        renderMode = RENDERMODE_CONTINUOUSLY
    }

    /**
     * 触屏手势 (纯相机操作, 无点击语义, 不需要 performClick 无障碍
     * 通道 —— 步骤导航走下方的实体大按钮)。
     */
    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.actionMasked == MotionEvent.ACTION_CANCEL) {
            touchPointCount = 0
            return true
        }

        // 只统计仍按住的触点 (UP/POINTER_UP 里正在抬起的那根不参与)
        val liftedIndex = when (event.actionMasked) {
            MotionEvent.ACTION_UP,
            MotionEvent.ACTION_POINTER_UP -> event.actionIndex
            else -> -1
        }
        val xs = ArrayList<Float>(event.pointerCount)
        val ys = ArrayList<Float>(event.pointerCount)
        for (i in 0 until event.pointerCount) {
            if (i == liftedIndex) continue
            xs.add(event.getX(i))
            ys.add(event.getY(i))
        }

        // 手指数变化的当帧只重定基准, 不产生相机位移
        val countStable = xs.size == touchPointCount

        if (xs.size == 1) {
            // 单指拖动 = 轨道旋转 (dp 位移, 密度无关手感与桌面一致)
            if (countStable) {
                TutorialSceneNative.dragRotate(
                    ((xs[0] - anchorX) / density).toDouble(),
                    ((ys[0] - anchorY) / density).toDouble())
            }
            anchorX = xs[0]
            anchorY = ys[0]
        } else if (xs.size >= 2) {
            // 三指及以上取前两指 (与 Qt 同策略)
            val midX = (xs[0] + xs[1]) * 0.5f
            val midY = (ys[0] + ys[1]) * 0.5f
            val spread = hypot(xs[0] - xs[1], ys[0] - ys[1])
            if (countStable) {
                // 双指捏合 = 缩放: 双指过近时指距比噪声过大, 低于阈值
                // 的帧只重定基准 (kMinPinchSpreadPx 同款守卫)
                val minSpread = MIN_PINCH_SPREAD_DP * density
                if (spread > minSpread && lastSpread > minSpread) {
                    TutorialSceneNative.pinchZoom((spread / lastSpread).toDouble())
                }
                // 双指同向滑动 = 平移 (中点位移, 物理像素对视口高)
                TutorialSceneNative.pan(
                    (midX - anchorX).toDouble(), (midY - anchorY).toDouble(),
                    height.coerceAtLeast(1))
            }
            anchorX = midX
            anchorY = midY
            lastSpread = spread
        }
        touchPointCount = xs.size
        return true
    }

    /** GL 渲染线程回调: 初始化 / 尺寸 / 每帧绘制全部转发原生层。 */
    private class SceneRenderer : Renderer {
        private var width = 0
        private var height = 0
        private val clockStartMs = SystemClock.uptimeMillis()

        override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
            // 表面创建 / Home 后返回的上下文重建: 原生侧重建 GL 资源
            TutorialSceneNative.surfaceCreated()
        }

        override fun onSurfaceChanged(gl: GL10?, w: Int, h: Int) {
            width = w
            height = h
        }

        override fun onDrawFrame(gl: GL10?) {
            TutorialSceneNative.drawFrame(
                width, height, (SystemClock.uptimeMillis() - clockStartMs) / 1000.0)
        }
    }

    companion object {
        /** 捏合最小指距 (dp): 与 Qt kMinPinchSpreadPx (逻辑像素) 同值。 */
        private const val MIN_PINCH_SPREAD_DP = 8f
    }
}

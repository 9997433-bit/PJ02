package com.magtile.studio

/**
 * 3D 教程视口的 JNI 桥 (实现见 jni/magtile_scene_jni.cpp)。
 *
 * 原生侧复用与桌面 GLFW/ImGui、Qt FBO 教程视口完全同一份场景渲染器
 * `render::GlSceneRenderer` (magtile_render_scene, GLES3 下着色器版本
 * 头自动切 300 es) 与 `tutorial::TutorialEngine` 步骤语义: 当前步新增
 * 片橙色描边 + 呼吸动画, 未放片 ghost 淡化轮廓, 参照片琥珀描边 ——
 * 三端同一口径。相机手势常量 (0.32°/px 旋转、12%/格缩放) 单一来源
 * 在原生层, 与桌面完全一致。
 *
 * 线程约定: [surfaceCreated] / [drawFrame] 只能在 GLSurfaceView 渲染
 * 线程调用 (GL 资源属于该线程的 EGL 上下文); 其余方法可从主线程 /
 * 工作线程调用, 会话状态由原生互斥锁保护。
 */
object TutorialSceneNative {

    /**
     * 加载教程场景 (dataDir = 解包后的数据目录, modelId 经模型库目录
     * 解析到模型 JSON, 与 getTutorialSteps 同一口径): 创建教程引擎 +
     * 按最终成品包围盒取景 + 跳到断点步 resumeStep (0 = 从头 ->
     * 第 1 步, 越界自动夹到合法区间)。返回教程步骤数; 失败返回 -1
     * (视口温和降级为只画地面网格, 文字分步照常可用)。
     */
    external fun loadScene(dataDir: String, modelId: String, resumeStep: Int): Int

    /**
     * 跳到指定步 (1..stepCount, "当前展示步" 语义: 该步新增片以描边 +
     * 呼吸态显示, 之后的片为 ghost 轮廓): 越界自动夹取; 未加载时空操作。
     */
    external fun setStep(step: Int)

    /** 释放会话 (教程页销毁时调用); GL 资源随 EGL 上下文由系统回收。 */
    external fun releaseScene()

    /**
     * 单指拖动 = 轨道旋转: dx/dy 为逻辑像素 (dp) 位移 —— 原生按
     * 0.32°/px 换算 (与桌面鼠标左键拖动 / Qt 触屏单指同一手感)。
     */
    external fun dragRotate(dxDp: Double, dyDp: Double)

    /**
     * 双指捏合 = 缩放: spreadRatio 为本帧指距 / 上帧指距, 原生经对数
     * 换算成等效滚轮格数 (与 Qt 捏合 / 桌面滚轮共用 12%/格 缩放口径,
     * 指距张大一倍成品恰好放大一倍, 缩放跟手不窜)。
     */
    external fun pinchZoom(spreadRatio: Double)

    /**
     * 双指同向滑动 = 平移: dx/dy 与 viewportHeightPx 均为物理像素
     * (原生按视口高换算世界距离, 只依赖比值, 屏幕密度自然抵消)。
     */
    external fun pan(dxPx: Double, dyPx: Double, viewportHeightPx: Int)

    /** 表面创建 / EGL 上下文重建 (仅 GL 渲染线程): 重建 GL 资源。 */
    external fun surfaceCreated()

    /**
     * 绘制一帧 (仅 GL 渲染线程): timeSeconds 为单调递增秒数, 驱动
     * 本步新增片的呼吸动画。场景未加载时画清屏 + 地面网格。
     */
    external fun drawFrame(width: Int, height: Int, timeSeconds: Double)

    init {
        // 与 MainActivity / MagTileNative 共用同一 libmagtile_core.so
        System.loadLibrary("magtile_core")
    }
}

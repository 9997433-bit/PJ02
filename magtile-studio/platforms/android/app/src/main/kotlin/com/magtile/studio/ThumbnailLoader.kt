package com.magtile.studio

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Handler
import android.os.Looper
import android.util.LruCache
import android.widget.ImageView
import java.util.Collections
import java.util.concurrent.Executors

/**
 * 模型卡片缩略图加载器: 直接流式读取 APK assets/thumbnails/<id>.png
 * (320x240, 约 30 KB/张), 不解包落盘。
 *
 * - 解码在单线程池执行, 主线程只做缓存命中与 setImageBitmap;
 * - LruCache 以字节计容量 (上限取进程内存 1/8), 320x240 ARGB_8888
 *   单张约 300 KB, 全库 131 张约 38 MB, 低内存机型按 LRU 逐出;
 * - asset 缺失 (模型无缩略图) 记入负缓存, 避免复用滚动反复尝试 IO;
 * - RecyclerView 复用安全: ImageView 以 asset 路径作 tag, 解码完成
 *   回主线程时 tag 已变 (view 被复用于其他卡片) 则丢弃结果。
 */
object ThumbnailLoader {

    private val decodeExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())

    private val cache = object : LruCache<String, Bitmap>(
        ((Runtime.getRuntime().maxMemory() / 8).coerceAtMost(Int.MAX_VALUE.toLong())).toInt()
    ) {
        override fun sizeOf(key: String, value: Bitmap) = value.byteCount
    }

    /** 打开/解码失败过的 asset 路径 (通常是缩略图不存在), 不再重试。 */
    private val missing: MutableSet<String> = Collections.synchronizedSet(mutableSetOf())

    /**
     * 把 assetPath 对应的缩略图异步装入 view; 缺失或解码前显示占位背景
     * (view 的 background 即占位, 这里只清空前景)。在主线程调用。
     */
    fun load(view: ImageView, assetPath: String) {
        view.tag = assetPath

        cache.get(assetPath)?.let {
            view.setImageBitmap(it)
            return
        }
        view.setImageBitmap(null)
        if (assetPath in missing) return

        val appContext = view.context.applicationContext
        decodeExecutor.execute {
            val bitmap = decode(appContext, assetPath)
            if (bitmap == null) {
                missing.add(assetPath)
                return@execute
            }
            cache.put(assetPath, bitmap)
            mainHandler.post {
                if (view.tag == assetPath) view.setImageBitmap(bitmap)
            }
        }
    }

    private fun decode(context: Context, assetPath: String): Bitmap? = try {
        context.assets.open(assetPath).use { BitmapFactory.decodeStream(it) }
    } catch (_: Exception) {
        null
    }
}

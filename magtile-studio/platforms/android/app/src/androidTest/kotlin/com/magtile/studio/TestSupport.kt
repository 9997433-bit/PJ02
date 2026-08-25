package com.magtile.studio

import android.content.Context
import android.os.SystemClock
import org.json.JSONObject
import org.junit.Assert.fail
import java.io.File

/**
 * 仪器测试共享工具 (androidTest 专用, 不进产品 APK):
 *
 *   - [waitUntil]: 轮询等待 (启动链路在工作线程, Espresso 不会自动
 *     等待, 与 MainActivitySmokeTest 同一稳定性策略);
 *   - [deleteProgressStore]: 删除 progress.db 回到首启状态 (年龄段回
 *     默认 7-9 档 / 未订阅 / 库存未登记 / 无教程进度), 各测试 @Before
 *     调用, 断言不受上一次运行残留影响;
 *   - [installedCatalog]: 解包数据资产后直读 model_catalog.json,
 *     供测试在启动 Activity 前按目录挑选模型 (免费判定与
 *     core::isFreeTierModel 同口径 —— 目录 tags 含「免费」; 列表
 *     顺序 = listModels JNI 下发顺序 = 目录顺序, 卡片 position
 *     可直接对位)。刻意在 Activity 启动前调用, 避免与 Activity
 *     工作线程的首次解包并发。
 */
object TestSupport {

    /** 首启加载上限: 含 assets/data 解包 + JNI 目录加载 (慢设备兜底)。 */
    const val FIRST_LOAD_TIMEOUT_MS = 120_000L

    /** 纯 UI 状态变化 (筛选刷新 / 下一帧布局 / 弹窗) 的等待上限。 */
    const val UI_TIMEOUT_MS = 10_000L

    /** 进度落盘等待上限 (写档在单线程 backgroundExecutor, 秒级足够)。 */
    const val SAVE_TIMEOUT_MS = 15_000L

    private const val POLL_INTERVAL_MS = 100L

    /** 轮询等待条件成立, 超时 fail 并带出等待目标 (中文可读)。 */
    fun waitUntil(what: String, timeoutMs: Long, condition: () -> Boolean) {
        val deadline = SystemClock.elapsedRealtime() + timeoutMs
        while (SystemClock.elapsedRealtime() < deadline) {
            if (condition()) return
            SystemClock.sleep(POLL_INTERVAL_MS)
        }
        fail("等待超时 (${timeoutMs}ms): $what")
    }

    /** 删除进度存档回到首启状态 (资产解包版本戳不在此文件, 不受影响)。 */
    fun deleteProgressStore(context: Context) {
        File(context.filesDir, MainActivity.PROGRESS_DB_NAME).delete()
    }

    /**
     * 模型库目录一行 (测试视角的最小字段集):
     * @param position 目录序 = 无筛选时模型库列表的卡片 position
     * @param free 免费层判定 (目录 tags 含「免费」, 与桌面同口径)
     * @param stepCount 教程步数 (目录 step_count 字段)
     */
    data class CatalogEntry(
        val position: Int,
        val id: String,
        val name: String,
        val free: Boolean,
        val stepCount: Int,
    )

    /** 解包 (幂等, 版本戳一致零拷贝) 并直读 model_catalog.json。 */
    fun installedCatalog(context: Context): List<CatalogEntry> {
        val dataDir = DataAssetInstaller.ensureInstalled(context)
        val models = JSONObject(File(dataDir, "model_catalog.json").readText())
            .getJSONArray("models")
        return (0 until models.length()).map { i ->
            val model = models.getJSONObject(i)
            val tags = model.optJSONArray("tags")
            var free = false
            if (tags != null) {
                for (j in 0 until tags.length()) {
                    if (tags.getString(j) == "免费") free = true
                }
            }
            CatalogEntry(
                position = i,
                id = model.getString("id"),
                name = model.getString("name"),
                free = free,
                stepCount = model.optInt("step_count"),
            )
        }
    }

    /** 步数最少的免费模型 (教程走查用, 至少 4 步保证断点断言有意义;
     *  免费层直达教程, 不需要订阅即可开搭)。 */
    fun smallestFreeModel(context: Context): CatalogEntry =
        installedCatalog(context)
            .filter { it.free && it.stepCount >= 4 }
            .minByOrNull { it.stepCount }
            ?: error("模型库目录中没有 >= 4 步的免费模型 (免费层清单异常)")

    /** 目录序第一个非免费模型 (订阅锁可见性断言用)。 */
    fun firstNonFreeModel(context: Context): CatalogEntry =
        installedCatalog(context).firstOrNull { !it.free }
            ?: error("模型库目录中没有非免费模型 (目录异常)")
}

package com.magtile.studio

import android.content.Context
import android.content.res.AssetManager
import java.io.File

/**
 * 把 APK assets/data (Gradle stageMagTileAssets 任务打入的仓库 data/
 * 子集: tile_catalog.json + model_catalog.json + models/) 解包到
 * filesDir/data —— magtile_core 走 std::filesystem 读取真实文件路径,
 * 不能直接读 assets 流, 故首次启动 (或 APK 更新后) 需要落盘一次。
 *
 * 解包完成后写入版本戳 (APK lastUpdateTime); 版本戳一致时直接复用,
 * 日常启动零拷贝。
 */
object DataAssetInstaller {

    private const val ASSET_ROOT = "data"
    private const val STAMP_FILE = ".data_stamp"

    /** 确保数据资产已解包, 返回 filesDir/data 目录。在工作线程调用。 */
    fun ensureInstalled(context: Context): File {
        val targetDir = File(context.filesDir, ASSET_ROOT)
        val stampFile = File(context.filesDir, STAMP_FILE)
        val currentStamp = context.packageManager
            .getPackageInfo(context.packageName, 0)
            .lastUpdateTime.toString()

        if (targetDir.isDirectory && stampFile.isFile &&
            stampFile.readText() == currentStamp
        ) {
            return targetDir
        }

        // APK 更新后全量重解包, 防止旧版残留文件与新目录混杂
        targetDir.deleteRecursively()
        copyAssetTree(context.assets, ASSET_ROOT, targetDir)
        stampFile.writeText(currentStamp)
        return targetDir
    }

    /** 递归复制 assets 子树。AssetManager.list() 对文件返回空数组。 */
    private fun copyAssetTree(assets: AssetManager, assetPath: String, dest: File) {
        val children = assets.list(assetPath).orEmpty()
        if (children.isEmpty()) {
            dest.parentFile?.mkdirs()
            assets.open(assetPath).use { input ->
                dest.outputStream().use { output -> input.copyTo(output) }
            }
        } else {
            children.forEach { child ->
                copyAssetTree(assets, "$assetPath/$child", File(dest, child))
            }
        }
    }
}

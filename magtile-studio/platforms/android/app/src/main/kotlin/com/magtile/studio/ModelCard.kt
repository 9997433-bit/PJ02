package com.magtile.studio

import org.json.JSONObject

/**
 * 模型库中一张卡片的展示元数据 (JNI listModels() 返回的 JSON 条目)。
 * 只含展示字段, 模型几何与教程步骤在用户点击后按需加载。
 */
data class ModelCard(
    val id: String,
    val name: String,
    val nameEn: String,
    val description: String,
    val difficulty: Int,
    val totalPieces: Int,
    val stepCount: Int,
    val theme: String,
    /** 模型 JSON 绝对路径 (filesDir 下), 可直接传给 validateModel()。 */
    val filePath: String,
    /** BOM 是否判定成功 (模型文件有问题时 false, 按 "BOM 未知" 降级)。 */
    val bomKnown: Boolean,
    /** 只用核心 9 片型即可搭建 (原生层 core::isCoreTile 共享口径判定)。 */
    val core9Only: Boolean,
    /** 库存足够搭建 (库存已登记且 BOM 满足; 未登记时恒 false)。 */
    val canBuild: Boolean,
    /** 库存对照 BOM 共缺几片 (未登记 / BOM 未知时为 0)。 */
    val missingTotal: Int,
    /** 免费层模型 (原生层 core::isFreeTierModel 共享口径: 目录 tags
     *  含「免费」); 非免费只在详情作温和订阅提示, 浏览不受限。 */
    val isFree: Boolean,
) {
    /** 难度星显示: 实心 = 难度值, 补空心到 5 星, 如 ★★☆☆☆。 */
    val difficultyStars: String
        get() {
            val filled = difficulty.coerceIn(0, 5)
            return "★".repeat(filled) + "☆".repeat(5 - filled)
        }

    /**
     * 卡片缩略图在 APK assets 中的路径 (thumbnails/<id>.png 约定,
     * 与核心库 findThumbnail 的 data/thumbnails/<id>.png 约定一致)。
     * 缩略图只被 Kotlin UI 消费, 不解包到 filesDir, 由 ThumbnailLoader
     * 直接流式读取; asset 不存在时显示占位背景。
     */
    val thumbnailAssetPath: String
        get() = "thumbnails/$id.png"

    /** 需要扩展装角标: BOM 已知且用到了核心 9 片之外的片型。 */
    val needsExpansion: Boolean
        get() = bomKnown && !core9Only

    companion object {
        /**
         * 解析 listModels() 的返回值。
         * @throws IllegalStateException 原生层报错 ({"error": "..."})。
         */
        fun libraryFromJson(payload: String): ModelLibrary {
            val root = JSONObject(payload)
            if (root.has("error")) {
                throw IllegalStateException(root.getString("error"))
            }
            val models = root.getJSONArray("models")
            return ModelLibrary(
                inventoryConfigured = root.optBoolean("inventory_configured", false),
                cards = List(models.length()) { index ->
                    fromJson(models.getJSONObject(index))
                },
            )
        }

        private fun fromJson(obj: JSONObject) = ModelCard(
            id = obj.getString("id"),
            name = obj.getString("name"),
            nameEn = obj.optString("name_en"),
            description = obj.optString("description"),
            difficulty = obj.getInt("difficulty"),
            totalPieces = obj.getInt("total_pieces"),
            stepCount = obj.getInt("step_count"),
            theme = obj.optString("theme"),
            filePath = obj.getString("file"),
            bomKnown = obj.optBoolean("bom_known", false),
            core9Only = obj.optBoolean("core9_only", false),
            canBuild = obj.optBoolean("can_build", false),
            missingTotal = obj.optInt("missing_total", 0),
            // 字段缺失按免费处理 (宁可少提示, 不误锁内容)
            isFree = obj.optBoolean("free", true),
        )
    }
}

/**
 * listModels() 的完整解析结果: 卡片列表 + 磁力片库存是否已登记
 * (未登记时「我能搭的」筛选禁用并引导去录入, 与桌面 GL 同口径)。
 */
data class ModelLibrary(
    val inventoryConfigured: Boolean,
    val cards: List<ModelCard>,
)

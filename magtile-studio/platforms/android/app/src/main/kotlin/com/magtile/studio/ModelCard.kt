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
) {
    /** 难度星显示: 实心 = 难度值, 补空心到 5 星, 如 ★★☆☆☆。 */
    val difficultyStars: String
        get() {
            val filled = difficulty.coerceIn(0, 5)
            return "★".repeat(filled) + "☆".repeat(5 - filled)
        }

    companion object {
        /**
         * 解析 listModels() 的返回值。
         * @throws IllegalStateException 原生层报错 ({"error": "..."})。
         */
        fun listFromJson(payload: String): List<ModelCard> {
            val root = JSONObject(payload)
            if (root.has("error")) {
                throw IllegalStateException(root.getString("error"))
            }
            val models = root.getJSONArray("models")
            return List(models.length()) { index ->
                fromJson(models.getJSONObject(index))
            }
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
        )
    }
}

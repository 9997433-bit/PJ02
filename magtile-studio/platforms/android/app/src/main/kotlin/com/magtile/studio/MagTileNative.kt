package com.magtile.studio

/**
 * 进度存档 / 磁力片库存的 JNI 桥 (实现见 jni/magtile_jni.cpp)。
 *
 * 直接复用核心库 progress::ProgressStore —— 与桌面 CLI `inventory set`
 * / GL / Qt 录入界面同一份 SQLite schema (tile_inventory 表), 存档文件
 * 互相兼容。数据库放在 filesDir/progress.db (应用私有目录, 随
 * allowBackup 自动备份)。
 *
 * 放在独立 object 上 (而非 MainActivity): MainActivity 与
 * InventoryActivity 都要调用, 且原生上下文本就是进程级单例。
 */
object MagTileNative {

    /** 打开 (不存在则创建) 进度存档数据库; 失败返回 false (详见 logcat)。 */
    external fun openProgressStore(dbPath: String): Boolean

    /**
     * 库存录入界面数据源 JSON (全部片型按核心 9 片在前的枚举顺序):
     * {"configured":bool,"total":N,"shapes":[{"id","name_zh","expansion","count"},...]}
     */
    external fun inventoryRows(): String

    /**
     * 保存库存快照 JSON ({"square":12,...}): 数量夹到 [0,999], 未知
     * 片型跳过; count=0 也保留记录 ("明确没有" 不再触发引导)。
     * 存档未打开或写入失败返回 false (界面温和提示, 不弹 "失败")。
     */
    external fun saveInventory(countsJson: String): Boolean

    /**
     * 库存是否足够搭建模型 (jsonPath = listModels 返回的 file 字段):
     * 1 = 够搭, 0 = 缺片, -1 = 无法判定 (未登记库存 / 模型文件有问题)。
     */
    external fun canBuildModel(jsonPath: String): Int

    /**
     * 缺片清单 JSON: {"configured","can_build","missing_total",
     * "missing":[{"id","name_zh","count"}],"text":"缺 2 片正方形、…"}
     * 或 {"error":"..."}; 措辞与桌面 Qt missingText 一致。
     */
    external fun missingPiecesJson(jsonPath: String): String

    init {
        // 与 MainActivity 共用同一 libmagtile_core.so (loadLibrary 幂等)
        System.loadLibrary("magtile_core")
    }
}

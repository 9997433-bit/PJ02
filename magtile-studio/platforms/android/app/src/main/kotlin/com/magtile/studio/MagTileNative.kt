package com.magtile.studio

/**
 * 进度存档 / 磁力片库存 / 分步教程的 JNI 桥 (实现见 jni/magtile_jni.cpp)。
 *
 * 直接复用核心库 progress::ProgressStore —— 与桌面 CLI `inventory set`
 * / GL / Qt 录入界面同一份 SQLite schema (tile_inventory 表), 存档文件
 * 互相兼容。数据库放在 filesDir/progress.db (应用私有目录, 随
 * allowBackup 自动备份)。
 *
 * 放在独立 object 上 (而非 MainActivity): MainActivity /
 * InventoryActivity / ProgressActivity / TutorialActivity 都要调用,
 * 且原生上下文本就是进程级单例。
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

    /**
     * 当前年龄段模式标识: "age_4_6" / "age_7_9" / "age_10_12"
     * (settings 表 age_mode 键 —— 与桌面 GL/Qt/CLI 同键, 同一份
     * SQLite 存档语义)。存档未打开 / 从未设置 / 存量脏值一律返回
     * 默认档 "age_7_9" (原生层自带兜底), 调用方无需判空。
     */
    external fun ageModeId(): String

    /**
     * 保存年龄段模式 (立即落盘): 未知标识返回 false 并忽略 (与桌面
     * SettingsBackend 一致); 存档未打开或落盘失败仍返回 true ——
     * 设置在本次运行内生效, 只是重启后回读不到 (温和降级)。
     */
    external fun setAgeModeId(modeId: String): Boolean

    /**
     * 进度页「我的作品」/ 成就墙数据源 JSON (dataDir = 解包后的数据
     * 目录, 与 listModels 同一入参; 口径与桌面 Qt StudioBackend 一致):
     * {"store_ready","completed_count","in_progress_count",
     *  "favorite_count","achievement_count",
     *  "in_progress":[{"id","name","current_step","step_count","play_text"}],
     *  "completed":[{"id","name","pieces","meta_text"}],
     *  "favorites":[{"id","name"}],
     *  "achievements":[{"id","name","condition","unlocked","unlocked_text"}]}
     * 或 {"error":"..."}。徽章 emoji 由 Kotlin 侧按 id 映射 (增补平面
     * 字符不过 NewStringUTF); 存档不可用时列表为空、徽章全未点亮,
     * 页面照常可看 (P3 零挫败)。
     */
    external fun progressOverviewJson(dataDir: String): String

    /**
     * 分步教程步骤数据源 JSON (dataDir = 解包后的数据目录, 与
     * listModels 同一入参; modelId 经模型库目录解析到模型 JSON):
     * {"model_id","name","step_count","total_pieces",
     *  "steps":[{"step_number","description","tip","pieces_added",
     *            "pieces_total"}]} 或 {"error":"..."}。
     * pieces_added = 本步骤新增片数, pieces_total = 累计已放片数
     * (末步 = total_pieces)。供 TutorialActivity 步骤浏览使用。
     */
    external fun getTutorialSteps(dataDir: String, modelId: String): String

    /**
     * 存档中该模型的当前步 (断点续搭): 无记录 / 存档不可用一律返回 0
     * (从头开始, 温和降级)。已完成模型返回总步数 (完成链路推到最后
     * 一步), 调用方据此进入完成态。
     */
    external fun savedTutorialStep(modelId: String): Int

    /**
     * 写教程进度 (与桌面 Qt TutorialViewport 同一口径, 同一份 SQLite
     * schema): step = 已完成到第几步, playSeconds = 本次新增游玩秒数
     * (存储层累加); 走到最后一步 (step >= stepCount) 记完成 + 解锁
     * 首搭成就。存档未打开 / 写入失败返回 false (不打断搭建, 进度仍
     * 在内存中 —— P3 零挫败)。
     */
    external fun saveTutorialStep(
        modelId: String, step: Int, stepCount: Int, playSeconds: Long): Boolean

    // ---- 家长门 (UI_UX_SPEC.md §9, 复用 core::ParentGate 共享状态机:
    //      乘法题 + 中文大写数字答案 + 3 次答错 60 秒冷却 + 15 分钟
    //      内存会话; 会话/冷却只存内存永不落盘, 防重启绕过) ----------

    /**
     * 进门出新题 (每次进门新题防背题, 与桌面 ParentGateBackend 同口径):
     * {"question":"叁 × 柒 = ?","attempts_remaining":N,
     *  "cooldown_seconds":N,"session_active":bool}。
     * 仍在上一轮冷却期时 cooldown_seconds > 0, 界面据此直接进温和的
     * 「休息一下」倒计时, 不显示题面。
     */
    external fun parentGateOpenJson(): String

    /**
     * 提交答案 (中文大写数字, 如 "贰拾壹"; 接受 "壹拾贰"/"拾贰" 变体):
     * {"result":"passed"|"wrong"|"cooling","attempts_remaining":N,
     *  "cooldown_seconds":N,"session_active":bool}。
     * passed = 15 分钟家长会话已开启; wrong = 答错温和提示再试;
     * cooling = 冷却期内 (含触发冷却那次), 温和提示稍后再试。
     */
    external fun parentGateSubmitJson(answer: String): String

    /**
     * 家长会话是否仍有效: true = 15 分钟守卫期内免重复验证 (与桌面
     * Qt 会话守卫同策略, 时长读 core::ParentGate 现有常量; 会话只存
     * 内存, 重启即失效)。
     */
    external fun parentGateSessionActive(): Boolean

    init {
        // 与 MainActivity 共用同一 libmagtile_core.so (loadLibrary 幂等)
        System.loadLibrary("magtile_core")
    }
}

# content_series_map.json — 内容系列权威词表

`content_meta.series` (schema v2 正字段, [CONTENT_STRATEGY.md](../docs/CONTENT_STRATEGY.md) §5.1) 与 `content_meta.matrix_bucket` 的**合法取值全集**, 外加全库 250 模型的归类底稿。三个数据节:

1. **`series` — 13 个策略主题** (每项 `matrix_bucket: null`): 与策略 §2.2「主题 × 难度分布矩阵」逐行对应, 中文名逐字一致; slug 为英文 snake_case, 其中 `bridge_engineering` 沿用策略 §5.1 schema 示例的既有写法。矩阵内模型 `content_meta.series` 取这 13 个 slug 之一, **计入矩阵进度**。`matrix_bucket: null` 表示该 series 本身在矩阵内; 若日后矩阵治理决断 (缺口审计 §6) 裁并某主题, 以此字段登记去向。
2. **`off_matrix_buckets` — 11 个矩阵外桶**: 与 [CONTENT_GAP_AUDIT.md](../docs/reports/CONTENT_GAP_AUDIT.md) §6 的矩阵外聚类一一对应 (城市生活/运动/田园/工程结构/音乐/自然世界/校园/游乐园/海洋航行/博物馆/其他); §6 的四个单例聚类 (极地/航天探索/夏日乐园/足球) 一律并入 `other` (即审计原文的「其他 4」)。矩阵外模型 `content_meta.series = null` 且 `content_meta.matrix_bucket` 取桶 slug, **不计入**矩阵格子。带 `_misc` 后缀者 (`engineering_misc`/`nature_misc`/`maritime_misc`) 是为了与矩阵主题 (`bridge_engineering`/`animal_world`·`plant_garden`/`sea_air_transport`) 明确区隔。
3. **`models` — 250 模型归类底稿**: 逐 id 登记 series 或 matrix_bucket, 录自缺口审计附录 A 的逐模型归类清单 (含批 F–I 裁定)。

## 消费方

- **`tools/backfill_content_series.py`** (幂等回填, 审计 §7.3 建议 3): 按 `models` 节把 series/matrix_bucket 写回每个模型 JSON, 只动这两个键; 词表校验以本文件 `series` / `off_matrix_buckets` 两节为准。
- **`tools/check_content_series`** (机检): 校验每个模型 JSON 的 `content_meta` ① series 与 matrix_bucket 恰有其一非空 ② 取值落在本词表内 ③ 与 `models` 节一致; 并输出矩阵内/外的主题 × 难度进度表, 替代人工归类。

## 维护规则

- **slug 一经回填不得改名** (改名 = 全库迁移 + 工具同步, 须策展人签发)。
- **新增/裁并 series 或桶是策展决断** (缺口审计 §6 的「修订矩阵 / 冻结矩阵外供给」二选一), 不得因单个模型难归类而随手加词; 确无归属的一律入 `other`。
- 新模型入库时在 `models` 节登记归类, 随后跑回填工具落盘。
- 中文名与策略/审计文档保持逐字一致; 词表节手工维护, 禁止任何工具生成覆盖。

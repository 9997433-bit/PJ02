# content_series_map.json — 内容系列权威词表

`content_meta.series` (schema v2 正字段, [CONTENT_STRATEGY.md](../docs/CONTENT_STRATEGY.md) §5.1) 的**合法取值全集**。全库回填与机检均以本文件为唯一词表来源, 两类条目共 24 个:

1. **13 个策略主题** (`matrix_bucket: null`): 与策略 §2.2「主题 × 难度分布矩阵」逐行对应, 中文名逐字一致; slug 为英文 snake_case, 其中 `bridge_engineering` 沿用策略 §5.1 schema 示例的既有写法。归入这 13 个 series 的模型**计入矩阵进度**。
2. **11 个矩阵外桶** (`matrix_bucket` 非空): 与 [CONTENT_GAP_AUDIT.md](../docs/reports/CONTENT_GAP_AUDIT.md) §6 的矩阵外聚类一一对应 (城市生活/运动/田园/工程结构/音乐/自然世界/校园/游乐园/海洋航行/博物馆/其他)。v1 词表中桶即 series, 故 `matrix_bucket` 等于自身 slug; 带 `_misc` 后缀者 (`engineering_misc`/`nature_misc`/`maritime_misc`) 是为了与矩阵主题 (`bridge_engineering`/`animal_world`·`plant_garden`/`sea_air_transport`) 明确区隔。归入矩阵外桶的模型**不计入**矩阵格子。

## 消费方

- **series 回填** (缺口审计 §7.3 建议 3): 以审计附录 A 逐模型归类清单为底稿, 把全库 250 个模型的 `content_meta.series` 回填为本词表的 slug (回填由 series-backfill 分支执行, 词表以本文件为准)。
- **`tools/check_content_series`** (机检): 校验每个模型 JSON 的 `content_meta.series` ① 存在 ② 落在本词表内; 并按 `matrix_bucket` 是否为 null 输出矩阵内/外的主题 × 难度进度表, 替代人工归类。

## 维护规则

- **slug 一经回填不得改名** (改名 = 全库迁移 + 工具同步, 须策展人签发)。
- **新增/裁并 series 是策展决断** (缺口审计 §6 的「修订矩阵 / 冻结矩阵外供给」二选一), 不得因单个模型难归类而随手加词; 确无归属的一律入 `other`。
- 中文名与策略/审计文档保持逐字一致; 本文件手工维护, 禁止任何工具生成覆盖。

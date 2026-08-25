# 内容矩阵进度: 主题 × 难度 (自动生成)

- 生成时间: 2026-08-25
- 数据源: `data/models/` 全库 250 个模型的 `content_meta.series` × `difficulty`
- 对照标尺: [CONTENT_STRATEGY.md](../CONTENT_STRATEGY.md) §2.2 主题 × 难度分布矩阵 (13 主题 × D1–D5, 终态目标 520)
- series 覆盖: 0/250 个模型已标注 `content_meta.series`
- 本文件由 `tools/update_model_catalog.py --matrix-report` 自动生成, 请勿手工编辑

## 矩阵进度暂不可用

全库 250 个模型的 `content_meta.series` 均未回填, 无法机检主题 × 难度矩阵进度。回填 (底稿见 [CONTENT_GAP_AUDIT.md](CONTENT_GAP_AUDIT.md) 附录 A, 词表见 `tools/update_model_catalog.py` 的 `MATRIX_THEMES`) 后重跑 `python3 tools/update_model_catalog.py --matrix-report` 即自动输出进度表。

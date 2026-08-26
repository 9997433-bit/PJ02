# 批 P 并入 foundation 评估与合并预案 (2026-08-26)

- 评估对象: `cursor/expansion-batch-p-a95b` (PR #5, 批 P 扩展片型 10 模型) 并入 `cursor/magtile-studio-foundation-a95b`
- 工作区: `/tmp/wt-risk-report/magtile-studio` (foundation @ `9aa146d`, 与 origin 同步)
- 基线提交:

| 分支/节点 | 提交 | 模型数 | 说明 |
| --- | --- | ---: | --- |
| foundation | `9aa146d` | 250 | 评估目标基线 (D1 20 / D2 23 / D3 156 / D4 45 / D5 6, D3 冻结已解冻) |
| expansion-batch-p (PR #5) | `ef8ce76` | 260 | 批 P 头; PR base 是 `cursor/content-batch-jm-a95b`, **不是 foundation** |
| content-batch-jm (批 P 父分支) | `3a7f718` | 250 | 批 J–M 整合后节点 (批 P 支自身未做退役, 250+10=260) |
| merge-base (foundation ↔ 批 P) | `8ee2fc7` | 250 | 两条线的共同祖先 |

## 0. 结论速览

**建议: cherry-pick subset —— 只摘批 P 自有的 10 个模型置换入 foundation (退役 10 个矩阵外 D3 保持 250), 不要整支合并; 整支携带的批 J–M 16 模型另行评估 (defer)。**

- 整支合并 **不干净**: `git merge-tree` 实测 3 处冲突 (§2)。按本次任务纪律 (仅干净合并才执行), **本报告只出预案, 未执行任何合并/退役**。
- 整支合并会把库推到 **276 (+26 超限)**, 所需 26 次退役超出现存矩阵外候选存量 (17 个), 必须动 9 个矩阵内超编主题模型 (§3)。
- 批 P 自有 10 模型在 foundation 基线上 **五关机检全部 PASS** (§4), 摘取路径无冲突面 (24 个自有文件中 22 个纯新增, 2 个冲突文件按"重建/并集"处理即可, §5–§6)。
- 摘取入库前有 4 项缺件需补: 缩略图 ×10、目录重建、词表登记 7 条、D3 白名单带入 (§5)。

## 1. 分叉画像 (为什么两边库不一样)

两条线自 `8ee2fc7` (250 模型) 分叉后各自做了**不同的路径 B 配额置换**:

- **foundation 侧**: 退役 25 个 D3 (含退役候选序 #1–#25 的绝大多数), 新增 25 个自有 D1/D2/D4/D5 模型 (`marble_starter_slope_01`、`giant_ferris_wheel_01`、`royal_citadel_01` 等), 250 → 250, 且已达成解冻 (D1 20 ≥ 20, D5 6 ≥ 6)。
- **批 P 支 (jm 段)**: 退役 16 个 D3 (候选序 #1–#16), 新增批 J–M 16 模型 (`guardian_dragon_01`、`temple_of_heaven_01` 等), 250 → 250; **批 P 段**再加 10 个扩展片型模型, 250 → 260 (批 P 支自身未执行其计划中的退役)。
- 两边库交集 **225**; foundation 独有 25; 批 P 支独有 35 (= 16 J–M + 10 批 P + 9 个 foundation 已退役但该支尚存的滞留模型)。
- **关键错位**: 批 P 报告 (`CONTENT_BATCH_P_2026-08-26.md`) 计划退役候选 #17–#26, 其中 **#17–#25 共 9 个已被 foundation 抢先退役** (`piano_stage_01`、`science_lab_01`、`supermarket_01`、`jungle_gym_01`、`recycling_center_01`、`water_slide_park_01`、`deep_sea_lab_01`、`swimming_pool_01`、`violin_shop_01`), 原计划只剩 #26 `er_entrance_01` 可用 —— 批 P 的退役名单必须在 foundation 基线上重新生成 (§3 已重算)。

## 2. 冲突评估 (git merge-tree 实测, 非推演)

`git merge-tree --write-tree foundation 批P` 结果: **不干净, 3 处冲突**; 其余全部自动合并 (jm 段对 `tools/audit_strict_physics.sh` 的 waiver 追加、`tools/magtile_gen.py`、`docs/STRICT_PHYSICS_AUDIT.md` 等 foundation 未触碰, 无冲突)。

| # | 路径 | 冲突类型 | 定性与正解 |
| --- | --- | --- | --- |
| 1 | `data/model_catalog.json` | content (双方大改) | 目录是 `tools/update_model_catalog.py` 的**派生物** (250 条 vs 260 条两套全量重写), 文本合并无意义; 正解: 冲突时任选一边, 文件落定后直接重建 |
| 2 | `data/content_series_map.json` | content (双方在 models 节各自追加) | 手工取并集即可 (foundation +25 条 vs 批 P 支 +3 条), 属低风险冲突 |
| 3 | `data/models/police_station_01.json` → `stone_arch_bridge_01.json` | rename/delete | **git 相似度误配**: J–M 新模型 `stone_arch_bridge_01` 因模型 JSON 结构样板高度相似被判为已退役 `police_station_01` (foundation 侧退役候选 #2) 的改名。语义正解: 保留 `stone_arch_bridge_01` 按"新增模型"走评审, 与 `police_station_01` 的退役互不相干 |

冲突本身都可解, 但 #1/#3 都要求合并者理解两边的置换史 —— 这不是一次"干净合并"。

## 3. 250 上限与退役需求

| 方案 | 合并后模型数 | 超限 | 所需退役 | 候选够不够 |
| --- | ---: | ---: | ---: | --- |
| 整支合并 | 276 (= 交集 225 + foundation 独有 25 + 新增 26) | +26 | 26 × D3 | **不够**: foundation 基线重算后矩阵外候选仅 17 个 (#1–#17), 还须动 9 个矩阵内"超编主题"模型 (`crane_tower_02`、`dragon_cave_01` 等), 与 520 矩阵终态目标相抵 |
| cherry-pick 批 P 10 个 | 260 → 退役 10 → 250 | 0 (置换后) | 10 × D3 | **正好**: 最新候选序前 10 全部是矩阵外 D3 (附录 B), 与批 P 原计划"退役矩阵外 D3"口径一致 |

cherry-pick 置换后难度分布: **D1 21 / D2 30 / D3 147 / D4 46 / D5 6 = 250** (D3 156 − 退役 10 + `sector_rotunda_01` 1), 解冻状态保持 (D1 21 ≥ 20, D5 6 ≥ 6)。

另: 批 J–M 16 模型的角色是"置换解冻 (8×D1+4×D2+1×D4+3×D5)", 而 foundation 已用自有批次完成解冻 —— 整支合并引入的是**重复补给**, 却要为此支付 9 个矩阵内模型的退役, 收益/代价不成比例。这是 defer 批 J–M 的核心理由 (选题本身不差, 见 §4 的补测数据)。

## 4. 批 P 10 模型在 foundation 基线的评审实测

把批 P 的 10 个模型 JSON 检出到 foundation 基线 (250→260) 后实跑
`tools/review_content_batch.sh --whitelist-file BATCH_P_D3_WHITELIST.txt <10 个 JSON>`:

| 关卡 | 结果 | 要点 |
| --- | --- | --- |
| 1. strict 物理校验 (零警告) | **PASS** | 10/10 零警告零错误, **不需要任何新增豁免** (waiver 白名单与 foundation 现状一致) |
| 2. 难度配额 (D3 冻结闸门) | **PASS** | 批内唯一 D3 `sector_rotunda_01` 有策展人白名单 (`docs/reports/BATCH_P_D3_WHITELIST.txt`); 且 foundation 基线 D3 冻结已解冻, 双保险 |
| 3. 内容系列归类 (--strict) | **PASS** | 10 个模型 `content_meta.series` 词值全部落在 foundation 词表 13 主题内 |
| 4. 片型分层 core-9 (--strict) | **PASS** | 260 库口径下扩展片型打标一致、免费层 80% 红线未破 |
| 5. 唯一性抽查 | **PASS** | 260 模型 33,670 对两两比对, 全库最相似对 0.504 (与批 P 无关), 零警告 |

补测 (为整支合并定性, 不影响上表):

- **276 联合库唯一性** (foundation 250 + J–M 16 + 批 P 10): 37,950 对全部通过, 最相似对仍为 0.504; 仅 1 条不阻断 WARN (geometric_art × T18_tessellation_art 达 3 个模型的拥挤提示)。担心过的近邻对 (`phone_stand_01`↔`phone_cradle_01`、`marble_cascade_01`↔`marble_grand_cascade_01`) 实测未触线。
- **J–M 16 模型 strict 校验 (foundation 基线)**: 15/16 零警告; `marble_relay_city_01` 有 19 条 `disconnected_assembly` 警告, 依赖 jm 段在 `tools/audit_strict_physics.sh` 里论证过的 waiver (整支合并会自动带入; 单摘时需连带)。
- 即: 批 J–M 内容质量本身过硬, defer 的理由是 §3 的配额/矩阵代价, 不是质量。

## 5. 摘取入库前的缺件清单 (机检 PASS ≠ 直接可入库)

1. **缩略图 ×10 缺失**: 批 P 支没有为 10 个模型生成 `data/thumbnails/<id>.png`, 其目录条目也无 `thumbnail` 字段 —— `check_v1_readiness.sh` R2 三方对账 (模型/目录/缩略图) 会 FAIL。入库时跑 `tools/generate_thumbnails.py`。
2. **目录条目要重建, 不要摘批 P 支的**: 批 P 支的 `model_catalog.json` 是 260 库口径且新条目缺 `thumbnail`; 文件落定后在 foundation 上跑 `tools/update_model_catalog.py` 重建。
3. **词表登记只做了 3/10**: `content_series_map.json` models 节仅登记 `plaza_canopy_01`/`conservatory_01`/`marble_splitter_01`, 还差 7 条 (`hex_honeycomb_01`、`rhombus_patchwork_01`、`trapezoid_awning_01`、`streetcar_01`、`switchback_ramp_01`、`sector_rotunda_01`、`expansion_orb_01`; 归类见附录 A) —— 模型文件内 `content_meta.series` 已齐, 只欠词表底稿登记 (CONTENT_STRATEGY.md §入库必填)。
4. **D3 白名单文件带入**: `docs/reports/BATCH_P_D3_WHITELIST.txt` (含 `sector_rotunda_01` 豁免论证) 随批检出。

## 6. 三选一论证

- **merge now ✗**: 3 处冲突 (含需要理解两边置换史的 rename/delete 误配); +26 超限, 退役需求 2.6 倍于历史单批最大值且要动矩阵内存量; 批 J–M 16 模型未在 foundation 基线走完整五关 (本报告仅补测了关 1/关 5); J–M 的解冻使命在 foundation 已闭环, 属重复补给。
- **defer ✗ (对批 P 10 个而言)**: 扩展片型缺口真实存在 (入库前基线 large_square 仅 7 模型、sector 仅 8); 10 模型在 foundation 基线机检全绿、零新增豁免; 自有足迹纯新增无冲突面 —— 没有等待收益, 拖越久与 foundation 的目录/词表漂移越大 (本次 #17–#25 被抢先退役就是漂移的直接后果)。
- **cherry-pick subset ✓**: 摘批 P 自有 24 文件 (10 模型 JSON + 10 生成器 + 2 文档 + 目录/词表两处派生改动按 §5 处理), 退役重算后的前 10 矩阵外 D3, 库保持 250、解冻保持、矩阵内存量零损失。

## 7. 执行清单 (按置换纪律, 待用户书面批准后执行)

1. 退役预览→执行: `tools/retire_models.sh --dry-run <附录 B 前 10>` → `--execute` (删 JSON + 缩略图 + 重建目录);
2. 摘取批 P 文件: `git checkout origin/cursor/expansion-batch-p-a95b -- <10 个 data/models/*.json> <10 个 tools/generate_*.py> docs/reports/CONTENT_BATCH_P_2026-08-26.md docs/reports/BATCH_P_D3_WHITELIST.txt`;
3. 词表登记 10 条 (models 节, 归类按附录 A);
4. `tools/generate_thumbnails.py` 补 10 张缩略图 → `tools/update_model_catalog.py` 重建目录;
5. 复跑 `tools/review_content_batch.sh --whitelist-file docs/reports/BATCH_P_D3_WHITELIST.txt <10 个 JSON>` 五关 + `tools/check_v1_readiness.sh --quick` 对账 R1/R2;
6. 提交推送 foundation; PR #5 标注"由 foundation 摘取入库替代整支合并", 批 J–M 16 模型另开评估 (若将来要摘, `marble_relay_city_01` 需连带其 waiver 与论证)。

## 附录 A: 批 P 10 模型 (foundation 基线实测口径)

| # | id | D | 片/步 | series | 主打片型 |
| --- | --- | --- | --- | --- | --- |
| P1 | `plaza_canopy_01` | D1 | 25pc/7st | practical_utility | large_square |
| P2 | `conservatory_01` | D2 | 41pc/9st | plant_garden | window_square |
| P3 | `hex_honeycomb_01` | D2 | 32pc/6st | geometric_art | hexagon |
| P4 | `rhombus_patchwork_01` | D2 | 39pc/10st | geometric_art | rhombus |
| P5 | `trapezoid_awning_01` | D2 | 31pc/8st | plant_garden | trapezoid |
| P6 | `marble_splitter_01` | D2 | 30pc/8st | marble_run | door_frame |
| P7 | `streetcar_01` | D2 | 48pc/9st | land_transport | wheel_base |
| P8 | `switchback_ramp_01` | D2 | 45pc/11st | marble_run | right_triangle |
| P9 | `sector_rotunda_01` | D3 | 52pc/13st | landmark_architecture | sector |
| P10 | `expansion_orb_01` | D4 | 78pc/18st | geometric_art | 菱+梯+六+扇 |

注: 实际难度分布为 1×D1 + 7×D2 + 1×D3 + 1×D4, 批 P 报告头部写的 "2×D1 + 6×D2" 与其自表/目录不符, 以目录为准。

## 附录 B: 退役候选前 10 (foundation 基线重算, `plan_quota_substitution.py` 2026-08-26)

全部为矩阵外非免费 D3, 排序规则与 `QUOTA_SUBSTITUTION_PLAN_2026-08-25.md` 相同:

| # | 模型 id | 归类 | 片数 |
| ---: | --- | --- | ---: |
| 1 | `er_entrance_01` | city_life | 63 |
| 2 | `bamboo_house_01` | farm | 62 |
| 3 | `bike_rack_park_01` | city_life | 62 |
| 4 | `climbing_wall_01` | sports | 62 |
| 5 | `diving_tower_01` | sports | 62 |
| 6 | `hydro_dam_01` | engineering_misc | 62 |
| 7 | `dental_clinic_01` | city_life | 61 |
| 8 | `lego_style_house_01` | farm | 61 |
| 9 | `flag_plaza_01` | campus | 60 |
| 10 | `skate_park_01` | sports | 60 |

## 附录 C: 取证命令

```
git merge-base origin/cursor/expansion-batch-p-a95b origin/cursor/magtile-studio-foundation-a95b   # 8ee2fc7
git merge-tree --write-tree --name-only origin/cursor/magtile-studio-foundation-a95b \
    origin/cursor/expansion-batch-p-a95b        # 3 处冲突 (§2), 结果树 data/models 276 个 JSON
tools/review_content_batch.sh --whitelist-file /tmp/batch_p_d3_whitelist.txt <批P 10 个 JSON>   # 五关全 PASS
python3 tests/test_library_uniqueness.py data/models /tmp/union26/*.json --catalog data/tile_catalog.json  # 276 库 PASS
python3 tools/plan_quota_substitution.py --markdown /tmp/quota_plan_foundation.txt   # 附录 B 候选
```

—— 评估与实测: claude-fable-5-thinking-xhigh, 2026-08-26; 库文件均已还原, foundation 工作区未留任何评估残留。

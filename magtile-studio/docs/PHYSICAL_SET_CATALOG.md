# 实物磁力片套装目录 (Physical Set Catalog)

本文档定义 `data/physical_set_catalog.json` 的结构与用法: **家长勾选家里拥有的盒装套装 → 应用按片型求和得到 `tile_inventory` → 现有 `canBuild` / `inventory match` 直接可用**。

片型的几何与 `tier` 分层以 [`data/tile_catalog.json`](../data/tile_catalog.json) 为唯一事实来源; 全部 13 种片型速查见 [TILE_SET.md](TILE_SET.md)。

## 1. 设计目标

| 环节 | 说明 |
| --- | --- |
| 录入 | 库存录入界面 (UI_UX_SPEC §10.2) 提供「标准102片套装」「豪华198片」等快捷预填, 减少逐片计数 |
| 存储 | 落盘仍是 `tile_inventory` 表 (片型 → 数量), 与 CLI `inventory set` / 图形录入共库 |
| 匹配 | `ProgressStore::canBuild` / `inventory match` 对照模型 BOM, 逻辑不变 |
| 扩展 | 后续可追加品牌专属套装 (如 `connetix_102`), 不改库存 API |

## 2. JSON 结构

```json
{
  "schema_version": 1,
  "comment": "...",
  "sets": [
    {
      "id": "standard_102",
      "brand": "generic",
      "name_zh": "标准102片套装",
      "name_en": "Standard 102-Piece Set",
      "piece_count_label": 102,
      "tier_scope": "core",
      "ui_preset_label_zh": "标准102片套装",
      "description_zh": "...",
      "pieces": { "square": 36, "equilateral_triangle": 24, ... }
    }
  ]
}
```

### 2.1 顶层字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `schema_version` | 整数 | 当前为 `1`; 破坏性变更时递增 |
| `comment` | 字符串 | 人类可读说明 (不参与运行时逻辑) |
| `sets` | 数组 | 套装条目列表, `id` 必须唯一 |

### 2.2 套装条目 (`sets[]`)

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | 字符串 | 是 | 稳定标识, 见 §3 |
| `brand` | 字符串 | 是 | 品牌命名空间, 见 §3 |
| `name_zh` / `name_en` | 字符串 | 是 | 展示名 |
| `piece_count_label` | 整数 | 是 | 盒装/marketing 片数 (如 102、198); **近似值**, 见 §5 |
| `tier_scope` | 字符串 | 是 | `core` = 仅核心 9 片型; `core+expansion` = 含扩展 4 片型 |
| `ui_preset_label_zh` | 字符串 | 否 | 录入界面快捷按钮文案 (对齐 UI_UX_SPEC §10.2) |
| `description_zh` | 字符串 | 否 | 家长向说明 |
| `pieces` | 对象 | 是 | 片型标识 → 非负整数数量; 键必须是 `tile_catalog.json` 中的 `type` |

### 2.3 `tier_scope` 与片型分层

- `tier_scope: "core"`: `pieces` 中的每个片型在 `tile_catalog.json` 中必须为 `tier: "core"` (核心 9 片型)。
- `tier_scope: "core+expansion"`: 可含 `tier: "expansion"` 片型 (菱形/梯形/六边形/扇形), 也可只列部分扩展片型 (未出现的扩展片型视为 0)。
- 产品端「只用核心 9 片」筛选与 `需要扩展装` 角标仍按模型 BOM 与片型 `tier` 判定, 套装目录不替代模型标签。

## 3. 品牌与套装 `id` 命名

格式: **`{brand}_{piece_count_label}`** 或 **`{brand}_{marketing_slug}`**。

| 约定 | 示例 | 说明 |
| --- | --- | --- |
| `brand` | `generic`, `connetix`, `magformers` | 小写 ASCII; `generic` = 品牌无关的常见盒装口径 |
| `id` | `standard_102`, `deluxe_198`, `connetix_102` | 全库唯一; 只用 `[a-z0-9_]` |
| 数字后缀 | `102`, `198` | 与 `piece_count_label` 对齐, 便于识别 |

新增品牌套装时: 复制 `generic` 条目结构, 改 `brand`/`id`/histogram, 在 §5 注明数据来源与偏差。

## 4. 多套装合并 (derive inventory)

用户可同时勾选多个套装 (例如基础盒 + 扩展包)。合并规则:

1. 对每个片型 `type`, 将各选中套装的 `pieces[type]` **相加** (缺失键视为 0)。
2. 结果写入 `tile_inventory` 表 (与手动 `inventory set` 同 schema)。
3. 若用户之后手动改某一片型计数, 以手动值为准 (套装勾选仅作初始/批量预填, 不锁定来源)。

伪代码:

```python
inventory = {}
for set_id in selected_set_ids:
    for tile_type, count in catalog.sets[set_id].pieces.items():
        inventory[tile_type] = inventory.get(tile_type, 0) + count
store.setInventory(inventory)
```

## 5. 片数近似声明 (免责声明)

**盒装片数为近似值, 不作为法律或售后承诺。**

- 不同品牌、批次、是否含贴纸/人仔/非磁力配件, 盒面数字与按片型拆开计数会有偏差。
- 目录中的 `pieces` histogram 依据常见 100/200 片级盒装的市场口径整理, 用于「我能搭的」**估算**, 精确匹配请家长对照实物微调。
- `piece_count_label` 是 marketing 总数; 校验工具要求 `sum(pieces.values()) == piece_count_label` 以保持内部一致, 这不表示与某一品牌实物 100% 一致。
- 快捷预填后 UI 应提示「照着盒子数一数, 不对就改」 (UI_UX_SPEC §10.2)。

## 6. 内置预设 (schema_version 1)

| `id` | 展示名 | `tier_scope` | 片型数 | 合计 |
| --- | --- | --- | --- | --- |
| `standard_102` | 标准102片套装 | `core` | 9 | 102 |
| `deluxe_198` | 豪华198片套装 | `core+expansion` | 13 | 198 |

`standard_102` 仅含核心 9 片型, 对齐免费模型库默认片型集。`deluxe_198` 额外含菱形/梯形/六边形/扇形, 可搭带「需要扩展装」标签的模型。

## 7. 校验与 QA

```bash
python3 tools/verify_physical_set_catalog.py
```

断言:

- 所有 `pieces` 键存在于 `tile_catalog.json`;
- 所有数量 ≥ 0;
- `sets[].id` 唯一;
- `sum(pieces) == piece_count_label`;
- `tier_scope` 与片型 `tier` 一致 (core 套装不得含 expansion 片型)。

随 `tests/run_full_qa.sh` 常开 (关卡「实物套装目录校验」); 亦可通过 `tests/test_physical_set_catalog.sh` 单独运行。

## 8. 相关文档

- [UI_UX_SPEC.md](UI_UX_SPEC.md) §10.2 — 库存录入界面与快捷套装按钮
- [TILE_CATALOG.md](TILE_CATALOG.md) — 片型 `tier` 与产品分层
- [PROGRESS.md](PROGRESS.md) — `tile_inventory` 表与 `canBuild`
- [TESTING.md](TESTING.md) — QA 流水线

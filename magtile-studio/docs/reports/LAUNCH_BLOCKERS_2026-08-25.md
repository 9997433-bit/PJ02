# 商用上架阻塞项决策单 (Launch Blockers)

> **本单已被取代 (2026-08-26)**: 路径 B 难度配额已解冻 (D1 20/20, D5 6/6, strict 守卫转绿),
> 双红灯口径失效 —— 最新决策单见 [LAUNCH_BLOCKERS_2026-08-26.md](LAUNCH_BLOCKERS_2026-08-26.md)
> (唯一软件侧相邻阻塞 = 路径 A 实物复核 0/51 + 路径 C Manual P0)。本文仅作历史留痕。

- 生成时间: 2026-08-25 22:06 UTC
- 基线提交: `6e55c50` (`cursor/magtile-studio-foundation-a95b`)
- 对账单: [V1_LAUNCH_CHECKLIST.md](../V1_LAUNCH_CHECKLIST.md) (34 个 P0)
- 工程天花板: [ENGINEERING_CEILING_2026-08-25.md](ENGINEERING_CEILING_2026-08-25.md) —— **无可自主推进的工程项**
- 本单用途: 把剩余阻塞按**可并行路径**拆开, 标明每条路径解锁哪些清单项、第一步做什么、做完怎么验

## 0. 当前门禁快照 (实跑)

```bash
tools/check_v1_readiness.sh --quick    # 14 PASS / 2 FAIL / 9 SKIP —— 唯二 P0 FAIL: R6/R7
tools/run_release_gate.sh --full --fail-on-pending   # 退出码 1, 双红灯 (见下)
```

| 红灯 | 探测/关卡 | 现状 | 谁能解 |
| --- | --- | --- | --- |
| 实物复核 | R6/R7 + G2 L3 | D4+ **0/46** 已复核 | **你** (实搭 + 落盘 `physical_verified`) |
| 难度配额 | G2 QA 关卡 21 strict | D1 **0/20**, D5 **1/6** (D3 冻结中) | **你决策** → 工程可执行补库/置换 |
| Manual P0 | 清单 23 项 🔶/⬜ | 载体已备, 动作未做 | **你** (账号/实机/法务/沙盒) |

软件侧 (CTest 556/556、strict、L2 46×50、系列归类 250/250) **已全部常绿**。

## 1. 路径 A —— 实物签核 (解锁 R6/R7 / S1/S2 / G2 红灯 ①)

**不依赖行政账号**, 可与路径 B/C 并行, 是 G2 终防线硬前置之一。

### 第一步

```bash
# 导出按风险分排序的排产单 (勿手改导出件)
python3 tools/export_physical_review_queue.py \
  --csv docs/reports/PHYSICAL_REVIEW_QUEUE.csv \
  --markdown docs/reports/PHYSICAL_REVIEW_QUEUE.md
```

打开 [PHYSICAL_REVIEW_QUEUE.md](PHYSICAL_REVIEW_QUEUE.md) —— **必搭 36 个 ≈ 42.8h**, 可缓建 10 个 ≈ 11.7h。

### 执行纪律

- 规程: [PHYSICAL_REBUILD_CHECKLIST.md](../PHYSICAL_REBUILD_CHECKLIST.md)
- 桌边记录: [PHYSICAL_SIGNOFF_WORKSHEET.md](PHYSICAL_SIGNOFF_WORKSHEET.md)
- 上手指南: [PHYSICAL_REVIEW_USER_GUIDE.md](PHYSICAL_REVIEW_USER_GUIDE.md)
- **未实搭严禁标记 `physical_verified`**; 失败走 `tools/physical_failure_registry.py`

### 验收

每完成一批模型落盘后:

```bash
tools/check_v1_readiness.sh --quick          # R6/R7 计数下降
tools/list_physical_pending.py               # 待复核清单缩短
```

全部必搭 36 个落盘且 D4+ 覆盖口径满足 S2 后:

```bash
tools/run_release_gate.sh --full --fail-on-pending   # L3 红灯应灭 (配额红灯可能仍在)
```

## 2. 路径 B —— 难度配额解冻 (解锁 G2 红灯 ②)

D3 冻结硬闸门 (`check_difficulty_quota.py --strict`) 要求 **D1 ≥ 20 且 D5 ≥ 6** 同时达标。
当前全库 250/250 顶格, 解冻须三选一:

| 选项 | 做法 | 工程可执行性 | 对内容库影响 |
| --- | --- | --- | --- |
| **B1 置换** | 在 250 上限内用 D1×20 + D5×5 **替换**存量 D3 (净换题, 不扩库) | ✅ 批 J–M 选题池已备 ([CONTENT_GAP_AUDIT.md](CONTENT_GAP_AUDIT.md) §8) | 需策展选定被换下的 D3 名单 |
| **B2 扩库** | 上调 250 上限, 净增 D1/D5 | ✅ 工程可产, 需改 CONTENT_STRATEGY 决议 | 超原 V1 体量目标 |
| **B3 豁免** | V1 出包档调整配额守卫口径并留痕签核 | 文档 + 闸门配置变更 | 产品/合规决策 |

**你若选 B1**: 回复「批准批 J–M 置换模式」—— 工程侧按 `review_content_batch.sh` 五关机检 + D3 冻结闸门执行。退役候选序与分阶段演算见 [QUOTA_SUBSTITUTION_PLAN_2026-08-25.md](QUOTA_SUBSTITUTION_PLAN_2026-08-25.md) (`tools/plan_quota_substitution.py`); 退役执行 `tools/retire_models.sh` (默认 dry-run, `--execute` 落盘); **批 J–M 仅到 D1=8/D5=4 仍冻结, 全解冻还需再置换 14 次**。

### 验收

```bash
python3 tools/check_difficulty_quota.py --strict   # 退出码 0
tools/run_release_gate.sh --full --fail-on-pending # 配额红灯灭 (L3 可能仍红)
```

## 3. 路径 C —— Manual P0 (行政 / 实机 / 法务 / 沙盒)

工程侧载体已全部交付; 按依赖顺序建议:

```
L4 运营主体定稿 (第 0 步, 阻塞 V2/D5/A5)
    ├── L1 软著 (30~40 工作日, 尽早)
    ├── L2 ICP 备案
    ├── L3 四商店 + Apple 开发者账号
    └── D5 Authenticode 证书

并行不互斥:
    D2 Windows CI 首跑 (需仓库 dispatch 权限)
    D3/D4 桌面实机 + D4 公证
    A3 keystore → A4 真机 → A5 商店素材
    B3 沙盒付费 (依赖 L3 商品配置)
    V2 隐私法务定稿 + V4 三平台自查单
    E2 矩阵人工要点签核 (随实机同批)
```

明细工时与材料: [USER_HANDOFF.md](../USER_HANDOFF.md) §4。

### 验收

```bash
tools/check_v1_readiness.sh            # 全量: R4/R5/R17 亦跑
tools/check_v1_readiness.sh --strict   # 签核档: SKIP 算失败
```

## 4. 放行条件 (清单 §10)

以下**全部**满足方可标记商用上架完成:

1. [V1_LAUNCH_CHECKLIST.md](../V1_LAUNCH_CHECKLIST.md) 34 个 P0 项 ✅ 或已记录豁免
2. `check_v1_readiness.sh` **零 P0 FAIL**
3. `run_release_gate.sh --full --fail-on-pending` **退出码 0**

当前距放行: **路径 A + B 各至少完成一项决策/执行**, 且 **路径 C** 中阻塞项清零。

## 5. 工程侧不再自主推进的事项

依据 [ENGINEERING_CEILING_2026-08-25.md](ENGINEERING_CEILING_2026-08-25.md):

- 不再派发无产出子代理 (内容/文档/工具链已触顶)
- 不在未获决策前启动批 J–M 或修改 250 上限
- 不伪造 `physical_verified` 或调低 strict 守卫绕过红灯

**你的下一个动作** (任选其一即可推进):

1. 实物: 按 `PHYSICAL_REVIEW_QUEUE.md` 排名第 1 的模型开搭 —— **已开工单** [PATH_A_SESSION_01_SKYSCRAPER.md](PATH_A_SESSION_01_SKYSCRAPER.md) (`skyscraper_01`, 预算 120min)
2. 配额: 回复 B1/B2/B3 决策
3. 行政: 启动 L4 定稿 + L1 软著材料准备

# 路径 A · 第 1 场实搭 —— `skyscraper_01` 城市摩天大楼

- 决策: 用户选定 **路径 A** (实物签核)
- 刷新: 2026-08-26 05:25 UTC (52 口径对齐)
- 基线: `cursor/magtile-studio-foundation-a95b` @ `a90d04b`
- 本场目标: 抽样包 **#4/10** (按风险分排产 **#1/52**) —— 通过后 R6 缺口 10→9、R7 缺口 **52→51**

## 1. 为什么从它开始

| 维度 | 值 |
| --- | --- |
| 模型 | `skyscraper_01` — 城市摩天大楼 |
| 难度 | **D5** (6 个 D5 之一, 风险分最高) |
| 规模 | **122 片 / 26 步** |
| 风险分 | **63.9** (队列最高) |
| L2 标记 | `tall_structure`、`tall_wall_chain` |
| 排产 | **必搭** (上架抽样包 S2 + 单模型族) |
| 预算 | **120 分钟** (建议单独安排一场, 不与其他模型同日) |

## 2. 开工前准备 (桌边勾选)

- [ ] 打印 [PHYSICAL_SIGNOFF_WORKSHEET.md](PHYSICAL_SIGNOFF_WORKSHEET.md) §1 (`skyscraper_01` 段, 含逐步 26 步表)
- [ ] 官方基准品牌磁力片, 优先满磁新片; 旧片过弱磁标定 ([BUILD_VERIFICATION.md](../BUILD_VERIFICATION.md) §3.5)
- [ ] 平整硬质桌面 + 15~30°C + 秒表 + 固定机位录像
- [ ] 教程载体就绪 (平板 tutorial GUI 或打印分步图) —— **只看教程, 不看 JSON**

### 备料 BOM (共 122 片, 逐行清点)

| 片型 | 颜色分布 | 数量 |
| --- | --- | ---: |
| 正方形 | blue 43, cyan 33, gray 22, purple 4 | 102 |
| 等边三角形 | yellow 9 | 9 |
| 直角三角形 | orange 6 | 6 |
| 等腰三角形 | yellow 4 | 4 |
| 长方形 | orange 1 | 1 |

颜色瓶颈: **蓝色正方形 43 片**。同片型代色允许, 须在工作单「问题记录」注明。

## 3. 软件预检 (开搭前必跑)

```bash
cd magtile-studio
./build/magtile_app validate data/models/skyscraper_01.json --data-dir data
./build/magtile_app validate data/models/skyscraper_01.json --data-dir data --profile strict
./build/magtile_app validate data/models/skyscraper_01.json --data-dir data --profile strict --jitter 50
```

前两档须 **零 Error**; jitter 档须全绿 (有豁免须在工作单注明)。

## 4. 实搭当天流程

| 阶段 | 动作 | 规程 |
| --- | --- | --- |
| 搭建 | 只看教程逐步搭, 每步勾完成 + 记耗时 | [PHYSICAL_REBUILD_CHECKLIST.md](../PHYSICAL_REBUILD_CHECKLIST.md) §2 |
| 成品 | 静置 30s → 敲击 (顶+腰各 3 次) → 提起 → 拆解重搭 | §3~§5 |
| 记录 | 卡壳/歧义/掉片当场记; 非人为坍塌记 F01~F12 并拍照 | 工作单「问题记录」 |
| 照片 | `docs/reports/qa_photos/skyscraper_01/final_overview.jpg` 等 | [PHYSICAL_REVIEW_USER_GUIDE.md](PHYSICAL_REVIEW_USER_GUIDE.md) §7 |

## 5. 通过后落盘

**推荐** (签核 CLI, 内置守卫: 难度≥4 + strict 校验):

```bash
python3 tools/mark_physical_verified.py skyscraper_01 \
  --date 2026-08-26 \
  --notes "品牌___ / 新片|旧片 / 耗时___min / 敲击Pass 提起Pass 拆解重搭Pass"
```

落盘后刷新报告与门禁计数:

```bash
python3 tools/list_physical_pending.py
python3 tools/physical_sample_pack.py
python3 tools/export_physical_review_queue.py \
  --csv docs/reports/PHYSICAL_REVIEW_QUEUE.csv \
  --markdown docs/reports/PHYSICAL_REVIEW_QUEUE.md
tools/check_v1_readiness.sh --quick    # 期望 R6 9/10, R7 51/52
```

## 6. 不通过时

```bash
python3 tools/physical_failure_registry.py --help   # 登记失效编码 + 照片
```

**严禁**未实搭写入 `physical_verified`。

## 7. 本场之后

按风险分排产, 下一场建议 `stellar_launch_gantry_01` (D5, 61.8, 120min); 抽样包内其余 D5 优先 (`marble_grand_cascade_01` / `giant_ferris_wheel_01` / `strait_rainbow_bridge_01` / `royal_citadel_01`), 再跟 S3 档 D4。完整顺序见 [PHYSICAL_REVIEW_QUEUE.md](PHYSICAL_REVIEW_QUEUE.md)。

抽样包 10 个清完后 (≈16.7h), 继续必搭缩减集其余 31 个 → 合计必搭 **41 个 ≈ 52.8h** (全集 52 个 ≈ 65.7h)。

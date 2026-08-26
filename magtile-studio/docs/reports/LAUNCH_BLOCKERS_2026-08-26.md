# 商用上架阻塞项决策单 (Launch Blockers, 2026-08-26 刷新)

- 生成时间: 2026-08-26 05:05 UTC
- 基线提交: `ad6d35c` (`cursor/magtile-studio-foundation-a95b`, 内容库 250 模型; 批 P `53615ea` + 治理刷新)
- 取代版本: [LAUNCH_BLOCKERS_2026-08-25.md](LAUNCH_BLOCKERS_2026-08-25.md) (双红灯口径, 已过时)
- 对账单: [V1_LAUNCH_CHECKLIST.md](../V1_LAUNCH_CHECKLIST.md) (34 个 P0)
- 工程天花板: [ENGINEERING_CEILING_2026-08-26.md](ENGINEERING_CEILING_2026-08-26.md) 结论**在本基线重新确认成立** —— 软件工程侧无可自主推进项 (见 §5)
- 本单用途: 登记 2026-08-25 决策单发出后的推进结果 (**路径 B 配额解冻已完成**), 并把剩余阻塞收敛为**两条路径**: 路径 A 实物签核 (唯一软件侧相邻阻塞) 与路径 C Manual P0

## 0. 当前门禁快照 (基线 `ad6d35c` 实跑)

```bash
python3 tools/check_difficulty_quota.py --strict     # 退出码 0 —— D1 21/20, D5 6/6, D3 冻结解除
tools/check_v1_readiness.sh --quick                  # 14 PASS / 2 FAIL / 9 SKIP —— 唯二 P0 FAIL: R6/R7
tools/run_release_gate.sh --full --fail-on-pending   # 退出码 1, 唯一红灯 = L3 实物 0/52 (见下)
```

| 红灯 | 探测/关卡 | 现状 | 谁能解 |
| --- | --- | --- | --- |
| 实物复核 | R6/R7 + G2 L3 | D4+ **0/52** 已复核 (46 D4 + 6 D5) | **你** (实搭 + 落盘 `physical_verified`) |
| ~~难度配额~~ | ~~G2 QA 关卡 41 strict~~ | **已解冻 (绿灯)** —— D1 21/20, D5 6/6 | 已解, 维持解冻线即可 (§2) |
| Manual P0 | 清单 23 项 🔶/⬜ (M1~M6) | 载体已备, 动作未做 | **你** (账号/实机/法务/沙盒) |

软件侧**已全部常绿**: 全量 QA 42 子关卡 0 失败 (CTest **557/557**, strict 静态档 249 过 + 1 白名单豁免零警告, 唯一性 0 警告, 免费层 30/30, 系列归类矩阵内 211 + 矩阵外 39 缺失/非法 0, **D4+ 抗扰动 52/52 × 50 轮全绿**); 实跑留痕
[RELEASE_GATE_STATUS.md](RELEASE_GATE_STATUS.md)。**软件工程天花板已达 —— `--full --fail-on-pending` 距全绿只差 L3 实物一道硬闸门。**

## 1. 路径 A —— 实物签核 (唯一软件侧相邻阻塞, 解锁 R6/R7 / S1/S2 / G2)

**不依赖行政账号**, 可与路径 C 并行; 配额红灯已灭 (§2), 实搭清零后 G2 出包终防线即全绿。

### 排产单 (已刷新至 52 口径)

[PHYSICAL_REVIEW_QUEUE.md](PHYSICAL_REVIEW_QUEUE.md) (`8974b4b` 导出, 快照一致零告警):
**待复核 52 个 = 必搭 41 个 ≈ 52.8h + 可缓建 11 个 ≈ 12.8h** (族去重口径, 全集 52 个 ≈ 65.7h);
风险 Top3: `skyscraper_01` 63.9 / `stellar_launch_gantry_01` 61.8 / `marble_grand_cascade_01` 57.6
([PHYSICAL_RISK_REPORT.md](PHYSICAL_RISK_REPORT.md), Top15 ≈ 22.0h)。较配额批前净增 1 个 D4
(`expansion_orb_01`, 批 P `53615ea`); 此前 5 个 D5 与 3 个返工加固项 (`531860e` / `d78f419` / `acdc834`)
均已通过 strict --jitter 50, 可直接排实搭。

### 第一步

**已开工单**: [PATH_A_SESSION_01_SKYSCRAPER.md](PATH_A_SESSION_01_SKYSCRAPER.md)
(`skyscraper_01`, 队列排名第 1, 预算 120min)。

### 执行纪律 (不变)

- 规程: [PHYSICAL_REBUILD_CHECKLIST.md](../PHYSICAL_REBUILD_CHECKLIST.md)
- 桌边记录: [PHYSICAL_SIGNOFF_WORKSHEET.md](PHYSICAL_SIGNOFF_WORKSHEET.md)
- 上手指南: [PHYSICAL_REVIEW_USER_GUIDE.md](PHYSICAL_REVIEW_USER_GUIDE.md)
- **未实搭严禁标记 `physical_verified`**; 失败走 `tools/physical_failure_registry.py`

### 验收

每完成一批模型落盘后:

```bash
python3 tools/export_physical_review_queue.py \
  --csv docs/reports/PHYSICAL_REVIEW_QUEUE.csv \
  --markdown docs/reports/PHYSICAL_REVIEW_QUEUE.md   # 队列刷新 (片数/预算/复核状态同步)
tools/check_v1_readiness.sh --quick                  # R6/R7 计数下降
tools/list_physical_pending.py                       # 待复核清单缩短
```

全部必搭 41 个落盘且 D4+ 覆盖口径满足 S2 后:

```bash
tools/run_release_gate.sh --full --fail-on-pending   # 预期全绿 —— 配额红灯已不存在, L3 是最后一道
```

## 2. 路径 B —— 难度配额解冻 (✅ 已完成, 2026-08-26 转绿)

**B1 置换模式已执行完毕并通过全部机检**, D3 冻结解除:

| 事项 | 落地 |
| --- | --- |
| D1 补齐 20/20 | 入门批 ×5 共 20 个模型 (`fdc4557` / `8e16b4c` / `f8b0167` / `85bd8ca` / `b31e933`) |
| D5 补齐 6/6 | 大师批 +5 (`b212b74` ×2 + `20d9349` ×3), 加上存量 `skyscraper_01` 共 6 |
| B1 净换题 | 按 [QUOTA_SUBSTITUTION_PLAN_2026-08-25.md](QUOTA_SUBSTITUTION_PLAN_2026-08-25.md) 退役 25 个 D3, 总量保持 **250** (+25/−25) |
| 批次引入的 5 个软件侧红项清零 | ① 20 个 D1 片数下限冲突走**治理决策**落盘 —— QA 关卡 4/5 片数下限转难度感知 (D1 ≥ 20 / 其余 ≥ 40, `b925eba`, 同步 TESTING.md); ② 2 个 D5 扩规模至片数带 [110, 180] (`531860e` / `d78f419`); ③ `strait_rainbow_bridge_01` 第 23/25 步按 R9 放置重排 (`acdc834`); 全部经 `validate --profile strict --jitter 50` 逐个复验全绿 |

当前分布: D1 20 (8.0%) / D2 23 (9.2%) / D3 156 (62.4%) / D4 45 (18.0%) / D5 6 (2.4%)。

**遗留约束 (维持项, 非阻塞)**: 后续内容批不得使 D1 < 20 或 D5 < 6 (跌破即 D3 冻结自动重新生效);
批次评审一键机检 `tools/review_content_batch.sh` 与 CTest 常开闸门 `difficulty_quota_gate` 会自动拦截。

### 验收 (已实跑通过)

```bash
python3 tools/check_difficulty_quota.py --strict   # 退出码 0 (2026-08-26 04:00 UTC @ 9aa146d 实跑)
```

## 3. 路径 C —— Manual P0 (行政 / 实机 / 法务 / 沙盒, 不变)

工程侧载体已全部交付; 按依赖顺序建议 (与 08-25 版一致):

```
L4 运营主体定稿 (第 0 步, 阻塞 V2/D5/A5)
    ├── L1 软著 (30~40 工作日, 尽早; 源程序鉴别材料一键导出已入库 `8ee2fc7`)
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

## 4. 放行条件 (清单 §10, 不变)

以下**全部**满足方可标记商用上架完成:

1. [V1_LAUNCH_CHECKLIST.md](../V1_LAUNCH_CHECKLIST.md) 34 个 P0 项 ✅ 或已记录豁免
2. `check_v1_readiness.sh` **零 P0 FAIL**
3. `run_release_gate.sh --full --fail-on-pending` **退出码 0**

当前距放行: **路径 A 实搭清零** (必搭 41 个 ≈ 52.8h) + **路径 C** Manual P0 清零。
路径 B 已不在阻塞清单上。

## 5. 工程侧不再自主推进的事项

[ENGINEERING_CEILING_2026-08-26.md](ENGINEERING_CEILING_2026-08-26.md) 的结论在
`9aa146d` 基线重新确认: 路径 B 是 08-25 天花板报告中唯一的工程可执行决策项, 决策
落地后工程侧已执行完毕并清零随批红项 —— **软件工程侧再次触顶, 无可自主推进项**:

- 不再派发无产出子代理 (内容/文档/工具链已触顶; 配额解冻线已达标, 无新的内容侧 P0 缺口)
- 不伪造 `physical_verified` 或调低 strict 守卫绕过 L3 红灯
- D8 自动更新 (P1) 的「实现 vs 降级 V1.1」决策仍在你处, 不阻断 V1 出包判定链

**你的下一个动作** (任选其一即可推进):

1. 实物: 按 [PHYSICAL_REVIEW_QUEUE.md](PHYSICAL_REVIEW_QUEUE.md) 排名第 1 的模型开搭 —— **已开工单** [PATH_A_SESSION_01_SKYSCRAPER.md](PATH_A_SESSION_01_SKYSCRAPER.md) (`skyscraper_01`, 预算 120min)
2. 行政: 启动 L4 定稿 + L1 软著材料准备 (导出工具 `tools/export_copyright_source_pages.py` 已入库)

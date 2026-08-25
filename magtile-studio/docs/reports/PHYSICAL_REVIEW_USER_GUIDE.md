# 实物复核用户指南 (Physical Review User Guide)

- 面向读者: **准备动手实搭的用户 / QA 复核人** —— 不需要读代码, 照本指南把磁力片、时间、打印件准备好, 就能开工。
- 定位: V1 上架清单 [§8 实物复核 (L2 三层缩减流程)](../V1_LAUNCH_CHECKLIST.md) 两项 P0 缺口 (S1 缩减集实搭 / S2 D4+ 全覆盖清零, 探测 R6 抽样包 0/10、R7 全集 0/46) 是**唯一无法由软件代劳的人手缺口**, 本指南把「需要人做什么」一页说清。判定标准以 [PHYSICAL_REBUILD_CHECKLIST.md](../PHYSICAL_REBUILD_CHECKLIST.md) 规程为准; 桌边逐步记录用 [PHYSICAL_SIGNOFF_WORKSHEET.md](PHYSICAL_SIGNOFF_WORKSHEET.md) 工作单; 模型级签核摘要与落盘操作见 [PHYSICAL_SAMPLE_V1.md](PHYSICAL_SAMPLE_V1.md)。
- 数据快照: 2026-08-25, 250 模型库基线 (模型库 / 复核状态变化后, 本文第 2、3 节的备料与工时数字以重新生成的工作单为准)。

## 1. 现状与目标

- **现状**: 全库 250 个模型中 D4+ 共 46 个 (45 个 D4 + 1 个 D5), 全部待实物复核。`tools/check_v1_readiness.sh --quick` 退出码 1, 自动侧 P0 FAIL **仅剩** R6 (抽样包缺口 10/10) 与 R7 (全集缺口 46/46) 两项 —— 软件侧已全绿, 上架卡在实搭人手。
- **目标 (分两步走)**:
  1. **先清抽样包 (S1 首批 / R6)**: 按确定性抽样规则选出的 10 个高风险模型 (1 个 D5 旗舰 + 9 个大体量 D4), 逐个实搭签核, 预算约 **750 分钟 ≈ 12.5 小时** (单人);
  2. **再清缩减集 (S1/S2 / R7)**: 全集 46 个**不再逐个实搭** —— 按 L2 三层流程只实搭 **risk Top 15 + 结构族代表** (清单以 [PHYSICAL_RISK_REPORT.md](PHYSICAL_RISK_REPORT.md) 与 [PHYSICAL_FAMILY_PACK.md](PHYSICAL_FAMILY_PACK.md) 250 基线实跑输出为准): 族去重后必搭 36 个 (含本抽样包 10 个) 合计约 2570 分钟 ≈ 42.8 小时, 可缓建 10 个约 700 分钟 (省 21%, 须策展签核; 原全集口径 46 个 ≈ 3270 分钟 ≈ 54.5 小时), 未实搭成员由「同族代表实搭通过 + 第二层 jitter 全绿」覆盖 —— 抽样包全绿**不豁免**缩减集清零, 但能先解除最大结构风险并支撑上架风险评估。
- **红线**: 软件 strict 全绿是入库必要条件不是充分条件; **未实际搭过的模型严禁标记通过** —— 伪造复核结论比不复核更危险。

## 2. 需要准备的磁力片

- **品牌**: 官方基准品牌一套, 优先满磁新片; 旧片须通过弱磁标定 (方法见 [BUILD_VERIFICATION.md](../BUILD_VERIFICATION.md) 3.5 节), 磁力衰减超标的剔除。
- **数量口径**: 一次只搭一个模型, 搭完 (含拆解重搭测试) 拆净再搭下一个, 因此按**单模型最大需求**备料即可, 不需要 10 个模型的总和。单模型最大 **122 片** (`skyscraper_01`)。
- **片型覆盖**: 形状库 13 种中抽样包用到 **11 种** (不需要扇形与车轮底座)。各片型跨模型最大需求 (哪个模型要得最多):

| 片型 | 单模型最大需求 | 需求最高的模型 |
| --- | ---: | --- |
| 正方形 | 102 | `skyscraper_01` |
| 长方形 | 21 | `treehouse_02` |
| 等边三角形 | 13 | `treehouse_02` |
| 窗格方 | 11 | `ferry_terminal_01` |
| 直角三角形 | 6 | `skyscraper_01` |
| 等腰三角形 | 4 | `skyscraper_01` |
| 梯形 | 4 | `castle_drawbridge_01` |
| 大正方形 | 4 | `ferry_terminal_01` |
| 门框方 | 2 | `ferry_terminal_01` |
| 六边形 | 2 | `ball_run_tower_01` |
| 菱形 | 2 | `subway_station_01` |

- **颜色是实际瓶颈**: 教程按颜色指引找片, 逐模型「片型 + 颜色」清单见工作单各模型的「备料 BOM」表。单色需求最高的几处: 灰色正方形 **65** (`elephant_01`)、蓝色正方形 43 (`skyscraper_01`)、橙色正方形 34 (`treehouse_02`)、透明窗格方 11 (`ferry_terminal_01`)。若套件颜色凑不齐, 可同片型代色 (颜色不影响结构结论), 但代色会增加照教程找片的歧义, **必须在工作单「问题记录」栏注明代色情况**。
- **其他物料**: 平整硬质桌面 (木质/塑面, 禁桌布/地毯/玻璃面), 环境温度 15~30°C; 秒表 (手机即可); 固定机位录像 + 拍照设备; 打印好的工作单 (见第 4 节); 教程载体与真实产品一致 (平板运行 tutorial GUI 或打印分步图) —— **只看教程, 不看模型 JSON / 生成器脚本**。

## 3. 预估工时

抽样包 10 个, 单人含敲击/提起/拆解重搭与记录, 合计 **750 分钟 ≈ 12.5 小时**:

| 排产 | 模型 | 预算 |
| --- | --- | ---: |
| 旗舰 D5 (单独安排一场) | `skyscraper_01` (122 片, 26 步) | 120 分钟 |
| 大体量 D4 × 9 (每场建议 ≤ 2 个防疲劳) | `stadium_gate_01` / `ferry_terminal_01` / `castle_drawbridge_01` / `treehouse_02` / `elephant_01` / `ball_run_tower_01` / `stonehenge_01` / `subway_station_01` / `tennis_court_01` | 各 70 分钟 |

预算是规程第 2 节的难度预算 (D4: 70 / D5: 120 分钟), **超时本身要记 Warning 反馈步骤拆分**, 所以别赶工。多人分摊时按模型切分即可 (每个模型由一人完整走完全程, 不要中途换手)。缩减集清零 (S2) 抽样包之外的必搭 26 个 D4 每个同样按 70 分钟预算排产 (名单见 [PHYSICAL_FAMILY_PACK.md](PHYSICAL_FAMILY_PACK.md) 代表清单与建议排产顺序)。

## 4. 如何打印工作单

1. **确认工作单是新的**: 模型库 / 免费层 / 复核状态变化后先重新生成 (仓库内只保存空白模板, 勿手改):

```bash
python3 tools/physical_sample_pack.py --print-checklist docs/reports/PHYSICAL_SIGNOFF_WORKSHEET.md
```

2. **打印或转工单**: 用 Markdown 预览 (IDE / 浏览器插件) 打印 [PHYSICAL_SIGNOFF_WORKSHEET.md](PHYSICAL_SIGNOFF_WORKSHEET.md), 或 `pandoc PHYSICAL_SIGNOFF_WORKSHEET.md -o worksheet.pdf` 转 PDF; 也可以整段复制到 QA 工单里勾选。**实际勾选与笔记写在打印件 / 工单上, 不回填仓库里的空白模板。**
3. **桌边核对**: 开搭前跑 `python3 tools/physical_sample_pack.py` 可随时打出抽样清单 + 逐模型备料 BOM 与逐步片型摘要 (加 `--json` 得机器可读版)。

## 5. 复核当天流程 (概览)

细则以工作单「§0 使用方法」与规程各节为准, 这里只给顺序骨架:

| 阶段 | 做什么 | 依据 |
| --- | --- | --- |
| 开工前 | 该模型 default + strict 双档软件预检零 Error (命令印在工作单每模型「复核前置」节); 按 BOM 逐行清点备料, **不多备** | 规程 §0 / §1 |
| 搭建中 | 只看教程逐步搭, 每步勾「完成」记耗时; 卡壳 / 歧义 / 掉片当场记录, 非人为失误的坍塌记失效编码 (F01~F12) 并拍照 | 规程 §2 |
| 成品后 | 静置 30 秒 → 敲击测试 → 提起测试 → 拆解重搭 (D4+ 建议项), 逐项圈选结果 | 规程 §3~§5 |
| 收尾 | 补齐照片位 (第 7 节) 与结论签核; 通过 → 按第 6 节落盘; 不通过 → 失效编码 + 照片反馈设计师, **不写字段** | 规程 §6~§7 |

## 6. 通过后如何落盘 `physical_verified`

**前提: 该模型全部适用项实搭 Pass。** 完整操作见 [PHYSICAL_SAMPLE_V1.md](PHYSICAL_SAMPLE_V1.md) 第 5 节, 摘要:

1. 编辑 `data/models/<model_id>.json`, 在 `content_meta` 下追加三字段:

```jsonc
"content_meta": {
  "physical_verified": true,
  "physical_verified_at": "2026-08-25",   // 实际复核日期 (ISO 8601)
  "physical_notes": "品牌/新旧片 + 耗时 + 敲击/提起/拆解重搭结论 一句话"
}
```

2. 验证缺口计数变化并重新生成两份报告 (已复核模型自动折叠为一行):

```bash
python3 tools/list_physical_pending.py data/models            # 该模型转入「已复核」
python3 tools/physical_sample_pack.py                          # 抽样包缺口 -1
python3 tools/physical_sample_pack.py --markdown docs/reports/PHYSICAL_SAMPLE_V1.md
python3 tools/physical_sample_pack.py --print-checklist docs/reports/PHYSICAL_SIGNOFF_WORKSHEET.md
tools/check_v1_readiness.sh --quick                            # 全部落盘后 R6/R7 转 PASS
```

3. **纪律** (规程第 7 节): 模型 `final_assembly` / `steps` 任何改动后三字段必须一并清除 (旧实物结论对新结构无效); 复核不通过不写字段; 可对照已落盘示范 `castle_foundation_01` / `great_wall_01` / `tokyo_tower_01` 的 `content_meta` 写法。

## 7. 照片归档约定

- **目录**: 每模型一个目录 `docs/reports/qa_photos/<model_id>/`; 照片体积大时也可作为 QA 工单附件, 在工作单「照片位」表填链接即可。
- **文件名** (与工作单「照片位」表一致):

| 照片 | 何时必拍 | 文件名 |
| --- | --- | --- |
| 成品全景 | 必拍 | `final_overview.jpg` |
| 敲击后状态 (最高点 + 中部敲击点) | 必拍 | `after_knock.jpg` |
| 提起悬停中 | 提起测试适用时 | `lift_hold.jpg` |
| 失效瞬间 | 每次失效一张 | `fail_step<NN>_F<XX>.jpg` (NN=步骤号, F<XX>=失效编码) |

- **失效编码** F01~F12 的定义与典型照片描述见 [BUILD_VERIFICATION.md](../BUILD_VERIFICATION.md) 第 4 节 (桌边速查: `python3 tools/physical_failure_registry.py codes`); 每次失效必须归档「编码 + 照片 + 模型 id + 步骤号」, 这是回填软件规则回归用例的原料 —— 回到电脑前用登记工具入账 (`python3 tools/physical_failure_registry.py add --model <id> --step <N> --code F<XX> --photo <照片路径>`), 后续「登记 → 下沉负例夹具 → CI 回归」的闭环见 [PHYSICAL_CALIBRATION_WORKFLOW.md](../PHYSICAL_CALIBRATION_WORKFLOW.md)。
- **隐私**: 只拍结构与必要的手部特写, 不入镜人物面部; 涉及儿童测试的拍摄须单独同意 (BUILD_VERIFICATION.md 3.6.1 节)。

## 8. 常见问题

- **手上不是官方基准品牌 / 只有旧片?** 可以搭, 但 strict 预检必须通过 (弱磁片更接近 strict 档参数), 并在工作单表头「磁力片品牌/状态」如实登记; strict 有豁免须注明。
- **平铺类模型提不起来怎么办?** 教程明确注明「不可移动」的平铺类, 提起测试圈 n-a 跳过, 不算 Fail。
- **拆解重搭是必须的吗?** D4+ 为建议项但强烈建议做 —— 第二次耗时 ≤ 第一次 80% 且零失效, 是步骤设计质量最便宜的复检。
- **搭到一半塌了还继续吗?** 记失效编码 + 拍照后, 修复继续或终止由 QA 决定 (规程 §2); 无论继续与否, 该步的失效记录都要保留, 并按第 7 节登记进失效账本。
- **儿童测试也要现在做吗?** 不阻塞 R6/R7 —— 本指南覆盖的是成人复核人按规程实搭落盘 `physical_verified`; T4/T5 的儿童测试与品牌兼容性全测按 [BUILD_VERIFICATION.md](../BUILD_VERIFICATION.md) 第 3 节由 QA 另行组织。

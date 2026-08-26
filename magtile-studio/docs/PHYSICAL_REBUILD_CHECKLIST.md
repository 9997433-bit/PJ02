# 实物搭建复核规程 (Physical Rebuild Checklist)

本文档是**面向内容作者与 QA 的逐步实物搭建复核规程**: 拿真实磁力片, 照着教程把模型完整搭一遍, 用固定动作验证"软件全绿的模型在真实世界也立得住", 并把结论落盘到模型元数据, 供 `tools/list_physical_pending.py` 跟踪。

- **定位**: 本规程是 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) L3 实物验证的**作者级轻量执行清单** —— 单人、一套磁力片、一小时内可完成; 品牌兼容性全测、儿童测试等完整 L3 项目仍按 BUILD_VERIFICATION.md 第 3 节由 QA 组织执行。
- **适用范围** (与 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 4.3 节实物复核率一致):
  - **difficulty ≥ 4 (D4/D5): 每个模型必做**。全库 strict 巡检报告 (见 `docs/reports/STRICT_AUDIT_2026-08-25.md` 第 5 节) 列出的 41 个 D4+ 模型是当前待复核清单;
  - D3: 抽检 30%; D1–D2: 抽检 10%; 新系列首发模型建议必做。
- **原则**: 软件校验 (L1 strict 全绿) 是入库**必要条件, 不是充分条件**; 实物复核不通过的模型不得标记 `physical_verified`, 必须回到设计端整改。

## 0. 复核前软件预检 (弱磁档 strict_consumer 建议)

实物复核开始前, 先在软件端把该模型的两档校验都跑绿, 避免把作者的时间浪费在软件本可拦截的问题上:

```bash
# 默认档 (标准品牌参数): 必须零 Error
./build/magtile_app validate data/models/<model_id>.json --data-dir data

# 弱磁严格档 strict_consumer: 悬挂额定 120g/单位边长 x 安全系数 0.7
# = 有效悬挂预算 84g/边长, 抗弯预算 17.5 g·单位 (docs/PHYSICS_RULES.md 1.4 节)
./build/magtile_app validate data/models/<model_id>.json --data-dir data --profile strict
```

**strict 档建议** (为什么复核前要多跑这一档):

1. 实物复核用的磁力片**不保证是满磁新片** —— 库存旧片磁力衰减、非官方基准品牌磁力偏弱, 都更接近 strict 档参数而非默认档;
2. strict 档报 Warning/Error 的模型, 实物复核时**优先安排弱磁品牌或旧片实搭**, 让实物测试覆盖软件标出的最薄弱连接;
3. strict 档有未豁免警告的模型不要开始实物复核 —— 先按 [STRICT_PHYSICS_AUDIT.md](STRICT_PHYSICS_AUDIT.md) 的零警告政策处理 (整改或书面论证豁免), 再进入实物环节。

## 0.5 先跑 L2 再决定人手范围 (仿真先行)

实物复核是三层验证里最贵的一层 (0.5~2 小时/模型)。排产人手之前, 先把 L2 仿真层 (jitter 蒙特卡洛 + 风险标记, [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 2.1 节接口约定) 跑完, 用机器结果决定"谁先搭、谁后搭、抽检抽谁":

```bash
# 1) 风险报告: 列出被 L2 标记的模型与命中编码 (l1_warning / tall_structure / tall_wall_chain /
#    critical_com_margin / weak_edge_load_bearing / manual_flag, 编码表见 BUILD_VERIFICATION.md 第 2 节)
python3 tools/physical_risk_report.py data/models --json

# 2) 对 l2_required 模型跑 jitter 蒙特卡洛 (±1.5mm/±2° × 20 副本, 通过率 ≥ 90% 才算过)
./build/magtile_app validate data/models/<model_id>.json --data-dir data --jitter
```

**L2 结果 → 人手范围决策**:

| L2 结果 | 人手动作 |
| --- | --- |
| jitter 未过 (通过率 < 90%) | **不要开始实搭** —— 先回设计端加固/调序, 软件层修绿再排人手; 实搭一个 jitter 已判失稳的模型是纯浪费人时 |
| 被标记 (flagged) 且 jitter 通过 | **优先排产实搭**, 且实搭时重点盯风险报告命中的位置 (临界重心、垂直墙链、弱磁承重位) —— 让最贵的人时先花在机器认为最可疑的模型上 |
| 未被标记且 jitter 通过 | 排后; 抽检类分级 (D3 30% / D1–D2 10%) 的抽样名额**优先分给被标记模型**, 全绿模型在剩余名额内随机补足 |

**边界 (不因 L2 全绿而放松)**:

1. D4+ 每模型必做实搭的覆盖率承诺**不因 L2 全绿而豁免** ([CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 4.3 节) —— L2 只决定顺序与抽检取舍, 不缩小 D4+ 全集;
2. L2 只覆盖错位累积失稳 (F08) 与静力判定的扰动稳健性; 品牌磁力差异 (F05)、手抖连锁塌 (F07)、拆不下来 (F10) 等"仅 L3"失效模式仍只有实物层能发现 (BUILD_VERIFICATION.md 第 4 节"首个能发现的层");
3. 抽样包排产 (第 8 节) 同理: 先跑 L2 再定场次顺序, jitter 未过的模型不进入当期抽样场次。

## 1. 准备

| 项目 | 要求 |
| --- | --- |
| 磁力片 | 官方基准品牌一套, 剔除磁力衰减超标旧片 (标定法见 BUILD_VERIFICATION.md 3.5 节); 按教程"所需磁力片清单" (BOM) 备齐, 不多备 |
| 桌面 | 平整硬质桌面 (木质/塑面), 禁止桌布/地毯/玻璃面; 环境温度 15~30°C |
| 教程载体 | 与真实产品一致: 平板运行 tutorial GUI, 或打印分步图。**只看教程, 不看设计源文件 (模型 JSON / 生成器脚本)** |
| 计时与记录 | 秒表 (手机即可) + 第 5 节记录模板一份; 建议固定机位录像, 失效瞬间必须拍照 |
| 心态 | 严格按步骤操作, **不允许"凭经验加固"** —— 你替用户加固的每一片, 都是发布后用户家里塌掉的一片 |

## 2. 逐步搭建

1. 从教程第 1 步开始, 逐字按步骤说明与 tip 操作, 每步记录耗时;
2. 随手记录: 犹豫点 (说明读了两遍以上才理解)、说明歧义、放置时结构晃动/掉片事件、手伸不进去的放置动作;
3. 任何一步发生**非人为失误的掉片或坍塌**: 该步骤记 Fail, 拍照并对照 BUILD_VERIFICATION.md 第 4 节失效分类学记录编码 (F01~F12), 然后决定修复后继续或终止;
4. 总耗时对照难度预算 (D1: 10 分钟 / D2: 20 / D3: 40 / D4: 70 / D5: 120), 超时记 Warning 并反馈内容设计师评估步骤拆分。

## 3. 敲击测试 (Knock Test)

成品完成后**静置 30 秒**, 然后:

1. 用食指指腹从 10cm 距离水平轻敲**结构最高点侧面** 3 次 (力度以敲击自己手背不感到痛为准);
2. 再轻敲**结构几何中部侧面** 3 次;
3. 判定:

| 结果 | 现象 |
| --- | --- |
| Pass | 无片脱落、无可见永久位移 |
| Conditional | 掉落 1~2 片装饰性片 (不承重), 记录位置并反馈设计师 |
| Fail | 承重片脱落或连锁坍塌 |

## 4. 提起测试 (Lift Test)

1. 双手托住模型**底座两侧**, 匀速提起 5cm, 悬停 10 秒, 匀速放回;
2. 判定: 完整保持 → Pass; 任何片脱落 → Fail;
3. 例外: 设计上明确为"桌面固定"的平铺类模型标注 `lift_test: n/a` 跳过本项, 但教程文案必须提示"此模型不适合拿起移动"。

## 5. 拆解重搭 (建议项)

按步骤**逆序**拆解 (记录难以分离的死角连接), 立即按教程第二次完整搭建并计时。第二次耗时应 ≤ 第一次的 80% 且零失效; 若第二次仍在同一步骤出问题, 该步骤设计缺陷实锤, 记 Fail 并反馈。D4+ 模型建议执行; 抽检类模型可省略。

## 6. 记录模板

每次复核填写一份, 归档到复核任务 (issue / QA 工单), 结论摘要写入模型元数据 (第 7 节):

```markdown
## 实物搭建复核记录
- 模型: <model_id> (D<难度>, <片数> 片, <步骤数> 步)
- 复核人: ___  日期: YYYY-MM-DD
- 磁力片品牌/状态: ___ (新片 / 旧片, 弱磁档预检结论: 通过 / 豁免)
- 软件预检: default ___ / strict ___

### 分步搭建
- 总耗时: ___ 分钟 (预算内 / 超时)
- 卡壳或歧义步骤: 第 __ 步, 现象: ___
- 掉片/坍塌事件: 无 / 第 __ 步, 失效编码 F__, 照片: ___

### 固定动作
- 敲击测试: Pass / Conditional / Fail — 细节: ___
- 提起测试: Pass / Fail / n-a — 细节: ___
- 拆解重搭 (D4+ 建议): 第二次耗时 ___ 分钟 (≤ 第一次 80%?), 结果: ___

### 结论
- [ ] 通过 → 按第 7 节写入 physical_verified 字段
- [ ] 不通过 → 失效编码 + 照片 + 反馈设计师, 不得标记 verified
```

## 7. 结论落盘: 模型元数据字段

复核**全部适用项 Pass** 后, 在模型 JSON 的 `content_meta` 下写入三个可选字段 (schema 定义见 [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) 5.1 节):

```jsonc
"content_meta": {
  "physical_verified": true,             // 实物复核通过; 缺省/false = 未复核
  "physical_verified_at": "2026-08-25",  // 复核日期 (ISO 8601), verified=true 时必填
  "physical_notes": "官方基准品牌新片实搭 38 分钟; 敲击/提起/拆解重搭全 Pass; strict 预检零警告"
}
```

**纪律**:

1. 只有实际执行过本规程且全部适用项 Pass, 才允许写 `physical_verified: true`; 复核记录 (第 6 节模板) 必须可追溯;
2. 模型内容一旦变更 (`final_assembly` / `steps` 任何改动, 含生成器重跑), 三个字段必须一并清除 —— 旧的实物结论对新结构无效 (与 BUILD_VERIFICATION.md 5.2 节内容哈希回退语义一致);
3. 这三个字段是**轻量摘要**, 供清单工具与产品端快速判读; 完整验证记录 (分步耗时、品牌兼容、儿童测试、失效照片) 的权威载体仍是 BUILD_VERIFICATION.md 5.2 节规划的旁车文件 `data/verification/<model_id>.json`, 旁车管线落地后以旁车为准 (`tools/list_physical_pending.py` 两者都认);
4. 复核不通过: **不写字段**, 按失效编码反馈整改, 整改后从第 0 节重走。

## 8. 待复核清单跟踪

```bash
# 列出全部 D4+ 且未 physical_verified 的模型 (QA 排产依据)
python3 tools/list_physical_pending.py data/models

# 机器可读输出 / 门禁模式 (发布打包前可用)
python3 tools/list_physical_pending.py data/models --json
python3 tools/list_physical_pending.py data/models --fail-on-pending
```

工具判定口径: `content_meta.physical_verified == true`, **或**存在旁车文件 `data/verification/<model_id>.json` 且 `status == "physical_passed"` 且内容哈希与当前模型一致。`tests/run_full_qa.sh` 的"L3 实物复核缺口报告"关卡每次全量 QA 都会输出未复核数量 (仅报告, 不阻断 CI)。

**排产顺序: V1 上架优先抽样包先行。** 全集清零前, 先按 [reports/PHYSICAL_SAMPLE_V1.md](reports/PHYSICAL_SAMPLE_V1.md) 的确定性抽样包 (免费层 D4+ 全数 + D5 全数 + 付费 D4 高片数按主题补足, 约 10 个) 逐个实搭签核 —— 该文档带逐模型勾选表, 由 `tools/physical_sample_pack.py` 生成, 判定口径与 `list_physical_pending.py` 同源; 桌边随搭随填的逐步级原始记录 (逐步勾选栏 / 问题记录栏 / 照片位) 用配套工作单 [reports/PHYSICAL_SIGNOFF_WORKSHEET.md](reports/PHYSICAL_SIGNOFF_WORKSHEET.md), 打印或复制到 QA 工单后填写:

```bash
python3 tools/physical_sample_pack.py                          # 抽样清单 + 逐模型备料 BOM 与逐步片型摘要 (桌边核对用)
python3 tools/physical_sample_pack.py --fail-on-missing-sample # 抽样包有缺口即退出码 1 (门禁挂接用, 默认仅报告)
python3 tools/physical_sample_pack.py --markdown docs/reports/PHYSICAL_SAMPLE_V1.md  # 重新生成签核文档
python3 tools/physical_sample_pack.py --print-checklist docs/reports/PHYSICAL_SIGNOFF_WORKSHEET.md  # 重新生成逐步签核工作单 (勾选/问题记录/照片位)
```

抽样包全绿**不豁免**全集清零 —— `--fail-on-pending` 终防线仍以 D4+ 全集为准。

## 9. 与其他文档的关系

| 文档 | 关系 |
| --- | --- |
| [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) | L3 完整规程 (品牌兼容 / 儿童测试 / 失效分类学 / 旁车文件与状态机); 本规程是其单人轻量子集 |
| [CONTENT_STRATEGY.md](CONTENT_STRATEGY.md) | 4.3 节实物复核率 (D4/D5 100%, D3 30%, D1–D2 10%); 5.1 节字段 schema |
| [PHYSICS_RULES.md](PHYSICS_RULES.md) | 1.4 节 strict_consumer 档位参数依据 |
| [STRICT_PHYSICS_AUDIT.md](STRICT_PHYSICS_AUDIT.md) | strict 零警告政策与豁免白名单 (复核前置条件) |
| [TESTING.md](TESTING.md) | 质量金字塔全景与全量 QA 关卡 |

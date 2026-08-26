# 实物搭建验证工作流 (Build Verification)

本文档定义 MagTile Studio 商业内容管线的**真实世界搭建验证**工作流。它回答一个软件无法独自回答的问题: **孩子拿着真实的磁力片, 照着教程搭, 真的能搭起来吗?**

软件校验 (见 [PHYSICS_RULES.md](PHYSICS_RULES.md)) 能保证几何与静力学上的正确性, 但以下真实世界因素是纯软件难以覆盖的:

- **品牌间磁力差异**: Magna-Tiles / Connetix / Playmags 的磁铁强度、磁条布局、边缘倒角各不相同, 混用时连接强度显著下降;
- **装配摩擦与干涉**: 往半封闭结构里放最后一片时, 手指够不着、或放置动作蹭倒已有墙体;
- **儿童手部抖动**: 4~6 岁儿童放置高处磁力片时的抖动足以震塌未加固的墙;
- **微小错位累积**: 每一步 1~2mm 的贴合误差逐步累积, 到后段步骤"对不上缝", 或在轻微扰动下整体坍塌。

因此每个模型在进入发布内容库前, 必须按难度分级通过下述**三层验证金字塔**。

## 1. 三层验证金字塔

```
            ▲  成本/模型 高
           ╱ ╲
          ╱L3 ╲   实物搭建验证 (人 + 真实磁力片)      —— 按分级要求执行
         ╱─────╲
        ╱  L2   ╲  仿真抽检 (jitter 蒙特卡洛 + 风险标记) —— 被标记的模型, 第一期已实现
       ╱─────────╲
      ╱    L1     ╲ 自动软件规则 (几何 + 静力学)       —— 全部模型, 每次提交
     ╱─────────────╲
            ▼  覆盖模型数 多
```

### L1 自动软件规则 (几何 + 静力学)

- **内容**: `magtile_app validate` 执行的全部检查 —— 几何规则 R1 接地支撑、R2 磁力吸合、R3 无重叠、R4 重心稳定, 静力学/工艺规则 R5 悬挂承重、R6 悬臂力矩、R7 装配可达 (逐片放置模拟)、R8 结构冗余警告, 覆盖成品与每个教程中间状态; 外加教程一致性质检 (步骤连续、每片恰放一次、引用存在、说明非空)。
- **执行者**: CI, 每次内容提交自动运行 (见第 6 节)。
- **成本**: 秒级。**覆盖**: 100% 模型, 100% 提交。
- **通过标准**: 零 Error; Warning (如 `disconnected_assembly`) 须在教程文案中有对应说明, 否则视为未通过。

### L2 物理仿真抽检 (容差抖动蒙特卡洛, 第一期已实现)

- **落地形态 (第一期, 已实现)**: 不等完整刚体引擎, 先在校验器内落地**容差抖动蒙特卡洛 (jitter)** —— 对成品及全部中间状态的每片位姿注入 ±1.5mm / ±2° 随机误差, 生成 N 个扰动副本 (默认 N=50, 固定随机种子, CI 可复现), 逐副本重跑整套 R1~R8 (连接识别容差按注入误差最坏情况放大, 等效于连接拓扑按未扰动模型取定), **任一副本任一装配体出错即拒绝** (严于最初设计"通过率 ≥ 90%"的最低口径, PHYSICS_RULES.md 第 5 节宁严勿松) —— 专门捕捉"微小错位累积坍塌" (失效分类 F08)。触发标记由 `tools/physical_risk_report.py` 自动判定, 执行入口与字段约定见 2.1 节接口约定, 规则细节见 PHYSICS_RULES.md R9 节。
- **后续增强 (仍为规划)**: 接入刚体物理引擎 (候选: [Jolt Physics](https://github.com/jrouwe/JoltPhysics) 或 [Rapier](https://rapier.rs/)), 磁吸边建模为**可断裂约束** (按品牌标定的最大拉力/力矩), 补齐两段动力学测试: ① **静置沉降** —— 重力下模拟 5 秒, 任何片位移 > 5mm 或约束断裂即失败; ② **扰动脉冲** —— 对最高点施加水平小冲量 (模拟轻碰), 结构须回稳。任务登记: [PHYSICS_VERIFICATION_DEEP_DIVE.md](PHYSICS_VERIFICATION_DEEP_DIVE.md) 第 5 节 P1-3 剩余项。
- **执行者**: 工程师本地与 CI 均可即刻执行 (工具入库, 门禁挂接见第 6 节), 不再依赖人工排期。QA 流水线门禁挂钩三接入点 (统一入口: D4+ 模型 `validate --profile strict --jitter 50`): `tools/run_strict_audit.sh` 阶段 3 / `tests/run_full_qa.sh` 可选关卡 19 / `tools/run_release_gate.sh --full --l2` —— CLI 实装 `--jitter` 前为占位, 实装后自动启用, 挂钩契约与启用条件见 [TESTING.md](TESTING.md) 3.17 节。
- **成本**: 秒~分钟级/模型。**覆盖**: 被标记的模型 (见第 2 节触发条件, 全部可自动检测)。
- **定位**: L2 是 L1 的**抽检补强**, 不是替代 —— L1 的规则永远先跑、永远全量; L2 全绿同样不豁免 L3 分级要求 (人手排产用法见 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md) 0.5 节)。

### L3 实物搭建验证 (人 + 真实磁力片)

- **内容**: 人类测试员使用真实磁力片, 按第 3 节规程完整执行: 计时分步搭建、敲击测试、提起测试、拆解重搭、品牌兼容性、儿童测试。
- **执行者**: 内容 QA 测试员; 儿童测试由测试员在监护人陪同下组织。
- **成本**: 0.5~2 小时/模型 (儿童测试另计)。**覆盖**: 按难度分级 (见第 2 节)。
- **产出**: 验证记录 JSON (见第 5 节) + 失效照片归档 (见第 4 节)。

## 2. 各难度分级的验证要求 (T1~T5)

难度分级 T1~T5 与模型 JSON 的 `difficulty` 字段 (1~5) 一一对应。

| 分级 | 典型模型 | L1 软件规则 | L2 仿真抽检 | L3 实物验证 |
| --- | --- | --- | --- | --- |
| T1 (difficulty=1) | 平铺图案、小房子 | ✅ 必须, 每次提交 | 仅被标记时 | 每系列抽检 ≥ 1/5 (成人测试员, 完整规程) |
| T2 (difficulty=2) | 花朵、火箭、单层建筑 | ✅ 必须 | 仅被标记时 | 每系列抽检 ≥ 1/3 |
| T3 (difficulty=3) | 城堡地基与城墙、双层建筑 | ✅ 必须 | 被标记 100% + 随机 20% | **每个模型必做** (成人测试员) |
| T4 (difficulty=4) | 塔楼、穹顶、动物立体像 | ✅ 必须 | **每个模型必做** | 每个模型必做 + **目标年龄段儿童测试** |
| T5 (difficulty=5) | 摩天轮、大跨度桥、多层建筑群 | ✅ 必须 | 每个模型必做 (含蒙特卡洛) | 每个模型必做, **两名测试员独立各搭一次** + 儿童测试 + 品牌兼容性全测 |

**L2 标记触发条件** (满足任一即被标记): 五条触发条件已全部落实为 `tools/physical_risk_report.py` 的**可检测项** —— 每条对应一个机器可读检测编码, CI 与编辑器共用同一判定, 不存在"口头条件":

| # | 触发条件 | 检测编码 | 判定口径与数据来源 |
| --- | --- | --- | --- |
| 1 | L1 产生任何 Warning | `l1_warning` | 与 `magtile_app validate` 同一套规则实现产出的 Warning 集合 (含每个教程中间状态), 非零即命中 |
| 2a | 结构高度 > 6 个单位 | `tall_structure` | 成品最高点高度, 单位制与 `unbraced_wall_max_height` 一致 |
| 2b | 连续 ≥ 3 片的垂直墙链 (墙上立墙再立墙) | `tall_wall_chain` | 沿磁吸边逐级立置的竖直片链长 ≥ 3 |
| 3 | 重心投影到接地凸包边界距离 < `stability_margin` 的 50% (临界稳定) | `critical_com_margin` | 成品与每个中间状态取最小裕量与阈值比较 |
| 4 | 使用扇形/六边形等低磁力边占比形状承重 | `weak_edge_load_bearing` | 形状目录磁力边元数据 × 支撑路径判定 (该片位于其他片通往地面的支撑路径上) |
| 5 | 内容设计师手动标记 (见第 5 节) | `manual_flag` | 模型 `content_meta` 手动标记字段或旁车文件 `flags`; 手动标记只可追加, **不可取消**自动命中 |

**复验触发条件** (任一发生则已通过的 L2/L3 结果作废, 状态回退):

- `final_assembly` 或 `steps` 发生任何改动 (以内容哈希判定, 见第 5 节);
- `tile_catalog.json` 中该模型用到的形状几何或磁力边定义变更;
- 失效库新增了与该模型结构模式匹配的失效类型 (由 QA 评估)。

### 2.1 L2 工具接口约定 (权威口径)

L2 第一期由三件套落地 (与本约定同批并行入库; 名称与字段以本节为约定基线, 工具提交向本节对齐):

1. **标记判定 / 风险报告 `tools/physical_risk_report.py`**:
   - 输入: 模型目录或单个模型 JSON (+ `--data-dir data`); 默认人读报告, `--json` 输出机器可读;
   - 每模型输出至少含: `model_id`、`flags` (上表检测编码数组)、`flagged` (任一编码命中)、`l2_required` (综合结论: `flagged`, 或 `difficulty` 达到本节分级表 T4/T5 "每个模型必做"档; T3 另加随机 20% 抽检);
   - 退出码: 默认报告型 (恒 0); 门禁旗标 (`--fail-on-flagged` 语义) 下, 存在 `l2_required` 且无有效 L2 通过凭据的模型 → 非零。
2. **jitter 蒙特卡洛** (校验器内建, `magtile_app validate` 的 `--jitter [N]` 模式, 实现 `PhysicsValidator::validateModelWithJitter`, 规则号 R9):
   - 不变量 (约定, 不随实现漂移): 注入幅度 ±1.5mm (0.021 单位/轴, 水平) / ±2° (偏航)、副本数默认 N=50 (CLI 可调 1~10000, 显式 0/负数按参数错误退出码 2)、**任一副本任一受测装配体出错即非零退出** (收紧自最初设计的"通过率 ≥ 90%": 每 10 次搭建塌 1 次的模型不允许发布)、固定随机种子 + 自带均匀分布映射 (CI 跨平台逐轮可复现)、连接识别容差按注入误差最坏情况放大 (等效于连接拓扑按未扰动模型取定 —— 不把刻意注入的错位误判成"没连上", 避免容差自嗨; 稳定裕量与静力预算保持所选档位原值, 它们才是受测对象), 可与 `--profile strict` 叠加;
   - 报告: 汇总一条 `placement_jitter_failure` Error —— 失败副本数/总副本数、涉及的底层错误码集合、首个失败样本的完整消息 (自带"最终成品/第 N 步"装配体上下文) 与涉事片 id; 全绿时打印 "N/N 轮全部通过" 统计行。
3. **回归夹具与 ctest**: 抖动负例夹具 (静态 R1~R8 全绿但注入误差后必挂的边缘设计, 复现 F08 型累积失稳) 放入 `tests/test_physics_jitter/` 并配 `.expected` sidecar —— 专用执行器 `tests/test_physics_jitter.sh` 先断言普通 validate 放行 (证明静态规则原理上放不掉)、再断言 `--jitter` 以 `placement_jitter_failure` 拒绝, 目录 glob 零配置注册为 `physics_jitter_*`; 同目录不带 sidecar 的为抖动正例 (加固后同构造放行, 防矫枉过正), `tests/test_physics_positive/` 全部正例自动追加抖动档 (`physics_jitter_positive_*`); 旗舰模型抖动回归注册为 `validate_jitter_*` (与 `validate_strict_*` 同一批旗舰清单)。另一条并行通道: `tests/test_physics_negative/` 的负例执行器支持 sidecar 声明 `jitter=<N>` —— 声明后该负例改以 `validate --jitter N` 运行 (R9 型负例走此通道时进入负例注册表与 `physics_negative_*` 关卡, 如 `jitter_sensitive`); 两条通道的差异在于专用执行器额外断言 "名义模型普通 validate 放行" 这一前提, 负例通道只断言最终拒绝。

机器结果落盘: 写入 5.2 节旁车文件 `records[]` 一条 `layer: "L2"` 记录, 至少含 `date`、执行方 (`ci` / 工程师)、jitter 参数 (副本数与注入幅度) 与 `pass_rate`, 状态机按 5.2 节进入 `sim_passed`。

## 3. 实物测试规程

### 3.0 准备与环境

- **标准测试套件**: 官方基准品牌 (第一优先支持品牌) 全新套装一套, 磁力衰减超标 (见 3.5 标定法) 的旧片剔除;
- **桌面**: 平整硬质桌面 (木质/塑面), 禁止桌布/地毯; 环境温度 15~30°C;
- **记录**: 每次测试填写一份验证记录 (字段与第 5 节 JSON 对应), 全程固定机位录像, 失效瞬间截图归档;
- **原则**: 测试员**只看教程, 不看设计源文件**, 严格按步骤操作, 不允许"凭经验加固"。

### 3.1 计时分步搭建

1. 打开教程, 从第 1 步开始, 每步启动计时;
2. 逐字按步骤说明与提示操作, 记录: 每步耗时、犹豫点 (读了两遍以上才理解)、说明歧义、结构晃动/掉片事件;
3. 任何一步发生**非人为失误的掉片或坍塌** → 该步骤记 Fail, 拍照、记录失效类型 (第 4 节编码), 测试终止或修复后继续 (由 QA 决定);
4. 总耗时超出分级预算 (T1: 10 分钟 / T2: 20 / T3: 40 / T4: 70 / T5: 120) 记 Warning, 反馈给内容设计师评估步骤拆分。

### 3.2 敲击测试 (Knock Test)

成品完成后静置 30 秒, 然后:

1. 用食指指腹从 10cm 距离水平轻敲**结构最高点侧面** 3 次 (力度以敲击自己手背不感到痛为准);
2. 再轻敲**结构几何中部侧面** 3 次;
3. 判定: 无片脱落、无可见永久位移 → Pass; 掉落 1~2 片装饰性片 (不承重) → Conditional (记录并反馈); 承重片脱落或连锁坍塌 → Fail。

### 3.3 提起测试 (Lift Test)

1. 双手托住模型底座两侧, 匀速提起 5cm, 悬停 10 秒, 匀速放回;
2. 判定: 完整保持 → Pass; 任何片脱落 → Fail;
3. 例外: 设计上明确为"桌面固定" 的平铺类模型 (如曼陀罗图案) 在元数据中标注 `lift_test: "n/a"`, 跳过本项, 但教程文案必须提示"此模型不适合拿起移动"。

### 3.4 拆解重搭测试

1. 按步骤**逆序**拆解, 记录难以分离的连接 (磁力过强的死角、需要指甲抠的位置);
2. 立即按教程第二次完整搭建, 计时;
3. 判定: 第二次耗时应 ≤ 第一次的 80%, 且零失效; 若第二次仍在同一步骤出问题 → 该步骤设计缺陷实锤, Fail 并反馈。

### 3.5 品牌兼容性测试

**适用**: T5 全测; T3/T4 在模型元数据声明多品牌支持时执行; 其余抽检。

1. **单品牌全搭**: 用 Magna-Tiles、Connetix、Playmags 各完整搭一次 (几何差异: 各品牌单位边长、倒角、片厚不同, 对应 `tile_catalog.json` 的 `unit_mm` 标定分目录);
2. **混品牌搭建**: 结构下半部用品牌 A、上半部用品牌 B (取磁力最弱组合), 完成后重复 3.2 敲击 + 3.3 提起;
3. **磁力标定** (每季度一次, 非每模型): 用弹簧秤测各品牌"两片正方形整边吸合后垂直拉开"的拉力, 记录到品牌参数表, 作为 L2 仿真约束断裂阈值的输入;
4. 判定与产出: 每个品牌组合各记 Pass/Fail, 写入验证记录的 `brand_compat`; 任何 Fail 组合在产品端显示"不建议使用 XX 品牌搭建此模型"。

### 3.6 儿童测试规程 (4 岁以上)

**适用**: T4/T5 必做; T1~T3 新系列首发模型抽做。这是"儿童照着教程搭得出来"这一承诺唯一的直接证据来源。

#### 3.6.1 伦理与安全 (先于一切)

- 监护人**书面**知情同意; 儿童本人口头同意, **任何时刻可以不给理由退出**;
- 全程监护人或测试员在场; 3 岁以下磁铁玩具禁令严格执行, 产品面向 4 岁以上;
- 测试是"陪玩", 不是"考试": 不催促、不比较、不在儿童面前记录负面评价;
- 数据匿名化: 只记年龄段与编号, 不记姓名; 拍摄仅限手部/结构特写且需单独同意;
- 单场时长上限: 4~6 岁 20 分钟, 7~9 岁 35 分钟, 10 岁+ 45 分钟。到时未完成也正常结束并致谢, 记录中断点 (T4/T5 允许分多场累计)。

#### 3.6.2 年龄组与目标分级

| 年龄组 | 形式 | 目标分级 | 通过标准 |
| --- | --- | --- | --- |
| 4~6 岁 | 家长共读教程, 儿童动手, 家长可扶稳底座但不代放 | T1~T2 | 完成率 ≥ 80%, 实质协助 (L3 级) 人均 ≤ 1 次, 无挫败弃搭 |
| 7~9 岁 | 独立跟随教程, 观察员只记录不干预 | T2~T4 | 完成率 ≥ 80%, 卡壳步骤 (>3 分钟) ≤ 2 处 |
| 10+ 岁 | 完全独立, 含拆解重搭 | T3~T5 | 完整通过 3.1~3.4 全部项目 |

测试环境与 3.0 节一致 (平稳桌面 + 防滑垫); 磁力片按"所需磁力片清单"备齐但**不预分拣** —— 找片本身是真实体验的一部分; 教程载体与真实产品一致 (平板运行 tutorial GUI 或打印分步图)。

#### 3.6.3 协助阶梯 (Hint Ladder)

在场成人只能按以下顺序逐级升级协助, 且每次协助都记录级别 —— 协助级别本身就是步骤设计质量的量化信号:

| 级别 | 允许的动作 | 记录含义 |
| --- | --- | --- |
| L0 | 不介入, 仅鼓励 ("你自己再看看图?") | 正常 |
| L1 | 重读/复述当前步骤文字 | 文案对该年龄段可能偏难 |
| L2 | 指出参照物 ("看看这片蓝色的旁边") | 步骤缺 highlight_tiles 提示 |
| L3 | 示范放置一片 (由成人放) | 该步骤对该年龄段过难, 计一次**实质协助** |

在场成人**永远不可以**整理儿童已搭的结构, 或代放超过一片。

#### 3.6.4 观察记录与判定

逐步记录: 每步耗时与是否理解说明 (是/否/求助); 放错次数 (位置/朝向) 与是否自我纠正; 各级协助次数; **坍塌事件** (发生步骤、脱落的连接、诱因: 结构自身 / 手抖误碰 / 桌面震动); 挫败情绪事件与出现步骤; 中断点; 结束后的主观趣味评分 (三档笑脸卡, 儿童自选); 儿童原话反馈。

**同一模型至少 2 名目标年龄段儿童**, 结论取较差者。在 3.6.2 表格通过标准之上, 追加以下硬性判定:

1. **结构自身坍塌 0 次容忍** (非外力误碰的坍塌): 出现即 Fail, 且必须回答"L1/L2 为什么没拦住", 按第 4 节回填失效编码与回归用例;
2. 手抖/误碰导致坍塌 ≥ 2 次 → 结构冗余不足 (对照 `single_point_of_failure` / `no_structural_redundancy` 警告位置), 加固后重测;
3. 任何单一步骤 ≥ 50% 的儿童触发 L3 协助, 或 ≥ 30% 首次放错 → 该步必须整改 (拆步 / 加 tip / 补 highlight_tiles);
4. 主观评分"不开心"占比 > 20% → 转内容团队评审 (不阻断物理发布, 但记档)。

儿童测试暴露的问题优先修改教程与模型 (拆步、加提示、调整放置顺序、按警告点位加固), 而不是降低通过标准; 若校验器拒绝但儿童反复轻松搭成, 记录实测证据后方可评估放宽对应参数 (须保证全部负例夹具仍被拒绝)。

### 3.7 综合判定

| 结论 | 条件 | 后续 |
| --- | --- | --- |
| Pass | 全部适用项 Pass | 写入验证记录, 状态置为 `physical_passed` |
| Conditional | 仅装饰片级小问题, 已反馈 | 设计师修订后仅复测受影响项 |
| Fail | 任何承重失效 / 儿童测试不达标 | 状态置 `rejected`, 附失效编码与照片, 回到编辑器修改 |

## 4. 失效分类学 (Failure Taxonomy)

每种真实失效模式给出: 编码、现场照片描述 (照片按 `assets/failures/<编码>_<模型id>_<序号>.jpg` 归档)、**应当由哪条软件规则拦截** (含尚未实现的规划规则, 引用 PHYSICS_RULES.md 第 8 节)。凡"软件本应拦截却漏过"的实物失效, 一律回填为该规则的回归测试用例。

| 编码 | 失效模式 | 典型照片描述 | 应拦截的软件规则 | 首个能发现的层 |
| --- | --- | --- | --- | --- |
| F01 | 错位半搭 | 两片正方形错开半格叠搭, 磁条未对齐, 上片下垂翘起 | R2 磁力吸合 (端点重合判定, `connect_tolerance`) | L1 |
| F02 | 空中孤片 | 教程截图里"贴"在墙侧的装饰片, 实物中直接掉落在桌面 | R1 接地支撑 (`floating_tile`) | L1 |
| F03 | 悬挑倾覆 | 外挑阳台放到第 3 片时整体绕支撑边翻倒, 照片为倒塌瞬间连拍 | R4 重心稳定 + **R6 悬臂力矩** (`cantilever_overload`) | L1 |
| F04 | 同层穿插 | 编辑时两片菱形在地台同一平面重叠, 实物根本无法同时放下 | R3 无重叠 (共面 SAT) | L1 |
| F05 | 混品牌弱磁脱落 | Connetix 墙体上接 Playmags 城齿, 敲击测试第 1 下即整排剥离, 照片见剥离面磁条错位 | 软件不可拦截 → L3 品牌测试; 缓解: 品牌兼容元数据 + 产品端提示 | **仅 L3** |
| F06 | 放置干涉 (够不着) | 四面墙合拢后教程要求在内侧放地台补片, 成人手指伸入即碰倒后墙 | **R7 装配可达** (`enclosed_placement`); "单手可放置的操作空间"仍属规划 (§8.3) | L1 (完全包围) / L3 (操作空间) |
| F07 | 手抖连锁塌 | 6 岁儿童往双层墙顶放三角城齿, 手腕抖动带倒整面上层墙 | 无法直接拦截; 缓解规则: **R8 结构冗余警告** (`single_point_of_failure` / `no_structural_redundancy`) + 每步 ≤ 8 片的步骤粒度规范 | L3 儿童测试 |
| F08 | 错位累积失稳 | 16 步模型搭到第 12 步, 累积 ~5mm 歪斜, 静置 20 秒后自行坍塌 | **L2 jitter 容差抖动 (蒙特卡洛, 已实现)** —— `validate --jitter` (2.1 节接口约定), F08 型负例夹具锁死行为; 长链结构预警 (第 2 节 `tall_structure` / `tall_wall_chain`) | L2 |
| F09 | 底面滑移 | 敲击测试中底座在光滑玻璃桌面整体滑动散架 | 非模型缺陷 → 测试环境规范 (3.0) + 教程通用提示"在防滑桌面搭建" | L3 |
| F10 | 拆不下来 | 六边形被三面包围, 拆解时需暴力掰, 儿童直接拉裂贴膜 | 规划中的可达性校验逆向应用 (拆解顺序 = 逆步骤序) | L3 |
| F11 | 重心出界 | 单侧加装饰后整体缓慢倾倒, 照片为倾倒后全景 | R4 重心稳定 (`unstable_center_of_mass`) | L1 |
| F12 | 磁力衰减片 | 库存旧片磁力减弱, 标准结构也挂不住 | 非内容缺陷 → 测试套件管理 (3.0 剔除 + 3.5 季度标定) | L3 |

维护要求: 每次 L3 失效必须归档"编码 + 照片 + 模型 id + 步骤号" —— 归档载体是登记工具 `tools/physical_failure_registry.py` 维护的账本 `data/physical_failures.json` (逐条跟踪"是否已下沉 L1 负例夹具", `check` 子命令校验账本完整性并列出待下沉欠账); 每季度复盘一次分类表, 出现 ≥ 3 次的"仅 L3"失效模式, 立项评估能否规则化下沉到 L1/L2 (`check` 自动盘点该信号)。从实搭失败到负例夹具到 CI 回归的完整闭环规程见 [PHYSICAL_CALIBRATION_WORKFLOW.md](PHYSICAL_CALIBRATION_WORKFLOW.md)。

## 5. 内容编辑器集成 (规划: 阶段 2 编辑器)

### 5.1 "需要实物复核"自动标记

编辑器在保存时实时计算并展示验证要求徽章:

- 依据第 2 节表格由 `difficulty` 得出 L2/L3 是否必做;
- 依据第 2 节标记触发条件 (Warning、高墙链、临界重心、弱磁形状承重) 自动点亮 **"需要实物复核"** 标记 —— 判定与 `tools/physical_risk_report.py` 共用同一套检测编码 (第 2 节表格), 编辑器不另造口径;
- 设计师可手动追加标记 (例如自觉某步骤"手感"存疑), 但**不能取消**自动标记。

### 5.2 验证状态机与记录格式

验证记录不写入模型 JSON 本体, 而是存放在旁车文件 `data/verification/<model_id>.json`, 通过**内容哈希**绑定被验证的那个版本 (哈希取 `final_assembly` + `steps` 的规范化 JSON 的 SHA-256)。模型改动 → 哈希失配 → 状态自动回退, 杜绝"改完接着用旧的实物验证结论"。

```json
{
  "model_id": "castle_foundation_01",
  "content_hash": "sha256:9f2a…",
  "status": "physical_passed",
  "required_layers": ["L1", "L2", "L3"],
  "flags": ["tall_wall_chain"],
  "records": [
    {
      "layer": "L3",
      "date": "2026-08-20",
      "tester": "qa_zhang",
      "tile_brand": "connetix",
      "build_time_sec": 1930,
      "step_times_sec": [95, 120, 88],
      "knock_test": "pass",
      "lift_test": "pass",
      "rebuild_test": "pass",
      "brand_compat": { "magna_tiles": "pass", "connetix": "pass", "playmags": "fail", "mixed_worst": "fail" },
      "child_test": { "age_band": "7-9", "testers": 2, "completion": "pass", "stuck_steps": [11] },
      "failures": ["F05"],
      "evidence": ["assets/failures/F05_castle_foundation_01_001.jpg"],
      "notes": "Playmags 城齿吸力不足, 已在产品端标注品牌建议"
    }
  ]
}
```

状态机 (只能按箭头前进, 内容改动回退到 `software_passed` 重新走):

```
draft → software_passed → sim_passed → physical_pending → physical_passed
                 ↑                                              │
                 └────────── 内容哈希失配 (模型被修改) ←──────────┘
          任何环节失败 → rejected (附失效编码, 修改后从 draft 重走)
```

不需要 L2 的模型从 `software_passed` 直接进入 `physical_pending`; 不需要 L3 的模型 (T1/T2 未被抽中) 在 `software_passed` / `sim_passed` 即视为可发布。

### 5.3 编辑器工作流

1. 设计师保存 → 编辑器内嵌 L1 校验, 红线实时标注问题片;
2. L1 全绿 → 状态 `software_passed`, 若需 L2/L3, 一键"提交复核"生成 QA 任务 (含模型、内容哈希、自动标记原因);
3. QA 按第 3 节规程测试, 在编辑器复核面板填写记录表单 (即 5.2 JSON 的表单化), 上传失效照片自动归档命名;
4. 编辑器模型列表展示状态徽章与筛选器 ("待实物复核"、"已被改动待复验"), 内容负责人据此排产。

## 6. 内容 CI/CD

内容仓库 (模型 JSON + 验证旁车文件) 的每个合并请求必须通过以下流水线, **任何一步失败即阻断合并**:

```
PR → [1] Schema 校验 → [2] L1 物理+教程质检 → [3] 验证状态门禁 → [4] L2 仿真 (被标记模型) → 允许合并
```

1. **Schema 校验**: 变更的模型 JSON 符合 `schema_version` 对应的 JSON Schema; 验证旁车文件符合 5.2 格式;
2. **L1 质检**: 对每个变更模型运行 `magtile_app validate`, 零 Error; 有 Warning 时要求对应步骤 `tip`/`description` 含分组说明关键字;
3. **验证状态门禁**: 按第 2 节表格核对 —— 该 `difficulty` 要求的层是否都有记录、`content_hash` 是否与当前文件一致、`status` 是否达到可发布态; T5 额外要求 records 中存在两名不同 `tester` 的 L3 记录;
4. **L2 仿真 Job**: 先跑 `tools/physical_risk_report.py` 得出被标记清单, 对 `l2_required` 模型执行 jitter 蒙特卡洛 (2.1 节接口约定); jitter 未过、或缺有效 L2 通过凭据 (旁车 `layer: "L2"` 记录) 即阻断。刚体沉降/脉冲增强落地后在同一 Job 内追加, 不另开门禁。

门禁脚本 `tools/ci_validate_content.py` (随内容仓库提供) 的核心逻辑:

```python
#!/usr/bin/env python3
"""内容合并门禁: 每个模型 JSON 合并前必须通过。用法: ci_validate_content.py <changed_files...>"""
import hashlib, json, subprocess, sys

REQUIRED = {1: "software_passed", 2: "software_passed",
            3: "physical_passed", 4: "physical_passed", 5: "physical_passed"}
ORDER = ["draft", "software_passed", "sim_passed", "physical_pending", "physical_passed"]

def content_hash(model):
    payload = json.dumps({"final_assembly": model["final_assembly"], "steps": model["steps"]},
                         sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

def check(model_path):
    model = json.load(open(model_path, encoding="utf-8"))
    # 1) L1: 物理规则 + 教程一致性
    r = subprocess.run(["./build/magtile_app", "validate", model_path])
    if r.returncode != 0:
        return f"{model_path}: L1 质检失败"
    # 2) 验证状态门禁
    ver_path = f"data/verification/{model['id']}.json"
    try:
        ver = json.load(open(ver_path, encoding="utf-8"))
    except FileNotFoundError:
        ver = {"status": "software_passed", "content_hash": content_hash(model), "records": []}
        if model["difficulty"] >= 3:
            return f"{model_path}: 缺少验证记录 {ver_path} (T{model['difficulty']} 必须实物验证)"
    if ver["content_hash"] != content_hash(model):
        return f"{model_path}: 模型已被修改, 验证记录 {ver_path} 已过期, 需复验"
    need = REQUIRED[model["difficulty"]]
    if ORDER.index(ver["status"]) < ORDER.index(need):
        return f"{model_path}: 状态 {ver['status']} 未达到 T{model['difficulty']} 要求的 {need}"
    if model["difficulty"] == 5:
        testers = {rec.get("tester") for rec in ver["records"] if rec.get("layer") == "L3"}
        if len(testers) < 2:
            return f"{model_path}: T5 要求两名测试员独立实物验证"
    return None

errors = [e for p in sys.argv[1:] if p.endswith(".json") and "models/" in p if (e := check(p))]
for e in errors:
    print(f"[门禁失败] {e}")
sys.exit(1 if errors else 0)
```

对应的 CI 配置要点 (以 GitHub Actions 为例):

```yaml
on:
  pull_request:
    paths: ["data/models/**", "data/verification/**", "data/tile_catalog.json"]
jobs:
  content-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j
      - run: git diff --name-only origin/${{ github.base_ref }}... | xargs python3 tools/ci_validate_content.py
```

配套治理规则:

- 内容仓库主干开启分支保护, `content-gate` 为必需检查;
- `data/verification/**` 的改动仅允许 QA 角色批准合并 (CODEOWNERS), 防止设计师自证通过;
- `tile_catalog.json` 变更触发**全库** L1 重跑, 并列出内容哈希涉及形状的待复验模型清单;
- 每次发布打包前, 全量运行门禁脚本作为最终防线。

## 7. 与其他文档的关系

- 作者级逐步实搭执行清单 (敲击/提起/记录模板/`content_meta.physical_verified` 轻量落盘): [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md), D4+ 待复核清单由 `tools/list_physical_pending.py` 跟踪 (本文档 5.2 节旁车文件与轻量字段两种凭据都认, 旁车带内容哈希绑定为权威); 排产人手前先跑 L2 决定顺序与抽检取舍: 其 0.5 节;
- 面向用户/QA 复核人的上手指南 (V1 抽样包需备哪些磁力片、预估工时、打印工作单、落盘与照片归档约定): [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md);
- 实物失效回填软件规则的闭环规程 (抽样实搭 → 失败登记 `tools/physical_failure_registry.py` → 生成负例夹具 → CI 回归, 即第 4 节维护要求的执行载体): [PHYSICAL_CALIBRATION_WORKFLOW.md](PHYSICAL_CALIBRATION_WORKFLOW.md);
- 软件规则 (L1) 的精确定义与演进路线: [PHYSICS_RULES.md](PHYSICS_RULES.md);
- 编辑器与内容量产管线的阶段规划: [ROADMAP.md](ROADMAP.md) 阶段 2 与阶段 4;
- L2 第一期 (jitter 蒙特卡洛 + `physical_risk_report` 风险标记) 已按 2.1 节接口约定落地; 其余规划项 (刚体沉降/脉冲增强、验证旁车文件、门禁脚本、编辑器复核面板) 随阶段 2 编辑器一并落地, 在此之前 L3 流程即刻以人工表单执行 —— **实物验证从今天起就是 T3+ 模型入库的硬性要求, 不等工具**。

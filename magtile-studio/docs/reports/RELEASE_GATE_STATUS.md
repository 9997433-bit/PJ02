# 发布门禁状态报告 (Release Gate Status)

- 生成时间: 2026-08-25 17:21 UTC
- 基线提交: `262ebc3` (`cursor/magtile-studio-foundation-a95b`)
- 结果有效性: 本报告描述**基线 `262ebc3` 时点**的门禁状态。巡检期间分支持续推进 —— 至 `58e5173` 的 7 个提交均为纯文档不影响结果; 其后抖动接力批已开始落地 R9 修复: `ball_run_tower_01` (`8d07fe5`, 外缘加双层门式立柱) 与 `lego_style_house_01` (`24fd0ec`, 教程步骤重排) 已入分支, `marble_run_spiral_01` / `rainforest_canopy_01` 修复在途。**修复批合入完毕后须重跑两条门禁命令刷新本报告**
- 构建配置: CMake Release, 全新 worktree 干净构建
- 执行命令:
  1. `tools/run_strict_audit.sh --jitter-only --jitter require` → **退出码 1**
  2. `tools/run_release_gate.sh --full --l2 --fail-on-pending` → **退出码 1**

## 1. 结论速览

| 关卡 | 结果 | 失败归因 |
| --- | --- | --- |
| L2 抗扰动巡检 (`--jitter-only --jitter require`) | **未通过** (42/45 D4+ 通过) | 已知抖动敏感模型 3 个 (见 §2) |
| 发布门禁 · 全量 QA (39 子关卡) | **FAIL** (36 通过 / 2 跳过 / 1 失败) | 唯一失败子关卡 = 弱磁严格档全库巡检, 其抖动阶段挂在同一批 3 个已知模型上; 其余 36 个子关卡 (CTest 全量回归、模型库质检、负例夹具、免费层对齐、文案守卫等) 全绿 |
| 发布门禁 · L2 抗扰动档 (D4+ jitter 全绿) | **FAIL** | 同 §2 的 3 个已知模型 |
| 发布门禁 · L3 实物复核缺口 (硬闸门, `--fail-on-pending`) | **FAIL** | D4+ 45 个模型全部待实物复核 (已复核 0), 属流程固有缺口: 只能由人手按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭清零, 软件侧无法代劳 |

**判定: 无新增缺陷。** 两条命令的全部失败均落在已知抖动敏感模型清单 (§2) 与 L3 实物复核固有缺口 (§3) 之内, 不存在其他类别的失败, 本轮不需要代码或模型修复。

## 2. 已知抖动敏感模型 (R9 `placement_jitter_failure`)

已知清单共 4 个模型。其中 3 个为 D4, 直接命中 D4+ 门禁; 第 4 个 `lego_style_house_01` 为 D3, 不在 D4+ 巡检范围内 (不影响门禁计数), 但单跑 `validate --profile strict --jitter 50` 仍失败, 一并登记如下。

| # | 模型 | 难度 | 片数/步骤 | 失败轮数 | 底层错误码 | 首个失败样本 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `ball_run_tower_01` (螺旋滚珠塔) | D4 | 90 片 / 19 步 | 4/50 | `cantilever_overload` | 第 7 轮, 第 16 步完成后: 3 片外挑 35.3 g·单位 > 预算 35.0 (总长 2.0 磁力边) |
| 2 | `marble_run_spiral_01` (弹珠螺旋滑道) | D4 | 77 片 / 18 步 | 3/50 | `cantilever_overload` | 第 12 轮, 第 12 步完成后: 3 片外挑 35.1 g·单位 > 预算 35.0 (总长 2.0 磁力边) |
| 3 | `rainforest_canopy_01` (雨林树冠天桥) | D4 | 84 片 / 18 步 | 3/50 | `cantilever_overload` | 第 18 轮, 第 11 步完成后: 1 片外挑 18.6 g·单位 > 预算 17.5 (总长 1.0 磁力边) |
| 4 | `lego_style_house_01` (乐高风小屋) | D3 | — | 7/50 | `enclosed_placement` | 第 5 轮, 第 14 步: 补片手部通道对毫米级误差零裕量 (处置记录见 `docs/PHYSICS_RULES.md` R9 节) |

共同特征: 名义几何在 strict 档静态规则 (R1~R8) 下压线放行, 注入 ±1.5mm/±2° 蒙特卡洛放置误差 (R9, 默认 50 轮、任一轮出错即拒) 后小概率越预算 —— 即 `BUILD_VERIFICATION.md` F08 "微小错位累积坍塌" 类边缘设计。

**处置方向** (待内容侧后续批次收口, 非本报告范围): 三个 D4 模型按 R9 报错建议在外挑远端补支撑柱 / 三角斜撑, 使铰链成环让悬臂分析自然消失 (参考正例夹具 `jitter_reinforced_cantilever` 的门式框架改法); `lego_style_house_01` 调整第 14 步补片顺序, 在封闭结构合拢之前放置。

## 3. L3 实物复核缺口 (硬闸门)

`--fail-on-pending` 生效: 扫描 209 个模型, D4+ 共 45 个, 已复核 0、待复核 45, 硬闸门按约定置红。该缺口由发布流程设计使然 —— L1/L2 软件全绿不豁免实物复核 (`docs/BUILD_VERIFICATION.md`), 只能由人手实搭按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 逐个清零 (缩减流程见 `docs/USER_HANDOFF.md` §4.3: risk Top 15 + 结构族代表)。此项不计为软件缺陷。

## 4. 明细日志出处

- L2 抗扰动巡检: `tools/run_strict_audit.sh --jitter-only --jitter require`, 小计 "D4+ 共 45 个模型, 通过 42, 失败 3"
- 发布门禁: `tools/run_release_gate.sh --full --l2 --fail-on-pending`, 报告 "3 个门禁关卡中 3 个失败, 不可发布"
- 全量 QA 内唯一失败子关卡 "弱磁严格档全库巡检 (strict)" 的失败行与本报告 §2 前 3 行逐一对应, 无其他失败模型

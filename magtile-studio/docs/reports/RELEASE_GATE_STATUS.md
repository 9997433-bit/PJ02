# 发布门禁状态报告 (Release Gate Status)

- 生成时间: 2026-08-25 19:26 UTC
- 基线提交: `3d24d74` (`cursor/magtile-studio-foundation-a95b`, 内容库 234 模型)
- 构建配置: CMake Release, `/tmp/wt-gate-234/magtile-studio` 干净构建 → **退出码 0**
- 执行命令:
  1. `cmake --build build -j4` → **退出码 0**
  2. `tools/run_release_gate.sh build --full --l2 --fail-on-pending` → **退出码 1** (仅 L3 硬闸门红)

## 1. 结论速览

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 全量 QA (39 子关卡: 37 过 2 可选跳过) | **PASS** | CTest 522/522, 模型库 234/234 全过 (validate/反平凡/逻辑/逐步装配/教程), 唯一性 27261 对 0 警告, strict 零警告审计, 免费层 30/30 对齐, 儿童文案 285 文件 8429 段全绿 |
| L2 抗扰动档 (D4+ jitter 50) | **PASS** | 45/45 D4+ 模型 50/50 轮全绿 (`run_strict_audit.sh --jitter-only --jitter require` 实跑) |
| L3 实物复核缺口 (硬闸门) | **FAIL** | 扫描 234 模型, D4+ 45 个待复核 0/45 —— 用户侧人手实搭, 非软件缺陷 |

**工程侧判定: 软件门禁在 234 模型基线上保持上限状态。** 209 → 234 扩容 (内容批 A~E 合入) 未引入任何软件侧回归; 唯一剩余失败仍为 L3 实物复核硬闸门 (`--fail-on-pending`), 按设计须用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭清零 (缩减流程: risk Top 15 + 结构族代表, 见 `docs/USER_HANDOFF.md` §4.3)。

## 2. R9 抖动敏感模型 —— 修复保持有效

| 模型 | 修复提交 | 手法 | 234 基线复验 |
| --- | --- | --- | --- |
| `ball_run_tower_01` | `8d07fe5` / `5b915a0` | 西线转角外缘双层门式立柱 (94 片) | 50/50 全绿 |
| `marble_run_spiral_01` | `114c154` | 三块转角台下挂直角三角斜撑 (80 片) | 50/50 全绿 |
| `rainforest_canopy_01` | `2ffc06e` | 树冠平台板根斜撑 (90 片) | 50/50 全绿 |
| `lego_style_house_01` | `24fd0ec` | 第 14 步补片顺序重排 (封闭前放置) | 50/50 全绿 |

内容批 A~E 新增的 25 模型无一进入 D4+ 抖动敏感名单 (D4+ 仍为 45 个, 全部存量)。

## 3. L3 实物复核缺口

扫描 234 模型, D4+ 45 个全部待复核 (与 209 基线同一批 —— 新增 25 模型均为 D2/D3, 未扩大 L3 缺口)。`check_v1_readiness.sh --quick` 对应 R6/R7 两项 P0 FAIL —— 预期状态, 待用户实搭后回填 `physical_verified` 标记。

## 4. 下一步

1. 用户侧: 按 `docs/USER_HANDOFF.md` §4 完成实物/行政/实机/沙盒验收
2. 工程侧可选: 内容扩至 250 模型 (C5 P1)、Windows D2 workflow 首跑

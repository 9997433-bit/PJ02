# 发布门禁状态报告 (Release Gate Status)

- 生成时间: 2026-08-25 20:53 UTC
- 基线提交: `ced770c` (`cursor/magtile-studio-foundation-a95b`, 内容库 250 模型)
- 构建配置: CMake Release, `/tmp/wt-gate-250/magtile-studio` 干净构建 → **退出码 0**
- 执行命令:
  1. `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j4` → **退出码 0**
  2. `tools/run_release_gate.sh --full --l2` → **退出码 0** (本次基线刷新未加 `--fail-on-pending`, L3 走报告型口径; L3 红色状态见下表与 §3)

## 1. 结论速览

| 关卡 | 结果 | 说明 |
| --- | --- | --- |
| 全量 QA (39 子关卡: 37 过 2 可选跳过) | **PASS** | CTest 554/554, 模型库 250/250 全过 (validate/反平凡/逻辑/逐步装配/教程), 唯一性 31125 对 0 警告, strict 零警告审计, 免费层 30/30 对齐, 儿童文案 301 文件 8874 段全绿 |
| L2 抗扰动档 (D4+ jitter 50) | **PASS** | 46/46 D4+ 模型 50/50 轮全绿 (`run_strict_audit.sh --jitter-only --jitter require` 实跑) |
| L3 实物复核缺口 | **RED (预期)** | 扫描 250 模型, D4+ 46 个待复核 0/46 —— 用户侧人手实搭, 非软件缺陷; 本次未加 `--fail-on-pending`, 该项按报告型记录, 正式出包终防线仍会红 |

**工程侧判定: 软件门禁在 250 模型基线上保持上限状态。** 234 → 250 扩容 (内容批 F~I 合入) 未引入任何软件侧回归; 唯一红项仍为 L3 实物复核 (待复核 45 → 46, 新增 1 个为批 F 旗舰 `stonehenge_01` D4 91 片), 按设计须用户按 `docs/PHYSICAL_REBUILD_CHECKLIST.md` 实搭清零 (缩减流程: risk Top 15 + 结构族代表, 见 `docs/USER_HANDOFF.md` §4.3)。

## 2. R9 抖动敏感模型 —— 修复保持有效

| 模型 | 修复提交 | 手法 | 250 基线复验 |
| --- | --- | --- | --- |
| `ball_run_tower_01` | `8d07fe5` / `5b915a0` | 西线转角外缘双层门式立柱 (94 片) | 50/50 全绿 (L2 档内) |
| `marble_run_spiral_01` | `114c154` | 三块转角台下挂直角三角斜撑 (80 片) | 50/50 全绿 (L2 档内) |
| `rainforest_canopy_01` | `2ffc06e` | 树冠平台板根斜撑 (90 片) | 50/50 全绿 (L2 档内) |
| `lego_style_house_01` | `24fd0ec` | 第 14 步补片顺序重排 (封闭前放置) | 50/50 全绿 (D3, L2 档外单独复验) |

内容批 F~I 新增的 16 模型中仅 `stonehenge_01` (D4) 进入 D4+ 抗扰动名单, 首跑即 50/50 全绿; 其余存量 45 个 D4+ 全部保持全绿。

## 3. L3 实物复核缺口

扫描 250 模型, D4+ 46 个全部待复核 (234 基线 45 个 + 新增 `stonehenge_01` D4 91 片 19 步)。`check_v1_readiness.sh --quick` 对应 R6/R7 两项 P0 FAIL —— 预期状态, 待用户实搭后回填 `physical_verified` 标记。族去重后必搭 36 个 (≈ 42.8h), 可缓建 10 个, 明细见 `docs/reports/PHYSICAL_FAMILY_PACK.md` 与 `docs/reports/PHYSICAL_RISK_REPORT.md` (同为 250 基线)。

## 4. 下一步

1. 用户侧: 按 `docs/USER_HANDOFF.md` §4 完成实物/行政/实机/沙盒验收
2. 工程侧: 内容库已达 200~250 上限目标 (250/250), 转入维护态; Windows D2 workflow 首跑待行政侧解锁
3. 正式出包前: 以 `tools/run_release_gate.sh --full --l2 --fail-on-pending` 复跑终防线 (L3 清零后应全绿)

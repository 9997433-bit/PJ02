# 实物校准闭环工作流 (Physical Calibration Workflow)

本手册定义 MagTile Studio 的**实物校准闭环**: 把 L3 实物复核 (人 + 真实磁力片) 发现的每一次真实失效, 系统性地回填成 L1/L2 自动规则的**永久回归资产**, 让软件校验器随着每一次实搭失败变得更准。

- **定位**: [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 第 4 节给出失效分类学 (F01~F12) 与"凡软件本应拦截却漏过的实物失效, 一律回填为回归测试用例"的纪律; 本手册把这条纪律落为**四步可执行闭环**, 载体是登记工具 `tools/physical_failure_registry.py` 与账本 `data/physical_failures.json`。
- **一句话**: 实搭失败不是坏消息, 是最贵的校准数据 —— 但只有入账、下沉、进 CI 的失败才算被消化, 口头"记住了"等于丢了。

## 1. 闭环总览

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ ① 抽样 10 实搭    │     │ ② 失败登记        │     │ ③ 生成负例夹具    │     │ ④ CI 回归         │
│ physical_sample_ │ --> │ physical_failure_│ --> │ tests/test_      │ --> │ fixture_registry │
│ pack.py 排产,    │     │ registry.py add  │     │ physics_negative/│     │ 关卡 + 负例执行器 │
│ 按规程逐模型实搭  │     │ (F编码+照片+步骤) │     │ 最小复现 + 断言   │     │ 每次提交自动重放  │
└──────────────────┘     └──────────────────┘     └────────┬─────────┘     └──────────────────┘
                                                           │ mark-sunk (账本闭环)
                                  不可规则化的编码 (F05/F09/F10/F12) --> 季度复盘计数 (§6)
```

四步全部走完, 一次实物失败才算**关账**: 账本里该条目 `fixture_sunk: true`, 且对应夹具已进必备清单、CI 变绿前提是"该夹具被正确拒绝"。

## 2. 第 ① 步: 抽样 10 实搭

按 V1 抽样包排产实搭 (备料/工时/打印工作单见 [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md), 判定动作见 [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md)):

```bash
python3 tools/physical_sample_pack.py                 # 抽样清单 + 逐模型备料 BOM (桌边核对)
python3 tools/physical_sample_pack.py --print-checklist docs/reports/PHYSICAL_SIGNOFF_WORKSHEET.md
                                                      # 重新生成逐步签核工作单后打印
```

实搭中与本手册相关的**唯一要求**: 任何一步发生非人为失误的掉片/坍塌, 或敲击/提起/拆解重搭阶段失效, 当场做三件事 ——

1. **拍照** (失效瞬间或失效后状态), 按 [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md) §7 约定命名: `docs/reports/qa_photos/<model_id>/fail_step<NN>_F<XX>.jpg`;
2. **对照失效分类学定编码** (F01~F12, 定义见 [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 第 4 节; 桌边速查: `python3 tools/physical_failure_registry.py codes`);
3. **在工作单"问题记录"栏写下步骤号与现象** —— 回到电脑前第 ② 步入账的原始凭据。

通过的模型照常按规程落盘 `physical_verified`, 与本闭环互不阻塞; **失败的模型不写字段**, 走下面的登记流程。

## 3. 第 ② 步: 失败登记 (入账)

回到电脑前, 把工作单上的每一次失效登记进账本 (一次失效一条, 同一模型多次失效登记多条):

```bash
python3 tools/physical_failure_registry.py add \
    --model skyscraper_01 --step 12 --code F08 \
    --photo docs/reports/qa_photos/skyscraper_01/fail_step12_F08.jpg \
    --tester qa_zhang \
    --notes "搭到第 12 步累积歪斜, 静置约 20 秒自行坍塌"
```

要点:

- `--step 0` 表示失效发生在**成品固定动作阶段** (敲击/提起/拆解重搭), 不在某个教程步骤内;
- `--photo` 接受仓库相对路径或 QA 工单附件 URL; 照片暂未拷入仓库时工具只警告不阻断, `check` 会持续提醒直到后补;
- 工具会当场校验: 编码必须合法 (F01~F12)、模型必须在库、步骤号超出模型步数会提示复核; 并按该编码的下沉目标直接打印**下一步动作** (必须下沉 L1 / 建议缓解性下沉 / 归 L2 管线 / 不可规则化只计数);
- 复发照登记: 同模型同步骤同编码再次失效**登记新条目** (工具会提示已有同类条目) —— 复发次数本身是 §6 季度复盘的输入;
- 查账: `python3 tools/physical_failure_registry.py list` (`--pending-sink` 只看欠账, `--json` 机器可读)。

## 4. 第 ③ 步: 生成负例夹具 (下沉)

对账本中每条**下沉目标为 L1** 的失效 (F01/F02/F03/F04/F06/F11; F07 建议做 warning 级缓解夹具), 把真实失效提炼为最小复现负例:

1. **提炼最小复现结构**: 不要整个模型照抄 —— 从失效模型中抽出触发失效的最小片组 (参考现有夹具体量, 一般 ≤ 8 片), 写成 `tests/test_physics_negative/<失效名>.json` (格式对照现有夹具, 如 `cantilever_overload.json`: `description` 写清"反面教材"机理与实物表现, `tags` 含"测试夹具", 步骤末步给出错误示范说明);
2. **写断言 sidecar** `tests/test_physics_negative/<失效名>.expected`:

```text
# <失效名>.expected — 物理负例期望声明 (sidecar, 由 test_physics_negative.sh 读取)
# 回填来源: data/physical_failures.json PF-XXXX (<model_id> 第 <N> 步, F<XX>)
expected_fail_rule=<校验器错误/警告码, 如 cantilever_overload>
severity=error        # error = 必须非零退出拒绝; warning = 零退出但必须输出 [警告] 行
```

3. **登记必备清单**: 在 `tests/test_physics_fixture_registry.sh` 的 `REQUIRED_NEGATIVE` 列表中加入夹具名 —— 没进必备清单的夹具被误删时只会静默消失, 不算完成下沉;
4. **本地验证夹具确实被拒**:

```bash
./build/magtile_app validate tests/test_physics_negative/<失效名>.json --data-dir data   # 应非零退出
bash tests/test_physics_negative.sh ./build/magtile_app data tests/test_physics_negative/<失效名>.json
bash tests/test_physics_fixture_registry.sh tests                                        # 必备清单完整
```

5. **账本关账**:

```bash
python3 tools/physical_failure_registry.py mark-sunk PF-0001 \
    --fixture tests/test_physics_negative/<失效名>.json
```

`mark-sunk` 会拒绝不存在的夹具、缺 sidecar 的夹具、未进 `REQUIRED_NEGATIVE` 的夹具 (过渡期可 `--allow-unregistered`, 但欠账仍在)。

**两种校准分支** (决定第 1 步怎么写夹具):

- **规则漏拦 (该拒未拒)**: 夹具喂给 `validate` 当前**放行** —— 这正是要修的规则缺口。先把夹具入库并让它红着, 再修 L1 规则/参数直到该夹具被拒**且全部正例 (`tests/test_physics_positive/`) 与全库模型仍然放行** (防矫枉过正, 见 [PHYSICS_RULES.md](PHYSICS_RULES.md) 参数演进约定);
- **规则已拦但实物仍塌 (参数偏松)**: 软件预检绿灯的结构实物失效, 说明档位参数高估了真实磁力 —— 对照 [STRICT_PHYSICS_AUDIT.md](STRICT_PHYSICS_AUDIT.md) 与 PHYSICS_RULES.md 1.4 节评估收紧参数或新增规则, 夹具锁住收紧后的判定。

**不下沉 L1 的编码怎么办**:

| 编码 | 去向 |
| --- | --- |
| F08 (错位累积失稳) | 归 L2 蒙特卡洛容差抖动 (仿真管线落地前, 可评估长链/高墙类 L1 代理夹具, 如现有 `unbraced_wall_too_tall` / `hanging_chain_long`) |
| F07 (手抖连锁塌) | 建议做 R8 结构冗余 warning 级缓解夹具 (对照 `single_point_of_failure` / `no_structural_redundancy`), 同时检查步骤粒度 (每步 ≤ 8 片) |
| F05 / F09 / F10 / F12 | 不可规则化 (品牌/环境/套件问题), 只入账计数, 走 §6 季度复盘 |

## 5. 第 ④ 步: CI 回归 (锁死)

下沉完成后, 该失效模式从"人肉记忆"变成每次提交自动重放的回归用例:

- **负例执行器**: `tests/test_physics_negative.sh` 按 sidecar 断言逐夹具执行 —— error 级必须非零退出拒绝且错误码匹配, warning 级必须零退出且输出 [警告] 行; CTest 按目录 glob 自动注册 (`physics_negative_<夹具名>`), **新增夹具后重新跑一次 CMake 配置**, 或直接用一键 QA;
- **套件防缩水**: `physics_fixture_registry` 关卡 (`tests/test_physics_fixture_registry.sh`) 断言必备清单每项"夹具 + sidecar"在位、目录内一一对应、正例非空 —— 误删夹具会让关卡变红, 而不是让用例静默消失;
- **账本门禁**: `python3 tools/physical_failure_registry.py check` 校验账本完整性 (编码合法/模型在库/已下沉项的夹具与 sidecar 在位且已进必备清单), 报告待下沉欠账与季度复盘信号; 加 `--fail-on-pending-sink` 可升级为硬门禁 (存在 L1 必下沉而未下沉项即退出码 1);
- **执行入口**:

```bash
bash tests/run_full_qa.sh                                          # 一键 QA (含关卡 3/12/13)
ctest --test-dir build -R "physics_fixture_registry|physics_negative_" --output-on-failure
python3 tools/physical_failure_registry.py check                   # 账本完整性 (秒级, 无需构建)
```

## 6. 季度复盘 (不可规则化编码的出口)

[BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) 第 4 节维护要求: 每季度复盘一次分类表, 出现 **≥ 3 次**的"仅 L3"失效模式 (F05/F09/F10/F12), 立项评估能否规则化下沉到 L1/L2。账本让这件事不再靠翻工单:

```bash
python3 tools/physical_failure_registry.py check    # "季度复盘立项信号"段自动列出 >= 3 次的编码
python3 tools/physical_failure_registry.py list --code F05 --json   # 逐条取证 (照片/模型/步骤)
```

复盘产出三选一并记档: (a) 立项规则化 → 回到第 ③ 步下沉; (b) 产品端缓解 (如品牌兼容提示) → 在对应文档登记; (c) 维持"仅 L3" → 写明理由, 计数清零重新累计。

## 7. 纪律红线

1. **失效必入账**: 没有登记的失效等于没发生 —— 工作单"问题记录"栏有 F 编码而账本没有对应条目, 视为流程违规;
2. **下沉不许假**: `mark-sunk` 的夹具必须真实存在、带 sidecar、进必备清单, 且本地验证确实被拒; 把"打算做"标成"已下沉"比不下沉更危险;
3. **夹具只进不退**: 负例套件不允许缩水, 删除任何必备夹具须有书面评审理由 (与 `test_physics_fixture_registry.sh` 头注约定一致);
4. **放宽参数须过负例全绿**: 任何 L1/L2 参数放宽 (含儿童实测证据驱动的放宽, 见 BUILD_VERIFICATION.md 3.6.4 节) 必须保证全部负例夹具仍被拒绝;
5. **照片可后补, 编码不可后补**: 现场没定编码, 事后凭记忆补编码容易失真 —— 桌边就用 `codes` 子命令速查定码。

## 8. 与其他文档的关系

| 文档 | 关系 |
| --- | --- |
| [BUILD_VERIFICATION.md](BUILD_VERIFICATION.md) | 第 4 节失效分类学 (F01~F12 定义与"应拦截规则"映射) 是本闭环的分类依据; 本手册是其"回填为回归用例"纪律的执行载体 |
| [reports/PHYSICAL_REVIEW_USER_GUIDE.md](reports/PHYSICAL_REVIEW_USER_GUIDE.md) | 抽样实搭的备料/工时/照片归档约定 (第 ① 步的上手指南) |
| [PHYSICAL_REBUILD_CHECKLIST.md](PHYSICAL_REBUILD_CHECKLIST.md) | 实搭判定动作与记录模板 (失效编码的现场来源) |
| [PHYSICS_RULES.md](PHYSICS_RULES.md) | L1 规则精确定义与第 8 节规划规则 (下沉时"应拦截规则"的落点) |
| [STRICT_PHYSICS_AUDIT.md](STRICT_PHYSICS_AUDIT.md) | 档位参数收紧/豁免的政策依据 (校准分支二) |
| [TESTING.md](TESTING.md) | 质量金字塔全景与一键 QA 关卡顺序 (第 ④ 步的执行环境) |

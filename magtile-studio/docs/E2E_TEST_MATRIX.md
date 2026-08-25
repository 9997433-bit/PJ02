# V1 上架必测: 核心用户路径 E2E 矩阵

本矩阵是 **V1 商用上架前的验收清单**: 以真实用户路径 (而非代码模块)
为单位, 列出上架前必须逐条走通的端到端场景, 标注每条路径的平台、
优先级与自动化程度。与 [TESTING.md](TESTING.md) 的关系:

- TESTING.md 管**代码与内容质量关卡** (物理/教程/体量/唯一性, 按提交全量跑);
- 本矩阵管**用户视角的完整路径** (安装 → 浏览 → 搭建 → 庆祝 → 付费边界),
  是上架签核的最后一道对账单。

## 0. 字段口径

| 字段 | 取值 | 含义 |
| --- | --- | --- |
| 优先级 | **P0** | 上架阻断: 任一 P0 路径不通, 不允许出包上架 |
|  | **P1** | 重要: 允许带已记录的已知问题上架, 但必须在签核记录中留痕 |
| 自动化 | **Auto** | 有自动化载体, 随 `tools/run_e2e_smoke.sh` / CTest / CI 可重复跑 |
|  | **Auto(部分)** | 数据链路/状态机已自动化, 视觉与真机体验仍需人工补 |
|  | **Manual** | 人工验收, 按「人工要点」列的步骤逐条打钩 |
| 平台 | Qt 桌面 | `magtile_studio_qt` (Windows / macOS / Linux 商用桌面壳) |
|  | GL 桌面 | `magtile_app library --dev-gui` (GLFW+ImGui 壳, 已退役为内容工具/内部评审, 非用户入口) |
|  | CLI | `magtile_app` 终端命令 (质检与无显示环境兜底) |
|  | Android | `platforms/android` APK (真机验收) |
|  | Win 包 | Windows 安装包 (打包产物, 见 `scripts/package_windows.md`) |

自动子集一键跑: `tools/run_e2e_smoke.sh` (见第 2 节); 全量软件 QA:
`tests/run_full_qa.sh`; 发布门禁: `tools/run_release_gate.sh --full`。

## 1. 路径矩阵

| 编号 | 用户路径 | 平台 | 优先级 | 自动化 | 自动化载体 / 人工要点 |
| --- | --- | --- | --- | --- | --- |
| E2E-01 | **安装启动 (桌面)**: 冷启动 → 首页可交互, 目录与模型库加载成功, 无崩溃无错误弹窗 | Qt 桌面 | P0 | Auto | `qt_gui_smoke` 默认启动项 (offscreen 无头, QML 加载失败即非零); `run_e2e_smoke.sh` E2E-01a 另跑 CLI `catalog` 冒烟 (13 种片型齐全)。真窗口首启人工补看一遍 |
| E2E-02 | **安装启动 (Windows 包)**: 安装器安装 → 开始菜单启动 → 数据/存档路径正确 → 卸载干净 | Win 包 | P0 | Manual | 按 `scripts/package_windows.md` 出包后走查; starter 子集包另验只含 30 免费模型 |
| E2E-03 | **安装启动 (Android)**: `adb install` → 首启解包数据资产 → 状态栏「N/N 个模型 · 13 种磁力片形状」→ 缩略图卡片列表流畅滚动 | Android | P0 | Auto(部分) | CI `android.yml` assemble-debug 校验 APK 内容 (原生库/数据/缩略图); `run_e2e_smoke.sh` E2E-14a 本地 JNI 符号断言。真机首启与滚动流畅度人工 |
| E2E-04 | **模型库筛选**: 难度 / 主题 / 只看免费 / 只用核心 9 片 / 我能搭的 五维筛选, 分龄三档收放 (被收起维度清零, 不悄悄过滤) | Qt 桌面 | P0 | Auto(部分) | `qt_backend_bridges` (LibraryFilterModel 筛选口径单测); `qt_ui_paths_smoke` / `run_e2e_smoke.sh` E2E-04a: 页面级筛选切换自动驾驶 (`--smoke-library-filters`, 免费筛选数量对账 + 主题筛选 + 难度 1~5 分片求和 = 全库 + 清除复位, 与 FilterChip 同一条属性写路径)。人工: 切三档年龄段观察筛选栏收放与卡片密度 (UI_UX_SPEC §2/§5) |
| E2E-05 | **详情页 3D 预览**: 卡片 → 详情 → 3D 成品预览旋转/缩放 → 「开始搭建」进教程 | Qt 桌面 | P0 | Manual | offscreen 平台无 GL, 视口画面自动化不覆盖; 有显示/xvfb 环境可用 `--smoke-open-model <id> --smoke-screenshot <png>` 抓屏辅助核对非纯色 |
| E2E-06 | **教程步进 (核心屏 ★)**: 上一步/下一步 → 每步高亮与片数对账 → 断点续搭 → 进度落盘 → 走完全程 | Qt 桌面 / CLI | P0 | Auto(部分) | `run_e2e_smoke.sh` E2E-06a: CLI 打开免费模型教程全程步进, 断言「教程结束」且放置片数 = `total_pieces`; CTest `tutorial_*` 全库逐模型实跑。3D 视口交互 (拖转/缩放/键盘翻步) 人工 |
| E2E-07 | **完成庆祝**: 末步「完成 🎉」→ 庆祝页 (彩带/星星/成就卡/再搭一个推荐) → 存档记录完成 + 首搭成就解锁 | Qt 桌面 | P0 | Auto | `qt_gui_smoke` 的 `--smoke-complete-model` 项 (完成链路 + SQLite `completed_at` 断言); 推荐桥有 `qt_backend_bridges` 单测。庆祝动效与减少动效降级人工看一眼 |
| E2E-08 | **家长门**: 入口出题 (中文数字乘法) → 答对开 15 分钟会话 → 答错温和提示 → 3 次答错 60s 冷却 → 会话内免重复验证 | Qt 桌面 / GL / Android | P0 | Auto(部分) | 三端共享 `core::ParentGate` 状态机, `parent_gate` CTest 单测全覆盖; `qt_gui_smoke` 的 `--parent-gate` 深链与 `--smoke-parent-flow` 过门流。Android 中文大写数字软键盘真机人工 |
| E2E-09 | **库存录入 → 我能搭的**: 录入 (步进器/直接输入) → 保存落盘 → 「我能搭的」筛选联动 → 详情缺片清单 | Qt 桌面 / GL / CLI | P0 | Auto | `inventory_cli` (set/show/match 全流程 + 边界); `inventory_gui_smoke` (GL 图形录入与 CLI 共库); `qt_backend_bridges` (InventoryBackend); `qt_ui_paths_smoke` / `run_e2e_smoke.sh` E2E-09a: Qt 库存页深链自动驾驶 (`--smoke-open-inventory`, 步进器 +3 → 「保存库存」落盘 → SQLite 直读全片型入表且总数对账) |
| E2E-10 | **订阅门**: 订阅入口 (首页温和入口/家长中心/设置) 必过家长门 → 门后订阅页 → 儿童侧无价格与催购 | Qt 桌面 | P0 | Auto(部分) | `qt_gui_smoke` 的 `--smoke-parent-flow` 项 (门 → 家长中心 → 设置 → 订阅逐页实例化)。UI_UX_SPEC §11 文案红线 (无倒计时/无焦虑话术) 人工核对 |
| E2E-11 | **免费锁**: 「只看免费」恰 30 个; 免费模型直达教程; 非免费点击给温和订阅提示、不开教程 | Qt / GL / CLI / Android | P0 | Auto(部分) | `tools/verify_free_tier.py` (免费标签恰 30 + 全 core-9 + starter 清单对齐); `run_e2e_smoke.sh` E2E-11b: CLI `library --free-only` 与清单数量对账; `qt_ui_paths_smoke` / `run_e2e_smoke.sh` E2E-11c: Qt 非免费点击路径自动驾驶 (`--smoke-locked-model`, 详情页 locked 上锁 → 「请家长来解锁」落家长门不开教程 → SQLite 直读断言零进度写档)。非免费模型点击路径 (GL/CLI/Android 三端) 人工 |
| E2E-12 | **进度页 / 成就墙**: 「我的进度」儿童可达无门 → 统计三格 / 进行中 / 已完成 / 收藏 → 成就墙徽章 (未解锁灰剪影 + 达成条件) | Qt 桌面 | P1 | Auto | `run_e2e_smoke.sh` E2E-12a: 先 `--smoke-complete-model` 造非空存档, 再 `--smoke-open-progress` 深链实例化进度页 (统计/已完成列表/成就墙数据源), QML 运行时错误一票否决; `qt_ui_paths_smoke` / `run_e2e_smoke.sh` E2E-12b: 有数据断言 (`--smoke-progress-data`, 已完成列表与统计对账 + 成就列表非空 + 至少一枚徽章点亮 + 成就墙全览复核) |
| E2E-13 | **设置**: 字号三档 / 减少动效 / 年龄段 / 朗读开关, 改动即时生效且 CLI/GL/Qt 三端共库 | Qt / GL / CLI | P1 | Auto(部分) | `age_tts` / `settings_cli_smoke` / `settings_tts_cli` / `qt_backend_bridges` 共库契约。字号与动效视觉人工 |
| E2E-14 | **Android 列表 + 详情**: 分龄筛选栏 → 卡片详情弹窗 (简介/套装/库存对照/缺片清单) → 物理校验摘要 | Android | P0 | Auto(部分) | `run_e2e_smoke.sh` E2E-14a: NDK 交叉编译 + JNI 符号断言 (符号清单运行时解析自 CI `android.yml` ndk-so, 口径自动同步); assemble-debug APK 内容校验在 CI。真机按 `platforms/android/README.md` 第一节走查 |
| E2E-15 | **Android 教程步进**: 免费模型「开始搭建」→ 分步教程 (步骤列表/上一步/下一步) → 断点续搭 → 完成 + 首搭成就 | Android | P0 | Manual | 真机走查; 进度写档与桌面同一 SQLite schema, 可顺带抽查跨端口径 (完成后进度页立即可见) |
| E2E-16 | **TTS 朗读**: 4-6 岁启蒙自动朗读 / 🔊 手动朗读 / 总开关关闭全端静音降级 | Qt / GL | P1 | Auto(部分) | `age_tts` (映射与开关契约) + `settings_tts_cli`。真实发声与音色人工 (无声环境自动静音降级不算失败) |
| E2E-17 | **跨端存档互通**: CLI 完成模型 → Qt 进度页显示已完成; Qt 录库存 → CLI `inventory match` 一致; 近期新增设置键 (`age_mode` / `subscription_active` / `onboarding_age_done` / 成就解锁) 四端同一 settings 键契约 | Qt / GL / CLI / Android | P1 | Auto(部分) | CTest `cross_platform_progress` (样例存档: 年龄段/订阅/引导标记/完成记录/成就解锁, settings 键名编译期 static_assert + 落盘键值双锁, 第二连接按 Qt 读取口径回读) + `cross_platform_progress_cli` (CLI 真实二进制从同一存档回读完成/成就/年龄段); `qt_backend_bridges` 共库契约 + `progress_roundtrip` / `inventory_cli`; `run_e2e_smoke.sh` E2E-17a 轻量键契约断言。Android 真机同库读写人工抽查 (随 E2E-15 走查) |
| E2E-18 | **GL 桌面壳 (内部工具)**: `magtile_app library --dev-gui` 模型库 → 教程 → 返回模型库, 画面非纯色 | GL 桌面 | P1 | Auto(部分) | `tests/test_gl_smoke.sh` (xvfb 真渲染 + 截图校验 + `--gui` 别名回归, CI 常跑)。交互走查人工 |
| E2E-19 | **触屏手势**: 教程视口与详情预览 单指旋转 / 双指捏合缩放 / 双指平移, 与鼠标并存 | Qt 触屏设备 | P1 | Manual | offscreen 平台不投递 TouchUpdate, 自动化不覆盖; 真机触屏或 xvfb+uinput 按 QT_UI_PLAN QT-3 验证方案走查 |
| E2E-20 | **离线可用**: 断网环境下 E2E-01/03 主链路全功能可用 (零联网承诺) | 全平台 | P1 | Manual | 断网重走安装启动与教程主链路; 承诺依据 SECURITY_AND_PRIVACY.md |

## 2. 自动子集一键跑 (`tools/run_e2e_smoke.sh`)

把矩阵中已自动化的关键路径串成一条命令, 供上架前快速回归与 CI 消费
(CI 载体: `.github/workflows/qa.yml` 的 `e2e-strict` job 在**每次 push**
以 `--strict` 档执行, 见第 3 节):

```bash
tools/run_e2e_smoke.sh                 # 默认: CLI + 免费层 + Qt 无头五连跑 + Android 符号 (环境允许时)
tools/run_e2e_smoke.sh --skip-android  # 无 NDK 环境跳过 Android 项
tools/run_e2e_smoke.sh --strict        # 验收档: 任何 SKIP 也按失败处理 (上架签核用)
tools/run_e2e_smoke.sh --help          # 完整用法
```

覆盖的自动项 (对应矩阵编号):

| 冒烟项 | 矩阵编号 | 内容 |
| --- | --- | --- |
| CLI 启动冒烟 | E2E-01a | `magtile_app catalog` 目录加载, 13 种片型齐全 |
| 免费层清单对齐 | E2E-11a | `tools/verify_free_tier.py`: 免费标签恰 30 + 全 core-9 + starter 清单一致 |
| CLI 免费筛选对账 | E2E-11b | `library --free-only` 数量与 starter 清单一致, 目录元数据对账通过 |
| CLI 免费模型教程步进 | E2E-06a | 免费模型教程全程步进, 放置片数与 `total_pieces` 对账 |
| 跨端存档键契约 | E2E-17a | CLI 写 `age_mode` → python sqlite 直读键名/编码契约 + `settings show` 回读; 构建目录有 `magtile_cross_platform_test` 时另跑全量跨端互通断言 |
| Qt 无头冒烟 | E2E-01/07/08/10 | `tests/test_qt_smoke.sh` 全部路径: 首页 / 家长门深链 / 过门流 (含订阅页) / 完成庆祝 + 存档断言等 (以该脚本为准), 外加 QML 运行时错误一票否决 |
| Qt 进度页深链 | E2E-12a | 先 `--smoke-complete-model` 造非空存档, 再 `--smoke-open-progress` 实例化进度页/成就墙数据源 |
| Qt 按钮级路径冒烟 | E2E-04a / 09a / 11c / 12b | `tests/test_qt_ui_paths_smoke.sh` (ctest: `qt_ui_paths_smoke`): 模型库筛选切换对账 / 库存页深链保存落盘 / 非免费锁走家长门 (不开教程, 零进度写档) / 进度页有数据时成就列表非空, 自动驾驶断言 + SQLite 直读 |
| Android JNI 符号断言 | E2E-14a | NDK 交叉编译 `libmagtile_core.so` + JNI 符号齐全 (符号清单运行时解析自 CI `android.yml`, 与流水线口径自动同步); 无 NDK 环境自动 SKIP |

退出码: **0** = 全部执行项通过 (SKIP 不算失败, `--strict` 下算);
**1** = 存在失败项; **2** = 环境/参数不满足。结尾输出 PASS/FAIL/SKIP
分项摘要与耗时, 失败项保留分项日志目录。

## 3. 上架签核规则

1. **自动侧**: `tools/run_e2e_smoke.sh --strict` 全绿 (Qt 与 Android
   项不允许 SKIP) **且** `tools/run_release_gate.sh --full
   --fail-on-pending` 全绿 (软件/内容/实物三层门禁, 见 TESTING.md 第 5 节);
   其中 strict 档由 CI 常态兑现 —— `.github/workflows/qa.yml` 的
   `e2e-strict` job 在**每次 push** 于装齐 Qt6 + 固定版本 NDK 的 runner
   上执行 `tools/run_e2e_smoke.sh --strict`, 9 个冒烟项全部真实执行,
   任何 FAIL 或 SKIP 都红灯**阻断 PR 合入**; 签核时只需确认目标提交的
   `e2e-strict` 绿灯 (环境缺失导致的 SKIP 不可能混入), 发布门禁
   (release-gate.yml) 仍按 TESTING.md 第 5 节手动触发补齐;
2. **人工侧**: 本矩阵全部 P0 的 Manual / Auto(部分) 人工要点逐条打钩,
   记录到发布检查单 (含执行人 / 日期 / 设备型号); Android 真机至少覆盖
   一台 arm64 中端机 (API 26+);
3. **P1 例外**: P1 路径允许带已知问题上架, 但必须在签核记录中写明
   问题与影响面; P0 无例外。

## 4. 维护约定

- 新增用户可见路径 (新页面 / 新付费边界 / 新平台) 时**先在本矩阵登记**,
  再决定自动化载体; 能进 `run_e2e_smoke.sh` 或 CTest 的尽量自动化,
  Manual 是最后选择;
- 自动化载体改名/增删时同步更新本矩阵「自动化载体」列与
  [TESTING.md](TESTING.md) 对应小节, 两处引用不允许漂移;
- 本矩阵只登记路径与口径, **不承载模型内容质量标准** —— 那是
  TESTING.md 第 7 节「内容入库标准」的职责。

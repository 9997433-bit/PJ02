# Windows CI 首跑预检清单 (Pre-dispatch Preflight)

- 生成时间: 2026-08-25 (UTC)
- 基线提交: `2b2c4ff` (`cursor/magtile-studio-foundation-a95b`, 250 模型
  基线), 已含 workflow 加固 (标签校验步 env 间接注入, 见 §2 A-5)
- 定位: `windows-release` 流水线**触发之前**的把关清单。触发方法、
  预期产物、失败排查与签核登记见
  [`../../scripts/package_windows.md`](../../scripts/package_windows.md) §8
  (本文 = 触发前; §8.1–§8.5 = 触发中与触发后)。
- 对应 V1 清单条目: D2 (Windows 安装包在真实 runner 出包, 流水线转正)。

## 1. 本地可验部分 —— 本基线已全绿 (工程侧完成)

以下各项已在本基线实际执行, 结果如实登记; 重跑命令附后, 换基线
触发前建议重跑一遍 (§3)。

| # | 验证项 | 工具 / 环境 | 结果 |
| --- | --- | --- | --- |
| 1 | actionlint 全 workflow 静态检查 (4 个 workflow, 含 `windows-release.yml` 加固后版本) | actionlint 1.7.7 | **零告警** |
| 2 | `windows-release.yml` YAML 语法解析 | python3 + PyYAML | **通过** |
| 3 | `scripts/smoke_qt_linux_pack.sh` shellcheck 静态检查 | shellcheck 0.9.0 (warning 级) | **零告警** (info 级仅 SC2015, 系 `ok`/`bad` 计数器的刻意写法, 安全) |
| 4 | 「提取 CMake 工程版本号」步逻辑复刻: 对真实 CMakeCache.txt 提取 | pwsh 7.4.6 (与 runner 同大版本) | **通过** (提取到 `0.1.0`) |
| 5 | 「校验标签与工程版本号一致」步 (加固后) 三用例: 一致通过 / 不一致检出 / 含单引号注入载荷的恶意标签名仅作数据比较不执行 | pwsh 7.4.6 | **3/3 通过** |
| 6 | `scripts/smoke_qt_linux_pack.sh` 全量替身冒烟 (并存 TGZ / NSIS makensis 编译 / Qt-only / starter 30 子集 / 解包 offscreen 启动 / LGPL 合规) | Ubuntu, CMake 3.28.3, Qt 6.4.2, makensis 3.09, Python 3.12.3 | **41 项通过, 0 项失败** (3 项 WARN 为发布前追加项: Qt 精确版本注记 + LGPL/GPL 许可全文, 冒烟档不阻塞, 见手册第十一节待办) |
| 7 | starter 清单漂移守卫 `tools/verify_free_tier.py` | python3 | **通过** (扫描 250 模型, 免费标签 30 = starter 清单 30, 全 core-9, 零差异) |

本地验证的**边界** (首跑仍可能暴露、无法在 Linux 侧预验的项):
MSVC 平台编译差异、Windows runner 上 choco/NSIS 实装、FetchContent
在 runner 的出网 —— 均已备排查表 (§8.3), 属首跑预期风险而非缺口。

## 2. 用户触发前逐项核对 (pre-dispatch checklist)

### A. 平台与仓库前提

- [ ] **A-1 workflow 已在默认分支**: `workflow_dispatch` 入口只有该
      workflow 文件已合入仓库默认分支时才可见可用 (GitHub 平台限制)。
      未合入前的替代路径 (对本分支打 `v<版本>` 标签触发, 试跑后删
      草稿与标签) 见 §8.1 路径 A 前提说明。
- [ ] **A-2 Actions 已启用且 runner 可用**: 仓库 Settings → Actions
      未禁用; 私有仓库确认 Actions 分钟额度充足 (`windows-latest`
      计费倍率 2x, 首跑预计 15~40 分钟)。
- [ ] **A-3 workflow 写权限** (仅标签路径需要): 标签触发建 Release
      草稿需 `contents: write`; workflow 已自声明, 若组织策略把默认
      权限收成只读且禁止声明提权, 在 Settings → Actions → General
      放开 (排查条目见 §8.3 表 403 行)。`workflow_dispatch` 试跑
      不建 Release, 不依赖此项。
- [ ] **A-4 runner 出网**: 配置期 FetchContent 拉 GLFW/Dear ImGui,
      打包前 choco 装 NSIS, 均需出网; 自托管 runner 或出网白名单
      环境须放行 github.com / chocolatey.org。托管 runner 默认满足。
- [ ] **A-5 分支含加固后的 workflow**: 待触发分支上的
      `windows-release.yml` 已含「校验标签」步 env 间接注入加固
      (标签名不再 `${{ }}` 内插进脚本体, 防 pwsh 脚本注入)。

### B. 仓库状态

- [ ] **B-1 版本号确认**: `magtile-studio/CMakeLists.txt` 的
      `project(MagTileStudio VERSION x.y.z)` 是预期版本 (本基线
      `0.1.0`); 走标签路径时标签 `v<版本>` 与其逐字符一致, 不一致
      流水线在「校验标签」步按设计失败。
- [ ] **B-2 starter 清单未漂移**: `python3 tools/verify_free_tier.py`
      退出码 0 (免费标签 = starter 清单 = 30, 全 core-9)。
- [ ] **B-3 Linux 替身冒烟全绿**: `bash scripts/smoke_qt_linux_pack.sh`
      0 失败 (§3 重跑命令); 换过基线后必跑。
- [ ] **B-4 actionlint 零告警**: 改过任何 workflow 后重跑 (§3)。

### C. 触发参数与场次纪律

- [ ] **C-1 场次顺序**: 首跑 `model_set=full` 一场 → 全绿后
      `model_set=starter` 一场 (验收清单要求含 starter 档;
      两场全绿即 D2 转正口径, §8.4)。
- [ ] **C-2 产物勿混放**: starter 档产物**文件名与 full 档相同**
      (CPack 包名不带档位后缀), 两场下载物分目录存放; 甄别看包内
      `data/models/` 条数 (starter 恰 30, full 与
      `model_catalog.json` 登记条数一致, 本基线 250)。
- [ ] **C-3 逐场登记**: 每场按 §8.4 签核表登记 run 链接、提交、
      SHA256 与结果; 两场全绿后按 §8.5 一次性翻状态
      (D2 ✅ / README 打钩 / 去「草案」注记)。

## 3. 预检命令速查 (换基线后重跑)

在 `magtile-studio/` 目录执行 (actionlint 在仓库根执行):

```bash
# 1) workflow 静态检查 (仓库根; 未装 actionlint 时先装:
#    https://github.com/rhysd/actionlint/releases)
(cd .. && actionlint)

# 2) 冒烟脚本静态检查
shellcheck -S warning scripts/smoke_qt_linux_pack.sh

# 3) Linux 替身冒烟全量 (需系统 Qt >= 6.4 + makensis; 约数分钟)
bash scripts/smoke_qt_linux_pack.sh

# 4) starter 清单漂移守卫
python3 tools/verify_free_tier.py
```

## 4. 预检通过后的动作序列

1. 按 §8.1 路径 A 触发 `workflow_dispatch` (网页或 `gh workflow run
   windows-release --ref <分支> -f model_set=full`)。
2. 按 §8.2 核对产物 (exe + zip 齐 / 版本号 / 模型条数 / SHA256)。
3. 失败按 §8.3 CI 专属排查表处置 (通用打包故障见手册第十节)。
4. 按 §8.4 登记签核; 两场全绿后按 §8.5 收尾翻状态。

## 相关文档

- [`../../scripts/package_windows.md`](../../scripts/package_windows.md)
  §8 — 触发 / 预期产物 / 排查 / 签核 (本文的下游)。
- [`../../platforms/windows/README.md`](../../platforms/windows/README.md)
  — Windows 端验收清单 (D2 转正打钩位)。
- [`../V1_LAUNCH_CHECKLIST.md`](../V1_LAUNCH_CHECKLIST.md) D2 行 —
  发布清单挂点。

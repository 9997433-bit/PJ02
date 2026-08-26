# Windows 构建与打包指南

本文是 MagTile Studio Windows 端从源码到安装包的完整操作手册。
打包资产位于 `platforms/windows/packaging/`, 自动化流水线位于
仓库根 `.github/workflows/windows-release.yml` (workflow 必须放在
仓库根才会被 GitHub 识别, 本工程位于仓库的 `magtile-studio/` 子目录)。

> 状态: **IN_PROGRESS**。CPack/NSIS + WiX 配置、模型子集打包与许可
> 文件安装均已就位; 安装规则与文件清单已在 Linux CI 环境冒烟通过
> (TGZ 全量/子集两档, 见第九节), 但**尚未在真实 Windows 机器出过
> exe/msi**。CI 流水线首跑的触发/预期产物/排查/签核见第八节;
> 首次实机打包按第十节排查表逐项核对,
> 验收项见 `platforms/windows/README.md`。

## 一、前置条件

| 组件 | 要求 | 说明 |
| --- | --- | --- |
| Visual Studio 2022 | 工作负载"使用 C++ 的桌面开发" | MSVC 19.3x, 支持 C++20 |
| CMake | ≥ 3.20 | VS 自带的即可; `cpack` 随 CMake 一起安装 |
| NSIS | ≥ 3.x | 产出 `.exe` 安装器; [nsis.sourceforge.io](https://nsis.sourceforge.io/) 或 `winget install NSIS.NSIS`; GitHub `windows-latest` (Windows Server 2025 镜像) **已移除预装**, CI 流水线打包前经 Chocolatey 自装 |
| Python | 3.8+ (仅子集打包需要) | `-DMAGTILE_PACKAGE_MODEL_SET=starter/清单` 时运行 `tools/make_data_subset.py`; VS 自带的 Python 或 python.org 均可 |
| WiX Toolset | v4 (可选) | 仅走 MSI 路径时需要: `dotnet tool install --global wix` |
| Qt | ≥ 6.4 (可选) | 仅 `-DMAGTILE_BUILD_QT=ON` 打包 Qt 商用界面时需要 (MSVC 2022 64-bit 套件); Qt ≥ 6.5 打包时可自动部署运行库 |
| 网络 | 首次配置需要 | FetchContent 拉取 GLFW 3.4 / Dear ImGui |

## 二、打包内容 (安装布局)

NSIS 安装器 / 便携 ZIP / MSI 三种产物布局一致:

```
MagTile Studio\
├── magtile_app.exe        主程序 (CLI + GUI 一体)
├── magtile_studio_qt.exe  Qt 商用界面 (仅 -DMAGTILE_BUILD_QT=ON 构建时;
│                          含 Qt 运行库 DLL / QML 模块, 见第五节)
├── data\                  磁力片形状目录 + 模型库 (运行必需)
│   ├── tile_catalog.json
│   ├── model_catalog.json   (子集打包时为过滤后的目录)
│   ├── models\*.json
│   └── thumbnails\*.png
├── licenses\
│   ├── License.rtf                EULA (占位文本, 发布前替换法务审定版)
│   └── THIRD_PARTY_NOTICES.md     第三方组件许可声明
├── README.md
└── vcruntime140*.dll      MSVC CRT 运行库 (InstallRequiredSystemLibraries)
```

`data/` 的范围由配置项 `MAGTILE_PACKAGE_MODEL_SET` 决定:

| 取值 | 内容 |
| --- | --- |
| `full` (默认) | 完整模型库 (当前 250 模型 + 全部缩略图, 约 14 MiB) |
| `starter` | 免费层 30 模型 (与模型 `免费` 标签集合一致, 全 core-9; 对齐决议见 `docs/FREE_TIER_MANIFEST.md`), 清单 `platforms/windows/packaging/starter_models.txt` |
| 清单文件路径 | 自定义子集 (每行一个模型 id, 支持 `#` 注释) |

子集模式在安装/打包阶段自动调用 `tools/make_data_subset.py`:
拷贝清单模型 + 对应缩略图 + `tile_catalog.json`, 并**同步过滤**
`model_catalog.json` —— 运行时加载器对"目录登记了但文件缺失"的条目
直接报错, 因此绝不能只删模型不过滤目录, 脚本保证两者一致。
清单拼写错误在 CMake 配置期即失败, 不会拖到打包才发现。

## 三、构建与测试

在 "x64 Native Tools Command Prompt" 或普通终端执行 (中文输出乱码时
先 `chcp 65001`):

```bat
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64
cmake --build build-win --config Release --parallel
ctest --test-dir build-win -C Release --output-on-failure
```

打模型子集包时在配置命令追加 `-DMAGTILE_PACKAGE_MODEL_SET=starter`
(或清单路径); 该开关只影响打包内容, 构建与测试仍针对完整仓库数据。

要点:

- 全部源码与数据均为 UTF-8, 根 CMakeLists 已对 MSVC 强制 `/utf-8`。
- GL 渲染后端在 Windows 上经 GLFW 使用 WGL, 无额外系统依赖;
  GLFW 静态链接进 exe, 分发物不含第三方 DLL。
- `library_gui_smoke` / `inventory_gui_smoke` 需要可创建 OpenGL 窗口
  的显示环境, 无显示的机器 (含多数 CI) 用
  `ctest ... -E "(library|inventory)_gui_smoke"` 跳过。
- 打包前必须先完成 Release 构建 —— `cpack -C Release` 只做安装与
  打包, 不会替你编译。

## 四、CPack 打包 (首选路径: NSIS 安装器 + 便携 ZIP)

版本号**唯一来源**是根 `CMakeLists.txt` 的
`project(MagTileStudio VERSION x.y.z)`, CPack 自动读取, 任何地方都
不要手抄版本号。

```bat
cd build-win
cpack -G "NSIS;ZIP" -C Release
```

产物 (在 `build-win\` 下, `<版本>` 即 project VERSION):

| 文件 | 内容 |
| --- | --- |
| `MagTileStudio-<版本>-win64.exe` | NSIS 安装器: 装入 `%ProgramFiles%\MagTile Studio\`, 创建开始菜单快捷方式 (直达 `library --dev-gui` GL 开发者模型库; Qt 构建时另有 "MagTile Studio (Qt)" 快捷方式, 商用主入口), 带卸载器 |
| `MagTileStudio-<版本>-win64.zip` | 便携版: 解压即用, 免安装 |

打包配置见 `platforms/windows/packaging/CPackWindows.cmake`;
安装器许可页文本为 `platforms/windows/packaging/License.rtf`
(**当前为占位文本, 正式发布前必须替换为法务审定版本**)。

打包后快速自检 (便携 ZIP 解压目录内):

```bat
magtile_app.exe library --db %TEMP%\magtile_check.db
magtile_app.exe validate data\models\castle_foundation_01.json --data-dir data
```

`library` 会顺带做目录对账 —— 子集包若目录与模型文件不一致会当场报错。

## 五、Qt 商用界面打包 (可选, -DMAGTILE_BUILD_QT=ON)

> Qt 界面打包的完整操作手册 (windeployqt/macdeployqt 步骤、Qt-only
> 包形态 `-DMAGTILE_PACKAGE_QT_ONLY=ON`、LGPL 合规清单、Linux 冒烟)
> 见 `scripts/package_qt_desktop.md`; 本节只保留 Windows 侧摘要。

Qt 界面 (`magtile_studio_qt.exe`, QML) 默认**不参与**构建与打包;
需要随包分发时:

```bat
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64 ^
    -DMAGTILE_BUILD_QT=ON ^
    -DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64
cmake --build build-win --config Release --parallel
cd build-win
cpack -G "NSIS;ZIP" -C Release
```

Qt 运行库 (Core/Gui/Qml/Quick/QuickControls2 DLL + QML 模块) 的部署:

- **Qt ≥ 6.5**: 安装规则 (`apps/desktop_qt/CMakeLists.txt` 尾部) 使用
  官方部署 API (`qt_generate_deploy_qml_app_script`), `cpack` 时自动
  把 Qt 运行库收进安装布局, 无需手工干预。
- **Qt 6.4**: 部署 API 尚为技术预览, 未启用 —— cpack 产物只含
  `magtile_studio_qt.exe` 本体, 需手动对安装目录补运行库后重打:

  ```bat
  C:\Qt\6.4.x\msvc2022_64\bin\windeployqt.exe ^
      --qmldir apps\desktop_qt\qml ^
      <解压后的安装目录>\magtile_studio_qt.exe
  ```

- Qt 采用 LGPLv3 动态链接分发, 许可合规说明见随包
  `licenses/THIRD_PARTY_NOTICES.md`, 逐项核对清单见
  `scripts/package_qt_desktop.md` 第八节; 商用闭源发布前由法务确认
  走 LGPL 合规或购买 Qt 商业许可。
- 只发 Qt 界面的 **Qt-only 包**: 追加 `-DMAGTILE_PACKAGE_QT_ONLY=ON`
  (省略 magtile_app, 包名加 `-qt` 后缀, 详见
  `scripts/package_qt_desktop.md` 第六节); WiX 方式 B 不支持该形态。
- MSI 路径 (第六节) 暂不收割 Qt 运行库, Qt 版分发走 NSIS/ZIP。
- **MSIX 商店包 (Microsoft Store 渠道)**: 商店订阅计费仅 MSIX 商店包
  身份下可用, 商店出包配置须加 `-DMAGTILE_BILLING_WINDOWS_STORE=ON`
  (根 CMakeLists 选项, 默认 OFF, 本地开发档走假计费); MSIX 装配本身
  待补 (见 `scripts/package_qt_desktop.md` 商店渠道待办)。Partner
  Center 商品配置、测试安装与购买/恢复/断网宽限期沙盒验收步骤见
  [`../docs/WINDOWS_STORE_BILLING_SANDBOX_QA.md`](../docs/WINDOWS_STORE_BILLING_SANDBOX_QA.md)
  (V1 清单 §2 B3 Windows 侧)。

不装 Qt / 不加开关时, 上述内容完全不影响 CLI/GL 版打包。

## 六、WiX / MSI 路径 (企业分发, 可选)

面向组策略部署与静默安装 (`msiexec /qn`) 场景。两种方式:

**方式 A — CPack WIX 生成器** (需已安装 WiX):

```bat
cd build-win
cpack -G WIX -C Release
```

**方式 B — 独立 wix build** (使用 `platforms/windows/packaging/Product.wxs`):

```bat
cmake --build build-win --config Release
wix build platforms\windows\packaging\Product.wxs ^
    -d Version=0.1.0 ^
    -d BuildDir=build-win\Release ^
    -d DataDir=data ^
    -d LicensesDir=platforms\windows\packaging ^
    -o build-win\MagTileStudio-0.1.0-win64.msi
```

方式 B 打**模型子集** MSI 时, 先手工装配数据目录再指过去:

```bat
python tools\make_data_subset.py --data-dir data ^
    --manifest platforms\windows\packaging\starter_models.txt ^
    --out-dir build-win\package_data
wix build platforms\windows\packaging\Product.wxs ^
    -d Version=0.1.0 ^
    -d BuildDir=build-win\Release ^
    -d DataDir=build-win\package_data ^
    -d LicensesDir=platforms\windows\packaging ^
    -o build-win\MagTileStudio-0.1.0-starter-win64.msi
```

方式 B 的 `-d Version=` 必须与 project VERSION 一致 (CI 中从
CMakeCache 提取后传入, 人工操作时请核对)。两条路径共用同一个
UpgradeCode (`6FE5F9D7-79A7-4829-B13A-8C3B1517CA61`), 因此互相可
原地升级; **此 GUID 永久固定, 严禁改动**, 换掉它等于发布一个
"新产品", 已装机器将无法被升级替换。

## 七、版本号管理

1. 唯一来源: 根 `CMakeLists.txt` 中 `project(MagTileStudio VERSION x.y.z)`。
2. 升版只改这一处; CPack 文件名、NSIS/MSI 内部版本号全部自动跟随。
3. 发布标签命名 `v<版本>` (如 `v0.1.0`), 推送标签即触发
   `windows-release.yml` 流水线; 流水线会校验标签与 project VERSION
   一致, 不一致直接失败, 防止"标签说 0.2.0 包里是 0.1.0"。
4. WiX 方式 B 的 `-d Version=` 为显式传参, 见第六节。

## 八、CI 流水线: 触发、预期产物与首跑签核

仓库根 `.github/workflows/windows-release.yml`:

- 步骤: MSVC 配置构建 → 从 CMakeCache 提取版本号并校验标签 →
  `ctest` (跳过需显示环境的两个 GUI 冒烟) → 安装 NSIS
  (runner 钉 `windows-2022`; `windows-latest` 自 2026-06 起为
  VS 2026 且不再预装 NSIS, 见 actions/runner-images#14017 /
  #12677; 流水线仍经 Chocolatey 自装以防镜像变化) →
  `cpack -G "NSIS;ZIP"` → 上传构建产物;
  标签触发时另建 GitHub Release **草稿** (人工核对后再发布)。
- 验证状态: 首跑阻断项 (镜像移除预装 NSIS) 已修; 2026-08-26
  `v0.1.0` 在 `windows-latest` 上因 VS 2022 生成器找不到而失败,
  已改钉 `windows-2022`; 「校验标签」步已
  加固为 env 间接注入 (标签名不再 `${{ }}` 内插进脚本体 —— git
  标签名允许含单引号, 直接内插可被构造成 pwsh 脚本注入); 静态与
  替身验证全绿 (actionlint 零告警 + pwsh 7.4 对真实 CMakeCache
  实测版本提取与标签校验三用例 + Linux 侧 `smoke_qt_linux_pack.sh`
  41 项全绿), 但**尚未在真实 runner 上出过包** —— 触发前先逐项过
  预检清单
  [`../docs/reports/WINDOWS_CI_PREFLIGHT.md`](../docs/reports/WINDOWS_CI_PREFLIGHT.md)
  (平台前提 / 仓库状态 / 场次纪律), 再按 §8.1 触发、§8.2 核对产物、
  §8.3 排查失败、§8.4 登记签核, 两场试跑全绿后按 §8.5 一次性翻状态。

### 8.1 如何触发

> 触发前先过一遍
> [`../docs/reports/WINDOWS_CI_PREFLIGHT.md`](../docs/reports/WINDOWS_CI_PREFLIGHT.md)
> 预检清单: 平台前提 (默认分支 / Actions 额度 / 写权限 / 出网)、
> 仓库状态 (版本号 / starter 守卫 / 本地冒烟)、场次纪律。

**路径 A — `workflow_dispatch` 手动试跑 (首跑用这条, 可反复触发)**

不建 Release、不需要打标签, 只产出构建产物, 失败无副作用:

- 网页: 仓库 → Actions → `windows-release` → `Run workflow` →
  选分支与 `model_set` (full / starter) → 运行。
- 命令行 (gh CLI):

  ```bash
  gh workflow run windows-release --ref <分支> -f model_set=full
  gh run list --workflow=windows-release --limit 3   # 找到刚起的 run
  gh run watch <run-id> --exit-status                # 跟进度, 失败退非零
  ```

- 前提: `workflow_dispatch` 入口只有在该 workflow 文件**已存在于
  仓库默认分支**时才可见/可用 (GitHub 平台限制, 网页与 gh CLI 同
  受限; `--ref` 可指到含该文件的其它分支, 但列表登记以默认分支
  为准)。workflow 未合入默认分支前无法 dispatch, 替代法是走
  路径 B 对本分支提交打 `v<版本>` 标签触发 (标签事件按标签指向
  提交上的 workflow 文件执行, 不受默认分支限制), 试跑完删除
  Release 草稿与远端标签即可, 版本号不被烧掉。
- 首跑建议顺序: `model_set=full` 一场 → `model_set=starter` 一场
  (`platforms/windows/README.md` 验收清单要求含 starter 档试跑),
  逐场按 §8.4 登记。

**路径 B — 推送 `v*` 标签 (正式发布)**

1. 确认 `magtile-studio/CMakeLists.txt` 的
   `project(MagTileStudio VERSION x.y.z)` 就是要发布的版本号。
2. 打标签并推送 (标签必须与 project VERSION 逐字符一致,
   `v` 前缀 + 三段号; 不一致时流水线在"校验标签"步直接失败,
   防呆见第七节):

   ```bash
   git tag v0.1.0          # 缺省打在当前 HEAD; 也可显式指定提交
   git push origin v0.1.0
   ```

3. 数据集固定 full (标签发布不吃 `model_set` 输入); 成功后自动
   创建 GitHub Release **草稿** —— 草稿不对外可见, 按第十一节
   待办清单人工核对 (License 替换/签名/实机冒烟) 后再 Publish。
4. 撤回/重来: 网页删除 Release 草稿 +
   `git push origin :refs/tags/v0.1.0` 删远端标签; 修复后重打
   同名标签即可 (标签删除后版本号可复用)。

### 8.2 预期产物

- run 时长: 首跑无 FetchContent 缓存 + MSVC 全量构建, 预计
  15~40 分钟, 上限 `timeout-minutes: 60`; 缓存 (`build/_deps`)
  命中后的后续 run 明显缩短。
- 两种触发都产出 Actions 构建产物: run 页面 Artifacts 区一个
  `MagTileStudio-<版本>-win64` (GitHub 下载时外面统一再套一层
  zip), 内含:

| 文件 | 内容 |
| --- | --- |
| `MagTileStudio-<版本>-win64.exe` | NSIS 安装器 (布局见第二节) |
| `MagTileStudio-<版本>-win64.zip` | 便携版, 解压即用 |

- **starter 档产物文件名与 full 档相同** (CPack 包名不带档位
  后缀, 仅 Qt-only 形态加 `-qt`), 两场试跑的下载物勿混放一个
  目录; 甄别看包内 `data/models/` 条数 (starter 恰 30)。
- CI 配置未开 `-DMAGTILE_BUILD_QT`, 产物为 CLI/GL 档包, **不含**
  `magtile_studio_qt.exe` (Qt 商用界面打包目前走实机路径,
  见第五节与 `scripts/package_qt_desktop.md`)。
- 标签触发额外产出: GitHub Release **草稿**一份
  (名 `MagTile Studio v<版本> (Windows)`), 附上述两文件;
  `fail_on_unmatched_files: true` 保证缺文件时步骤失败,
  不会发出空草稿。

产物下载解包后快速核验 (Linux/macOS; Windows 用
`tar -tf` + `certutil -hashfile <文件> SHA256` 同效):

```bash
unzip -l MagTileStudio-<版本>-win64.zip        # 清单: exe + data/ + licenses/ + README
unzip -l MagTileStudio-<版本>-win64.zip | grep -c 'data/models/.*\.json'
    # full = 与 data/model_catalog.json 登记条数一致; starter = 30
sha256sum MagTileStudio-<版本>-win64.exe MagTileStudio-<版本>-win64.zip
    # 登记进 §8.4 签核表
```

安装/卸载/快捷方式/中文显示等深度验收属 Windows 实机验收
(V1 清单 D3), 按 `platforms/windows/README.md` 验收清单执行,
不阻塞本节流水线转正。

### 8.3 首跑失败排查 (CI 专属; 通用打包故障见第十节)

| 症状 | 原因 | 处置 |
| --- | --- | --- |
| 配置步 FetchContent 拉取失败/超时 | runner 出网抖动 | Re-run failed jobs; `actions/cache` 命中 `build/_deps` 后不再拉网 |
| 「安装 NSIS」步 choco 失败 | Chocolatey 社区源抖动/限流 | 重跑该 job; 持续失败可临时钉版本 (`choco install nsis --version=<版本> -y`) 或改 `winget install NSIS.NSIS` |
| cpack 报 `Cannot initialize generator NSIS` (NSIS 步已绿) | makensis 不在 PATH 且注册表未写 | 回看「安装 NSIS」步日志确认真装成; CPack 另经注册表 `HKLM\SOFTWARE\NSIS` 定位, choco 安装会写注册表, 正常两条路径都命中 |
| 「校验标签与工程版本号一致」步失败 | 标签与 project VERSION 不一致 | 先升 `CMakeLists.txt` 版本号, 再重打对应 `v<版本>` 标签 (第七节) |
| ctest 步失败 | MSVC 平台差异首次暴露 (此前测试仅在 Linux 常跑) | 摘 ctest 日志在本地 VS2022 复现 (第三节), 修复合入后重触发 |
| 「上传构建产物」步报 no files found | cpack 实际没出包 (上一步失败被吞) 或产物名不符 `MagTileStudio-*-win64.*` | 回看 cpack 步日志; 版本号异常时核对 project VERSION |
| 「创建 GitHub Release 草稿」步 403 | 仓库/组织把 workflow 默认权限收成只读且不允许声明提权 | workflow 已声明 `permissions: contents: write`; 仍 403 时在仓库 Settings → Actions → General 放开 workflow 写权限 |
| job 60 分钟超时被杀 | 首跑全量构建 + 无缓存 | 直接重跑 (缓存已落, 二跑显著缩短); 反复超时再考虑升 `timeout-minutes` |

### 8.4 首跑签核登记表

D2 (流水线转正) 的验收口径: 第 1、2 两场全绿且产物核验通过。
第 3 场属正式发布动作, 不阻塞 D2, 首个 `v*` 标签发布时补登。

| # | 场次 | 触发方式 | run 链接 | 提交 / 标签 | 产物核验要点 (§8.2 命令) | SHA256 (exe / zip) | 结果 | 签核人 / 日期 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | full 档试跑 | `workflow_dispatch` `model_set=full` | ⬜ | | exe + zip 齐; 文件名版本号 = project VERSION; 模型条数与 `model_catalog.json` 一致 | | ⬜ | |
| 2 | starter 档试跑 | `workflow_dispatch` `model_set=starter` | ⬜ | | 模型 json 恰 30 + 缩略图恰 30 + `model_catalog.json` 同步过滤 | | ⬜ | |
| 3 | 首个正式标签 | push `v<版本>` | ⬜ | | "校验标签"步绿; Release 草稿两产物齐 | | ⬜ | |

### 8.5 两场试跑全绿后翻状态 (一次性收尾)

- [ ] `docs/V1_LAUNCH_CHECKLIST.md` D2 行 🔶→✅ (状态列登记
      run 链接或 §8.4 表位置)。
- [ ] `platforms/windows/README.md` 验收清单末项
      "`windows-release.yml` 在 `workflow_dispatch` 下于真实
      runner 跑通 (含 starter 档试跑)" 打 `[x]`。
- [ ] 去除三处"尚未在真实 runner 验证"注记: 本手册头部状态块与
      本节验证状态行、`windows-release.yml` 头注"草案"字样、
      `platforms/windows/README.md` 状态块。
- [ ] 注意 D2 转正 ≠ D3: Windows 实机安装验收 (装/卸/GUI 中文
      无乱码) 仍按 `platforms/windows/README.md` 待办段独立推进。

## 九、Linux/macOS 冒烟验证 (无 Windows 机器时)

打包配置的**安装规则与文件清单**可以在任何桌面平台验证 (产物为
TGZ, 仅冒烟用, 不是分发物):

```bash
cmake -S . -B build && cmake --build build --parallel --target magtile_app
(cd build && cpack -G TGZ)
tar tzf build/MagTileStudio-*-Linux.tar.gz | sort   # 核对文件清单

# 子集档: 重新配置后再打
cmake -S . -B build -DMAGTILE_PACKAGE_MODEL_SET=starter
(cd build && cpack -G TGZ)

# 解包后用 CLI 实测子集数据自洽 (目录对账 + 校验)
tar xzf build/MagTileStudio-*-Linux.tar.gz -C /tmp
/tmp/MagTileStudio-*/magtile_app library --data-dir /tmp/MagTileStudio-*/data --db /tmp/x.db
```

Linux 装有 `makensis` (`apt install nsis`) 时还可 `cpack -G NSIS`
冒烟 NSIS 脚本本身 (产出的 .exe 装的是 Linux 二进制, 仅验证安装器
脚本能过编译, 不可分发)。`Product.wxs` 可用 `xmllint --noout` 做
XML 良构检查。本仓库当前状态即按此流程冒烟通过 (结果登记在
`platforms/windows/README.md` 验收清单)。

## 十、常见失败排查

| 症状 | 原因 | 处置 |
| --- | --- | --- |
| 配置期卡在/失败于 `FetchContent... glfw` | 网络不通 / 代理未配置 | 设置 `HTTPS_PROXY`; 或纯 CLI 验证加 `-DMAGTILE_BUILD_GL_RENDERER=OFF` 完全离线; CI 用 actions/cache 缓存 `build/_deps` |
| `No CMAKE_CXX_COMPILER could be found` | 未装 VS2022 C++ 工作负载, 或不在 Native Tools 环境 | VS Installer 补装"使用 C++ 的桌面开发"; 用 "x64 Native Tools Command Prompt" |
| MSB8020 / 平台工具集不匹配 | build 目录残留旧生成器缓存 | 删除 build 目录重新配置; 切换 `-G`/`-A` 必须换新目录 |
| `cpack: Cannot find NSIS registry value` 或 `CPack Error: Cannot initialize generator NSIS` | 未装 NSIS 或 `makensis` 不在 PATH (CI 的 `windows-latest` 2025 镜像已移除预装) | `winget install NSIS.NSIS` (CI: `choco install nsis -y`) 后重开终端; 只要 ZIP 时改 `cpack -G ZIP` |
| `file INSTALL cannot find ".../Release/magtile_app.exe"` | 打包前没做 Release 构建 (只构建了 Debug, 或压根没构建) | 先 `cmake --build build-win --config Release`, 且 cpack 用同一 `-C Release` |
| cpack 找不到 CPackConfig.cmake | 没在 build 目录里执行 cpack | `cd build-win` 后再 `cpack`, 或 `cpack --config build-win/CPackConfig.cmake` |
| 配置期报 `打包清单 ... 引用了不存在的模型` | 子集清单模型 id 拼写错误, 或模型已改名/删除 | 按报错列出的 id 修正清单 (`starter_models.txt` 或自定义清单) |
| 打包期报 `以下清单模型未在 model_catalog.json 登记` | 新模型入库后没重跑目录生成器 | `python tools/update_model_catalog.py` 重新登记后再打包 |
| 子集模式配置报 `需要 Python3` | 机器无 Python | 装 Python 3.8+ (VS 安装器可勾选), 或改 `-DMAGTILE_PACKAGE_MODEL_SET=full` |
| `ctest` 中 `library_gui_smoke`/`inventory_gui_smoke` 失败 | 无显示环境 / 远程桌面无 OpenGL | `ctest ... -E "(library|inventory)_gui_smoke"` 跳过; 实机验收另跑 GUI |
| 控制台中文乱码 / 测试输出乱码 | 代码页不是 UTF-8 | `chcp 65001`; 源码层面已 `/utf-8`, 无需改代码 |
| `wix: command not found` | 未装 WiX v4 dotnet tool | `dotnet tool install --global wix` (需 .NET SDK), 重开终端 |
| MSI 安装报 "已安装更高版本" | Product.wxs 的 MajorUpgrade 降级保护 | 预期行为; 先卸载高版本, 或提升 `-d Version=` |
| 安装器被 SmartScreen 拦截 | 安装器未签名 | 发布前按第十一节签名; 内测阶段"更多信息 → 仍要运行" |
| NSIS 打包报 `File: ... -> no files found` | 安装规则产出为空 (常见于改动 CPackWindows.cmake 后未重新配置) | 重新 `cmake -S . -B build-win` 后再 cpack |
| 标签流水线在"校验标签"步失败 | 标签与 project VERSION 不一致 | 先升 `CMakeLists.txt` 版本号, 再打对应 `v<版本>` 标签 |

## 十一、正式发布前待办清单

- [ ] 替换 `License.rtf` 为法务审定的正式许可协议 (中文);
      同步复核 `THIRD_PARTY_NOTICES.md` (含 Qt LGPL 条目, 若随包)。
- [ ] 补充安装器素材: `icon.ico` / `banner.bmp` / `dialog.bmp`
      (放入 `platforms/windows/packaging/`, 在 CPackWindows.cmake
      与 Product.wxs 中启用对应 TODO 注释)。
- [ ] 代码签名: 申请代码签名证书, 用 `signtool sign /fd SHA256 ...`
      对 exe 与安装器签名 (计划脚本 `packaging/sign.ps1`), 否则
      SmartScreen 会拦截未签名安装器。
- [ ] 在干净的 Windows 10/11 虚拟机上实测: 安装 → 开始菜单启动
      模型库 → 教程进度存档写入 `%USERPROFILE%` → 卸载无残留
      (完整验收项见 `platforms/windows/README.md`)。
- [ ] 实测 MSI 原地升级 (低版本 → 高版本) 与静默安装 `msiexec /qn`。
- [ ] 确认发布档位 (full / starter) 与商业策略一致
      (免费层定义见 `docs/COMMERCIAL_PLAN.md` §2.1, 三端清单对齐
      见 `docs/FREE_TIER_MANIFEST.md`), 并跑
      `python3 tools/verify_free_tier.py` 确认 starter 清单未漂移。

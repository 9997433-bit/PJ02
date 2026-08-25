# Windows 构建与打包指南

本文是 MagTile Studio Windows 端从源码到安装包的完整操作手册。
打包资产位于 `platforms/windows/packaging/`, 自动化流水线位于
仓库根 `.github/workflows/windows-release.yml` (workflow 必须放在
仓库根才会被 GitHub 识别, 本工程位于仓库的 `magtile-studio/` 子目录)。

> 状态: **IN_PROGRESS**。CPack/NSIS + WiX 配置、模型子集打包与许可
> 文件安装均已就位; 安装规则与文件清单已在 Linux CI 环境冒烟通过
> (TGZ 全量/子集两档, 见第九节), 但**尚未在真实 Windows 机器出过
> exe/msi**。首次实机打包按第十节 checklist 逐项核对,
> 验收项见 `platforms/windows/README.md`。

## 一、前置条件

| 组件 | 要求 | 说明 |
| --- | --- | --- |
| Visual Studio 2022 | 工作负载"使用 C++ 的桌面开发" | MSVC 19.3x, 支持 C++20 |
| CMake | ≥ 3.20 | VS 自带的即可; `cpack` 随 CMake 一起安装 |
| NSIS | ≥ 3.x | 产出 `.exe` 安装器; [nsis.sourceforge.io](https://nsis.sourceforge.io/) 或 `winget install NSIS.NSIS`; GitHub `windows-latest` CI 镜像已预装 |
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
| `full` (默认) | 完整模型库 (当前 131 模型 + 全部缩略图, 约 7 MiB) |
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
| `MagTileStudio-<版本>-win64.exe` | NSIS 安装器: 装入 `%ProgramFiles%\MagTile Studio\`, 创建开始菜单快捷方式 (直达 `library --gui` 模型库主界面; Qt 构建时另有 "MagTile Studio (Qt)" 快捷方式), 带卸载器 |
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
  `licenses/THIRD_PARTY_NOTICES.md`; 商用闭源发布前由法务确认走
  LGPL 合规或购买 Qt 商业许可。
- MSI 路径 (第六节) 暂不收割 Qt 运行库, Qt 版分发走 NSIS/ZIP。

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

## 八、CI 流水线

仓库根 `.github/workflows/windows-release.yml`:

- 触发: 推送 `v*` 标签 (正式发布, 数据集固定 full) 或手动
  `workflow_dispatch` (试跑, 可选 `model_set=starter` 试打子集包)。
- 步骤: MSVC 配置构建 → 从 CMakeCache 提取版本号并校验标签 →
  `ctest` (跳过需显示环境的两个 GUI 冒烟) → `cpack -G "NSIS;ZIP"` →
  上传构建产物; 标签触发时另建 GitHub Release **草稿** (人工核对
  后再发布)。
- 该工作流尚未在真实 runner 上跑通过; 首跑失败优先排查
  FetchContent 网络与 NSIS 可用性 (见第十节)。

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
| `cpack: Cannot find NSIS registry value` 或 `CPack Error: Cannot initialize generator NSIS` | 未装 NSIS 或 `makensis` 不在 PATH | `winget install NSIS.NSIS` 后重开终端; 只要 ZIP 时改 `cpack -G ZIP` |
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

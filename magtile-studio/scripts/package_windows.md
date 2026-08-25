# Windows 构建与打包指南

本文是 MagTile Studio Windows 端从源码到安装包的完整操作手册。
打包资产位于 `platforms/windows/packaging/`, 自动化流水线草案位于
仓库根 `.github/workflows/windows-release.yml` (workflow 必须放在
仓库根才会被 GitHub 识别, 本工程位于仓库的 `magtile-studio/` 子目录)。

> 状态: **脚手架**。CPack/NSIS 与 WiX 配置已就位但尚未在真实
> Windows 机器上出过包; 首次实机打包时请按第七节清单逐项核对。

## 一、前置条件

| 组件 | 要求 | 说明 |
| --- | --- | --- |
| Visual Studio 2022 | 工作负载"使用 C++ 的桌面开发" | MSVC 19.3x, 支持 C++20 |
| CMake | ≥ 3.20 | VS 自带的即可; `cpack` 随 CMake 一起安装 |
| NSIS | ≥ 3.x | 产出 `.exe` 安装器; [nsis.sourceforge.io](https://nsis.sourceforge.io/) 或 `winget install NSIS.NSIS`; GitHub `windows-latest` CI 镜像已预装 |
| WiX Toolset | v4 (可选) | 仅走 MSI 路径时需要: `dotnet tool install --global wix` |
| 网络 | 首次配置需要 | FetchContent 拉取 GLFW 3.4 / Dear ImGui |

## 二、构建与测试

在 "x64 Native Tools Command Prompt" 或普通终端执行 (中文输出乱码时
先 `chcp 65001`):

```bat
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64
cmake --build build-win --config Release --parallel
ctest --test-dir build-win -C Release --output-on-failure
```

要点:

- 全部源码与数据均为 UTF-8, 根 CMakeLists 已对 MSVC 强制 `/utf-8`。
- GL 渲染后端在 Windows 上经 GLFW 使用 WGL, 无额外系统依赖;
  GLFW 静态链接进 exe, 分发物不含第三方 DLL。
- `library_gui_smoke` 测试需要可创建 OpenGL 窗口的显示环境,
  无显示的机器 (含多数 CI) 用 `ctest ... -E library_gui_smoke` 跳过。

## 三、CPack 打包 (首选路径: NSIS 安装器 + 便携 ZIP)

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
| `MagTileStudio-<版本>-win64.exe` | NSIS 安装器: 装入 `%ProgramFiles%\MagTile Studio\`, 创建开始菜单快捷方式 (直达 `library --gui` 模型库主界面), 带卸载器 |
| `MagTileStudio-<版本>-win64.zip` | 便携版: 解压即用, 免安装 |

安装布局 (两种产物一致):

```
MagTile Studio\
├── magtile_app.exe     主程序 (CLI + GUI 一体)
├── data\               磁力片形状目录 + 模型库 (运行必需)
├── README.md
└── vcruntime140*.dll   MSVC CRT 运行库 (InstallRequiredSystemLibraries)
```

打包配置见 `platforms/windows/packaging/CPackWindows.cmake`;
安装器许可页文本为 `platforms/windows/packaging/License.rtf`
(**当前为占位文本, 正式发布前必须替换为法务审定版本**)。

## 四、WiX / MSI 路径 (企业分发, 可选)

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
    -o build-win\MagTileStudio-0.1.0-win64.msi
```

方式 B 的 `-d Version=` 必须与 project VERSION 一致 (CI 中从
CMakeCache 提取后传入, 人工操作时请核对)。两条路径共用同一个
UpgradeCode (`6FE5F9D7-79A7-4829-B13A-8C3B1517CA61`), 因此互相可
原地升级; **此 GUID 永久固定, 严禁改动**, 换掉它等于发布一个
"新产品", 已装机器将无法被升级替换。

## 五、版本号管理

1. 唯一来源: 根 `CMakeLists.txt` 中 `project(MagTileStudio VERSION x.y.z)`。
2. 升版只改这一处; CPack 文件名、NSIS/MSI 内部版本号全部自动跟随。
3. 发布标签命名 `v<版本>` (如 `v0.1.0`), 推送标签即触发
   `windows-release.yml` 流水线; 流水线会校验标签与 project VERSION
   一致, 不一致直接失败, 防止"标签说 0.2.0 包里是 0.1.0"。
4. WiX 方式 B 的 `-d Version=` 为显式传参, 见第四节。

## 六、CI 流水线 (草案)

仓库根 `.github/workflows/windows-release.yml`:

- 触发: 推送 `v*` 标签 (正式发布) 或手动 `workflow_dispatch` (试跑)。
- 步骤: MSVC 配置构建 → 从 CMakeCache 提取版本号并校验标签 →
  `ctest` (跳过需显示环境的 GUI 冒烟) → `cpack -G "NSIS;ZIP"` →
  上传构建产物; 标签触发时另建 GitHub Release **草稿** (人工核对
  后再发布)。
- 该工作流为草案, 尚未在真实 runner 上验证; 首跑失败优先排查
  FetchContent 网络与 NSIS 可用性。

## 七、正式发布前待办清单

- [ ] 替换 `License.rtf` 为法务审定的正式许可协议 (中文)。
- [ ] 补充安装器素材: `icon.ico` / `banner.bmp` / `dialog.bmp`
      (放入 `platforms/windows/packaging/`, 在 CPackWindows.cmake
      与 Product.wxs 中启用对应 TODO 注释)。
- [ ] 代码签名: 申请代码签名证书, 用 `signtool sign /fd SHA256 ...`
      对 exe 与安装器签名 (计划脚本 `packaging/sign.ps1`), 否则
      SmartScreen 会拦截未签名安装器。
- [ ] 在干净的 Windows 10/11 虚拟机上实测: 安装 → 开始菜单启动
      模型库 → 教程进度存档写入 `%USERPROFILE%` → 卸载无残留。
- [ ] 实测 MSI 原地升级 (低版本 → 高版本) 与静默安装 `msiexec /qn`。

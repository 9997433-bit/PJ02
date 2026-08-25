# MagTile Studio — Windows 平台构建与安装包 (脚手架)

本目录规划 Windows 端的构建与分发。桌面版本身是跨平台 CMake 工程,
Windows 不需要独立的构建入口 —— 本目录只承载 **打包/安装器** 资产
(见 `packaging/`) 与本说明文档。

> 状态: **脚手架**。MSVC 构建路径当前即可用 (仓库根 CMakeLists.txt
> 已内置 `/W4 /utf-8` 等 MSVC 配置); 打包配置 (CPack/NSIS + WiX stub)
> 已入库但尚未实机出包, 完整操作手册见 `scripts/package_windows.md`,
> CI 流水线草案见 `.github/workflows/windows-release.yml`。

## 一、MSVC 构建

前置条件:

- Visual Studio 2022 (工作负载 "使用 C++ 的桌面开发", MSVC 19.3x, 支持 C++20)
- CMake ≥ 3.20 (VS 自带的即可)
- 联网 (首次配置经 FetchContent 拉取 GLFW 3.4 / Dear ImGui; 纯 CLI
  验证可加 `-DMAGTILE_BUILD_GL_RENDERER=OFF` 完全离线构建)

在 "x64 Native Tools" 命令行或普通终端执行:

```bat
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64
cmake --build build-win --config Release
ctest --test-dir build-win -C Release --output-on-failure

build-win\Release\magtile_app.exe validate data\models\castle_foundation_01.json --data-dir data
build-win\Release\magtile_app.exe tutorial data\models\castle_foundation_01.json --data-dir data --gui
```

要点:

- 全部源码与数据均为 UTF-8, 根 CMakeLists 已对 MSVC 强制 `/utf-8`;
  控制台若中文乱码, 先执行 `chcp 65001`。
- GL 渲染后端在 Windows 上使用 WGL (由 GLFW 封装), 无额外系统依赖。

## 二、安装包 (脚手架已入库, 未实机出包)

两条打包路径, 配置均已就位 (详细步骤见 `scripts/package_windows.md`):

1. **CPack — NSIS 安装器 + 便携 ZIP** (首选): 复用现有 CMake 工程,
   版本号自动取自根 `project(VERSION)`。

   ```bat
   cd build-win
   cpack -G "NSIS;ZIP" -C Release
   ```

2. **WiX v4 — 标准 MSI** (企业分发、组策略、静默安装 `msiexec /qn`):
   独立描述文件 `packaging/Product.wxs`, 版本号经 `-d Version=` 注入。
   两条路径共用固定 UpgradeCode, 互相可原地升级。

安装布局 (两条路径一致):

```
%ProgramFiles%\MagTile Studio\
├── magtile_app.exe       主程序 (CLI + GUI 一体)
├── data\                 形状目录 + 模型库 (来自仓库 data/)
├── README.md
└── vcruntime140*.dll     MSVC CRT 运行库
```

待办: 代码签名 (signtool)、安装器图标/横幅素材、正式许可文本
(见 `scripts/package_windows.md` 第七节清单)。

## 目录结构

```
platforms/windows/
├── README.md        本文档
└── packaging/       安装器资产 (CPackWindows.cmake、Product.wxs、License.rtf)
```

## 相关文档

- `scripts/package_windows.md` — Windows 构建/打包完整操作手册
  (前置条件、CPack/NSIS、WiX/MSI、版本号管理、发布前清单)。
- `.github/workflows/windows-release.yml` — Windows 发布流水线草案
  (标签触发, 构建 + 测试 + 打包 + Release 草稿)。
- `docs/PLATFORM_ARCHITECTURE.md` — 跨平台技术架构总纲 (含发布流水线
  与各平台打包策略); 本目录即其第 8 节规划的 `platforms/windows/`
  落地脚手架。
- `docs/ARCHITECTURE.md` — 核心分层与模块职责。
- `docs/ROADMAP.md` — 发布节奏。
- `platforms/android/README.md` — Android 端 NDK 构建与 JNI 接入。

# MagTile Studio — Windows 平台构建与安装包 (脚手架)

本目录规划 Windows 端的构建与分发。桌面版本身是跨平台 CMake 工程,
Windows 不需要独立的构建入口 —— 本目录只承载 **打包/安装器** 资产
(见 `packaging/`) 与本说明文档。

> 状态: **脚手架**。MSVC 构建路径当前即可用 (仓库根 CMakeLists.txt
> 已内置 `/W4 /utf-8` 等 MSVC 配置); 安装器为规划中, 资产目录已就位。

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

## 二、安装包规划 (MSI, 未实装)

首选 **WiX Toolset v4** 产出标准 MSI (企业分发、组策略、静默安装
`msiexec /qn` 都友好); 若后期需要更轻的自解压体验, 备选 **NSIS**。

计划安装布局:

```
%ProgramFiles%\MagTile Studio\
├── magtile_app.exe
└── data\                 形状目录 + 模型库 (来自仓库 data/)
```

打包步骤 (待实装, 资产放入 `packaging/`):

1. `cmake --build ... --config Release` 产出 exe;
2. `wix build packaging\Product.wxs -d BuildDir=build-win\Release -o MagTileStudio.msi`;
3. 后续接入代码签名 (signtool) 与升级码 (UpgradeCode 固定, 支持原地升级)。

也会评估 CMake 自带的 CPack (`CPack WIX` 生成器), 若能满足需求则直接
复用现有 CMake 工程, 减少一份独立的打包脚本。

## 目录结构

```
platforms/windows/
├── README.md        本文档
└── packaging/       MSI/安装器资产占位 (Product.wxs、图标、许可文本等)
```

## 相关文档

仓库暂无 `docs/PLATFORM_ARCHITECTURE.md`, 平台拆分约定先记录于各平台
README (本文档与 `platforms/android/README.md`); 总体架构见
`docs/ARCHITECTURE.md`, 发布节奏见 `docs/ROADMAP.md`。

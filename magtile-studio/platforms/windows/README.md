# MagTile Studio — Windows 平台构建与安装包

本目录规划 Windows 端的构建与分发。桌面版本身是跨平台 CMake 工程,
Windows 不需要独立的构建入口 —— 本目录只承载 **打包/安装器** 资产
(见 `packaging/`) 与本说明文档。

> 状态: **IN_PROGRESS**。MSVC 构建路径当前即可用 (仓库根 CMakeLists.txt
> 已内置 `/W4 /utf-8` 等 MSVC 配置); 打包配置 (CPack/NSIS + ZIP、
> WiX/MSI、模型子集开关、许可文件、Qt 界面安装规则) 已全部入库,
> 安装规则与文件清单已在 Linux CI 环境冒烟通过 (见下方验收清单),
> **尚未在 Windows 实机出过 exe/msi**。完整操作手册见
> `scripts/package_windows.md`, CI 流水线见仓库根
> `.github/workflows/windows-release.yml`。

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
build-win\Release\magtile_app.exe tutorial data\models\castle_foundation_01.json --data-dir data --dev-gui
```

要点:

- 全部源码与数据均为 UTF-8, 根 CMakeLists 已对 MSVC 强制 `/utf-8`;
  控制台若中文乱码, 先执行 `chcp 65001`。
- GL 渲染后端在 Windows 上使用 WGL (由 GLFW 封装), 无额外系统依赖。
- Qt 商用界面: `-DMAGTILE_BUILD_QT=ON -DCMAKE_PREFIX_PATH=C:/Qt/6.x.y/msvc2022_64`
  (可选, 默认关; 打包细节见 `scripts/package_windows.md` 第五节)。

## 二、安装包

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

安装布局 (各路径一致):

```
%ProgramFiles%\MagTile Studio\
├── magtile_app.exe        主程序 (CLI + GUI 一体)
├── magtile_studio_qt.exe  Qt 商用界面 (仅 -DMAGTILE_BUILD_QT=ON 时)
├── data\                  形状目录 + 模型库 (full 全库 或 starter 精选
│                          30 模型子集, 由 -DMAGTILE_PACKAGE_MODEL_SET 决定)
├── licenses\              EULA + 第三方许可声明
├── README.md
└── vcruntime140*.dll      MSVC CRT 运行库
```

## 三、验收清单

Linux CI 环境可冒烟的项已验证 (标 `[x]`, 环境: Ubuntu + CMake 3.28,
TGZ 生成器走同一套安装规则); 标 `[ ]` 的项必须在 Windows 实机完成,
全绿后状态才能翻 DONE。

**打包配置正确性 (Linux CI 已验)**

- [x] `cmake` 配置在 full / starter 两档均成功, starter 档报告
      "打包数据集 = 模型子集 (30 个)"。
- [x] 清单含拼写错误的模型 id 时配置期即失败 (不拖到打包)。
- [x] `cpack` (full 档) 产物含 `magtile_app` + `data/` 全库
      (131 模型 + 131 缩略图 + 双目录文件) + `licenses/{License.rtf,
      THIRD_PARTY_NOTICES.md}` + `README.md`。
- [x] `cpack` (starter 档) 产物 `data/models/` 恰为清单 30 模型,
      `model_catalog.json` 同步过滤为 30 条, 缩略图 30 张。
- [x] 解包后 `magtile_app library` 对子集数据目录对账通过
      (无 "目录登记但文件缺失" 报错), `validate` 旗舰模型通过。
- [x] `ctest` 全量通过 (Linux, 含全库 validate/tutorial/质检门)。
- [x] `Product.wxs` XML 良构 (xmllint); `windows-release.yml` YAML 合法。
- [x] NSIS 脚本冒烟: Linux `makensis` 经 `cpack -G NSIS` 能产出安装器
      (产物装的是 Linux 二进制, 仅验证 NSIS 脚本编译通过, 不可分发)。

**Windows 实机验收 (待办)**

- [ ] VS2022 x64 Release 构建成功, `/W4` 无新增警告。
- [ ] `ctest -C Release` 全绿 (无显示环境跳过两个 GUI 冒烟)。
- [ ] `cpack -G "NSIS;ZIP" -C Release` 产出
      `MagTileStudio-<版本>-win64.exe` 与 `.zip`, 文件名版本号与
      project VERSION 一致。
- [ ] NSIS 安装器: 许可页正常显示 → 安装到 `%ProgramFiles%\MagTile
      Studio\` → 开始菜单快捷方式启动模型库 GUI → 中文界面无乱码。
- [ ] 便携 ZIP 解压即用: `magtile_app.exe library --dev-gui` (GL 内部
      工具) 可启动, 教程进度存档写入用户目录。
- [ ] starter 子集安装包: 模型库界面恰显示 30 个模型, 卡片缩略图齐全。
- [ ] 卸载干净: `%ProgramFiles%` 目录与开始菜单项移除 (用户存档保留)。
- [ ] WiX 方式 B `wix build` 出 MSI; `msiexec /qn` 静默安装可用;
      低版本 → 高版本原地升级成功 (NSIS ↔ MSI 互升亦验)。
- [ ] (可选, Qt) `-DMAGTILE_BUILD_QT=ON` 打包后 `magtile_studio_qt.exe`
      在干净机器可启动 (Qt ≥ 6.5 自动部署 / 6.4 手动 windeployqt)。
- [ ] `windows-release.yml` 在 `workflow_dispatch` 下于真实 runner
      跑通 (含 starter 档试跑)。

首次实机验收时若发现问题, 排查入口: `scripts/package_windows.md`
第十节"常见失败排查"。

## 目录结构

```
platforms/windows/
├── README.md        本文档
└── packaging/       安装器资产 (CPackWindows.cmake、Product.wxs、
                     License.rtf、THIRD_PARTY_NOTICES.md、
                     starter_models.txt)
```

## 相关文档

- `scripts/package_windows.md` — Windows 构建/打包完整操作手册
  (前置条件、CPack/NSIS、WiX/MSI、模型子集、Qt 打包、版本号管理、
  常见失败排查、发布前清单)。
- `scripts/package_qt_desktop.md` — Qt 商用界面打包手册 (QT-6:
  windeployqt/macdeployqt、Qt-only 包形态 `MAGTILE_PACKAGE_QT_ONLY`、
  LGPL 合规清单、Linux 冒烟)。
- 仓库根 `.github/workflows/windows-release.yml` — Windows 发布
  流水线 (标签触发, 构建 + 测试 + 打包 + Release 草稿; 手动试跑
  支持 starter 档)。
- `tools/make_data_subset.py` — 打包用数据子集装配器 (CPack 子集
  模式与 WiX 子集路径共用)。
- `docs/PLATFORM_ARCHITECTURE.md` — 跨平台技术架构总纲 (含发布流水线
  与各平台打包策略); 本目录即其第 8 节规划的 `platforms/windows/`
  落地。
- `docs/ARCHITECTURE.md` — 核心分层与模块职责。
- `docs/ROADMAP.md` — 发布节奏。
- `platforms/android/README.md` — Android 端 NDK 构建与 JNI 接入。

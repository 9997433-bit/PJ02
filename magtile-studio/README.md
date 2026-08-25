# MagTile Studio · 磁力片搭建教程

MagTile Studio 是一款面向消费市场的桌面应用: 用交互式 3D 分步教程, 教孩子和家长用标准磁力片 (磁力积木) 搭建从入门到大师级的数百个模型。每一个入库模型都经过内置物理校验器质检, 保证"照着教程搭, 一定搭得起来"。

## 核心特性

- **标准磁力片形状库**: 共 13 种, 分核心/扩展两层 (见 `docs/TILE_CATALOG.md` 与 `docs/TILE_SET.md`) —— 核心 9 种 = 6 基础片型 (实物照片确认的 正方形、等边三角形、直角三角形、等腰三角形 [瘦高, 底 1 高 2]、长方形, 加新增核心大片 大正方形 [边长 2, 每边可吸 1 条长边或 2 片共线小方]) + 3 变体 (窗格方、门框方、车轮底座); 扩展 4 种: 菱形、梯形、六边形、扇形。几何数据由 `data/tile_catalog.json` 驱动, 可扩展非标配件。
- **分步教程引擎**: 上一步 / 下一步 / 跳转 / 进度, 每一步给出中文说明、操作提示、新增磁力片与高亮参照片。
- **物理规则校验**: 八条规则两组把关 —— 几何/拓扑 (接地支撑、磁力边吸合、无重叠、重心稳定) + 静力学/工艺 (悬挂承重、悬臂力矩、装配可达、结构冗余, 磁吸边按"铰链"而非刚性节点建模); 不仅校验成品, 还逐步校验教程每个中间状态乃至步骤内逐片放置顺序 (保证不会"搭到一半塌掉"或"照着图纸搭却掉下来"), 详见 `docs/PHYSICS_RULES.md`。
- **模型库主界面**: `library --gui` 打开商业版主入口 —— 模型卡片网格 (难度星级 / 片数步数 / 主题色徽章 / 完成对勾), 按名称搜索、按难度与主题筛选、收藏置顶查看, 进行中的模型在顶部"继续搭建"区一键断点续搭, 点击卡片即进入 3D 教程并自动记录进度。
- **3D 交互教程**: GLFW + OpenGL 4.1 渲染后端 —— 半透明彩色磁力片、成品轮廓虚影、当前步骤高亮描边、轨道相机, 教程 HUD 支持按钮与键盘双通道导航。
- **渲染层解耦**: 核心逻辑与渲染完全隔离; 无窗口渲染器用于 CLI 与 CI, 窗口后端隐藏在同一 `IRenderer` 接口之后 (详见架构文档)。
- **本地进度存档**: SQLite 单文件存档 —— 每个模型的教程进度、完成状态、收藏、成就与磁力片库存; 离线优先, 写入语义天然支持未来云同步 (详见 `docs/PROGRESS.md`)。

## 快速开始

要求: CMake ≥ 3.20, 支持 C++20 的编译器 (MSVC 2022 / Clang 14+ / GCC 11+)。

图形后端默认开启, GLFW 与 Dear ImGui 在配置阶段自动获取 (优先系统安装的 GLFW, 否则 FetchContent 联网拉取)。Linux 额外需要 X11 开发头文件:

```bash
# Ubuntu / Debian
sudo apt install libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev
# 可选: 无显示环境的纯 CI 构建可完全跳过图形后端
#   cmake -S . -B build -DMAGTILE_BUILD_GL_RENDERER=OFF
```

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j

# 打开模型库主界面 (商业版入口): 搜索/筛选模型卡片, 点击进入 3D 教程,
# 进度自动存档, 未搭完的模型下次启动出现在顶部"继续搭建"区
./build/magtile_app library --gui

# 终端查看模型库与进度 (兼作目录元数据与模型文件的一致性对账)
./build/magtile_app library

# 直接打开单个模型的 3D 教程窗口 (鼠标左键旋转 / 右键平移 / 滚轮缩放, ←→ 切换步骤)
./build/magtile_app tutorial data/models/castle_foundation_01.json --gui

# 查看磁力片形状目录
./build/magtile_app catalog

# 质检示例模型 (物理规则 + 教程一致性)
./build/magtile_app validate data/models/castle_foundation_01.json

# 在终端预览分步教程
./build/magtile_app tutorial data/models/castle_foundation_01.json

# 查看教程进度存档 (progress show/reset <model_id> 查看/重置单个模型)
./build/magtile_app progress list

# 登记家里的磁力片库存并列出能搭建的模型 (inventory show 查看库存)
./build/magtile_app inventory set square 40 equilateral_triangle 24
./build/magtile_app inventory match

# 运行测试
ctest --test-dir build --output-on-failure

# 图形模式冒烟测试 (无显示环境, 需 xvfb): 渲染 30 帧并保存截图
xvfb-run -a ./build/magtile_app tutorial data/models/castle_foundation_01.json \
    --gui --step 10 --frames 30 --screenshot /tmp/magtile.ppm
```

## 目录结构

```
magtile-studio/
├── CMakeLists.txt          # 构建入口
├── docs/                   # 架构 / 路线图 / 物理规则文档
├── include/magtile/        # 公共头文件 (core / physics / tutorial / render / progress)
├── src/
│   ├── core/               # 磁力片类型、模型数据结构、JSON 读写
│   ├── physics/            # 几何工具与物理规则校验器
│   ├── tutorial/           # 分步教程引擎
│   ├── render/             # 渲染接口、轨道相机、无窗口实现与 GL 后端 (gl/)
│   ├── progress/           # 本地进度存档 (SQLite)
│   └── app/                # 应用入口 (CLI + 3D 教程窗口)
├── data/
│   ├── tile_catalog.json   # 13 种标准磁力片的几何与磁力边定义 (核心 9 + 扩展 4)
│   ├── model_catalog.json  # 模型库目录 (library 界面的卡片元数据)
│   └── models/             # 模型定义 (含示例: 城堡地基与城墙, 72 片 / 16 步)
├── assets/                 # 模型资源与贴图占位目录
├── platforms/              # 平台外壳 (android/ JNI 构建, windows/ 打包资产)
├── scripts/                # 操作手册 (Windows 构建与打包指南)
├── tools/                  # 内容生产脚本 (示例模型生成器)
└── third_party/            # 第三方库 (nlohmann/json 单头文件, SQLite3 amalgamation)
```

## 示例模型: 城堡地基与城墙

`data/models/castle_foundation_01.json` — 难度 3/5, 72 片 (56 正方形 + 16 等边三角形), 16 个教程步骤: 4×4 地台 → 双层四面围墙 → 四角角楼 → 三角城齿。由 `tools/generate_castle_model.py` 生成, 通过全部物理质检 (116 处磁力连接)。

## 分发与打包 (Windows)

Windows 端分发脚手架已就位 (配置入库, 尚未实机出包)。版本号唯一来源
是根 `CMakeLists.txt` 的 `project(MagTileStudio VERSION x.y.z)`,
安装包文件名与内部版本号全部自动跟随, 升版只改这一处。

```bat
:: MSVC 构建 + 打包: NSIS 安装器 + 便携 ZIP
cmake -S . -B build-win -G "Visual Studio 17 2022" -A x64
cmake --build build-win --config Release --parallel
cd build-win && cpack -G "NSIS;ZIP" -C Release
:: 产出 MagTileStudio-<版本>-win64.exe / .zip
```

- 完整操作手册 (前置条件 / WiX MSI 企业分发路径 / 版本号管理 /
  发布前清单): [scripts/package_windows.md](scripts/package_windows.md)
- 打包资产 (CPack 配置、WiX v4 stub、许可文本):
  [platforms/windows/packaging/](platforms/windows/packaging/)
- CI 发布流水线草案 (推送 `v*` 标签触发, 构建 + 测试 + 打包 +
  Release 草稿): [仓库根 .github/workflows/windows-release.yml](../.github/workflows/windows-release.yml)
  (workflow 必须放在仓库根才会被 GitHub 识别, 本工程位于仓库的
  `magtile-studio/` 子目录)

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块划分、坐标约定、渲染选型、数据格式 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 面向 500+ 模型内容库的分阶段商业化路线 |
| [docs/CONTENT_STRATEGY.md](docs/CONTENT_STRATEGY.md) | 内容策略: 技法分类学、主题矩阵、反批量生成规则、生产管线 |
| [docs/PHYSICS_RULES.md](docs/PHYSICS_RULES.md) | 物理校验规则的精确定义与判定算法 |
| [docs/PROGRESS.md](docs/PROGRESS.md) | 进度存档模块: SQLite 结构、C++ API、CLI 命令与测试 |
| [docs/BUILD_VERIFICATION.md](docs/BUILD_VERIFICATION.md) | 实物搭建验证工作流: 三层验证金字塔、实物测试规程与内容 CI/CD 门禁 |

## 许可

商业项目, 版权所有。第三方组件: [nlohmann/json](https://github.com/nlohmann/json) (MIT)、[SQLite](https://www.sqlite.org/) (公有领域)、[GLFW](https://www.glfw.org/) (zlib/libpng)、[Dear ImGui](https://github.com/ocornut/imgui) (MIT)。

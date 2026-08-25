# MagTile Studio · 磁力片搭建教程

MagTile Studio 是一款面向消费市场的桌面应用: 用交互式 3D 分步教程, 教孩子和家长用标准磁力片 (磁力积木) 搭建从入门到大师级的数百个模型。每一个入库模型都经过内置物理校验器质检, 保证"照着教程搭, 一定搭得起来"。

## 核心特性

- **标准磁力片形状库**: 正方形、等边三角形、直角三角形、等腰三角形、长方形、菱形、梯形、六边形、扇形, 共 9 种, 几何数据由 `data/tile_catalog.json` 驱动, 可扩展非标配件。
- **分步教程引擎**: 上一步 / 下一步 / 跳转 / 进度, 每一步给出中文说明、操作提示、新增磁力片与高亮参照片。
- **物理规则校验**: 接地支撑、磁力边吸合、无重叠、重心稳定四大规则; 不仅校验成品, 还逐步校验教程每个中间状态 (保证不会"搭到一半塌掉")。
- **渲染层解耦**: 核心逻辑与渲染完全隔离, 第一阶段提供无窗口渲染器用于 CLI 与 CI, 正式 3D 后端采用 GLFW + OpenGL (详见架构文档)。

## 快速开始

要求: CMake ≥ 3.20, 支持 C++20 的编译器 (MSVC 2022 / Clang 14+ / GCC 11+)。

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j

# 查看磁力片形状目录
./build/magtile_app catalog

# 质检示例模型 (物理规则 + 教程一致性)
./build/magtile_app validate data/models/castle_foundation_01.json

# 在终端预览分步教程
./build/magtile_app tutorial data/models/castle_foundation_01.json

# 运行测试
ctest --test-dir build --output-on-failure
```

## 目录结构

```
magtile-studio/
├── CMakeLists.txt          # 构建入口
├── docs/                   # 架构 / 路线图 / 物理规则文档
├── include/magtile/        # 公共头文件 (core / physics / tutorial / render)
├── src/
│   ├── core/               # 磁力片类型、模型数据结构、JSON 读写
│   ├── physics/            # 几何工具与物理规则校验器
│   ├── tutorial/           # 分步教程引擎
│   ├── render/             # 渲染接口与无窗口实现 (GL 后端规划中)
│   └── app/                # 命令行入口
├── data/
│   ├── tile_catalog.json   # 9 种标准磁力片的几何与磁力边定义
│   └── models/             # 模型定义 (含示例: 城堡地基与城墙, 72 片 / 16 步)
├── assets/                 # 模型资源与贴图占位目录
├── tools/                  # 内容生产脚本 (示例模型生成器)
└── third_party/            # 第三方库 (nlohmann/json, 单头文件)
```

## 示例模型: 城堡地基与城墙

`data/models/castle_foundation_01.json` — 难度 3/5, 72 片 (56 正方形 + 16 等边三角形), 16 个教程步骤: 4×4 地台 → 双层四面围墙 → 四角角楼 → 三角城齿。由 `tools/generate_castle_model.py` 生成, 通过全部物理质检 (116 处磁力连接)。

## 文档

| 文档 | 内容 |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块划分、坐标约定、渲染选型、数据格式 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | 面向 500+ 模型内容库的分阶段商业化路线 |
| [docs/PHYSICS_RULES.md](docs/PHYSICS_RULES.md) | 物理校验规则的精确定义与判定算法 |

## 许可

商业项目, 版权所有。第三方组件: [nlohmann/json](https://github.com/nlohmann/json) (MIT)。

MagTile Studio 工程交付包
==========================
生成时间: 2026-08-25
基线分支: cursor/magtile-studio-foundation-a95b @ 77ee6ca

压缩包内容
----------
magtile-studio/          完整工程目录
  ├── src/ include/      C++ 源代码
  ├── apps/desktop_qt/   Qt 6 商用桌面界面 (QML)
  ├── platforms/         Android / Windows 打包资产
  ├── data/models/       250 个模型 JSON + 缩略图
  ├── docs/              全部设计与上架文档
  ├── tools/             质检 / 门禁 / 内容生产脚本
  ├── tests/             测试与 QA 流水线
  ├── build/magtile_app  Linux x86_64 CLI 可执行文件 (已编译)
  └── scripts/           打包手册

另附: SOFTWARE_FEATURE_STATUS.md —— 功能清单与缺口摘要

不包含
------
- .git 历史
- build/_deps (FetchContent 缓存, 可 cmake 重建)
- 其他 build-* 临时构建目录

快速运行 (Linux)
----------------
  sudo apt install libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev
  cd magtile-studio
  ./build/magtile_app library
  ./build/magtile_app tutorial data/models/castle_foundation_01.json --dev-gui

重建
----
  cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
  cmake --build build -j
  ctest --test-dir build

Qt 商用界面 (需 Qt 6.4+)
-------------------------
  cmake -S . -B build-qt -DMAGTILE_BUILD_QT=ON
  cmake --build build-qt --target magtile_studio_qt -j

关键文档入口
------------
  docs/V1_LAUNCH_CHECKLIST.md    上架清单 (34 个 P0)
  docs/USER_HANDOFF.md             工程 vs 用户分工
  docs/QT_UI_PLAN.md               Qt 界面功能说明
  docs/ADMIN_LAUNCH_CHECKLIST.md   软著/备案/账号办理

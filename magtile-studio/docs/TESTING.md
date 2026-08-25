# 测试指南

## 构建

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release   # 图形后端默认开启
cmake --build build -j
```

- 图形后端开关: `-DMAGTILE_BUILD_GL_RENDERER=ON|OFF` (默认 ON)。OFF 时不需要网络与 X11 开发库, CLI 与 CTest 完全不受影响。
- Linux 依赖: `sudo apt install libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev`; 若缺少 `wayland-scanner`, 构建会自动退回仅 X11 后端。
- 若默认编译器链接失败 (例如某些环境的 Clang 找不到 `-lstdc++`), 显式指定: `-DCMAKE_CXX_COMPILER=g++`。

## CLI 回归测试 (CTest)

```bash
ctest --test-dir build --output-on-failure
```

包含 3 个用例: `print_tile_catalog`、`validate_castle_foundation_01`、`tutorial_walkthrough`, 覆盖目录打印、物理/教程质检与终端分步教程。等价的手动命令:

```bash
./build/magtile_app catalog  --data-dir data
./build/magtile_app validate data/models/castle_foundation_01.json --data-dir data
./build/magtile_app tutorial data/models/castle_foundation_01.json --data-dir data
```

## 启动 3D 交互教程 (GUI)

```bash
./build/magtile_app tutorial data/models/castle_foundation_01.json --gui
```

操作: 鼠标左键旋转 / 右键平移 / 滚轮缩放, `←` `→` 或 HUD 按钮切换步骤, `R` 重置, `Esc` 退出。需要支持 OpenGL 4.1 的显示环境 (无独显机器上 Mesa llvmpipe 软件渲染亦可)。

## 图形后端冒烟测试 (无头 / CI)

```bash
tests/test_gl_smoke.sh          # 默认使用 build/ 下的可执行文件
tests/test_gl_smoke.sh mybuild  # 或指定构建目录
```

脚本自动选择运行方式: 优先 `xvfb-run` (需 `apt install xvfb`), 其次现有 `DISPLAY`; 渲染 5 帧并保存 PPM 截图, 校验截图尺寸与内容非纯色。两者都不可用时退化为链接检查 (确认 `--gui` 代码路径已编译进二进制)。

手动等价命令:

```bash
xvfb-run -a ./build/magtile_app tutorial data/models/castle_foundation_01.json \
    --gui --frames 30 --screenshot /tmp/magtile.ppm
```

`--frames N` 渲染 N 帧后自动退出, `--screenshot FILE` 在最后一帧保存画面, 两者专为 CI 冒烟测试设计。

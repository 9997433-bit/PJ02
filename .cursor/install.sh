#!/usr/bin/env bash
# =============================================================
# MagTile Studio - Cloud Agent 环境 install 脚本
#
# 幂等地准备开发环境:
#   1. 安装系统依赖 (FetchContent 源码构建 GLFW 所需的 X11 开发头,
#      无头 OpenGL 渲染的 xvfb + Mesa, 以及 GUI 的中日韩字体);
#   2. 用 GCC 配置 + 构建整个工程 (Release, GL 渲染后端开启),
#      此步经 FetchContent 联网拉取 GLFW/ImGui 并全量编译, 使从本
#      环境构建出的快照/新 agent 开箱即用。
#
# 与仓库 .github/workflows/qa.yml 的系统依赖清单保持一致。
# =============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# ---- 1. 系统依赖 ------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    cmake g++ make python3 \
    libx11-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev \
    xvfb libgl1 libglx-mesa0 libgl1-mesa-dri fonts-noto-cjk

# ---- 2. 配置 + 构建 (GL 渲染后端开启) ---------------------------
# 显式指定 GCC: 规避个别环境默认 c++ 指向缺 libstdc++ 搜索路径的
# Clang 导致的链接失败 (与 CI 一致, 见 magtile-studio/docs/TESTING.md)。
export CC=gcc
export CXX=g++
cmake -S magtile-studio -B magtile-studio/build -DCMAKE_BUILD_TYPE=Release
cmake --build magtile-studio/build -j "$(nproc)"

echo "MagTile Studio 环境准备完成: 已构建 magtile-studio/build/magtile_app"

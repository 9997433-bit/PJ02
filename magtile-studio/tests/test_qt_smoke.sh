#!/usr/bin/env bash
# =============================================================
# Qt 界面 QML 加载冒烟 (ctest: qt_gui_smoke)
#
# offscreen 平台无头加载 QML, 与显示环境无关, 任何 CI 均可运行:
#   1. 默认启动 (首页): QML 模块任何加载/语法错误都会让进程以
#      非零退出 (main.cpp 的 objectCreationFailed -> exit(1));
#   2. --parent-gate 深链: 家长门界面 (QT-2) 可加载;
#   3. --smoke-parent-flow 自动驾驶: 家长门 -> 提交标准答案过门 ->
#      家长中心 -> 设置 -> 订阅逐页实例化, 全程无误才返回 0
#      (Main.qml 置 smokeParentFlowOk, main.cpp 据此决定退出码)。
# 三次均以 --smoke-quit-ms 定时退出, 退出码 0 即通过。
#
# 用法: test_qt_smoke.sh <magtile_studio_qt 路径> <仓库根目录>
# =============================================================
set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "用法: $0 <magtile_studio_qt 路径> <仓库根目录>" >&2
    exit 2
fi

APP="$1"
ROOT="$2"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

export QT_QPA_PLATFORM=offscreen

echo "[1/3] 默认启动 (首页) ..."
"$APP" --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" --smoke-quit-ms 1500

echo "[2/3] --parent-gate 深链 (家长门界面) ..."
"$APP" --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" \
    --parent-gate --smoke-quit-ms 1500

echo "[3/3] --smoke-parent-flow 自动驾驶 (门->家长中心->设置->订阅) ..."
"$APP" --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" \
    --smoke-parent-flow --smoke-quit-ms 3000

echo "Qt 界面 QML 加载冒烟通过"

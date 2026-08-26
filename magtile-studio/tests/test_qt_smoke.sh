#!/usr/bin/env bash
# =============================================================
# Qt 界面 QML 加载冒烟 (ctest: qt_gui_smoke)
#
# offscreen 平台无头加载 QML, 与显示环境无关, 任何 CI 均可运行:
#   1. 默认启动 (首页): QML 模块任何加载/语法错误都会让进程以
#      非零退出 (main.cpp 的 objectCreationFailed -> exit(1));
#   2. --parent-gate 深链: 家长门界面 (QT-2) 可加载;
#   3. --smoke-parent-flow 自动驾驶: 进度页 -> 成就墙 (QT-4) ->
#      家长门 -> 提交标准答案过门 -> 家长中心 -> 设置 -> 订阅
#      逐页实例化, 全程无误才返回 0
#      (Main.qml 置 smokeParentFlowOk, main.cpp 据此决定退出码);
#   4. --smoke-complete-model 完成链路 (QT-4): completeBuild 写存档
#      完成状态 -> buildCompleted -> 完成庆祝页实例化, 随后校验
#      存档确已记录完成 (completed_at 非空);
#   5/6. --smoke-age-onboarding 首启年龄段引导 (QT-5, §10.1): 全新
#      存档首启引导出现 -> 自动选 4-6 档 -> 引导收起且落盘
#      (age_mode + onboarding_age_done); 同库二次启动引导不再出现
#      (只出现一次), 两次退出码均由 Main.qml 自动驾驶断言决定。
# 各次均以 --smoke-quit-ms 定时退出, 退出码 0 即通过。
#
# 另收集全程输出扫描 QML 运行时错误 (ReferenceError/TypeError):
# 这类错误只打告警不改退出码 (对象照常创建), 曾漏过 tts 上下文
# 未接线的 ReferenceError, 此处一票否决。
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

QML_LOG="$TMP_DIR/qml_output.log"

# 统一入口: 转存输出供末尾 QML 运行时错误扫描 (pipefail 保证
# 应用非零退出仍会中止脚本)
run_app() {
    "$APP" "$@" 2>&1 | tee -a "$QML_LOG"
}

echo "[1/6] 默认启动 (首页) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" --smoke-quit-ms 1500

echo "[2/6] --parent-gate 深链 (家长门界面) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" \
    --parent-gate --smoke-quit-ms 1500

echo "[3/6] --smoke-parent-flow 自动驾驶 (进度页->成就墙->门->家长中心->设置->订阅) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" \
    --smoke-parent-flow --smoke-quit-ms 3000

echo "[4/6] --smoke-complete-model 完成链路 (完成存档 -> 庆祝页, QT-4) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_smoke.db" \
    --smoke-complete-model castle_foundation_01 --smoke-quit-ms 2500
if command -v python3 >/dev/null 2>&1; then
    python3 - "$TMP_DIR/qt_smoke.db" <<'PYEOF'
import sqlite3, sys
row = sqlite3.connect(sys.argv[1]).execute(
    "SELECT completed_at FROM model_progress WHERE model_id='castle_foundation_01'"
).fetchone()
if row is None or row[0] is None:
    sys.exit("完成链路未写入存档: castle_foundation_01 无 completed_at")
PYEOF
else
    echo "  (python3 不可用, 跳过存档完成状态校验)"
fi

# 首启年龄段引导 (QT-5): 独立全新存档, 首启选档落盘 + 二次启动只出现
# 一次, 两次退出码均由 Main.qml 的 smokeAgeOnboardingOk 断言决定
echo "[5/6] --smoke-age-onboarding 首启年龄段引导 (引导出现 -> 选档落盘, QT-5) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_age_onboarding.db" \
    --smoke-age-onboarding --smoke-quit-ms 2500

echo "[6/6] --smoke-age-onboarding 同库二次启动 (引导只出现一次, QT-5) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_age_onboarding.db" \
    --smoke-age-onboarding --smoke-quit-ms 2500
if command -v python3 >/dev/null 2>&1; then
    python3 - "$TMP_DIR/qt_age_onboarding.db" <<'PYEOF'
import sqlite3, sys
rows = dict(sqlite3.connect(sys.argv[1]).execute(
    "SELECT key, value FROM settings"
    " WHERE key IN ('age_mode','onboarding_age_done')").fetchall())
if rows.get("age_mode") != "age_4_6":
    sys.exit("首启引导未落盘年龄段: age_mode=%r" % rows.get("age_mode"))
if rows.get("onboarding_age_done") != "1":
    sys.exit("首启引导未写完成标记: onboarding_age_done=%r"
             % rows.get("onboarding_age_done"))
PYEOF
else
    echo "  (python3 不可用, 跳过引导落盘校验)"
fi

# QML 运行时错误一票否决 (进程退出码不会体现这些告警)
if grep -E "ReferenceError|TypeError|is not defined" "$QML_LOG" >/dev/null 2>&1; then
    echo "发现 QML 运行时错误:" >&2
    grep -E "ReferenceError|TypeError|is not defined" "$QML_LOG" >&2
    exit 1
fi

echo "Qt 界面 QML 加载冒烟通过"

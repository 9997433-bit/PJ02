#!/usr/bin/env bash
# =============================================================
# Qt 界面按钮级路径冒烟 (ctest: qt_ui_paths_smoke)
#
# 在 qt_gui_smoke (tests/test_qt_smoke.sh) 的加载冒烟之上, 把四条
# 此前只能人工点按的「按钮级」用户路径收进无头自动驾驶 (offscreen
# 平台, 任何 CI 均可运行), 矩阵编号见 docs/E2E_TEST_MATRIX.md:
#   1. --smoke-library-filters 筛选切换 (E2E-04a): 免费筛选数量
#      = freeModelCount / 主题筛选真在过滤 / 难度 1~5 分片求和
#      = 全库 / 清除筛选复位, 全走 FilterChip 同一条属性写路径;
#   2. --smoke-open-inventory 库存页深链 (E2E-09a): 直开库存录入页
#      -> 步进器 +3 -> 「保存库存」落盘, 随后直读 SQLite 断言
#      tile_inventory 全片型入表 (0 也记「明确没有」) 且总数 = 3;
#   3. --smoke-locked-model 非免费锁 (E2E-11c): 非免费模型详情页
#      locked 上锁, 「请家长来解锁」落在家长门 (不开教程), 随后
#      直读 SQLite 断言该模型无任何进度写档;
#   4. --smoke-complete-model + --smoke-progress-data (E2E-12b):
#      完成链路造非空存档后直开进度页, 断言已完成列表与统计对账、
#      成就列表非空且至少一枚徽章点亮, 并进成就墙全览复核。
# 各次均以 --smoke-quit-ms 定时退出, 退出码由 Main.qml 自动驾驶
# 断言决定 (0 即通过)。
#
# 另收集全程输出扫描 QML 运行时错误 (ReferenceError/TypeError),
# 与 test_qt_smoke.sh 同口径一票否决。
#
# 免费/非免费抽样模型均派生自 starter 打包清单 (免费层事实来源,
# 与 run_e2e_smoke.sh 同口径, 不硬编码模型 id); 片型总数派生自
# data/tile_catalog.json (不硬编码 13)。
#
# 用法: test_qt_ui_paths_smoke.sh <magtile_studio_qt 路径> <仓库根目录>
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

if ! command -v python3 >/dev/null 2>&1; then
    echo "错误: 需要 python3 (SQLite 落盘断言依赖)" >&2
    exit 2
fi

# ---- 抽样模型派生 (免费层事实来源: starter 打包清单) ----------------
STARTER_LIST="$ROOT/platforms/windows/packaging/starter_models.txt"
[[ -f "$STARTER_LIST" ]] || { echo "错误: 缺少免费层打包清单 $STARTER_LIST" >&2; exit 2; }
FREE_MODEL="$(grep -vE '^[[:space:]]*(#|$)' "$STARTER_LIST" | head -n 1 | tr -d '[:space:]')"
LOCKED_MODEL=""
for json in "$ROOT"/data/models/*.json; do
    model_id="$(basename "$json" .json)"
    if ! grep -qxF "$model_id" "$STARTER_LIST"; then
        LOCKED_MODEL="$model_id"
        break
    fi
done
[[ -n "$FREE_MODEL" && -n "$LOCKED_MODEL" ]] || {
    echo "错误: 无法从 starter 清单派生免费/非免费抽样模型" >&2; exit 2; }
SHAPE_COUNT="$(python3 -c \
    "import json,sys; print(len(json.load(open(sys.argv[1]))['tiles']))" \
    "$ROOT/data/tile_catalog.json")"
echo "抽样: 免费=$FREE_MODEL 非免费=$LOCKED_MODEL 片型=$SHAPE_COUNT 种"

echo "[1/4] --smoke-library-filters 筛选切换对账 (免费/主题/难度/清除, E2E-04a) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_filters.db" \
    --smoke-library-filters --smoke-quit-ms 3500

echo "[2/4] --smoke-open-inventory 库存页深链 (步进 +3 -> 保存落盘, E2E-09a) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_inventory.db" \
    --smoke-open-inventory --smoke-quit-ms 2500
python3 - "$TMP_DIR/qt_inventory.db" "$SHAPE_COUNT" <<'PYEOF'
import sqlite3, sys
rows, total = sqlite3.connect(sys.argv[1]).execute(
    "SELECT COUNT(*), COALESCE(SUM(count), 0) FROM tile_inventory").fetchone()
if rows != int(sys.argv[2]):
    sys.exit("库存保存未记全片型 (0 也应记「明确没有」): %d/%s 行" % (rows, sys.argv[2]))
if total != 3:
    sys.exit("库存保存总数不符 (+3 步进后应为 3): %d" % total)
PYEOF

echo "[3/4] --smoke-locked-model 非免费锁 ($LOCKED_MODEL: 上锁 -> 家长门, E2E-11c) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_locked.db" \
    --smoke-locked-model "$LOCKED_MODEL" --smoke-quit-ms 2500
python3 - "$TMP_DIR/qt_locked.db" "$LOCKED_MODEL" <<'PYEOF'
import sqlite3, sys
row = sqlite3.connect(sys.argv[1]).execute(
    "SELECT COUNT(*) FROM model_progress WHERE model_id=?",
    (sys.argv[2],)).fetchone()
if row[0] != 0:
    sys.exit("非免费锁被绕过: %s 出现进度写档 (教程被误开)" % sys.argv[2])
PYEOF

echo "[4/4] --smoke-progress-data 进度页有数据断言 (完成造档 -> 成就非空, E2E-12b) ..."
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_progress_data.db" \
    --smoke-complete-model "$FREE_MODEL" --smoke-quit-ms 2500
run_app --data-dir "$ROOT/data" --db "$TMP_DIR/qt_progress_data.db" \
    --smoke-progress-data --smoke-quit-ms 2500

# QML 运行时错误一票否决 (进程退出码不会体现这些告警)
if grep -E "ReferenceError|TypeError|is not defined" "$QML_LOG" >/dev/null 2>&1; then
    echo "发现 QML 运行时错误:" >&2
    grep -E "ReferenceError|TypeError|is not defined" "$QML_LOG" >&2
    exit 1
fi

echo "Qt 界面按钮级路径冒烟通过"

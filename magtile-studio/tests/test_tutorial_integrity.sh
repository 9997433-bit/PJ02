#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 教程完整性检查
#
# 对 data/models/ 下每个模型:
#   1. 静态走查: 逐步累加 tiles_to_add, 验证
#      - 步骤序号从 1 连续递增;
#      - 每片磁力片恰好被一个步骤放置 (不重复、不遗漏);
#      - 走完全部步骤后的累计片数 == final_assembly 数 == total_pieces;
#   2. 运行时走查: magtile_app tutorial 完整跑一遍, 退出码为 0,
#      且最终报告的放置片数与模型 total_pieces 一致。
#
# 用法: test_tutorial_integrity.sh <magtile_app> <project_source_dir>
# =============================================================
set -u

if [ "$#" -ne 2 ]; then
    echo "用法: $0 <magtile_app> <project_source_dir>" >&2
    exit 2
fi

APP="$1"
SRC_DIR="$2"
MODELS_DIR="$SRC_DIR/data/models"
DATA_DIR="$SRC_DIR/data"

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "错误: 需要 python3 解析模型 JSON" >&2
    exit 2
fi

shopt -s nullglob
models=("$MODELS_DIR"/*.json)
shopt -u nullglob
if [ "${#models[@]}" -eq 0 ]; then
    echo "错误: $MODELS_DIR 下没有找到任何模型 JSON" >&2
    exit 1
fi

echo "=============================================================="
echo " 教程完整性检查: 共 ${#models[@]} 个模型"
echo "=============================================================="

failures=0
for model in "${models[@]}"; do
    name="$(basename "$model")"
    echo ""
    echo "---- $name ----"

    # ---- 1. 静态走查: 逐步累加并核对 ---------------------------
    if ! "$PYTHON" - "$model" <<'PYEOF'
import json, sys

m = json.load(open(sys.argv[1], encoding="utf-8"))
final_ids = [t["id"] for t in m["final_assembly"]]
final_set = set(final_ids)
total_pieces = m["total_pieces"]
problems = []

placed = set()
cumulative = 0
for i, step in enumerate(m["steps"]):
    expected_number = i + 1
    if step["step_number"] != expected_number:
        problems.append(f"第 {expected_number} 个步骤的 step_number 为 "
                        f"{step['step_number']}, 期望 {expected_number}")
    for tile_id in step["tiles_to_add"]:
        if tile_id not in final_set:
            problems.append(f"第 {expected_number} 步引用了不存在的磁力片: {tile_id}")
        elif tile_id in placed:
            problems.append(f"磁力片 {tile_id} 被多个步骤重复放置")
        else:
            placed.add(tile_id)
    cumulative += len(step["tiles_to_add"])
    print(f"  第 {expected_number} 步: +{len(step['tiles_to_add'])} 片, 累计 {cumulative} 片")

missing = final_set - placed
if missing:
    problems.append(f"{len(missing)} 片未被任何步骤放置: {sorted(missing)[:5]} ...")
if cumulative != len(final_ids):
    problems.append(f"步骤累计片数 {cumulative} != final_assembly 数 {len(final_ids)}")
if total_pieces != len(final_ids):
    problems.append(f"total_pieces ({total_pieces}) != final_assembly 数 ({len(final_ids)})")

for p in problems:
    print(f"  [错误] {p}")
sys.exit(1 if problems else 0)
PYEOF
    then
        echo "[失败] $name: 静态步骤走查未通过"
        failures=$((failures + 1))
        continue
    fi

    # ---- 2. 运行时走查: CLI 教程完整跑一遍 ---------------------
    total_pieces="$("$PYTHON" -c "import json,sys; print(json.load(open(sys.argv[1], encoding='utf-8'))['total_pieces'])" "$model")"
    output="$("$APP" tutorial "$model" --data-dir "$DATA_DIR" 2>&1)"
    status=$?
    if [ "$status" -ne 0 ]; then
        echo "$output"
        echo "[失败] $name: magtile_app tutorial 退出码 $status"
        failures=$((failures + 1))
        continue
    fi

    # 末行形如 "教程结束, 共放置 72 片磁力片。"
    reported="$(echo "$output" | tail -n 1 | grep -oE '[0-9]+' | head -n 1)"
    if [ -z "$reported" ] || [ "$reported" -ne "$total_pieces" ]; then
        echo "$output" | tail -n 3
        echo "[失败] $name: 教程引擎最终放置 ${reported:-?} 片, 期望 $total_pieces 片"
        failures=$((failures + 1))
        continue
    fi
    echo "[通过] $name: 教程引擎走完全部步骤, 放置 $reported/$total_pieces 片"
done

echo ""
echo "=============================================================="
if [ "$failures" -gt 0 ]; then
    echo " 结果: ${#models[@]} 个模型中有 $failures 个教程不完整"
    exit 1
fi
echo " 结果: 全部 ${#models[@]} 个模型教程完整"
exit 0

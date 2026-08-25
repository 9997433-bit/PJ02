#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 模型库全量质检
#
# 逐一校验 data/models/ 下的每一个模型 JSON:
#   1. magtile_app validate 必须通过 (物理规则 + 教程步骤一致性);
#   2. 报告每个模型的磁力片数与步骤数;
#   3. 任何模型磁力片总数 < MIN_PIECES (默认 40) 即失败
#      (少于 40 片的模型对用户来说没有搭建价值)。
#
# 用法: test_all_models.sh <magtile_app> <project_source_dir> [min_pieces]
# =============================================================
set -u

if [ "$#" -lt 2 ]; then
    echo "用法: $0 <magtile_app> <project_source_dir> [min_pieces]" >&2
    exit 2
fi

APP="$1"
SRC_DIR="$2"
MIN_PIECES="${3:-40}"
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
echo " 模型库全量质检: 共 ${#models[@]} 个模型, 最低片数要求 $MIN_PIECES"
echo "=============================================================="

failures=0
for model in "${models[@]}"; do
    name="$(basename "$model")"

    # 从 JSON 提取片数与步骤数 (与 C++ 加载器口径一致: 以 final_assembly 为准)
    counts="$("$PYTHON" - "$model" <<'PYEOF'
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    print(len(m["final_assembly"]), len(m["steps"]))
except Exception as e:
    print("ERROR", e, file=sys.stderr)
    sys.exit(1)
PYEOF
)"
    if [ "$?" -ne 0 ]; then
        echo "[失败] $name: JSON 无法解析或缺少必需字段"
        failures=$((failures + 1))
        continue
    fi
    pieces="$(echo "$counts" | awk '{print $1}')"
    steps="$(echo "$counts" | awk '{print $2}')"

    echo ""
    echo "---- $name: $pieces 片, $steps 步 ----"

    if [ "$pieces" -lt "$MIN_PIECES" ]; then
        echo "[失败] $name: 磁力片总数 $pieces < $MIN_PIECES, 模型规模太小不具备搭建价值"
        failures=$((failures + 1))
        continue
    fi

    if ! "$APP" validate "$model" --data-dir "$DATA_DIR"; then
        echo "[失败] $name: magtile_app validate 未通过"
        failures=$((failures + 1))
        continue
    fi
    echo "[通过] $name ($pieces 片 / $steps 步)"
done

echo ""
echo "=============================================================="
if [ "$failures" -gt 0 ]; then
    echo " 结果: ${#models[@]} 个模型中有 $failures 个未通过质检"
    exit 1
fi
echo " 结果: 全部 ${#models[@]} 个模型通过质检"
exit 0

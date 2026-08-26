#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 模型库全量质检
#
# 逐一校验 data/models/ 下的每一个模型 JSON:
#   1. magtile_app validate 必须通过 (物理规则 + 教程步骤一致性);
#   2. 报告每个模型的磁力片数与步骤数;
#   3. 片数下限按难度感知 (CONTENT_STRATEGY.md 2.1/2.4 节):
#      - difficulty=1 (D1 入门档): 下限 20 片 (D1 片数带 [20,28],
#        完整区间校验由 test_model_logic.py 负责);
#      - 其余难度: 下限 MIN_PIECES (默认 40) —— 太小的模型没有搭建价值。
#
# 用法: test_all_models.sh <magtile_app> <project_source_dir> [min_pieces]
#   min_pieces 只作用于非 D1 模型; D1 下限固定为 20 (内容策略权威口径)。
# =============================================================
set -u

if [ "$#" -lt 2 ]; then
    echo "用法: $0 <magtile_app> <project_source_dir> [min_pieces]" >&2
    exit 2
fi

APP="$1"
SRC_DIR="$2"
MIN_PIECES="${3:-40}"
# D1 入门档下限: CONTENT_STRATEGY.md 2.1 节片数带 [20,28] 的下沿
# (2.4 节反幼稚规则: 入门档降低的是操作难度, 不是作品的成品感)。
D1_MIN_PIECES=20
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
echo " 模型库全量质检: 共 ${#models[@]} 个模型"
echo " 最低片数要求: $MIN_PIECES (D1 入门档按 CONTENT_STRATEGY 片数带为 $D1_MIN_PIECES)"
echo "=============================================================="

failures=0
for model in "${models[@]}"; do
    name="$(basename "$model")"

    # 从 JSON 提取片数/步骤数/难度 (与 C++ 加载器口径一致: 以 final_assembly 为准)
    counts="$("$PYTHON" - "$model" <<'PYEOF'
import json, sys
try:
    m = json.load(open(sys.argv[1], encoding="utf-8"))
    difficulty = m.get("difficulty")
    print(len(m["final_assembly"]), len(m["steps"]),
          difficulty if isinstance(difficulty, int) else 0)
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
    difficulty="$(echo "$counts" | awk '{print $3}')"

    echo ""
    echo "---- $name: $pieces 片, $steps 步, 难度 D$difficulty ----"

    # 难度感知片数下限: D1 用内容策略片数带下沿, 其余用全局下限。
    # 难度值本身的合法性 (1~5) 与 D1 片数带上限 (28) 由 test_model_logic.py 把关。
    if [ "$difficulty" = "1" ]; then
        floor="$D1_MIN_PIECES"
    else
        floor="$MIN_PIECES"
    fi
    if [ "$pieces" -lt "$floor" ]; then
        echo "[失败] $name: 磁力片总数 $pieces < $floor (难度 D$difficulty 下限), 模型规模太小不具备搭建价值"
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

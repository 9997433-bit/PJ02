#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 模型退役脚本 (路径 B1 配额置换)
#
# 在 250 上限内净换题: 入库新 D1/D5 前, 从主库移除等量 D3 模型。
# 退役 = 删除 data/models/<id>.json + data/thumbnails/<id>.png (若存在),
# 然后重建 model_catalog.json。
#
# 安全闸 (默认拒绝):
#   - 免费层模型 (starter 清单或 tags 含「免费」) 不可退役
#   - D4/D5 不可退役 (实物复核 / 灯塔内容)
#   - 默认 --dry-run, 须显式 --execute 才真正删除
#
# 用法:
#   tools/retire_models.sh [--dry-run|--execute] <id> [id ...]
#   tools/retire_models.sh [--dry-run|--execute] --file ids.txt
#   tools/retire_models.sh --from-plan [N]   # 取 QUOTA 报告候选序前 N 个
#
# 退出码: 0 成功; 1 校验失败; 2 用法错误
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODELS_DIR="$ROOT/data/models"
THUMBS_DIR="$ROOT/data/thumbnails"
STARTER_FILE="$ROOT/platforms/windows/packaging/starter_models.txt"
PYTHON="${PYTHON:-python3}"
EXECUTE=0
FROM_PLAN=0
PLAN_COUNT=0
ID_FILE=""
IDS=()

usage() { sed -n '2,28p' "$0"; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --execute)   EXECUTE=1; shift ;;
        --dry-run)   EXECUTE=0; shift ;;
        --file)
            [ "$#" -ge 2 ] || { echo "错误: --file 需要路径" >&2; exit 2; }
            ID_FILE="$2"; shift 2 ;;
        --file=*)    ID_FILE="${1#--file=}"; shift ;;
        --from-plan)
            FROM_PLAN=1
            if [ "$#" -ge 2 ] && [[ "$2" =~ ^[0-9]+$ ]]; then
                PLAN_COUNT="$2"; shift 2
            else
                PLAN_COUNT=1; shift
            fi
            ;;
        -h|--help)   usage; exit 0 ;;
        -*)
            echo "错误: 未知选项 $1" >&2; exit 2 ;;
        *)
            IDS+=("$1"); shift ;;
    esac
done

if [ "$FROM_PLAN" -eq 1 ]; then
    [ "$PLAN_COUNT" -ge 1 ] || PLAN_COUNT=1
    RETIRE_ROOT="$ROOT" mapfile -t PLAN_IDS < <(
        RETIRE_ROOT="$ROOT" "$PYTHON" - "$PLAN_COUNT" <<'PY'
import json, os, sys
from pathlib import Path
root = Path(os.environ["RETIRE_ROOT"])
models = root / "data" / "models"
starter = set()
sf = root / "platforms/windows/packaging/starter_models.txt"
if sf.is_file():
    starter = {l.strip() for l in sf.read_text().splitlines() if l.strip()}
excess = {"land_transport","spacecraft","animal_world","sea_air_transport","fantasy_machinery","holiday_seasonal"}
rows = []
for p in sorted(models.glob("*.json")):
    m = json.loads(p.read_text())
    if m.get("difficulty") != 3:
        continue
    mid = m.get("id", p.stem)
    if mid in starter or "免费" in (m.get("tags") or []):
        continue
    meta = m.get("content_meta") or {}
    series = meta.get("series")
    tier = 0 if not series else (1 if series in excess else 2)
    rows.append((tier, -m.get("total_pieces", 0), mid))
rows.sort()
n = int(sys.argv[1])
for _, _, mid in rows[:n]:
    print(mid)
PY
    )
    IDS+=("${PLAN_IDS[@]}")
fi

if [ -n "$ID_FILE" ]; then
    [ -f "$ID_FILE" ] || { echo "错误: 文件不存在: $ID_FILE" >&2; exit 2; }
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%%#*}"
        line="$(echo "$line" | xargs)"
        [ -n "$line" ] && IDS+=("$line")
    done < "$ID_FILE"
fi

if [ "${#IDS[@]}" -eq 0 ]; then
    echo "错误: 未指定模型 id (用法见 --help)" >&2
    exit 2
fi

# 加载 starter
STARTER_IDS=""
if [ -f "$STARTER_FILE" ]; then
    STARTER_IDS="$(tr '\n' ' ' < "$STARTER_FILE")"
fi

fail=0
echo "=============================================================="
echo " 模型退役 (路径 B1 配额置换)"
echo " 模式: $([ "$EXECUTE" -eq 1 ] && echo 'EXECUTE (将删除文件)' || echo 'DRY-RUN (仅预览)')"
echo " 数量: ${#IDS[@]}"
echo "=============================================================="

for mid in "${IDS[@]}"; do
    json="$MODELS_DIR/${mid}.json"
    thumb="$THUMBS_DIR/${mid}.png"
    if [ ! -f "$json" ]; then
        echo "[失败] $mid —— JSON 不存在: $json"
        fail=1
        continue
    fi
    # difficulty + free tier check via python one-liner
    if ! "$PYTHON" - "$json" "$mid" <<'PY'
import json, sys
from pathlib import Path
path, mid = sys.argv[1], sys.argv[2]
root = Path(path).resolve().parents[2]
m = json.loads(Path(path).read_text())
diff = m.get("difficulty")
tags = m.get("tags") or []
starter = set()
sf = root / "platforms/windows/packaging/starter_models.txt"
if sf.is_file():
    starter = {l.strip() for l in sf.read_text().splitlines() if l.strip()}
if mid in starter or "免费" in tags:
    print(f"[失败] {mid} —— 免费层模型不可退役", file=sys.stderr)
    sys.exit(1)
if diff is None or diff >= 4:
    print(f"[失败] {mid} —— 仅允许退役 D3 (当前 difficulty={diff})", file=sys.stderr)
    sys.exit(1)
if diff != 3:
    print(f"[失败] {mid} —— 路径 B1 默认只退役 D3 (当前 D{diff})", file=sys.stderr)
    sys.exit(1)
PY
    then
        fail=1
        continue
    fi
    echo "[OK  ] $mid"
    echo "       - $json"
    [ -f "$thumb" ] && echo "       - $thumb"
    if [ "$EXECUTE" -eq 1 ]; then
        rm -f "$json" "$thumb"
    fi
done

if [ "$fail" -ne 0 ]; then
    echo "校验失败, 未执行退役。" >&2
    exit 1
fi

if [ "$EXECUTE" -eq 1 ]; then
    echo ""
    echo "重建目录..."
    "$PYTHON" "$ROOT/tools/update_model_catalog.py"
    echo ""
    echo "难度配额快照:"
    "$PYTHON" "$ROOT/tools/check_difficulty_quota.py" "$MODELS_DIR" | sed -n '1,14p'
    echo ""
    echo "退役完成: ${#IDS[@]} 个模型。请在同一提交中入库置换新批并跑 review_content_batch.sh。"
else
    echo ""
    echo "DRY-RUN 完成。确认后加 --execute 执行删除。"
    echo "规划报告: docs/reports/QUOTA_SUBSTITUTION_PLAN_2026-08-25.md"
fi

exit 0

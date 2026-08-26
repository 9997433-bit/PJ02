#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 物理夹具注册表完整性关卡
#
# 商用底线: 负例回归套件本身不允许悄悄缩水。负例测试按目录 glob
# 注册, 若有人误删一个夹具, 对应用例只是"消失"而不会变红 ——
# 本关卡把"套件必须完整"固化为一个会 FAIL 的测试:
#
#   1. 必备负例清单 (下方 REQUIRED_NEGATIVE) 每一项都必须存在
#      夹具 JSON + .expected sidecar, 缺任何一个即 FAIL;
#   2. 目录里每个负例 JSON 都必须有 sidecar (声明 expected_fail_rule
#      与合法 severity), 每个 sidecar 也必须有对应 JSON (防孤儿);
#   3. 正例目录 tests/test_physics_positive/ 不允许为空 (负例防
#      "该拒未拒", 正例防 "矫枉过正", 缺一不可)。
#
# 用法: test_physics_fixture_registry.sh <tests_dir>
# =============================================================
set -u

if [ "$#" -ne 1 ]; then
    echo "用法: $0 <tests_dir>" >&2
    exit 2
fi

TESTS_DIR="$1"
NEG_DIR="$TESTS_DIR/test_physics_negative"
POS_DIR="$TESTS_DIR/test_physics_positive"
failures=0

# 必备负例清单: 覆盖 R1~R9 与数据层/中间态的全部关键失效模式。
# 新增负例后请在此登记 (删除任何一行都必须有书面评审理由)。
# jitter_sensitive 为 R9 抖动负例 (sidecar 带 jitter= 键, 以 --jitter 运行)。
REQUIRED_NEGATIVE="
below_ground_tile
cantilever_overload
disconnected_assembly
enclosed_placement
floating_tile
hanging_chain_long
hanging_chain_overload
isolated_tile
jitter_sensitive
midstep_collapse
no_structural_redundancy
overlapping_tiles
single_point_of_failure
unbraced_wall_too_tall
unknown_tile_type
unplaceable_order
unstable_cantilever
"

echo "== 1. 必备负例清单 =="
for name in $REQUIRED_NEGATIVE; do
    if [ ! -f "$NEG_DIR/$name.json" ]; then
        echo "[失败] 必备负例夹具缺失: $NEG_DIR/$name.json"
        failures=$((failures + 1))
    elif [ ! -f "$NEG_DIR/$name.expected" ]; then
        echo "[失败] 必备负例缺少 sidecar: $NEG_DIR/$name.expected"
        failures=$((failures + 1))
    else
        echo "[通过] $name (夹具 + sidecar)"
    fi
done

echo ""
echo "== 2. 目录内夹具与 sidecar 一一对应 =="
for fixture in "$NEG_DIR"/*.json; do
    [ -e "$fixture" ] || continue
    name="$(basename "$fixture" .json)"
    sidecar="${fixture%.json}.expected"
    if [ ! -f "$sidecar" ]; then
        echo "[失败] 负例 $name.json 缺少 sidecar $name.expected"
        failures=$((failures + 1))
        continue
    fi
    rule="$(sed -n 's/^expected_fail_rule=//p' "$sidecar" | head -n 1)"
    severity="$(sed -n 's/^severity=//p' "$sidecar" | head -n 1)"
    if [ -z "$rule" ]; then
        echo "[失败] $name.expected 未声明 expected_fail_rule"
        failures=$((failures + 1))
    fi
    case "$severity" in
        error|warning) ;;
        *)
            echo "[失败] $name.expected 的 severity 非法: '$severity' (须为 error|warning)"
            failures=$((failures + 1))
            ;;
    esac
done
for sidecar in "$NEG_DIR"/*.expected; do
    [ -e "$sidecar" ] || continue
    if [ ! -f "${sidecar%.expected}.json" ]; then
        echo "[失败] 孤儿 sidecar (没有对应夹具 JSON): $sidecar"
        failures=$((failures + 1))
    fi
done
[ "$failures" -eq 0 ] && echo "[通过] 全部夹具与 sidecar 一一对应"

echo ""
echo "== 3. 正例目录非空 =="
positive_count=0
for fixture in "$POS_DIR"/*.json; do
    [ -e "$fixture" ] || continue
    positive_count=$((positive_count + 1))
done
if [ "$positive_count" -eq 0 ]; then
    echo "[失败] 正例目录为空: $POS_DIR (负例防该拒未拒, 正例防矫枉过正, 缺一不可)"
    failures=$((failures + 1))
else
    echo "[通过] 正例夹具 $positive_count 个"
fi

echo ""
if [ "$failures" -ne 0 ]; then
    echo "[失败] 物理夹具注册表存在 $failures 处缺口 —— 负例套件不允许缩水"
    exit 1
fi
echo "[通过] 物理夹具注册表完整"
exit 0

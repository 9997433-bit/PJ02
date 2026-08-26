#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 物理正例测试执行器
#
# 对 tests/test_physics_positive/ 下的正例夹具运行
# magtile_app validate, 断言:
#   1. 退出码为 0 (校验器必须放行该模型);
#   2. 输出中包含 "可发布" 结论 (确认走到了完整校验流程的
#      成功出口, 而不是因参数错误等原因提前返回 0)。
#
# 正例夹具是负例的"对照组": 处于承载预算之内的合法结构,
# 用于防止 R5/R6 等静力规则矫枉过正, 误杀磁力片的常规玩法。
#
# 用法: test_physics_positive.sh <magtile_app> <data_dir> <fixture.json>
# =============================================================
set -u

if [ "$#" -ne 3 ]; then
    echo "用法: $0 <magtile_app> <data_dir> <fixture.json>" >&2
    exit 2
fi

APP="$1"
DATA_DIR="$2"
FIXTURE="$3"

echo "正例夹具: $(basename "$FIXTURE") (期望: 校验通过, 模型可发布)"
echo "--------------------------------------------------------------"

output="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" 2>&1)"
status=$?
echo "$output"
echo "--------------------------------------------------------------"

if [ "$status" -ne 0 ]; then
    echo "[失败] 校验器拒绝了这个物理上完全成立的模型 (退出码 $status)"
    echo "       静力规则可能矫枉过正, 请核对 PhysicsConfig 预算参数与实测值"
    exit 1
fi

if ! echo "$output" | grep -q "可发布"; then
    echo "[失败] 退出码为 0 但输出中没有 \"可发布\" 结论"
    echo "       (可能因参数解析等无关原因提前返回, 属于夹具或代码问题)"
    exit 1
fi

echo "[通过] 校验器放行, 模型可发布 (退出码 0)"
exit 0

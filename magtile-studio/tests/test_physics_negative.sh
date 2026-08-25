#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 物理负例测试执行器
#
# 对 tests/test_physics_negative/ 下的负例夹具运行
# magtile_app validate, 断言:
#   1. 退出码非零 (校验器必须拒绝该模型);
#   2. 输出中包含期望的错误码 (拒绝原因必须正确, 防止因为
#      JSON 解析失败等无关原因"碰巧"返回非零)。
#
# 用法: test_physics_negative.sh <magtile_app> <data_dir> <fixture.json> <expected_error_code>
# =============================================================
set -u

if [ "$#" -ne 4 ]; then
    echo "用法: $0 <magtile_app> <data_dir> <fixture.json> <expected_error_code>" >&2
    exit 2
fi

APP="$1"
DATA_DIR="$2"
FIXTURE="$3"
EXPECTED_CODE="$4"

echo "负例夹具: $(basename "$FIXTURE") (期望错误码: $EXPECTED_CODE)"
echo "--------------------------------------------------------------"

output="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" 2>&1)"
status=$?
echo "$output"
echo "--------------------------------------------------------------"

if [ "$status" -eq 0 ]; then
    echo "[失败] 校验器竟然放行了这个物理上不成立的模型 (退出码 0)"
    exit 1
fi

if ! echo "$output" | grep -q "$EXPECTED_CODE"; then
    echo "[失败] 校验器拒绝了模型, 但输出中没有期望的错误码 $EXPECTED_CODE"
    echo "       (可能因 JSON 解析失败等无关原因返回非零, 属于夹具或代码问题)"
    exit 1
fi

echo "[通过] 校验器以退出码 $status 拒绝, 且报出期望错误码 $EXPECTED_CODE"
exit 0

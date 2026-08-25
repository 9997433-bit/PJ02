#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 物理负例测试执行器
#
# 对 tests/test_physics_negative/ 下的负例夹具运行
# magtile_app validate。每个夹具旁必须放一个同名 .expected
# sidecar 声明期望 (缺 sidecar 即 FAIL, 防止负例悄悄失去断言):
#
#   expected_fail_rule=<grep 正则>   # 输出必须匹配的错误/警告码
#   severity=error|warning           # 期望级别
#
# 断言逻辑:
#   - severity=error:   validate 必须以非零退出码拒绝, 且输出匹配
#     expected_fail_rule (防止因 JSON 解析失败等无关原因"碰巧"非零);
#   - severity=warning: validate 必须以零退出码放行 (Warning 不阻断
#     发布), 且输出必须包含匹配 expected_fail_rule 的 [警告] 行
#     —— 同时锁住"必须报告"与"不得升级为错误"两个方向的回归。
#
# 用法: test_physics_negative.sh <magtile_app> <data_dir> <fixture.json>
# =============================================================
set -u

if [ "$#" -ne 3 ]; then
    echo "用法: $0 <magtile_app> <data_dir> <fixture.json>" >&2
    exit 2
fi

APP="$1"
DATA_DIR="$2"
FIXTURE="$3"
SIDECAR="${FIXTURE%.json}.expected"

if [ ! -f "$FIXTURE" ]; then
    echo "[失败] 负例夹具缺失: $FIXTURE (负例套件不允许缩水)"
    exit 1
fi
if [ ! -f "$SIDECAR" ]; then
    echo "[失败] 负例夹具缺少 .expected sidecar: $SIDECAR"
    echo "       每个负例必须声明 expected_fail_rule 与 severity, 否则断言无从谈起"
    exit 1
fi

EXPECTED_RULE="$(sed -n 's/^expected_fail_rule=//p' "$SIDECAR" | head -n 1)"
SEVERITY="$(sed -n 's/^severity=//p' "$SIDECAR" | head -n 1)"

if [ -z "$EXPECTED_RULE" ]; then
    echo "[失败] sidecar 未声明 expected_fail_rule: $SIDECAR"
    exit 1
fi
case "$SEVERITY" in
    error|warning) ;;
    *)
        echo "[失败] sidecar 的 severity 必须是 error 或 warning (实际: '$SEVERITY'): $SIDECAR"
        exit 1
        ;;
esac

echo "负例夹具: $(basename "$FIXTURE") (期望: $SEVERITY 级, 匹配 '$EXPECTED_RULE')"
echo "--------------------------------------------------------------"

output="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" 2>&1)"
status=$?
echo "$output"
echo "--------------------------------------------------------------"

if [ "$SEVERITY" = "error" ]; then
    if [ "$status" -eq 0 ]; then
        echo "[失败] 校验器竟然放行了这个物理上不成立的模型 (退出码 0)"
        exit 1
    fi
    if ! echo "$output" | grep -q "$EXPECTED_RULE"; then
        echo "[失败] 校验器拒绝了模型, 但输出中没有匹配 '$EXPECTED_RULE' 的内容"
        echo "       (可能因 JSON 解析失败等无关原因返回非零, 属于夹具或代码问题)"
        exit 1
    fi
    echo "[通过] 校验器以退出码 $status 拒绝, 且报出期望错误 '$EXPECTED_RULE'"
    exit 0
fi

# severity=warning: Warning 不阻断发布 —— 必须零退出且输出 [警告] 行
if [ "$status" -ne 0 ]; then
    echo "[失败] warning 级负例被以退出码 $status 拒绝 (Warning 不应阻断发布,"
    echo "       若规则已升级为 Error, 请同步更新 sidecar 的 severity 声明)"
    exit 1
fi
if ! echo "$output" | grep -q "^\[警告\].*$EXPECTED_RULE"; then
    echo "[失败] 校验器放行了模型, 但输出中没有匹配 '$EXPECTED_RULE' 的 [警告] 行"
    echo "       (该报未报 —— 生产校验器出现回归, 或夹具几何被改动)"
    exit 1
fi
echo "[通过] 校验器以退出码 0 放行, 且报出期望警告 '$EXPECTED_RULE'"
exit 0

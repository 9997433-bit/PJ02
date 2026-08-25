#!/usr/bin/env bash
# =============================================================
# MagTile Studio - R9 蒙特卡洛容差抖动 (validate --jitter) 关卡执行器
#
# 抖动仿真对每片放置注入 ±1.5mm 平移 + ±2° 偏航后重跑物理校验,
# 专门捕捉 F08 "微小错位累积坍塌" (BUILD_VERIFICATION.md §4):
# 名义几何压线合法的模型静态校验放行, 但对毫米级放置误差零裕量。
# "该抓不抓" 与 "矫枉过正" 两个方向都必须锁死, 模式由夹具旁是否
# 存在同名 .expected sidecar 决定:
#
#   有 sidecar (抖动负例, 零裕量边缘设计):
#     1. 普通 validate 必须放行 (夹具前提是 "静态校验抓不住"; 若名义
#        模型都被拒, 夹具已退化成普通负例, 不再考核 R9 的增量检出);
#     2. validate --jitter 必须以非零退出码拒绝, 且输出匹配 sidecar
#        声明的 expected_fail_rule (placement_jitter_failure)。
#
#   无 sidecar (抖动正例 / 裕量充足的稳定模型):
#     validate --jitter 必须放行 (退出码 0), 且输出 "[通过] 蒙特卡洛
#     抖动仿真" 的 N/N 轮全绿行 (确认抖动真的跑了, 不是被悄悄跳过)
#     与 "可发布" 结论 —— 防止抖动关卡矫枉过正误杀常规玩法。
#
# 轮数用 CLI 默认值 (--jitter 省略数值 = 50 轮, 固定随机种子, CI
# 逐次可复现)。二进制不支持 --jitter 时按失败处理并打印指引 (旧版
# 把 --jitter 当未知参数拒绝: 退出码 2 + 用法文本里没有 --jitter)。
#
# 用法: test_physics_jitter.sh <magtile_app> <data_dir> <fixture.json>
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
    echo "[失败] 抖动夹具缺失: $FIXTURE (R9 关卡不允许缩水)"
    exit 1
fi

MODE="stable"
EXPECTED_RULE=""
if [ -f "$SIDECAR" ]; then
    MODE="sensitive"
    EXPECTED_RULE="$(sed -n 's/^expected_fail_rule=//p' "$SIDECAR" | head -n 1)"
    SEVERITY="$(sed -n 's/^severity=//p' "$SIDECAR" | head -n 1)"
    if [ -z "$EXPECTED_RULE" ]; then
        echo "[失败] sidecar 未声明 expected_fail_rule: $SIDECAR"
        exit 1
    fi
    if [ "$SEVERITY" != "error" ]; then
        echo "[失败] 抖动负例的 severity 必须是 error (实际: '$SEVERITY'): $SIDECAR"
        echo "       (placement_jitter_failure 是 Error 级汇总, 不存在 warning 级抖动负例)"
        exit 1
    fi
fi

echo "抖动夹具: $(basename "$FIXTURE") (模式: $MODE)"
echo "--------------------------------------------------------------"

jitter_output="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" --jitter 2>&1)"
jitter_status=$?
echo "$jitter_output"
echo "--------------------------------------------------------------"

# 旧版二进制把 --jitter 当多余位置参数: 解析失败 (退出码 2 + 用法),
# 且其用法文本不含 --jitter 字样 —— 与新版二进制的真实参数错误区分开。
if [ "$jitter_status" -eq 2 ] && echo "$jitter_output" | grep -q "用法" \
        && ! echo "$jitter_output" | grep -q -- "--jitter"; then
    echo "[失败] 该 magtile_app 不支持 validate --jitter (R9 特性缺失)"
    echo "       请先重新构建包含 R9 抖动仿真的 magtile_app"
    exit 1
fi

if [ "$MODE" = "stable" ]; then
    if [ "$jitter_status" -ne 0 ]; then
        echo "[失败] 抖动仿真拒绝了这个裕量充足的稳定模型 (退出码 $jitter_status)"
        echo "       R9 可能矫枉过正 (或注入幅度/容差补偿被改动), 请核对 JitterConfig"
        exit 1
    fi
    if ! echo "$jitter_output" | grep -q "\[通过\] 蒙特卡洛抖动仿真"; then
        echo "[失败] 退出码为 0 但没有 \"[通过] 蒙特卡洛抖动仿真\" 行"
        echo "       (抖动仿真可能根本没跑, 稳定性结论无从谈起)"
        exit 1
    fi
    if ! echo "$jitter_output" | grep -q "轮全部通过"; then
        echo "[失败] 没有 \"N/N 轮全部通过\" 字样, 无法确认全部轮次都执行并通过"
        exit 1
    fi
    if ! echo "$jitter_output" | grep -q "可发布"; then
        echo "[失败] 抖动全绿但输出中没有 \"可发布\" 结论"
        exit 1
    fi
    echo "[通过] 稳定夹具抖动仿真全绿, 模型可发布"
    exit 0
fi

# ---- 抖动负例 (sidecar 模式) ----------------------------------------
base_output="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" 2>&1)"
base_status=$?
if [ "$base_status" -ne 0 ] || ! echo "$base_output" | grep -q "可发布"; then
    echo "$base_output"
    echo "--------------------------------------------------------------"
    echo "[失败] 抖动负例的名义几何没有通过普通 validate (退出码 $base_status)"
    echo "       夹具前提被破坏: 它必须 \"静态校验放行、抖动仿真拒绝\","
    echo "       否则测的只是普通负例而不是 R9 的增量检出能力"
    exit 1
fi
echo "(前提成立: 名义模型普通 validate 放行)"

if [ "$jitter_status" -eq 0 ]; then
    echo "[失败] 抖动仿真竟然放行了这个零裕量模型 (退出码 0)"
    echo "       R9 出现 \"该抓不抓\" 回归: F08 误差累积失稳兜不住了"
    exit 1
fi
if echo "$jitter_output" | grep -q "跳过蒙特卡洛抖动仿真"; then
    echo "[失败] 抖动仿真被跳过 (基础校验未通过?), 拒绝原因不是 R9 本身"
    exit 1
fi
if ! echo "$jitter_output" | grep -q "$EXPECTED_RULE"; then
    echo "[失败] 抖动仿真拒绝了模型, 但输出中没有匹配 '$EXPECTED_RULE' 的内容"
    echo "       (可能因无关原因非零退出, 属于夹具或代码问题)"
    exit 1
fi
echo "[通过] 零裕量夹具名义放行、抖动仿真以退出码 $jitter_status 拒绝 ('$EXPECTED_RULE')"
exit 0

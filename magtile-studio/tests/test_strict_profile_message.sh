#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 档位参数文案回归 (2026-08-25 strict 巡检回填)
#
# 背景: 全库 strict 物理巡检发现 R5 悬挂链超重 (hanging_chain_overload)
# 的错误文案把抗碰撞安全系数硬编码为 "80%", 而 --profile strict 实际
# 生效的是 70% (knock_safety_factor = 0.7)。预算计算本身正确 (84g =
# 120 x 0.7), 但文案误导内容作者按 80% 反推预算, 属引擎文案 bug。
#
# 本测试锁死修复: 对同一个悬挂超重负例夹具分别以 default / strict
# 档运行 validate, 断言:
#   1. 两档均以非零退出码拒绝, 且报出 hanging_chain_overload;
#   2. default 档文案标注 "x 80% 抗碰撞裕量" (0.8);
#   3. strict  档文案标注 "x 70% 抗碰撞裕量" (0.7), 不得再出现 80%。
#
# 用法: test_strict_profile_message.sh <magtile_app> <data_dir> <fixture.json>
# =============================================================
set -u

if [ "$#" -ne 3 ]; then
    echo "用法: $0 <magtile_app> <data_dir> <fixture.json>" >&2
    exit 2
fi

APP="$1"
DATA_DIR="$2"
FIXTURE="$3"

fail=0

check_profile() {
    # $1 = 档位名, $2 = 期望的安全系数百分比文案
    local profile="$1" expected_pct="$2"
    local output status
    output="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" --profile "$profile" 2>&1)"
    status=$?

    echo "---- 档位 $profile (期望文案: x ${expected_pct} 抗碰撞裕量) ----"
    printf '%s\n' "$output" | grep -F 'hanging_chain_overload' || true

    if [ "$status" -eq 0 ]; then
        echo "[失败] $profile 档竟然放行了悬挂超重夹具 (退出码 0)"
        fail=1
        return
    fi
    if ! printf '%s\n' "$output" | grep -q 'hanging_chain_overload'; then
        echo "[失败] $profile 档拒绝了模型, 但没有报出 hanging_chain_overload"
        fail=1
        return
    fi
    local msg_lines
    msg_lines="$(printf '%s\n' "$output" | grep -F 'hanging_chain_overload')"
    if ! printf '%s\n' "$msg_lines" | grep -qF "x ${expected_pct} 抗碰撞裕量"; then
        echo "[失败] $profile 档的悬挂超重文案未标注 'x ${expected_pct} 抗碰撞裕量'"
        echo "       (安全系数文案必须跟随实际生效的 knock_safety_factor, 不得硬编码)"
        fail=1
        return
    fi
    echo "[通过] $profile 档拒绝且安全系数文案正确 (${expected_pct})"
}

check_profile default "80%"
check_profile strict "70%"

# strict 档文案中残留 80% 即为硬编码回归
strict_msgs="$("$APP" validate "$FIXTURE" --data-dir "$DATA_DIR" --profile strict 2>&1 \
    | grep -F 'hanging_chain_overload')"
if printf '%s\n' "$strict_msgs" | grep -qF '80%'; then
    echo "[失败] strict 档悬挂超重文案中残留 80% (硬编码回归)"
    fail=1
fi

if [ "$fail" -ne 0 ]; then
    echo "结论: 档位参数文案回归失败"
    exit 1
fi
echo "结论: default/strict 双档均正确拒绝, 且安全系数文案与档位参数一致"
exit 0

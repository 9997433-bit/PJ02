#!/usr/bin/env bash
# =============================================================
# MagTile Studio - 步骤朗读开关 CLI 测试 (ctest: settings_tts_cli)
#
# 覆盖 settings set-tts / show 对 "tts_enabled" 设置键
# (progress/ui_settings, 与图形版教程页眉开关 / Qt 版设置页同一
# 持久化契约) 的读写:
#   1. 全新存档 settings show: 朗读默认开 (UI_UX_SPEC.md §4.2);
#   2. set-tts off -> show 回读 "关" (跨进程持久化);
#   3. set-tts on 恢复 "开"; 数字别名 0/1 同样接受;
#   4. 非法开关值必须以退出码 2 拒绝且不改动存档;
#   5. 终端教程 --tts 在总开关关闭时静音降级 (总开关全局生效)。
#
# 用法:
#   tests/test_settings_tts_cli.sh <magtile_app 路径> <项目根>
# =============================================================
set -u

APP="${1:?用法: test_settings_tts_cli.sh <magtile_app> <项目根>}"
ROOT="${2:?用法: test_settings_tts_cli.sh <magtile_app> <项目根>}"
DATA_DIR="$ROOT/data"
MODEL="$DATA_DIR/models/castle_foundation_01.json"
WORK_DIR="$(mktemp -d /tmp/magtile_settings_tts_XXXXXX)"
DB="$WORK_DIR/progress.db"

failures=0
pass() { printf '[通过] %s\n' "$1"; }
fail() { printf '[失败] %s\n' "$1" >&2; failures=$((failures + 1)); }
cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT

if [[ ! -x "$APP" ]]; then
    fail "找不到可执行文件 $APP"
    exit 1
fi

# ---- 1. 全新存档: 朗读默认开 ---------------------------------------
output="$("$APP" settings show --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "步骤朗读: 开" <<<"$output"; then
    pass "全新存档 settings show 朗读默认开"
else
    fail "全新存档朗读开关不是默认开"
    printf '%s\n' "$output" >&2
fi

# ---- 2. set-tts off -> 新进程 show 回读 "关" ------------------------
output="$("$APP" settings set-tts off --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "已关闭" <<<"$output"; then
    pass "set-tts off 正常退出并回显已关闭"
else
    fail "set-tts off 行为异常"
    printf '%s\n' "$output" >&2
fi
if "$APP" settings show --db "$DB" 2>&1 | grep -q "步骤朗读: 关"; then
    pass "关闭状态跨进程持久化 (show 回读 \"关\")"
else
    fail "set-tts off 未持久化"
fi

# ---- 3. set-tts on / 数字别名 1|0 ----------------------------------
"$APP" settings set-tts on --db "$DB" >/dev/null 2>&1
if "$APP" settings show --db "$DB" 2>&1 | grep -q "步骤朗读: 开"; then
    pass "set-tts on 恢复开启"
else
    fail "set-tts on 未生效"
fi
"$APP" settings set-tts 0 --db "$DB" >/dev/null 2>&1
if "$APP" settings show --db "$DB" 2>&1 | grep -q "步骤朗读: 关"; then
    pass "数字别名 0 等价 off"
else
    fail "set-tts 0 未生效"
fi
"$APP" settings set-tts 1 --db "$DB" >/dev/null 2>&1
if "$APP" settings show --db "$DB" 2>&1 | grep -q "步骤朗读: 开"; then
    pass "数字别名 1 等价 on"
else
    fail "set-tts 1 未生效"
fi

# ---- 4. 非法开关值: 退出码 2 且不改动存档 ---------------------------
"$APP" settings set-tts maybe --db "$DB" >/dev/null 2>&1
if [[ $? -eq 2 ]]; then
    pass "非法开关值以退出码 2 拒绝"
else
    fail "非法开关值未被拒绝 (期望退出码 2)"
fi
if "$APP" settings show --db "$DB" 2>&1 | grep -q "步骤朗读: 开"; then
    pass "非法输入不改动存档 (仍为开)"
else
    fail "非法输入毒化了朗读开关"
fi

# ---- 5. 总开关全局生效: 终端教程 --tts 在关闭时静音降级 --------------
"$APP" settings set-tts off --db "$DB" >/dev/null 2>&1
output="$("$APP" tutorial "$MODEL" --data-dir "$DATA_DIR" --tts --db "$DB" 2>&1)"
if [[ $? -eq 0 ]] && grep -q "朗读总开关已关闭" <<<"$output"; then
    pass "终端教程 --tts 在总开关关闭时静音降级并温和提示"
else
    fail "终端教程 --tts 未遵守朗读总开关"
    printf '%s\n' "$output" | head -5 >&2
fi

echo
if [[ "$failures" -eq 0 ]]; then
    echo "步骤朗读开关 CLI 测试全部通过"
    exit 0
fi
echo "步骤朗读开关 CLI 测试失败: $failures 项未通过" >&2
exit 1

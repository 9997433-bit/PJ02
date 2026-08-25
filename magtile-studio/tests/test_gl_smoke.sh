#!/usr/bin/env bash
# =============================================================
# MagTile Studio - OpenGL 渲染后端冒烟测试
#
# 检查项:
#   1. magtile_app 可执行文件存在;
#   2. 用法输出中包含 --dev-gui 选项;
#   3. 图形模式可无头运行: 优先 xvfb-run, 其次现有 DISPLAY;
#      渲染 5 帧并保存 PPM 截图, 校验截图尺寸与内容非纯色;
#   4. 两者都不可用时退化为链接检查: --dev-gui 退出码不为 2
#      (2 = 构建未包含渲染后端)。
#
# 用法:
#   tests/test_gl_smoke.sh [构建目录]        # 默认 build
#   MAGTILE_APP=path/to/magtile_app tests/test_gl_smoke.sh
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="${1:-$ROOT/build}"
APP="${MAGTILE_APP:-$BUILD_DIR/magtile_app}"
MODEL="$ROOT/data/models/castle_foundation_01.json"
DATA_DIR="$ROOT/data"
SHOT="$(mktemp -u /tmp/magtile_gl_smoke_XXXXXX.ppm)"
FRAMES=5

failures=0
pass() { printf '[通过] %s\n' "$1"; }
fail() { printf '[失败] %s\n' "$1" >&2; failures=$((failures + 1)); }

# ---- 1. 可执行文件 ----------------------------------------------
if [[ -x "$APP" ]]; then
    pass "可执行文件存在: $APP"
else
    fail "找不到可执行文件 $APP (先构建: cmake -S . -B build && cmake --build build -j)"
    exit 1
fi

# ---- 2. 用法输出包含 --dev-gui --------------------------------------
usage_output="$("$APP" 2>&1 || true)"
if grep -q -- '--dev-gui' <<<"$usage_output"; then
    pass "用法输出包含 --dev-gui 选项"
else
    fail "用法输出未提及 --dev-gui"
fi

# ---- 2b. 退役别名 --gui 一期保留: 仍被解析且打温和迁移提示 ----------
# 提示在参数解析后、进入图形路径前输出, 无显示环境下窗口打开失败
# 也不影响本检查 (只看提示文本, 不看退出码)。
alias_output="$("$APP" library --data-dir "$DATA_DIR" --gui --frames 1 2>&1 || true)"
if grep -q -- '已更名为 --dev-gui' <<<"$alias_output"; then
    pass "退役别名 --gui 仍可用且输出温和迁移提示"
else
    fail "退役别名 --gui 未输出迁移提示 (期望包含 '已更名为 --dev-gui')"
fi
if grep -q '用法:' <<<"$alias_output"; then
    fail "退役别名 --gui 未被解析 (落入用法输出)"
else
    pass "退役别名 --gui 仍被正常解析 (未落入用法输出)"
fi

# ---- 3. 无头图形渲染 --------------------------------------------
run_gui() {
    # $@ = 前缀命令 (如 xvfb-run -a), 可为空
    "$@" "$APP" tutorial "$MODEL" --data-dir "$DATA_DIR" \
        --dev-gui --frames "$FRAMES" --screenshot "$SHOT"
}

check_screenshot() {
    if [[ ! -s "$SHOT" ]]; then
        fail "未生成截图 $SHOT"
        return
    fi
    local header
    header="$(head -c 32 "$SHOT" | head -n 2 | tr '\n' ' ')"
    if [[ "$header" != P6\ * ]]; then
        fail "截图不是 PPM (P6) 格式: $header"
        return
    fi
    pass "截图已生成: $SHOT ($header)"
    # 内容非纯色: 采样末尾 256KB, 至少出现 2 种字节值
    local distinct
    distinct="$(tail -c 262144 "$SHOT" | od -An -v -tx1 | tr ' ' '\n' | sort -u | grep -c . || true)"
    if [[ "$distinct" -ge 2 ]]; then
        pass "截图内容非纯色 (采样到 $distinct 种字节值)"
    else
        fail "截图疑似纯色/空白 (采样仅 $distinct 种字节值)"
    fi
}

TIMEOUT_CMD=()
command -v timeout >/dev/null 2>&1 && TIMEOUT_CMD=(timeout 120)

gui_exit=-1
if command -v xvfb-run >/dev/null 2>&1; then
    echo "[信息] 使用 xvfb-run 无头渲染 $FRAMES 帧..."
    "${TIMEOUT_CMD[@]}" xvfb-run -a -s "-screen 0 1600x1000x24" \
        "$APP" tutorial "$MODEL" --data-dir "$DATA_DIR" \
        --dev-gui --frames "$FRAMES" --screenshot "$SHOT"
    gui_exit=$?
elif [[ -n "${DISPLAY:-}" ]]; then
    echo "[信息] 使用现有 DISPLAY=$DISPLAY 渲染 $FRAMES 帧..."
    "${TIMEOUT_CMD[@]}" "$APP" tutorial "$MODEL" --data-dir "$DATA_DIR" \
        --dev-gui --frames "$FRAMES" --screenshot "$SHOT"
    gui_exit=$?
fi

if [[ "$gui_exit" -eq 0 ]]; then
    pass "图形模式渲染 $FRAMES 帧后正常退出"
    check_screenshot
elif [[ "$gui_exit" -gt 0 ]]; then
    fail "图形模式退出码 $gui_exit (期望 0)"
else
    # ---- 4. 退化: 仅验证渲染后端已链接 --------------------------
    echo "[信息] 无 xvfb-run 也无 DISPLAY, 退化为链接检查..."
    "$APP" tutorial "$MODEL" --data-dir "$DATA_DIR" --dev-gui --frames 1 \
        >/dev/null 2>&1
    link_exit=$?
    if [[ "$link_exit" -eq 2 ]]; then
        fail "构建未包含渲染后端 (--dev-gui 退出码 2); 请以 -DMAGTILE_BUILD_GL_RENDERER=ON 构建"
    else
        pass "渲染后端已链接 (--dev-gui 退出码 $link_exit, 非 2; 本机无显示环境, 跳过实际渲染)"
    fi
fi

rm -f "$SHOT"

echo
if [[ "$failures" -eq 0 ]]; then
    echo "冒烟测试通过"
    exit 0
fi
echo "冒烟测试失败: $failures 项未通过" >&2
exit 1

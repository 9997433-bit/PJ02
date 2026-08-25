#!/usr/bin/env bash
# =============================================================
# MagTile Studio — LGPL 合规自动核对 (V1 清单 D6; 对照
# scripts/package_qt_desktop.md 第八节, 逐项编号 §8-1 ~ §8-8)
#
# 对"出包产物" (TGZ 或解包目录) 自动断言第八节的可自动化项:
#   §8-1 仅动态链接: DT_NEEDED 含 libQt6*.so + ldd 全为共享库且
#        无 not found + 二进制动态符号表零 Qt 定义符号 (静态吸入检测)
#   §8-2 仅 LGPL 模块: 直接链接 ⊆ {Core,Gui,Qml,Quick,QuickControls2,
#        OpenGL,TextToSpeech} + QML 运行时随链 {QmlModels,Network}
#        (qt_add_qml_module/Quick 自动拉入, 同为 Essentials/LGPLv3);
#        传递闭包再放行 Essentials 白名单 (QuickTemplates2/
#        QmlWorkerScript/QmlMeta/DBus)。白名单外任何 Qt 库 (如
#        GPL-only 的 Charts/DataVisualization) 当场失败 —— 扩白名单
#        必须先过许可核对。
#   §8-4 随包许可声明 (LGPL 必备文件清单): licenses/
#        THIRD_PARTY_NOTICES.md (含 Qt+LGPL 条目) + licenses/
#        License.rtf + README.md 必须在包内。
#
# "正式发布前追加"项默认报 WARN 不算失败 (冒烟档保持绿, 缺口在
# 手册第十节待办登记), --release 档提升为硬性失败 (出正式包前必跑):
#   §8-4 追加: licenses/ 内 LGPLv3 + GPLv3 许可全文副本
#   §8-6:      THIRD_PARTY_NOTICES.md 注明 Qt 精确版本 (6.x.y) 与
#              官方源码地址 (download.qt.io)
#
# 不可自动化项打印 [--] 提示, 出包时对照手册第八节人工打钩:
#   §8-3 未修改 Qt 源码 / §8-5 可替换性 (LGPLv3 §4(d)) /
#   §8-7 界面署名 / §8-8 法务终审
#
# 用法 (仓库根目录; Linux, 需 binutils 的 readelf/nm + ldd):
#   bash scripts/check_lgpl_compliance.sh <包.tar.gz | 解包目录> [--release]
# 例:
#   bash scripts/check_lgpl_compliance.sh build-pack/MagTileStudio-0.1.0-Linux.tar.gz
# 退出码: 0 = 自动化项全过 (冒烟档 WARN 不算失败); 非 0 = 有失败。
# Linux 冒烟已挂接: scripts/smoke_qt_linux_pack.sh 第 6 步对解包产物
# 调用本脚本。macOS 侧动态链接核验用 otool -L (见手册 §8/§12),
# Windows 侧核验包内 Qt6*.dll (smoke_qt_windows.ps1 清单断言)。
# =============================================================
set -euo pipefail

usage() {
    echo "用法: bash scripts/check_lgpl_compliance.sh <包.tar.gz | 解包目录> [--release]"
    echo "  --release  发布档: 把'发布前追加'项 (LGPLv3/GPLv3 全文、精确版本+源码地址)"
    echo "             从 WARN 提升为硬性失败"
}

TARGET="${1:-}"
MODE="smoke"
if [[ "${2:-}" == "--release" ]]; then MODE="release"; fi
if [[ -z "$TARGET" || "$TARGET" == "-h" || "$TARGET" == "--help" ]]; then
    usage; exit 2
fi

PASS=0; FAIL=0; WARN=0
ok()   { echo "  [OK] $*"; PASS=$((PASS+1)); }
bad()  { echo "  [!!] $*"; FAIL=$((FAIL+1)); }
manual() { echo "  [--] 人工项 $*"; }
# 发布前追加项: 冒烟档 WARN (不算失败, 缺口见手册第十节), 发布档硬性失败
gap() {
    if [[ "$MODE" == "release" ]]; then
        bad "$* (--release 档为硬性项)"
    else
        echo "  [~~] WARN: $* (发布前必备, 冒烟档不算失败; --release 档会失败)"
        WARN=$((WARN+1))
    fi
}

for tool in readelf nm ldd tar; do
    command -v "$tool" >/dev/null || { echo "缺少工具 $tool (binutils/tar)"; exit 2; }
done

# ---- 定位产物根目录 (TGZ 先解包到临时目录) ------------------------
TMP=""
trap '[[ -n "$TMP" ]] && rm -rf "$TMP"' EXIT
if [[ -f "$TARGET" ]]; then
    TMP="$(mktemp -d)"
    tar xzf "$TARGET" -C "$TMP"
    ROOT="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
    [[ -n "$ROOT" ]] || { echo "TGZ 内无顶层目录: $TARGET"; exit 2; }
elif [[ -d "$TARGET" ]]; then
    ROOT="${TARGET%/}"
else
    echo "目标不存在: $TARGET"; usage; exit 2
fi

BIN="$ROOT/magtile_studio_qt"
echo "LGPL 合规自动核对 (${MODE} 档) — 产物: $TARGET"
[[ -f "$BIN" ]] || { echo "  [!!] 包内无 magtile_studio_qt (Qt 壳未随包, 本核对不适用)"; exit 1; }

# ---- §8-1 仅动态链接 (非静态链) -----------------------------------
NEEDED_QT="$(readelf -d "$BIN" | sed -n 's/.*(NEEDED).*\[\(libQt6[^]]*\)\].*/\1/p')"
if [[ -n "$NEEDED_QT" ]] && ! grep -vqE '\.so(\.[0-9]+)*$' <<<"$NEEDED_QT"; then
    ok "§8-1 DT_NEEDED 声明 $(grep -c . <<<"$NEEDED_QT") 个 libQt6*.so 动态依赖"
else
    bad "§8-1 DT_NEEDED 无 libQt6*.so 动态依赖 (Qt 被静态吸入或未链接)"
fi

LDD_QT="$(ldd "$BIN" | grep -iE 'libqt' || true)"
if [[ -z "$LDD_QT" ]]; then
    bad "§8-1 ldd 未见任何 Qt 库"
elif grep -q 'not found' <<<"$LDD_QT"; then
    bad "§8-1 ldd 有 Qt 库解析失败 (not found): $(grep 'not found' <<<"$LDD_QT" | head -3 | tr '\n' ' ')"
elif grep -vqE '\.so' <<<"$LDD_QT"; then
    bad "§8-1 ldd 中存在非 .so 的 Qt 条目"
else
    ok "§8-1 ldd 传递闭包 $(grep -c . <<<"$LDD_QT") 个 Qt 库全部为 .so 共享库"
fi

# 静态吸入检测: Qt 代码若被静态链入, 二进制会自带 Qt 类定义符号
# (_ZN7QObject.../_ZTV7QObject... 等 mangled 名; libQt6Core 数千命中,
# 干净的应用二进制应为零命中)
STATIC_QT="$(nm -D --defined-only "$BIN" 2>/dev/null \
    | grep -cE '_Z[A-Z]{0,3}[0-9]+Q[A-Z]|qt_version_tag' || true)"
if [[ "$STATIC_QT" -eq 0 ]]; then
    ok "§8-1 动态符号表零 Qt 定义符号 (无静态吸入)"
else
    bad "§8-1 二进制自带 $STATIC_QT 个 Qt 定义符号 (疑似静态链接了 Qt 代码)"
fi

# ---- §8-2 仅 LGPL 模块 (白名单) -----------------------------------
# 直接链接口径 = 手册 §8-2: Core/Gui/Qml/Quick/QuickControls2/OpenGL
# + 可选 TextToSpeech, 另加 qt_add_qml_module/Quick 自动随链的 QML
# 运行时库 QmlModels/Network (全部 Essentials/LGPLv3)
DIRECT_ALLOWED="Core Gui Qml Quick QuickControls2 OpenGL TextToSpeech QmlModels Network"
# 传递闭包额外放行的 Essentials/LGPLv3 依赖 (上述模块自身拉进来的):
TRANSITIVE_ALLOWED="$DIRECT_ALLOWED QuickTemplates2 QmlWorkerScript QmlMeta DBus"

check_whitelist() {  # check_whitelist <库名列表> <白名单> <标签>
    local libs="$1" allowed="$2" label="$3" bad_mods="" lib mod
    while IFS= read -r lib; do
        [[ -n "$lib" ]] || continue
        mod="$(sed -n 's/^libQt6\([A-Za-z0-9]*\)\.so.*/\1/p' <<<"$lib")"
        [[ -n "$mod" ]] || continue
        if ! grep -qw "$mod" <<<"$allowed"; then bad_mods="$bad_mods $mod"; fi
    done <<<"$libs"
    if [[ -z "$bad_mods" ]]; then
        ok "§8-2 $label 全部在 LGPL 白名单内"
    else
        bad "§8-2 $label 出现白名单外 Qt 模块:$bad_mods (先核对许可再扩白名单; Charts/DataVisualization 等 Add-on 是 GPL-only)"
    fi
}
check_whitelist "$NEEDED_QT" "$DIRECT_ALLOWED" \
    "直接链接 ($(grep -c . <<<"$NEEDED_QT") 个: $(tr '\n' ' ' <<<"$NEEDED_QT" | sed 's/libQt6//g; s/\.so\.[0-9]*//g'))"
LDD_QT_LIBS="$(awk '{print $1}' <<<"$LDD_QT")"
check_whitelist "$LDD_QT_LIBS" "$TRANSITIVE_ALLOWED" "传递闭包 ($(grep -c . <<<"$LDD_QT_LIBS") 个)"

# ---- §8-4 随包许可声明 (LGPL 必备文件清单) -------------------------
for f in licenses/THIRD_PARTY_NOTICES.md licenses/License.rtf README.md; do
    [[ -f "$ROOT/$f" ]] && ok "§8-4 $f 在包内" || bad "§8-4 缺 $f"
done
NOTICES="$ROOT/licenses/THIRD_PARTY_NOTICES.md"
if [[ -f "$NOTICES" ]]; then
    if grep -qi 'Qt' "$NOTICES" && grep -qi 'LGPL' "$NOTICES"; then
        ok "§8-4 THIRD_PARTY_NOTICES.md 含 Qt + LGPL 条目"
    else
        bad "§8-4 THIRD_PARTY_NOTICES.md 缺 Qt/LGPL 条目"
    fi
    # §8-6 源码获取途径: 精确版本 + 官方源码地址 (发布前追加项)
    if grep -qE 'Qt[^0-9]*6\.[0-9]+\.[0-9]+' "$NOTICES" \
            && grep -q 'download\.qt\.io' "$NOTICES"; then
        ok "§8-6 THIRD_PARTY_NOTICES.md 已注明 Qt 精确版本与 download.qt.io 源码地址"
    else
        gap "§8-6 THIRD_PARTY_NOTICES.md 未注明随包 Qt 精确版本 (6.x.y) 与 download.qt.io 源码地址"
    fi
fi
# §8-4 追加项: LGPLv3 + GPLv3 许可全文副本 (LGPLv3 是 GPLv3 的补充
# 条款, 两份都要带; 手册第十节待办)
LIC_DIR="$ROOT/licenses"
if ls "$LIC_DIR" 2>/dev/null | grep -qiE 'lgpl'; then
    ok "§8-4 licenses/ 含 LGPLv3 许可全文"
else
    gap "§8-4 licenses/ 缺 LGPLv3 许可全文副本"
fi
if ls "$LIC_DIR" 2>/dev/null | grep -iE 'gpl' | grep -vqiE 'lgpl'; then
    ok "§8-4 licenses/ 含 GPLv3 许可全文"
else
    gap "§8-4 licenses/ 缺 GPLv3 许可全文副本"
fi

# ---- 不可自动化项 (出包时对照手册第八节人工打钩) -------------------
manual "§8-3 未修改 Qt 源码 (官方二进制发行; 自编译打补丁须随包公开源码修改)"
manual "§8-5 可替换性 LGPLv3 §4(d) (不得校验 Qt 库指纹拒启动; 商店渠道沙箱影响须法务评估)"
manual "§8-7 界面署名 (家长中心「关于」页: 基于 Qt (qt.io), LGPLv3)"
manual "§8-8 法务终审 (走 LGPL 合规或改购 Qt 商业许可)"

echo
echo "LGPL 自动核对结果: $PASS 项通过, $FAIL 项失败, $WARN 项 WARN (${MODE} 档)"
if [[ "$FAIL" -gt 0 ]]; then
    echo "存在失败项: 任何一项做不到, 停发并走法务评估 (手册第八节)"
    exit 1
fi
if [[ "$WARN" -gt 0 && "$MODE" == "smoke" ]]; then
    echo "WARN 为发布前追加项缺口 (手册第十节待办); 出正式包前用 --release 档把关"
fi

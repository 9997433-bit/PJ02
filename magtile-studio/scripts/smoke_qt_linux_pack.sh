#!/usr/bin/env bash
# =============================================================
# MagTile Studio — Linux 打包冒烟 (QT-6, 无 Windows 机器时的替身验证)
#
# 自动化 scripts/package_qt_desktop.md 第九节的手动流程, 并追加
# NSIS 安装器脚本生成冒烟 (装有 makensis 时), 一次跑完:
#   1) 并存包 TGZ: 双主程序 + data 全库 + licenses + README 清单断言
#   2) NSIS 冒烟: cpack -G NSIS 走完 CPackWindows.cmake 的快捷方式/
#      安装规则并通过 makensis 编译 (产物装的是 Linux 二进制, 仅验
#      脚本能过编译, 不可分发)
#   3) Qt-only 包 TGZ: 无 magtile_app, 包名 -qt 后缀
#   4) starter 子集 TGZ: data/models 恰 30 个 + model_catalog 同步过滤
#   5) 解包实测: offscreen 启动吃包内 data/ (系统 Qt 运行)
#   6) LGPL 动态链接核验: ldd 中 Qt 全部为共享库 (手册第八节第一项)
#
# 用法 (仓库根目录):  bash scripts/smoke_qt_linux_pack.sh [构建目录]
#   构建目录默认 build-pack; 脚本会反复重配置该目录的打包开关,
#   结束时恢复为 "并存 + full" 档。需要系统 Qt >= 6.4 (apt 清单见
#   docs/QT_UI_PLAN.md §3.1); 无 makensis 时跳过 NSIS 档并提示。
#
# windeployqt 无法在 Linux 运行 (Windows 专用工具), Windows 实机
# 冒烟请在构建机上跑 scripts/smoke_qt_windows.ps1。
# =============================================================
set -euo pipefail

cd "$(dirname "$0")/.."
BUILD_DIR="${1:-build-pack}"
PASS=0; FAIL=0

ok()  { echo "  [OK] $*"; PASS=$((PASS+1)); }
bad() { echo "  [!!] $*"; FAIL=$((FAIL+1)); }
step() { echo; echo "==> $*"; }

# TGZ 清单断言: assert_tgz <tgz> <形态 coexist|qtonly> <期望模型数; 0=只要求非空>
assert_tgz() {
    local tgz="$1" form="$2" want_models="$3"
    local list; list="$(tar tzf "$tgz")"

    grep -qE '/magtile_studio_qt$' <<<"$list" \
        && ok "magtile_studio_qt 在包内" || bad "缺 magtile_studio_qt"
    if [[ "$form" == qtonly ]]; then
        if grep -qE '/magtile_app$' <<<"$list"; then
            bad "Qt-only 包内不应有 magtile_app"; else ok "Qt-only: 无 magtile_app"; fi
        [[ "$(basename "$tgz")" == *-qt.tar.gz ]] \
            && ok "包名带 -qt 后缀" || bad "包名缺 -qt 后缀: $(basename "$tgz")"
    else
        grep -qE '/magtile_app$' <<<"$list" \
            && ok "magtile_app 在包内 (并存)" || bad "并存包缺 magtile_app"
    fi
    for f in 'data/tile_catalog.json' 'data/model_catalog.json' \
             'licenses/License.rtf' 'licenses/THIRD_PARTY_NOTICES.md' 'README.md'; do
        grep -q "/$f\$" <<<"$list" && ok "$f 在包内" || bad "缺 $f"
    done
    local n_models n_thumbs
    n_models="$(grep -cE '/data/models/[^/]+\.json$' <<<"$list" || true)"
    n_thumbs="$(grep -cE '/data/thumbnails/[^/]+\.png$' <<<"$list" || true)"
    if [[ "$want_models" -gt 0 ]]; then
        [[ "$n_models" -eq "$want_models" ]] \
            && ok "data/models 恰 $want_models 个模型" \
            || bad "data/models 期望 $want_models 实际 $n_models"
    else
        [[ "$n_models" -ge 1 ]] && ok "data/models 非空 ($n_models 个)" || bad "data/models 为空"
    fi
    [[ "$n_thumbs" -ge 1 ]] && ok "data/thumbnails 非空 ($n_thumbs 张)" || bad "data/thumbnails 为空"
    # QML 已编进可执行体资源, 包内不应出现 qml/ 目录 (手册第四节)
    if grep -qE '/qml/' <<<"$list"; then
        bad "包内出现多余 qml/ 目录"; else ok "无多余 qml/ 目录 (QML 已编进资源)"; fi
}

# 目录登记一致性: 解包后 model_catalog.json 每条 file 必须存在,
# 子集档还要求登记数与磁盘模型数相等 (make_data_subset 的承诺)
assert_catalog_consistent() {
    local root="$1" exact="$2"
    python3 - "$root" "$exact" <<'PY'
import json, sys, pathlib
root = pathlib.Path(sys.argv[1]); exact = int(sys.argv[2])
cat = json.loads((root / "data/model_catalog.json").read_text(encoding="utf-8"))
entries = cat["models"]
missing = [e["file"] for e in entries if not (root / "data" / e["file"]).exists()]
if missing:
    sys.exit(f"目录登记但文件缺失 (加载器会当场报错): {missing[:5]} ...")
n_files = len(list((root / "data/models").glob("*.json")))
if exact and (len(entries) != exact or n_files != exact):
    sys.exit(f"子集不一致: 目录 {len(entries)} 条 / 磁盘 {n_files} 个 / 期望 {exact}")
print(f"目录一致: 登记 {len(entries)} 条全部存在, 磁盘 {n_files} 个模型")
PY
}

reconfigure() {  # reconfigure <QT_ONLY:ON|OFF> <MODEL_SET>
    cmake -S . -B "$BUILD_DIR" -DMAGTILE_BUILD_QT=ON \
        -DMAGTILE_PACKAGE_QT_ONLY="$1" -DMAGTILE_PACKAGE_MODEL_SET="$2" \
        >"$BUILD_DIR/.smoke_configure.log" 2>&1 \
        || { tail -20 "$BUILD_DIR/.smoke_configure.log"; echo "配置失败"; exit 1; }
}

STARTER_COUNT="$(grep -cvE '^\s*(#|$)' platforms/windows/packaging/starter_models.txt)"

step "构建 (并存 + full; 目录 $BUILD_DIR)"
mkdir -p "$BUILD_DIR"
BUILD_DIR="$(cd "$BUILD_DIR" && pwd)"   # 归一为绝对路径, 子 shell cd 后引用不歪
reconfigure OFF full
cmake --build "$BUILD_DIR" --parallel >"$BUILD_DIR/.smoke_build.log" 2>&1 \
    || { tail -30 "$BUILD_DIR/.smoke_build.log"; echo "构建失败"; exit 1; }
ok "构建完成 (日志 $BUILD_DIR/.smoke_build.log)"

step "1) 并存包 TGZ + 清单断言"
rm -f "$BUILD_DIR"/MagTileStudio-*-Linux.tar.gz
(cd "$BUILD_DIR" && cpack -G TGZ >/dev/null)
COEXIST_TGZ="$(ls "$BUILD_DIR"/MagTileStudio-*-Linux.tar.gz)"
echo "  产物: $COEXIST_TGZ"
assert_tgz "$COEXIST_TGZ" coexist 0

step "2) NSIS 安装器脚本生成冒烟 (cpack -G NSIS)"
if command -v makensis >/dev/null; then
    rm -rf "$BUILD_DIR"/MagTileStudio-*-Linux.exe "$BUILD_DIR"/_CPack_Packages/Linux/NSIS
    if (cd "$BUILD_DIR" && cpack -G NSIS >"$BUILD_DIR/.smoke_nsis.log" 2>&1); then
        NSI="$(ls "$BUILD_DIR"/_CPack_Packages/Linux/NSIS/project.nsi 2>/dev/null || true)"
        [[ -n "$NSI" ]] && ok "NSIS 脚本已生成: $NSI" || bad "未找到生成的 project.nsi"
        INSTALLER="$(ls "$BUILD_DIR"/MagTileStudio-*-Linux.exe 2>/dev/null || true)"
        [[ -n "$INSTALLER" ]] && ok "makensis 编译通过: $(basename "$INSTALLER") (仅冒烟, 不可分发)" \
                              || bad "makensis 未产出安装器"
        if [[ -n "$NSI" ]]; then
            grep -q "MagTile Studio (Qt).lnk" "$NSI" \
                && ok "NSIS 快捷方式: 并存包含 'MagTile Studio (Qt)'" \
                || bad "NSIS 脚本缺 Qt 界面快捷方式"
            grep -q "magtile_app.exe' 'library --dev-gui'" "$NSI" \
                && ok "NSIS 快捷方式: 主快捷方式直达 library --dev-gui" \
                || bad "NSIS 脚本缺 magtile_app 主快捷方式"
        fi
    else
        tail -20 "$BUILD_DIR/.smoke_nsis.log"; bad "cpack -G NSIS 失败"
    fi
else
    echo "  [--] 未装 makensis (apt install nsis), 跳过 NSIS 档"
fi

step "3) Qt-only 包 TGZ + 清单断言"
reconfigure ON full
rm -f "$BUILD_DIR"/MagTileStudio-*-Linux-qt.tar.gz
(cd "$BUILD_DIR" && cpack -G TGZ >/dev/null)
QTONLY_TGZ="$(ls "$BUILD_DIR"/MagTileStudio-*-Linux-qt.tar.gz)"
echo "  产物: $QTONLY_TGZ"
assert_tgz "$QTONLY_TGZ" qtonly 0

step "4) starter 子集 (Qt-only 叠加) TGZ + 清单断言"
reconfigure ON starter
(cd "$BUILD_DIR" && cpack -G TGZ >/dev/null)
STARTER_TGZ="$(ls "$BUILD_DIR"/MagTileStudio-*-Linux-qt.tar.gz)"
assert_tgz "$STARTER_TGZ" qtonly "$STARTER_COUNT"

step "5) 解包实测 (starter 档): 目录一致性 + offscreen 启动吃包内 data/"
UNPACK="$(mktemp -d)"
trap 'rm -rf "$UNPACK"' EXIT
tar xzf "$STARTER_TGZ" -C "$UNPACK"
PKG_ROOT="$(echo "$UNPACK"/MagTileStudio-*)"
if OUT="$(assert_catalog_consistent "$PKG_ROOT" "$STARTER_COUNT")"; then
    ok "$OUT"
else
    bad "$OUT"
fi
if QT_QPA_PLATFORM=offscreen "$PKG_ROOT/magtile_studio_qt" \
        --data-dir "$PKG_ROOT/data" --db "$UNPACK/qt_pack_smoke.db" \
        --smoke-quit-ms 1500 >/dev/null 2>&1; then
    ok "offscreen 启动冒烟通过 (QML 加载无错)"
else
    bad "offscreen 启动冒烟失败"
fi

step "6) LGPL 动态链接核验 (手册第八节第一项)"
QT_LINKS="$(ldd "$BUILD_DIR/apps/desktop_qt/magtile_studio_qt" | grep -iE 'libqt' || true)"
if [[ -n "$QT_LINKS" ]] && ! grep -vqE '\.so' <<<"$QT_LINKS"; then
    ok "Qt 全部为动态链接共享库 ($(wc -l <<<"$QT_LINKS") 个 libQt6*.so)"
else
    bad "Qt 链接形态异常 (应全为 .so 共享库)"
fi

step "恢复构建目录为默认档 (并存 + full)"
reconfigure OFF full
ok "已恢复"

echo
echo "结果: $PASS 项通过, $FAIL 项失败"
[[ "$FAIL" -eq 0 ]] || exit 1
echo "Linux 侧可验部分全绿; windeployqt/干净机安装验收仍需 Windows 实机"
echo "(scripts/smoke_qt_windows.ps1 + package_qt_desktop.md 第十一节清单)。"

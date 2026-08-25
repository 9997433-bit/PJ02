#!/usr/bin/env bash
# =============================================================
# MagTile Studio — macOS Qt 打包实机冒烟脚本 (QT-6)
#
# 在 macOS 构建机上一键走完 "检测环境 -> 构建 -> 测试 -> CPack ->
# 合成 .app bundle -> macdeployqt -> 签名 -> bundle 清单断言 ->
# 自足启动冒烟 -> DMG 打包与挂载断言" 全链路, 与操作手册
# scripts/package_qt_desktop.md 第三/四/五/十二节逐条对应;
# 断言口径与 Windows 侧 scripts/smoke_qt_windows.ps1 对齐
# (Windows 的 Qt DLL 六件套 <-> macOS 的 Qt 六框架, qwindows.dll
# <-> libqcocoa.dylib, qml/QtQuick 树 <-> Resources/qml/QtQuick 树,
# 目录登记一致性 / starter 恰按清单数 / Qt-only 无 magtile_app 同款)。
#
# 非 macOS (Linux CI) 上也可运行: 自动执行可移植子集 (构建 -> ctest
# -> CPack TGZ -> 包内清单断言 -> offscreen 启动 -> ldd 动态链接核验),
# macdeployqt / 签名 / bundle / DMG 各环节逐条打印 [--] SKIP 及原因,
# 结果标记为 PARTIAL —— SKIP 不算失败, 但 macOS 档必须在实机复跑
# 全绿后按手册第十二节人工验收才算收口。
#
# 关键设计: 当前 CMake 以 MACOSX_BUNDLE FALSE 出裸可执行文件 (便于
# Linux/CI 冒烟路径统一), 本脚本不改构建系统 —— 从 CPack 产物合成
# 最小 .app (Contents/MacOS + Info.plist + bundle 内 data/), 再对其
# 运行 macdeployqt。macdeployqt 只认 bundle 目录布局, 与 bundle 由
# CMake 还是脚本装配无关; data/ 必须在 bundle 内 (Contents/MacOS/data,
# 可执行文件向上探测第一跳命中), 否则拖装到 /Applications 后丢数据。
# 正式发布路径 (MACOSX_BUNDLE TRUE + Info.plist/图标资产) 见手册第五节。
#
# 用法 (仓库根目录):
#   bash scripts/smoke_qt_macos.sh [选项]
#
#   --qt-dir <路径>     Qt 套件前缀 (含 bin/qmake); 缺省自动探测:
#                       brew --prefix qt -> PATH 中 qmake6/qmake ->
#                       ~/Qt/6.*/macos 取最新
#   --build-dir <路径>  构建目录 (默认 build-mac-qt-smoke)
#   --qt-only           打 Qt-only 包 (-DMAGTILE_PACKAGE_QT_ONLY=ON,
#                       包内无 magtile_app, 包名 -qt 后缀)
#   --model-set <值>    full / starter / 自定义清单路径 (默认 full)
#   --sign-identity <id> codesign 身份 (Developer ID Application: ...);
#                       缺省用 ad-hoc 签名 (仅冒烟; Gatekeeper 仍拦,
#                       发布须真实签名 + 公证, 见手册第十二节)
#   --skip-tests        跳过 ctest (仅打包链路排障时用)
#   --dry-run           不构建不打包: 环境检测报告 + 执行计划 + 用
#                       模拟包目录/模拟 bundle 自检断言逻辑 (含故意
#                       删除目录登记模型 / libqcocoa.dylib 的双失败
#                       注入)。任何平台可跑。
#
# 退出码: 0 = 无失败 (可能含 SKIP, 见末尾 PARTIAL 提示);
#         非 0 = 任一环节失败 (信息见 FAILED / [!!] 行)。
#
# 兼容性: 兼容 macOS 系统自带 bash 3.2 (不用 mapfile/关联数组/
# declare -g/空数组展开), Linux bash 5 亦可。
# =============================================================
set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

# ---------------- 参数解析 ----------------
QT_DIR=""
BUILD_DIR="build-mac-qt-smoke"
QT_ONLY=0
MODEL_SET="full"
SIGN_IDENTITY=""
SKIP_TESTS=0
DRY_RUN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --qt-dir)        QT_DIR="$2"; shift 2 ;;
        --build-dir)     BUILD_DIR="$2"; shift 2 ;;
        --qt-only)       QT_ONLY=1; shift ;;
        --model-set)     MODEL_SET="$2"; shift 2 ;;
        --sign-identity) SIGN_IDENTITY="$2"; shift 2 ;;
        --skip-tests)    SKIP_TESTS=1; shift ;;
        --dry-run)       DRY_RUN=1; shift ;;
        -h|--help)       sed -n '2,55p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "未知参数: $1 (用 --help 看用法)"; exit 2 ;;
    esac
done

UNAME="$(uname -s)"
ON_MAC=0; [ "$UNAME" = "Darwin" ] && ON_MAC=1

PASS=0; FAIL=0; SKIP=0
ok()   { echo "  [OK] $*"; PASS=$((PASS+1)); }
bad()  { echo "  [!!] $*"; FAIL=$((FAIL+1)); }
skip() { echo "  [--] SKIP: $*"; SKIP=$((SKIP+1)); }
info() { echo "  $*"; }
step() { echo; echo "==> $*"; }
fail_hard() { echo; echo "FAILED: $*"; exit 1; }

# 外部命令封装: 回显命令行, 非零退出码即整体失败 (对齐 ps1 Invoke-Checked)
run_checked() {
    local desc="$1"; shift
    info "\$ $*"
    "$@" || fail_hard "$desc 失败 (退出码 $?)"
}

# ---------------- 环境检测 (手册第二节前置条件) ----------------
find_qt_prefix() {
    if [ -n "$QT_DIR" ]; then
        if [ -x "$QT_DIR/bin/qmake" ] || [ -x "$QT_DIR/bin/qmake6" ]; then
            echo "$QT_DIR"; return 0
        fi
        return 1
    fi
    if [ "$ON_MAC" = 1 ] && command -v brew >/dev/null 2>&1; then
        local p; p="$(brew --prefix qt 2>/dev/null || true)"
        if [ -n "$p" ] && [ -x "$p/bin/qmake" ]; then echo "$p"; return 0; fi
    fi
    local qm
    for qm in qmake6 qmake; do
        if command -v "$qm" >/dev/null 2>&1; then
            "$qm" -query QT_INSTALL_PREFIX 2>/dev/null && return 0
        fi
    done
    if [ "$ON_MAC" = 1 ]; then
        # Qt 官方安装器默认布局; 6.9/6.10 跨位数排序不精确, 可用 --qt-dir 显式指定
        local cand; cand="$(ls -d "$HOME"/Qt/6.*/macos 2>/dev/null | sort | tail -1 || true)"
        if [ -n "$cand" ] && [ -x "$cand/bin/qmake" ]; then echo "$cand"; return 0; fi
    fi
    return 1
}

qt_version_of() {  # qt_version_of <prefix>
    local qm="$1/bin/qmake"
    [ -x "$qm" ] || qm="$1/bin/qmake6"
    [ -x "$qm" ] || { echo ""; return 0; }
    "$qm" -query QT_VERSION 2>/dev/null || echo ""
}

step "环境检测 (手册第二节前置条件; 当前平台: $UNAME)"
CMAKE_BIN="$(command -v cmake || true)"
CPACK_BIN="$(command -v cpack || true)"
CTEST_BIN="$(command -v ctest || true)"
PYTHON_BIN="$(command -v python3 || true)"
QT_PREFIX="$(find_qt_prefix || true)"
QT_VERSION=""; MACDEPLOYQT=""
if [ -n "$QT_PREFIX" ]; then
    QT_VERSION="$(qt_version_of "$QT_PREFIX")"
    if [ -x "$QT_PREFIX/bin/macdeployqt" ]; then MACDEPLOYQT="$QT_PREFIX/bin/macdeployqt"
    else MACDEPLOYQT="$(command -v macdeployqt || true)"; fi
fi

if [ -n "$CMAKE_BIN" ]; then info "[ok] CMake: $CMAKE_BIN ($("$CMAKE_BIN" --version | head -1))"; else info "[--] 未找到 cmake"; fi
if [ -n "$CPACK_BIN" ]; then info "[ok] CPack: $CPACK_BIN"; else info "[--] 未找到 cpack (随 CMake 安装)"; fi
if [ -n "$QT_PREFIX" ]; then info "[ok] Qt 套件: $QT_PREFIX (版本 ${QT_VERSION:-未知})"; else info "[--] 未找到 Qt (macOS: brew install qt 或官方安装器 + --qt-dir)"; fi
if [ -n "$MACDEPLOYQT" ]; then info "[ok] macdeployqt: $MACDEPLOYQT"; else info "[--] 未找到 macdeployqt (随 Qt 套件; 非 macOS 平台本来就没有)"; fi
if [ -n "$PYTHON_BIN" ]; then info "[ok] Python3: $PYTHON_BIN"; else info "[--] 未找到 python3 (仅 --model-set starter/清单 需要)"; fi
if [ "$ON_MAC" = 1 ]; then
    for t in hdiutil codesign otool xcrun; do
        if command -v "$t" >/dev/null 2>&1; then info "[ok] $t: $(command -v "$t")"; else info "[--] 未找到 $t (Xcode Command Line Tools)"; fi
    done
fi

# ---------------- 期望模型数 (与 ps1 Get-ExpectedModelCount 同口径) --
expected_model_count() {  # expected_model_count <set>
    if [ "$1" = "full" ]; then echo 0; return 0; fi
    local manifest="$1"
    [ "$1" = "starter" ] && manifest="platforms/windows/packaging/starter_models.txt"
    [ -f "$manifest" ] || fail_hard "模型清单不存在: $manifest"
    sed -e 's/#.*//' "$manifest" | grep -c '[^[:space:]]' || true
}
EXPECTED_MODELS="$(expected_model_count "$MODEL_SET")"

# ---------------- 执行计划 (实跑与 dry-run 共用) ----------------
PKG_SUFFIX=""; [ "$QT_ONLY" = 1 ] && PKG_SUFFIX="-qt"
FORM_DESC="并存包 (magtile_app + magtile_studio_qt)"; [ "$QT_ONLY" = 1 ] && FORM_DESC="Qt-only 包"
CONFIGURE_ARGS="-S . -B $BUILD_DIR -DCMAKE_BUILD_TYPE=Release -DMAGTILE_BUILD_QT=ON"
if [ -n "$QT_PREFIX" ] && [ "$QT_PREFIX" != "/usr" ]; then
    CONFIGURE_ARGS="$CONFIGURE_ARGS -DCMAKE_PREFIX_PATH=$QT_PREFIX"
fi
[ "$QT_ONLY" = 1 ] && CONFIGURE_ARGS="$CONFIGURE_ARGS -DMAGTILE_PACKAGE_QT_ONLY=ON"
[ "$MODEL_SET" != "full" ] && CONFIGURE_ARGS="$CONFIGURE_ARGS -DMAGTILE_PACKAGE_MODEL_SET=$MODEL_SET"

step "执行计划 (形态: $FORM_DESC; 数据集: $MODEL_SET)"
info "1) cmake $CONFIGURE_ARGS"
info "2) cmake --build $BUILD_DIR --parallel"
if [ "$SKIP_TESTS" = 1 ]; then info "3) (跳过测试 --skip-tests)"
else info "3) ctest --test-dir $BUILD_DIR --output-on-failure -E \"(library|inventory)_gui_smoke\""; fi
info "4) cpack -G TGZ   (在 $BUILD_DIR 内; 产物 MagTileStudio-*-${UNAME}${PKG_SUFFIX}.tar.gz)"
info "5) 解包 -> 包内清单断言 (双主程序或 Qt-only / data 目录登记一致性 / licenses / 无多余 qml/)"
info "6) 解包目录 offscreen 启动冒烟 (--data-dir 指包内 data/, 1.5s 自动退出)"
info "7) 动态链接核验 (LGPL 手册第八节第一项: Linux ldd / macOS otool -L)"
if [ "$ON_MAC" = 1 ]; then
    info "8) 合成最小 .app (Contents/MacOS + Info.plist + bundle 内 data/) <- CPack 产物"
    info "9) macdeployqt <app> -qmldir=apps/desktop_qt/qml (Qt 框架 + libqcocoa + Resources/qml)"
    info "10) codesign ($([ -n "$SIGN_IDENTITY" ] && echo "身份: $SIGN_IDENTITY" || echo 'ad-hoc, 仅冒烟')) + 校验"
    info "11) bundle 清单断言 (Qt 六框架 / libqcocoa.dylib / Resources/qml/QtQuick / bundle 内 data)"
    info "12) bundle 自足启动冒烟 (cd /tmp 后无 --data-dir 启动, 验证拖装后可自定位数据)"
    info "13) hdiutil create DMG (.app + Applications 软链) -> 挂载断言 -> 卸载"
else
    info "8-13) macOS 专属环节 (合成 bundle/macdeployqt/签名/DMG) 在 $UNAME 上逐条 SKIP"
fi

# ---------------- 清单断言 (口径对齐 ps1 Test-PackageManifest) ------
# 结果经全局 A_FAIL 传递 (换行分隔字符串, 兼容 bash 3.2 无空数组坑)
A_FAIL=""
a_add()  { A_FAIL="${A_FAIL}${A_FAIL:+$'\n'}$*"; }
a_need() { [ -e "$1/$2" ] || a_add "缺少 $2"; }  # a_need <root> <相对路径>

# assert_package_dir <解包根> <coexist|qtonly> <期望模型数; 0=只要求非空>
assert_package_dir() {
    local root="$1" form="$2" want="$3"
    A_FAIL=""
    a_need "$root" "magtile_studio_qt"
    a_need "$root" "README.md"
    a_need "$root" "licenses/License.rtf"
    a_need "$root" "licenses/THIRD_PARTY_NOTICES.md"
    a_need "$root" "data/tile_catalog.json"
    a_need "$root" "data/model_catalog.json"
    if [ "$form" = "qtonly" ]; then
        [ -e "$root/magtile_app" ] && a_add "Qt-only 包内不应存在 magtile_app"
    else
        a_need "$root" "magtile_app"
    fi
    local n_models=0 n_thumbs=0
    [ -d "$root/data/models" ] && n_models="$(find "$root/data/models" -maxdepth 1 -name '*.json' -type f | wc -l | tr -d ' ')"
    [ -d "$root/data/thumbnails" ] && n_thumbs="$(find "$root/data/thumbnails" -maxdepth 1 -name '*.png' -type f | wc -l | tr -d ' ')"
    if [ "$want" -gt 0 ]; then
        [ "$n_models" -eq "$want" ] || a_add "data/models 应有 $want 个模型, 实际 $n_models"
    else
        [ "$n_models" -ge 1 ] || a_add "data/models 为空"
    fi
    [ "$n_thumbs" -ge 1 ] || a_add "data/thumbnails 缺失或为空"
    # QML 已编进可执行体资源, CPack 产物内不应出现 qml/ 目录 (手册第四节)
    [ -d "$root/qml" ] && a_add "包内出现多余 qml/ 目录 (QML 应已编进资源)"
    # 目录登记一致性: 登记了就必须存在 (加载器对缺文件当场报错);
    # 子集档还要求登记数与磁盘数恰等 (make_data_subset 的承诺)
    if [ -n "$PYTHON_BIN" ] && [ -f "$root/data/model_catalog.json" ]; then
        local out
        if ! out="$("$PYTHON_BIN" - "$root" "$want" <<'PY' 2>&1
import json, sys, pathlib
root = pathlib.Path(sys.argv[1]); exact = int(sys.argv[2])
cat = json.loads((root / "data/model_catalog.json").read_text(encoding="utf-8"))
entries = cat["models"]
missing = [e["file"] for e in entries if not (root / "data" / e["file"]).exists()]
if missing:
    sys.exit(f"目录登记但模型文件缺失 (加载器会当场报错): {missing[:5]}")
if exact and len(entries) != exact:
    sys.exit(f"model_catalog.json 应恰登记 {exact} 条 (子集须同步过滤), 实际 {len(entries)}")
PY
        )"; then a_add "$out"; fi
    fi
}

# assert_bundle <.app 路径>  —— macdeployqt 之后的 bundle 清单
# (Windows 侧 Qt DLL 六件套/qwindows/qml 树断言的 macOS 等价物)
assert_bundle() {
    local app="$1" fw
    A_FAIL=""
    [ -x "$app/Contents/MacOS/magtile_studio_qt" ] || a_add "缺少可执行文件 Contents/MacOS/magtile_studio_qt"
    a_need "$app" "Contents/Info.plist"
    for fw in QtCore QtGui QtQml QtQuick QtQuickControls2 QtOpenGL; do
        [ -d "$app/Contents/Frameworks/$fw.framework" ] || a_add "缺少 Qt 框架 Contents/Frameworks/$fw.framework"
    done
    [ -e "$app/Contents/PlugIns/platforms/libqcocoa.dylib" ] \
        || a_add "缺少平台插件 Contents/PlugIns/platforms/libqcocoa.dylib (启动即报 \"no Qt platform plugin\")"
    [ -d "$app/Contents/Resources/qml/QtQuick" ] \
        || a_add "缺少 QML 模块树 Contents/Resources/qml/QtQuick/ (macdeployqt 忘带 -qmldir 的典型症状, 启动黑屏)"
    # data 必须在 bundle 内: 拖装到 /Applications 只带走 .app 本身
    [ -f "$app/Contents/MacOS/data/tile_catalog.json" ] \
        || a_add "缺少 bundle 内数据 Contents/MacOS/data/ (拖装后应用将找不到数据)"
    # 动态链接核验 (LGPL): 可执行文件对 Qt 的引用应全为 .framework 动态引用
    if [ "$ON_MAC" = 1 ] && command -v otool >/dev/null 2>&1 \
       && [ -x "$app/Contents/MacOS/magtile_studio_qt" ]; then
        local qt_refs
        qt_refs="$(otool -L "$app/Contents/MacOS/magtile_studio_qt" 2>/dev/null | grep -E 'Qt[A-Za-z0-9]+' || true)"
        if [ -n "$qt_refs" ] && echo "$qt_refs" | grep -vq '\.framework/'; then
            a_add "可执行文件存在非 framework 的 Qt 引用 (应全为动态 .framework, 手册第八节)"
        fi
    fi
}

report_assert() {  # report_assert <说明>; 消费全局 A_FAIL
    if [ -z "$A_FAIL" ]; then ok "$1 清单断言全部通过"; return 0; fi
    local line
    while IFS= read -r line; do bad "$line"; done <<<"$A_FAIL"
    return 1
}

# ---------------- dry-run: 断言逻辑自检 (双失败注入) ----------------
if [ "$DRY_RUN" = 1 ]; then
    step "DryRun 自检 1: 模拟 CPack 解包目录 (口径对齐 smoke_qt_windows.ps1 -DryRun)"
    MOCK="$(mktemp -d)"
    trap 'rm -rf "$MOCK"' EXIT
    mkdir -p "$MOCK/pkg/licenses" "$MOCK/pkg/data/models" "$MOCK/pkg/data/thumbnails"
    for f in magtile_studio_qt magtile_app README.md licenses/License.rtf \
             licenses/THIRD_PARTY_NOTICES.md data/tile_catalog.json \
             data/models/mock_model_01.json data/thumbnails/mock_model_01.png; do
        echo mock > "$MOCK/pkg/$f"
    done
    chmod +x "$MOCK/pkg/magtile_studio_qt" "$MOCK/pkg/magtile_app"
    echo '{"schema_version": 1, "models": [{"id": "mock_model_01", "file": "models/mock_model_01.json"}]}' \
        > "$MOCK/pkg/data/model_catalog.json"
    SELF_OK=1
    assert_package_dir "$MOCK/pkg" coexist 1
    report_assert "模拟完整包" || SELF_OK=0
    # 失败注入 1: 目录登记但模型文件缺失 (加载器会当场报错的形态)
    rm "$MOCK/pkg/data/models/mock_model_01.json"
    assert_package_dir "$MOCK/pkg" coexist 1
    if echo "$A_FAIL" | grep -q "mock_model_01"; then
        ok "失败注入 1 (目录登记但模型缺失) 被正确检出"
    else
        bad "失败注入 1 未被检出 — 断言逻辑有漏"; SELF_OK=0
    fi

    step "DryRun 自检 2: 模拟 macdeployqt 后的 .app bundle"
    APP="$MOCK/magtile_studio_qt.app"
    mkdir -p "$APP/Contents/MacOS/data/models" "$APP/Contents/PlugIns/platforms" \
             "$APP/Contents/Resources/qml/QtQuick"
    for fw in QtCore QtGui QtQml QtQuick QtQuickControls2 QtOpenGL; do
        mkdir -p "$APP/Contents/Frameworks/$fw.framework"
    done
    echo mock > "$APP/Contents/MacOS/magtile_studio_qt"
    chmod +x "$APP/Contents/MacOS/magtile_studio_qt"
    echo mock > "$APP/Contents/Info.plist"
    echo mock > "$APP/Contents/PlugIns/platforms/libqcocoa.dylib"
    echo mock > "$APP/Contents/MacOS/data/tile_catalog.json"
    assert_bundle "$APP"
    report_assert "模拟 bundle" || SELF_OK=0
    # 失败注入 2: 抽掉平台插件 (常见事故: macdeployqt 没跑/没拷全)
    rm "$APP/Contents/PlugIns/platforms/libqcocoa.dylib"
    assert_bundle "$APP"
    if echo "$A_FAIL" | grep -q "qcocoa"; then
        ok "失败注入 2 (删 libqcocoa.dylib) 被正确检出"
    else
        bad "失败注入 2 未被检出 — 断言逻辑有漏"; SELF_OK=0
    fi

    echo
    [ "$SELF_OK" = 1 ] || fail_hard "DryRun 自检未通过"
    echo "DryRun 完成: 环境报告与执行计划如上, 清单断言逻辑自检通过 ($PASS 项)。"
    echo "去掉 --dry-run 即实跑; macOS 实机上将执行 macdeployqt/签名/DMG 全链路,"
    echo "其它平台执行可移植子集并对 macOS 专属环节显式 SKIP。"
    exit 0
fi

# ---------------- 实跑前置校验 ----------------
[ -n "$CMAKE_BIN" ] && [ -n "$CPACK_BIN" ] || fail_hard "缺少 cmake/cpack"
[ -n "$QT_PREFIX" ] || fail_hard "未找到 Qt 套件 (--qt-dir 指定; macOS: brew install qt / 官方安装器, Linux: apt 清单见 docs/QT_UI_PLAN.md §3.1)"
if [ "$MODEL_SET" != "full" ] && [ -z "$PYTHON_BIN" ]; then
    fail_hard "--model-set $MODEL_SET 需要 python3 (tools/make_data_subset.py)"
fi

# ---------------- 构建 / 测试 / 打包 (手册第三/四节) ----------------
step "配置 (手册第三节)"
mkdir -p "$BUILD_DIR"
BUILD_DIR="$(cd "$BUILD_DIR" && pwd)"   # 归一为绝对路径
# shellcheck disable=SC2086  # CONFIGURE_ARGS 由本脚本拼装, 需要按词拆分
run_checked "配置" "$CMAKE_BIN" $CONFIGURE_ARGS

step "构建 Release"
run_checked "构建" "$CMAKE_BIN" --build "$BUILD_DIR" --parallel

if [ "$SKIP_TESTS" != 1 ]; then
    step "测试 (GL 双 GUI 冒烟需显示环境, 按手册排除; Qt 侧测试 offscreen 照跑)"
    run_checked "测试" "$CTEST_BIN" --test-dir "$BUILD_DIR" --output-on-failure \
        -E "(library|inventory)_gui_smoke"
fi

step "CPack 打包 (生成器: TGZ; 手册第四节)"
rm -f "$BUILD_DIR"/MagTileStudio-*-"${UNAME}${PKG_SUFFIX}".tar.gz
(cd "$BUILD_DIR" && run_checked "打包" "$CPACK_BIN" -G TGZ)
TGZ="$(ls "$BUILD_DIR"/MagTileStudio-*-"${UNAME}${PKG_SUFFIX}".tar.gz 2>/dev/null | head -1 || true)"
[ -n "$TGZ" ] || fail_hard "未找到 TGZ 产物 (MagTileStudio-*-${UNAME}${PKG_SUFFIX}.tar.gz)"
ok "TGZ 产物: $(basename "$TGZ")"
PKG_VERSION="$(basename "$TGZ" | sed -E 's/^MagTileStudio-([0-9.]+)-.*/\1/')"

step "解包到 staging + 包内清单断言 (手册第五/九节口径)"
STAGING="$BUILD_DIR/smoke-staging"
rm -rf "$STAGING"; mkdir -p "$STAGING"
tar xzf "$TGZ" -C "$STAGING"
PKG_ROOT="$(find "$STAGING" -mindepth 1 -maxdepth 1 -type d | head -1)"
[ -n "$PKG_ROOT" ] || fail_hard "TGZ 解包后未见顶层目录"
info "解包目录: $PKG_ROOT"
FORM="coexist"; [ "$QT_ONLY" = 1 ] && FORM="qtonly"
if [ "$QT_ONLY" = 1 ]; then
    case "$(basename "$TGZ")" in
        *-qt.tar.gz) ok "包名带 -qt 后缀" ;;
        *) bad "Qt-only 包名缺 -qt 后缀: $(basename "$TGZ")" ;;
    esac
fi
assert_package_dir "$PKG_ROOT" "$FORM" "$EXPECTED_MODELS"
report_assert "CPack 解包目录" || true

step "解包目录 offscreen 启动冒烟 (吃包内 data/, 1.5s 自动退出)"
SMOKE_DB="$BUILD_DIR/qt_pack_smoke_macos.db"
rm -f "$SMOKE_DB"
if QT_QPA_PLATFORM=offscreen "$PKG_ROOT/magtile_studio_qt" \
        --data-dir "$PKG_ROOT/data" --db "$SMOKE_DB" \
        --smoke-quit-ms 1500 >/dev/null 2>&1; then
    ok "offscreen 启动冒烟通过 (QML 加载无错, 包内 data/ 命中)"
else
    bad "offscreen 启动冒烟失败"
fi

step "动态链接核验 (LGPL 手册第八节第一项)"
BUILT_EXE="$BUILD_DIR/apps/desktop_qt/magtile_studio_qt"
if [ "$ON_MAC" = 1 ]; then
    if command -v otool >/dev/null 2>&1 && [ -x "$BUILT_EXE" ]; then
        QT_REFS="$(otool -L "$BUILT_EXE" | grep -E 'Qt[A-Za-z0-9]+' || true)"
        if [ -n "$QT_REFS" ] && ! echo "$QT_REFS" | grep -vq '\.framework/'; then
            ok "Qt 全部为动态 framework 引用 ($(echo "$QT_REFS" | wc -l | tr -d ' ') 条)"
        else
            bad "Qt 链接形态异常 (应全为动态 .framework 引用)"
        fi
    else
        skip "otool 不可用, 动态链接核验未执行"
    fi
else
    QT_REFS="$(ldd "$BUILT_EXE" | grep -iE 'libqt' || true)"
    if [ -n "$QT_REFS" ] && ! echo "$QT_REFS" | grep -vq '\.so'; then
        ok "Qt 全部为动态链接共享库 ($(echo "$QT_REFS" | wc -l | tr -d ' ') 个 libQt6*.so)"
    else
        bad "Qt 链接形态异常 (应全为 .so 共享库)"
    fi
fi

# ---------------- macOS 专属环节: bundle + macdeployqt + DMG --------
if [ "$ON_MAC" != 1 ]; then
    step "macOS 专属环节 (在 $UNAME 上逐条 SKIP; 手册第十二节)"
    skip "合成 .app bundle + macdeployqt -qmldir (需 macOS + Qt 套件)"
    skip "codesign 签名与校验 (需 macOS)"
    skip "bundle 清单断言 (Qt 六框架/libqcocoa/Resources/qml 树/bundle 内 data)"
    skip "bundle 自足启动冒烟 (拖装自定位数据验证)"
    skip "DMG 打包 (hdiutil create) 与挂载断言"
elif [ -z "$MACDEPLOYQT" ]; then
    step "macOS 专属环节 (未找到 macdeployqt, 逐条 SKIP)"
    skip "macdeployqt 部署 (装 Qt 官方套件或 brew install qt 后重跑)"
    skip "codesign 签名与校验"
    skip "bundle 清单断言"
    skip "bundle 自足启动冒烟"
    skip "DMG 打包与挂载断言"
else
    step "合成最小 .app bundle (手册第十二节; 不改构建系统)"
    BUNDLE_DIR="$BUILD_DIR/smoke-bundle"
    APP="$BUNDLE_DIR/magtile_studio_qt.app"
    rm -rf "$BUNDLE_DIR"
    mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
    cp "$PKG_ROOT/magtile_studio_qt" "$APP/Contents/MacOS/"
    # data 进 bundle (Contents/MacOS/data): 可执行文件向上探测第一跳
    # 命中, 且拖装到 /Applications 后数据随 .app 走不丢
    cp -R "$PKG_ROOT/data" "$APP/Contents/MacOS/data"
    cp -R "$PKG_ROOT/licenses" "$APP/Contents/Resources/licenses"
    cp "$PKG_ROOT/README.md" "$APP/Contents/Resources/"
    printf 'APPL????' > "$APP/Contents/PkgInfo"
    cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>magtile_studio_qt</string>
    <key>CFBundleIdentifier</key><string>com.magtile.studio</string>
    <key>CFBundleName</key><string>MagTile Studio</string>
    <key>CFBundleDisplayName</key><string>MagTile Studio</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>${PKG_VERSION}</string>
    <key>CFBundleVersion</key><string>${PKG_VERSION}</string>
    <key>LSMinimumSystemVersion</key><string>11.0</string>
    <key>NSHighResolutionCapable</key><true/>
    <key>NSPrincipalClass</key><string>NSApplication</string>
</dict>
</plist>
PLIST
    ok "已合成 $APP (Info.plist 版本 $PKG_VERSION)"

    step "macdeployqt (-qmldir 指向 QML 源码目录; 手册第五节)"
    run_checked "macdeployqt" "$MACDEPLOYQT" "$APP" \
        -qmldir="$REPO_ROOT/apps/desktop_qt/qml"

    step "codesign ($([ -n "$SIGN_IDENTITY" ] && echo "身份: $SIGN_IDENTITY" || echo 'ad-hoc, 仅冒烟用'))"
    if command -v codesign >/dev/null 2>&1; then
        # macdeployqt 改写过库路径, 原签名已失效; arm64 上无有效签名
        # 直接拒载, 必须重签 (ad-hoc 足够本机冒烟, 分发须 Developer ID)
        if [ -n "$SIGN_IDENTITY" ]; then
            run_checked "codesign" codesign --force --deep --options runtime \
                --sign "$SIGN_IDENTITY" "$APP"
        else
            run_checked "codesign(ad-hoc)" codesign --force --deep --sign - "$APP"
            info "注意: ad-hoc 签名仅本机可跑; 分发需 Developer ID + 公证 (手册第十二节)"
        fi
        if codesign --verify --deep --strict "$APP" 2>/dev/null; then
            ok "codesign 校验通过"
        else
            bad "codesign 校验失败 (arm64 上应用将无法启动)"
        fi
    else
        skip "codesign 不可用 (装 Xcode Command Line Tools)"
    fi

    step "bundle 清单断言 (Windows Qt DLL 六件套断言的 macOS 等价物)"
    assert_bundle "$APP"
    report_assert "macdeployqt 后 bundle" || true

    step "bundle 自足启动冒烟 (cd /tmp 无 --data-dir, 模拟拖装后双击)"
    SMOKE_DB2="$BUILD_DIR/qt_bundle_smoke_macos.db"
    rm -f "$SMOKE_DB2"
    if (cd /tmp && QT_QPA_PLATFORM=offscreen \
            "$APP/Contents/MacOS/magtile_studio_qt" \
            --db "$SMOKE_DB2" --smoke-quit-ms 1500 >/dev/null 2>&1); then
        ok "bundle 自足启动通过 (bundle 内 data/ 自定位命中)"
    else
        bad "bundle 自足启动失败 (核对 Contents/MacOS/data 与 Qt 运行库)"
    fi

    step "DMG 打包 (hdiutil create: .app + Applications 软链) + 挂载断言"
    DMG="$BUILD_DIR/MagTileStudio-${PKG_VERSION}-macos${PKG_SUFFIX}.dmg"
    DMG_ROOT="$BUNDLE_DIR/dmg-root"
    rm -rf "$DMG_ROOT"; rm -f "$DMG"
    mkdir -p "$DMG_ROOT"
    cp -R "$APP" "$DMG_ROOT/"
    ln -s /Applications "$DMG_ROOT/Applications"
    run_checked "hdiutil create" hdiutil create -volname "MagTile Studio" \
        -srcfolder "$DMG_ROOT" -ov -format UDZO "$DMG"
    ok "DMG 产物: $DMG"
    MOUNT_POINT="$(mktemp -d)"
    if hdiutil attach -readonly -nobrowse -mountpoint "$MOUNT_POINT" "$DMG" >/dev/null 2>&1; then
        if [ -x "$MOUNT_POINT/magtile_studio_qt.app/Contents/MacOS/magtile_studio_qt" ] \
           && [ -L "$MOUNT_POINT/Applications" ]; then
            ok "DMG 挂载断言通过 (.app + Applications 软链均在)"
        else
            bad "DMG 结构异常 (缺 .app 或 Applications 软链)"
        fi
        hdiutil detach "$MOUNT_POINT" >/dev/null 2>&1 || true
    else
        bad "DMG 挂载失败 (hdiutil attach)"
    fi
    rmdir "$MOUNT_POINT" 2>/dev/null || true
fi

# ---------------- 汇总 ----------------
echo
echo "结果: $PASS 项通过, $FAIL 项失败, $SKIP 项跳过"
[ "$FAIL" -eq 0 ] || exit 1
if [ "$SKIP" -gt 0 ]; then
    echo "结果为 PARTIAL: macOS 专属环节已 SKIP (原因见上方 [--] 行) ——"
    echo "在 macOS 实机 (装 Qt + Xcode CLT) 上重跑本脚本至零 SKIP, 再按"
    echo "scripts/package_qt_desktop.md 第十二节人工验收, macOS 档才算收口。"
else
    echo "macOS 自动化冒烟全绿。剩余人工验收 (干净 macOS, 手册第十二节):"
    echo "  DMG 挂载 -> 拖装 /Applications -> Gatekeeper 放行 -> 启动进教程 ->"
    echo "  退出重启续档 -> 卸载 (拖废纸篓, 存档保留属预期)。"
fi
exit 0

#!/usr/bin/env bash
# =============================================================
# MagTile Studio - V1 上架就绪自动探测 (Readiness Probe)
#
# docs/V1_LAUNCH_CHECKLIST.md 的自动侧执行器: 把清单中所有能自动
# 探测的项串成一条命令跑一遍, 输出 PASS/FAIL/SKIP 摘要。每个检查
# 号 (R1..R16) 与清单「探测」列一一对应; 纯人工项 (实机验收 /
# 法务定稿 / 软著备案等) 以 SKIP[Manual] 列出提醒, 不参与判定。
#
# 检查项 (P0 = 上架阻断, 任一 FAIL 退出码非零; P1 = 报告不阻断):
#   R1  [P0] 内容体量        模型 JSON 数 >= 门槛 (默认 200, 目标区间 200~250)
#   R2  [P1] 目录/缩略图对账 JSON = 目录登记 = 缩略图登记, 无悬空引用
#   R3  [P0] 免费层对齐      tools/verify_free_tier.py (标签 30 + core-9 + starter 一致)
#   R4  [P0] E2E 冒烟        tools/run_e2e_smoke.sh (--strict 透传; --quick 跳过)
#   R5  [P0] 发布门禁快检    tools/run_release_gate.sh (--quick 跳过)
#   R6  [P0] 实物抽样包      tools/physical_sample_pack.py --fail-on-missing-sample
#   R7  [P0] D4+ 实物清零    tools/list_physical_pending.py --fail-on-pending
#   R8  [P0] 隐私合规文档    SECURITY_AND_PRIVACY.md + PRIVACY_POLICY_DRAFT.md 存在
#   R9  [P0] 桌面打包资产    打包手册 / CPack / WiX / starter 清单 / 第三方声明 / CI
#   R10 [P1] 计费适配层单测  build 内 magtile_billing_test 存在即实跑, 否则 SKIP
#   R11 [P0] 真实商店计费    分平台口径 —— Google Play (Android) 接线在位即
#                            PASS(部分): PlayBillingManager.kt 存在 + gradle
#                            依赖 billingclient + setSubscriptionActive 写入口
#                            调用在位 + store_billing_client.cpp 无 Google
#                            Play 未接入守卫; Windows 商店档单列 R11W ——
#                            WinRT StoreContext 接线证据全在位即 PASS(部分):
#                            store_billing_client.cpp 无 Windows 未接入守卫 +
#                            Windows.Services.Store 接入 + 购买流/许可证恢复 +
#                            setSubscriptionActive 写契约键 + 根 CMake 选项接线
#                            (MSIX 实包沙盒验收仍属人工项 B3/M1)
#   R12 [P1] Android 链路资产 android.yml + build.gradle.kts + README 存在
#   R13 [P0] Android 签名    signingConfigs 接线 + keystore.properties.example
#                            模板齐备 (真实 keystore 不入库, 生成与商店
#                            出包属人工项 M2; 流程 platforms/android/SIGNING.md)
#   R14 [P0] 商店上架文档守卫 tools/validate_store_listing.py
#                            (STORE_LISTING + store_assets 必填章节与内链)
#   R15 [P0] 国内合规清单守卫 tools/check_china_compliance_docs.py
#                            (CHINA_STORE_COMPLIANCE 章节/条目格式/交叉引用)
#   R16 [P0] 儿童友好文案守卫 tools/check_child_friendly_copy.py
#                            (Qt QML / Android strings.xml / Kotlin / 展示层
#                            C++ / 模型文案 全库秒级扫描: 无恐吓词与催促
#                            话术, UI_UX_SPEC P3/§4.3/§4.5/§11/§14 红线)
#
# 用法:
#   tools/check_v1_readiness.sh [选项]
#     --build-dir DIR      CLI 构建目录 (默认 build; 透传给 R5/R10)
#     --qt-build-dir DIR   Qt 构建目录 (默认 build-qt; 透传给 R4)
#     --quick              跳过两个长跑项 R4/R5 (记 SKIP; 日常快检用)
#     --strict             签核档: R4 的 E2E 冒烟加 --strict (SKIP 也算失败)
#     --model-target N     R1 内容体量门槛 (默认 200)
#     -h | --help          打印本说明
#
# 退出码: 0 = 无 P0 失败 (P1 失败与 SKIP 不阻断);
#         1 = 存在 P0 失败; 2 = 环境/参数不满足
# 颜色: FORCE_COLOR=1 强制 / NO_COLOR=1 禁用 (与 run_e2e_smoke.sh 同约定)
# =============================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$ROOT/build"
QT_BUILD_DIR="$ROOT/build-qt"
QUICK=0
STRICT=0
MODEL_TARGET=200

# 帮助 = 文件头注释块 (行 2 起至第一条闭合分隔线, 随头注增删自适应)
usage() { sed -n '2,/^# =\{20,\}$/p' "$0"; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --build-dir)
            [ "$#" -ge 2 ] || { echo "错误: --build-dir 需要目录参数" >&2; exit 2; }
            BUILD_DIR="$2"; shift 2 ;;
        --qt-build-dir)
            [ "$#" -ge 2 ] || { echo "错误: --qt-build-dir 需要目录参数" >&2; exit 2; }
            QT_BUILD_DIR="$2"; shift 2 ;;
        --quick)  QUICK=1; shift ;;
        --strict) STRICT=1; shift ;;
        --model-target)
            [ "$#" -ge 2 ] || { echo "错误: --model-target 需要数字参数" >&2; exit 2; }
            MODEL_TARGET="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "错误: 未知参数 $1 (用法见 --help)" >&2; exit 2 ;;
    esac
done
case "$BUILD_DIR"    in /*) ;; *) BUILD_DIR="$ROOT/$BUILD_DIR" ;; esac
case "$QT_BUILD_DIR" in /*) ;; *) QT_BUILD_DIR="$ROOT/$QT_BUILD_DIR" ;; esac
case "$MODEL_TARGET" in ''|*[!0-9]*)
    echo "错误: --model-target 必须是正整数 (收到: $MODEL_TARGET)" >&2; exit 2 ;;
esac

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "错误: 需要 python3 (免费层核验与实物复核报告依赖)" >&2
    exit 2
fi

# ---- 彩色输出 (与 run_e2e_smoke.sh / run_release_gate.sh 同约定) --
if { [ -t 1 ] || [ -n "${FORCE_COLOR:-}" ]; } && [ -z "${NO_COLOR:-}" ]; then
    RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    CYAN=$'\033[36m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
    RED=""; GREEN=""; YELLOW=""; CYAN=""; BOLD=""; RESET=""
fi

LOG_DIR="$(mktemp -d /tmp/magtile_v1_readiness_XXXXXX)"
CHECK_IDS=()
CHECK_NAMES=()
CHECK_PRIOS=()
CHECK_RESULTS=()
CHECK_TIMES=()
check_index=0

# run_check <编号> <P0|P1> <名称> <命令/函数...>
#   实时透传输出并留档; 失败不中断 (报告一次给全)。
run_check() {
    local id="$1" prio="$2" name="$3"; shift 3
    check_index=$((check_index + 1))
    local log="$LOG_DIR/$(printf '%02d' "$check_index")_${id}.log"
    echo ""
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    echo "${BOLD}${CYAN} $id [$prio] $name${RESET}"
    echo "${BOLD}${CYAN}==============================================================${RESET}"
    local start end status
    start=$(date +%s)
    "$@" 2>&1 | tee "$log"
    status=${PIPESTATUS[0]}
    end=$(date +%s)
    CHECK_IDS+=("$id"); CHECK_NAMES+=("$name"); CHECK_PRIOS+=("$prio")
    CHECK_TIMES+=("$((end - start))s")
    if [ "$status" -eq 0 ]; then
        CHECK_RESULTS+=("PASS")
        echo "${GREEN}${BOLD}[通过] $id $name${RESET}"
    else
        CHECK_RESULTS+=("FAIL")
        echo "${RED}${BOLD}[失败] $id $name (退出码 $status, 日志: $log)${RESET}"
    fi
    return "$status"
}

# skip_check <编号> <P0|P1> <名称> <原因>
skip_check() {
    local id="$1" prio="$2" name="$3" reason="$4"
    check_index=$((check_index + 1))
    CHECK_IDS+=("$id"); CHECK_NAMES+=("$name"); CHECK_PRIOS+=("$prio")
    CHECK_RESULTS+=("SKIP"); CHECK_TIMES+=("-")
    echo ""
    echo "${YELLOW}[跳过] $id [$prio] $name —— $reason${RESET}"
}

echo "${BOLD}=============================================================="
echo " MagTile Studio V1 上架就绪自动探测"
echo " 对账清单: docs/V1_LAUNCH_CHECKLIST.md"
echo " 项目根: $ROOT"
echo " 档位: $([ "$QUICK" -eq 1 ] && echo '--quick (跳过 E2E 冒烟 / 发布门禁)' || echo '全量')$([ "$STRICT" -eq 1 ] && echo ' + --strict (E2E 签核档)')"
echo " 内容体量门槛: $MODEL_TARGET (上架目标区间 200~250)"
echo "==============================================================${RESET}"

# =============================================================
# R1 内容体量: 模型 JSON 数 >= 门槛 (清单 §1 C1)
# =============================================================
check_model_count() {
    local count
    count="$(ls "$ROOT/data/models/"*.json 2>/dev/null | wc -l | tr -d ' ')"
    echo "模型 JSON: $count 个 (门槛 $MODEL_TARGET, 上架目标区间 200~250)"
    if [ "$count" -ge "$MODEL_TARGET" ]; then
        echo "[断言通过] 内容体量达标"
    else
        echo "[断言失败] 还差 $((MODEL_TARGET - count)) 个模型达到门槛"
        return 1
    fi
}

# =============================================================
# R2 目录登记 / 缩略图对账 (清单 §1 C3)
# =============================================================
check_catalog_sync() {
    "$PYTHON" - "$ROOT/data/models" "$ROOT/data/model_catalog.json" <<'PYEOF'
import json, sys
from pathlib import Path

models_dir, catalog_path = Path(sys.argv[1]), Path(sys.argv[2])
files = {p.stem for p in models_dir.glob("*.json")}
entries = json.loads(catalog_path.read_text(encoding="utf-8"))["models"]
ids = [m["id"] for m in entries]
with_thumb = [m["id"] for m in entries
              if m.get("thumbnail")
              and (catalog_path.parent / m["thumbnail"]).is_file()]
dangling = sorted(i for i in ids if i not in files)
unregistered = sorted(files - set(ids))
missing_thumb = sorted(set(ids) - set(with_thumb))

print(f"模型 JSON {len(files)} / 目录登记 {len(ids)} / 缩略图就绪 {len(with_thumb)}")
ok = True
if dangling:
    ok = False
    print(f"[断言失败] 目录悬空引用 (登记了但模型文件不存在) {len(dangling)} 个: "
          + " ".join(dangling[:10]))
if unregistered:
    ok = False
    print(f"[断言失败] 未登记进目录的模型 {len(unregistered)} 个: "
          + " ".join(unregistered[:10]) + (" ..." if len(unregistered) > 10 else ""))
if missing_thumb:
    ok = False
    print(f"[断言失败] 已登记但缩略图缺失/未就位 {len(missing_thumb)} 个: "
          + " ".join(missing_thumb[:10]) + (" ..." if len(missing_thumb) > 10 else ""))
if ok:
    print("[断言通过] 模型 / 目录 / 缩略图三方对账一致")
sys.exit(0 if ok else 1)
PYEOF
}

# =============================================================
# R8 隐私合规文档存在性 (清单 §5 V1; 定稿属 Manual, 见 M3)
# =============================================================
check_privacy_docs() {
    local missing=0 f
    for f in docs/SECURITY_AND_PRIVACY.md docs/PRIVACY_POLICY_DRAFT.md; do
        if [ -f "$ROOT/$f" ]; then
            echo "  存在: $f"
        else
            echo "[断言失败] 缺少 $f"; missing=1
        fi
    done
    [ "$missing" -eq 0 ] || return 1
    if grep -q "草稿" "$ROOT/docs/PRIVACY_POLICY_DRAFT.md" 2>/dev/null; then
        echo "  提示: 隐私政策仍为草稿, 法务定稿属人工项 (清单 §5 V2)"
    fi
    echo "[断言通过] 隐私合规文档齐备"
}

# =============================================================
# R9 桌面打包资产完备 (清单 §3 D1)
# =============================================================
check_packaging_assets() {
    local missing=0 f
    local files=(
        scripts/package_qt_desktop.md
        scripts/package_windows.md
        scripts/smoke_qt_linux_pack.sh
        scripts/check_lgpl_compliance.sh
        platforms/windows/packaging/starter_models.txt
        platforms/windows/packaging/THIRD_PARTY_NOTICES.md
        platforms/windows/packaging/CPackWindows.cmake
        platforms/windows/packaging/Product.wxs
    )
    for f in "${files[@]}"; do
        if [ -f "$ROOT/$f" ]; then
            echo "  存在: $f"
        else
            echo "[断言失败] 缺少 $f"; missing=1
        fi
    done
    local wf
    wf="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null)/.github/workflows/windows-release.yml"
    if [ -f "$wf" ]; then
        echo "  存在: .github/workflows/windows-release.yml (草案, 真实 runner 首跑属人工项 M1)"
    else
        echo "[断言失败] 缺少 .github/workflows/windows-release.yml"; missing=1
    fi
    [ "$missing" -eq 0 ] || return 1
    echo "[断言通过] 桌面打包资产齐备"
}

# =============================================================
# R10 计费适配层单测 (清单 §2 B1)
# =============================================================
check_billing_test() {
    local bin="$BUILD_DIR/magtile_billing_test"
    local db
    db="$(mktemp -u /tmp/magtile_readiness_billing_XXXXXX.db)"
    "$bin" "$db"
    local status=$?
    rm -f "$db"
    return "$status"
}

# =============================================================
# R11 真实商店计费接入探测 (清单 §2 B2, 分平台口径)
#
# Google Play (Android, 本检查): 真实计费在 Kotlin 壳层 ——
# PlayBillingManager.kt 持有 Play Billing Library (购买流 / 恢复 /
# 回执确认 / 启动静默恢复), 购买或恢复成功后经既有 JNI
# setSubscriptionActive 写 progress/subscription_settings 契约键
# (与 FakeBilling 同键, 免费层锁零改动)。探测四项接线证据:
#   1. PlayBillingManager.kt 存在;
#   2. 其内含 setSubscriptionActive 写入口调用 (回执 -> 契约键);
#   3. app/build.gradle.kts 引入 com.android.billingclient;
#   4. store_billing_client.cpp 无 Google Play 未接入守卫
#      (static_assert 拒绝档), 且文档化了 Kotlin 侧分工。
# 全部在位 = PASS (部分: 沙盒付费验收仍属人工项 B3)。
#
# Windows 商店档已单列 R11W 独立探测 (check_store_billing_windows,
# 见下), 不参与本检查口径。
# =============================================================
check_store_billing() {
    local src="$ROOT/src/billing/store_billing_client.cpp"
    local mgr="$ROOT/platforms/android/app/src/main/kotlin/com/magtile/studio/PlayBillingManager.kt"
    local gradle="$ROOT/platforms/android/app/build.gradle.kts"
    local failed=0
    if [ ! -f "$src" ]; then
        echo "[断言失败] 缺少 $src (计费适配层未落地)"; return 1
    fi
    if grep -q 'static_assert(false, "Google Play' "$src"; then
        echo "[断言失败] store_billing_client.cpp 的 Google Play 分支仍是未接入守卫 (static_assert 拒绝档)"
        failed=1
    else
        echo "  就绪: store_billing_client.cpp Google Play 分支已移除未接入守卫"
    fi
    if [ -f "$mgr" ]; then
        echo "  就绪: PlayBillingManager.kt (Kotlin 壳层 Play Billing 接线)"
        if grep -q "setSubscriptionActive" "$mgr"; then
            echo "  就绪: 购买/恢复回执经 setSubscriptionActive 写契约键 (与 FakeBilling 同键)"
        else
            echo "[断言失败] PlayBillingManager.kt 未调用 setSubscriptionActive —— 回执未接契约键写入口"
            failed=1
        fi
    else
        echo "[断言失败] 缺少 $mgr (Android Play Billing 未接线)"
        failed=1
    fi
    if [ -f "$gradle" ] && grep -q "com.android.billingclient" "$gradle"; then
        echo "  就绪: Play Billing Library 依赖已登记 (app/build.gradle.kts)"
    else
        echo "[断言失败] app/build.gradle.kts 未引入 com.android.billingclient:billing"
        failed=1
    fi
    [ "$failed" -eq 0 ] || return 1
    echo "[断言通过] Google Play 计费已接线 (部分就绪: Windows 商店档见 R11W; 沙盒付费验收仍属人工项 B3)"
}

# =============================================================
# R11W 真实商店计费接入探测 (Windows 商店档, 清单 §2 B2)
#
# Windows 侧真实计费在 C++ 跨商店接口缝内落地 (src/billing/
# store_billing_client.cpp 的 MAGTILE_BILLING_WINDOWS_STORE 宏分支):
# WinRT StoreContext (Windows.Services.Store, C++/WinRT 投影, 随
# Windows SDK 附带) 查商品 / RequestPurchaseAsync 收银台购买 /
# StoreAppLicense.AddOnLicenses 遍历有效订阅恢复 (商店账户即回执),
# 购买或恢复成功后写 progress/subscription_settings 契约键
# (setSubscriptionActive, 与 FakeBilling / Google Play 同键)。
# 宏仅 MSIX 商店包出包配置时开启 (商店上下文只在包身份下可用),
# 本地开发 / CI 保持 OFF 走 FakeBillingClient。探测五项接线证据:
#   1. store_billing_client.cpp 无 Windows 未接入守卫 (static_assert 拒绝档);
#   2. 其内含 winrt/Windows.Services.Store.h (WinRT SDK 接入);
#   3. RequestPurchaseAsync (购买流) 与 AddOnLicenses (许可证恢复) 在位;
#   4. setSubscriptionActive 写入口调用在位 (回执 -> 契约键);
#   5. 根 CMakeLists 有 MAGTILE_BILLING_WINDOWS_STORE 选项 + windowsapp 链接。
# 全部在位 = PASS (部分: Linux/CI 无法编译 WinRT 分支, 本探测只验
# 接线证据; MSIX 商店包出包 + Partner Center 商品配置 + 沙盒付费
# 验收仍属人工项 B3/M1)。
# =============================================================
check_store_billing_windows() {
    local src="$ROOT/src/billing/store_billing_client.cpp"
    local cmake_root="$ROOT/CMakeLists.txt"
    local failed=0
    if [ ! -f "$src" ]; then
        echo "[断言失败] 缺少 $src (计费适配层未落地)"; return 1
    fi
    if grep -q 'static_assert(false, "Windows' "$src"; then
        echo "[断言失败] store_billing_client.cpp 的 Windows 分支仍是未接入守卫 (static_assert 拒绝档)"
        failed=1
    else
        echo "  就绪: store_billing_client.cpp Windows 分支已移除未接入守卫"
    fi
    if grep -q 'winrt/Windows\.Services\.Store\.h' "$src"; then
        echo "  就绪: WinRT Windows.Services.Store 接入 (StoreContext)"
    else
        echo "[断言失败] store_billing_client.cpp 未接 winrt/Windows.Services.Store.h (WinRT SDK)"
        failed=1
    fi
    if grep -q 'RequestPurchaseAsync' "$src" && grep -q 'AddOnLicenses' "$src"; then
        echo "  就绪: 收银台购买流 (RequestPurchaseAsync) 与许可证恢复 (AddOnLicenses) 在位"
    else
        echo "[断言失败] 购买流 / 许可证恢复调用缺失 (RequestPurchaseAsync / AddOnLicenses)"
        failed=1
    fi
    if grep -q 'setSubscriptionActive' "$src"; then
        echo "  就绪: 购买/恢复回执经 setSubscriptionActive 写契约键 (与 FakeBilling / Google Play 同键)"
    else
        echo "[断言失败] store_billing_client.cpp 未调用 setSubscriptionActive —— 回执未接契约键写入口"
        failed=1
    fi
    if grep -q 'MAGTILE_BILLING_WINDOWS_STORE' "$cmake_root" && grep -q 'windowsapp' "$cmake_root"; then
        echo "  就绪: 构建接线 (根 CMakeLists MAGTILE_BILLING_WINDOWS_STORE 选项 + windowsapp 链接)"
    else
        echo "[断言失败] 根 CMakeLists.txt 缺 MAGTILE_BILLING_WINDOWS_STORE 选项或 windowsapp 链接"
        failed=1
    fi
    [ "$failed" -eq 0 ] || return 1
    echo "[断言通过] Windows 商店计费已接线 (部分就绪: MSIX 商店包出包 + Partner Center 商品配置 + 沙盒付费验收仍属人工项 B3/M1)"
}

# =============================================================
# R12 Android 构建链路资产 (清单 §4 A1)
# =============================================================
check_android_assets() {
    local missing=0 f
    for f in platforms/android/README.md \
             platforms/android/app/build.gradle.kts \
             platforms/android/jni/magtile_jni.cpp; do
        if [ -f "$ROOT/$f" ]; then
            echo "  存在: $f"
        else
            echo "[断言失败] 缺少 $f"; missing=1
        fi
    done
    local wf
    wf="$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null)/.github/workflows/android.yml"
    if [ -f "$wf" ]; then
        echo "  存在: .github/workflows/android.yml"
    else
        echo "[断言失败] 缺少 .github/workflows/android.yml"; missing=1
    fi
    [ "$missing" -eq 0 ] || return 1
    echo "[断言通过] Android 构建链路资产齐备"
}

# =============================================================
# R13 Android release 签名接线 (清单 §4 A3)
# 口径: build.gradle.kts 含 signingConfigs 块 + 签名配置模板
# keystore.properties.example 存在。真实 keystore 刻意不入库
# (从工程根 keystore.properties 运行期读取, .gitignore 已排除),
# 密钥生成与商店档出包属人工项 M2; 流程见 platforms/android/SIGNING.md。
# =============================================================
check_android_signing() {
    local gradle="$ROOT/platforms/android/app/build.gradle.kts"
    local example="$ROOT/platforms/android/keystore.properties.example"
    local failed=0
    [ -f "$gradle" ] || { echo "[断言失败] 缺少 $gradle"; return 1; }
    if grep -q "signingConfigs" "$gradle"; then
        echo "  存在: signingConfigs 块 (app/build.gradle.kts)"
    else
        echo "[断言失败] build.gradle.kts 无 signingConfigs —— release 签名未接线,"
        echo "  商店 release 出包前须补签名配置 (清单 §4 A3, 流程 platforms/android/SIGNING.md)"
        failed=1
    fi
    if [ -f "$example" ]; then
        echo "  存在: platforms/android/keystore.properties.example (配置模板)"
    else
        echo "[断言失败] 缺少 platforms/android/keystore.properties.example ——"
        echo "  签名配置模板缺失 (密钥不入库, 模板是唯一入库载体, 见 SIGNING.md)"
        failed=1
    fi
    [ "$failed" -eq 0 ] || return 1
    echo "[断言通过] release 签名已接线 (真实 keystore 生成与商店出包仍属人工项 M2, 见 SIGNING.md)"
}

# ---- 检查编排 ----------------------------------------------------
run_check R1 P0 "内容体量 (模型 JSON >= $MODEL_TARGET)"           check_model_count
run_check R2 P1 "目录登记 / 缩略图对账"                            check_catalog_sync
run_check R3 P0 "免费层清单对齐 (verify_free_tier)" \
    "$PYTHON" "$ROOT/tools/verify_free_tier.py" \
    --models-dir "$ROOT/data/models" \
    --catalog "$ROOT/data/tile_catalog.json"

if [ "$QUICK" -eq 1 ]; then
    skip_check R4 P0 "E2E 冒烟 (run_e2e_smoke.sh)"      "--quick (签核前必须全量跑)"
    skip_check R5 P0 "发布门禁快检 (run_release_gate.sh)" "--quick (签核前必须全量跑)"
else
    e2e_args=(--build-dir "$BUILD_DIR" --qt-build-dir "$QT_BUILD_DIR")
    [ "$STRICT" -eq 1 ] && e2e_args+=(--strict)
    run_check R4 P0 "E2E 冒烟 (run_e2e_smoke.sh$([ "$STRICT" -eq 1 ] && echo ' --strict'))" \
        bash "$ROOT/tools/run_e2e_smoke.sh" "${e2e_args[@]}"
    run_check R5 P0 "发布门禁快检 (run_release_gate.sh)" \
        bash "$ROOT/tools/run_release_gate.sh" "$BUILD_DIR"
fi

run_check R6 P0 "实物抽样包 V1 复核缺口 (physical_sample_pack)" \
    "$PYTHON" "$ROOT/tools/physical_sample_pack.py" "$ROOT/data/models" \
    --no-bom --fail-on-missing-sample
run_check R7 P0 "D4+ 实物复核全集清零 (list_physical_pending)" \
    "$PYTHON" "$ROOT/tools/list_physical_pending.py" "$ROOT/data/models" \
    --fail-on-pending
run_check R8 P0 "隐私合规文档存在性"                              check_privacy_docs
run_check R9 P0 "桌面打包资产完备"                                check_packaging_assets

if [ -x "$BUILD_DIR/magtile_billing_test" ]; then
    run_check R10 P1 "计费适配层单测 (magtile_billing_test)"      check_billing_test
else
    skip_check R10 P1 "计费适配层单测 (magtile_billing_test)" \
        "构建目录无该测试 (cmake --build \"$BUILD_DIR\" --target magtile_billing_test 后重试)"
fi

run_check R11 P0 "真实商店计费接入 (Google Play 接线)"            check_store_billing
run_check R11W P0 "真实商店计费接入 (Windows 商店档接线)"          check_store_billing_windows
run_check R12 P1 "Android 构建链路资产"                           check_android_assets
run_check R13 P0 "Android release 签名配置"                       check_android_signing
run_check R14 P0 "商店上架文档守卫 (validate_store_listing)" \
    "$PYTHON" "$ROOT/tools/validate_store_listing.py"
run_check R15 P0 "国内合规清单守卫 (check_china_compliance_docs)" \
    "$PYTHON" "$ROOT/tools/check_china_compliance_docs.py"
run_check R16 P0 "儿童友好文案守卫 (check_child_friendly_copy)" \
    "$PYTHON" "$ROOT/tools/check_child_friendly_copy.py"

# ---- 纯人工项提醒 (不参与判定, 对应清单各节 Manual 行) -----------
skip_check M1 P0 "Windows/macOS 实机打包验收 + 代码签名/公证" "Manual, 见清单 §3 D2~D6"
skip_check M2 P0 "Android 真机验收 + 商店上架资料"            "Manual, 见清单 §4 A4/A5"
skip_check M3 P0 "隐私政策法务定稿 + 合规自查单"              "Manual, 见清单 §5 V2/V4"
skip_check M4 P0 "E2E 矩阵 P0 人工要点打钩与签核记录"         "Manual, 见 E2E_TEST_MATRIX.md §3"
skip_check M5 P0 "实物抽样实搭签核 (R6/R7 只报告缺口)"        "Manual, 见清单 §8 与 PHYSICAL_REBUILD_CHECKLIST.md"
skip_check M6 P0 "软著 / ICP 备案 / 开发者账号 / 运营主体"    "Manual, 见清单 §9 与 CHINA_STORE_COMPLIANCE.md (文档完整性已由 R15 守卫)"

# ---- 总结报告 ----------------------------------------------------
pass_count=0; fail_count=0; skip_count=0; p0_fail=0
echo ""
echo "${BOLD}=============================================================="
echo " V1 上架就绪探测报告 (对账清单: docs/V1_LAUNCH_CHECKLIST.md)"
echo "==============================================================${RESET}"
for i in "${!CHECK_IDS[@]}"; do
    case "${CHECK_RESULTS[$i]}" in
        PASS) pass_count=$((pass_count + 1))
              printf '  %s%-6s%s %-4s [%s] %-46s %s\n' "$GREEN" "PASS" "$RESET" \
                  "${CHECK_IDS[$i]}" "${CHECK_PRIOS[$i]}" "${CHECK_NAMES[$i]}" "${CHECK_TIMES[$i]}" ;;
        FAIL) fail_count=$((fail_count + 1))
              [ "${CHECK_PRIOS[$i]}" = "P0" ] && p0_fail=$((p0_fail + 1))
              printf '  %s%-6s%s %-4s [%s] %-46s %s\n' "$RED" "FAIL" "$RESET" \
                  "${CHECK_IDS[$i]}" "${CHECK_PRIOS[$i]}" "${CHECK_NAMES[$i]}" "${CHECK_TIMES[$i]}" ;;
        SKIP) skip_count=$((skip_count + 1))
              printf '  %s%-6s%s %-4s [%s] %-46s %s\n' "$YELLOW" "SKIP" "$RESET" \
                  "${CHECK_IDS[$i]}" "${CHECK_PRIOS[$i]}" "${CHECK_NAMES[$i]}" "${CHECK_TIMES[$i]}" ;;
    esac
done
echo "${BOLD}--------------------------------------------------------------${RESET}"
total=$((pass_count + fail_count + skip_count))
echo " 合计 $total 项: ${GREEN}$pass_count PASS${RESET} / ${RED}$fail_count FAIL${RESET} / ${YELLOW}$skip_count SKIP${RESET} (其中 P0 失败 $p0_fail 项)"
if [ "$p0_fail" -gt 0 ]; then
    echo "${RED}${BOLD} 结论: 存在 $p0_fail 项 P0 失败 —— 未达上架就绪, 逐项对照清单补齐${RESET}"
    echo " 分项日志: $LOG_DIR"
    exit 1
fi
if [ "$fail_count" -gt 0 ]; then
    echo "${YELLOW} 提醒: 存在 $fail_count 项 P1 失败 (不阻断); 上架须在签核记录中留痕${RESET}"
fi
if [ "$skip_count" -gt 0 ]; then
    echo "${YELLOW} 提醒: $skip_count 项 SKIP (含 Manual 项); 人工侧按清单逐条打钩归档${RESET}"
fi
echo "${GREEN}${BOLD} 结论: 自动探测无 P0 失败${RESET}"
rm -rf "$LOG_DIR"
exit 0

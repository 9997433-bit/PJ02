#!/usr/bin/env bash
# =============================================================
# MagTile Studio - Android 主路径仪器冒烟 (androidTest) 设备执行脚本
#
# 有设备时跑, 无设备时温和跳过 —— CI/本地都能无脑挂上:
#   1. 定位 adb (PATH 优先, 退回 ANDROID_HOME / ANDROID_SDK_ROOT /
#      local.properties 的 sdk.dir);
#   2. 无 adb / 无在线设备: 打印跳过原因, 默认 exit 0 (无设备的
#      流水线不红); MAGTILE_REQUIRE_DEVICE=1 时改为 exit 1
#      (真机流水线要求必须有设备);
#   3. 设备 ABI 不含 arm64-v8a (APK 首发只出 arm64) 同样温和跳过;
#   4. 唤醒屏幕 + 解锁 keyguard (Espresso 点击需要窗口焦点), 然后
#      ./gradlew :app:connectedDebugAndroidTest 一条龙:
#      构建 app APK + 测试 APK -> 安装 -> 跑仪器测试套件 -> 卸载。
#      套件 (README 第五节; 真机 QA 可自动化部分, 人工项另见
#      docs/reports/QA_ANDROID_DEVICE_CHECKLIST.md):
#        MainActivitySmokeTest  启动 -> 列表非空 -> 首张免费卡 -> 详情弹窗
#        TutorialFlowTest       断点续搭 / 完成链路+首搭成就 / 手势事件链路
#        ParentGateFlowTest     家长门出门/答错温和/作答放行/会话守卫
#        SubscriptionLockTest   订阅锁可见性 (非免费温和提示 / 订阅解锁)
#        DeviceManualQaTest     人工项占位 (@Ignore, 报告中为 skipped)
#
# 用法 (任意目录均可):
#   platforms/android/run_instrumented_smoke.sh
#   MAGTILE_REQUIRE_DEVICE=1 platforms/android/run_instrumented_smoke.sh
#
# 无设备的 CI 编译门 (只编译不执行, 与本脚本互补):
#   ./gradlew :app:assembleDebugAndroidTest
#
# 测试报告: app/build/reports/androidTests/connected/
# =============================================================
set -euo pipefail
cd "$(dirname "$0")"

skip() {
    printf '[跳过] %s\n' "$1"
    if [[ "${MAGTILE_REQUIRE_DEVICE:-0}" == "1" ]]; then
        printf '[失败] MAGTILE_REQUIRE_DEVICE=1 要求必须有设备\n' >&2
        exit 1
    fi
    exit 0
}

# ---- 1. 定位 adb ---------------------------------------------------
ADB="$(command -v adb || true)"
if [[ -z "$ADB" ]]; then
    for sdk in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}" \
               "$(sed -n 's/^sdk\.dir=//p' local.properties 2>/dev/null)"; do
        if [[ -n "$sdk" && -x "$sdk/platform-tools/adb" ]]; then
            ADB="$sdk/platform-tools/adb"
            break
        fi
    done
fi
[[ -n "$ADB" ]] || skip "找不到 adb (PATH / ANDROID_HOME / local.properties 均无)"

# ---- 2. 是否有在线设备 (state == device, 排除 offline/unauthorized) --
mapfile -t DEVICES < <("$ADB" devices | awk 'NR>1 && $2=="device" {print $1}')
[[ ${#DEVICES[@]} -gt 0 ]] || skip "没有在线的 adb 设备 (真机/模拟器接入后重跑即可)"

# ---- 3. ABI 匹配 (APK 首发只出 arm64-v8a, README 第一节) -------------
# 多设备时 Gradle 会在全部设备上执行, 这里逐台校验并唤醒
for serial in "${DEVICES[@]}"; do
    abilist="$("$ADB" -s "$serial" shell getprop ro.product.cpu.abilist | tr -d '\r')"
    if [[ "$abilist" != *arm64-v8a* ]]; then
        skip "设备 $serial 不支持 arm64-v8a (abilist: $abilist); APK 首发只出 arm64"
    fi
    # 唤醒 + 解锁 (Espresso 点击需要窗口焦点; 失败不阻断, 设备可能本就亮屏)
    "$ADB" -s "$serial" shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1 || true
    "$ADB" -s "$serial" shell wm dismiss-keyguard >/dev/null 2>&1 || true
done

# ---- 4. 构建 + 安装 + 执行 + 卸载 (Gradle 托管的一条龙) --------------
printf '[执行] %d 台设备: %s\n' "${#DEVICES[@]}" "${DEVICES[*]}"
./gradlew :app:connectedDebugAndroidTest

printf '[通过] Android 主路径仪器冒烟全绿 (报告: app/build/reports/androidTests/connected/)\n'

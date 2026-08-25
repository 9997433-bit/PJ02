import QtQuick
import QtQuick.Controls
import MagTile.Studio

// =============================================================
// 主窗口: StackView 导航 (首页 -> 模型库 -> 模型详情 -> 教程 /
// 首页 -> 家长门|家长中心 -> 设置|订阅, 任意界面 <= 2 步回首页,
// UI_UX_SPEC.md §3 导航铁律)。最小窗口 1024x640 (§13)。
// 后端桥由 main.cpp 注入: studio (模型库) / inventory (库存) /
// parentGate (家长门, §9) / appSettings (设置, §8) / tts (朗读, §4.2)。
// 家长区路由: 无有效会话先进家长门 (过门后原位替换为家长中心),
// 15 分钟会话内免重复验证; 会话到期或锁定由下方守卫统一退回首页。
// 订阅入口 (首页儿童侧温和入口 / 家长中心 / 设置页) 统一经
// openSubscriptionZone 过同一道家长门 —— 订阅页只在门后可见 (§11)。
// 「开始搭建」统一走 studio.buildRequested 信号路由 —— QT-3 教程
// 视口就绪后只换 TutorialPage 内容, 路由不变。
// =============================================================
ApplicationWindow {
    id: window

    visible: true
    width: 1280
    height: 800
    minimumWidth: 1024
    minimumHeight: 640
    title: qsTr("MagTile 磁力片工坊")
    color: Theme.surfaceAlt

    Component.onCompleted: {
        // 字号三档与减少动效 (§4.7): 设置页改动经 Theme 单例即时全应用生效
        Theme.fontScale = Qt.binding(function() { return appSettings.fontScalePercent / 100.0 })
        Theme.reduceMotion = Qt.binding(function() { return appSettings.reduceMotion })
        // --parent-gate 深链: 启动直开家长门 (评审 / 冒烟, 同 GL 版)
        if (parentGate.deepLinkRequested) {
            parentGate.openGate()
            stack.push(parentGateComponent)
        }
        // --smoke-open-progress 深链: 启动直开进度页 (评审 / 冒烟, QT-4)
        if (smokeOpenProgress) {
            stack.push(progressComponent)
        }
    }

    /// 温和的占位提示 (P3 零挫败: 只说"即将上线", 永不弹"失败")
    function showToast(message) {
        toastLabel.text = message
        toast.open()
        toastTimer.restart()
    }

    /// 家长门通过后落地的页面: "area" = 家长中心 (默认), "subscription"
    /// = 订阅页 (QT-5 入口直达, 依旧在门后, §11)
    property string parentZoneTarget: "area"

    /// 家长区入口 (§9): 15 分钟会话内直达家长中心, 否则先过家长门
    function openParentZone() {
        parentZoneTarget = "area"
        if (parentGate.sessionActive) {
            stack.push(parentAreaComponent)
        } else {
            parentGate.openGate()   // 每次进门都是新题, 防背题
            stack.push(parentGateComponent)
        }
    }

    /// 订阅入口统一路由 (QT-5): 会话有效直达订阅页, 否则先过家长门
    /// (过门后原位替换为订阅页) —— 订阅页只可能出现在家长门之后 (§11),
    /// 且导航深度保持 1, 任意入口进来都 <= 2 步回首页 (§3)
    function openSubscriptionZone() {
        parentZoneTarget = "subscription"
        if (parentGate.sessionActive) {
            stack.push(subscriptionComponent)
        } else {
            parentGate.openGate()
            stack.push(parentGateComponent)
        }
    }

    StackView {
        id: stack
        anchors.fill: parent
        initialItem: homeComponent

        pushEnter: Transition {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.animMs; easing.type: Easing.OutQuad }
        }
        popExit: Transition {
            NumberAnimation { property: "opacity"; from: 1; to: 0; duration: Theme.animMs; easing.type: Easing.OutQuad }
        }
    }

    // 首启年龄段引导 (QT-5, §10.1): 盖在首页之上的温和全屏引导, 从未
    // 选过年龄段 (无 age_mode 键且无 onboarding_age_done 标记) 时出现
    // 一次; 三档大卡片选完即落盘并淡出露出首页, 家长之后可在设置改档
    AgeOnboardingPage {
        id: ageOnboarding
        anchors.fill: parent
    }

    Component {
        id: homeComponent
        HomePage {
            onOpenLibrary: stack.push(libraryComponent)
            onOpenModel: function(modelId) { stack.push(detailComponent, { modelId: modelId }) }
            onOpenInventory: stack.push(inventoryComponent)
            onOpenProgress: stack.push(progressComponent)
            onOpenParentArea: window.openParentZone()
            onOpenSubscription: window.openSubscriptionZone()
            onNotify: function(message) { window.showToast(message) }
        }
    }

    // 进度页「我的作品」+ 成就墙 (QT-4, §7): 首页儿童侧直达 (§5.3),
    // 作品行点击进模型详情 (继续/再搭都走详情页既有大按钮路由)
    Component {
        id: progressComponent
        ProgressPage {
            onBack: stack.pop()
            onOpenModel: function(modelId) { stack.push(detailComponent, { modelId: modelId }) }
            onOpenAchievements: stack.push(achievementsComponent)
            // 空态「去模型库挑一个」: 落到 首页 -> 模型库 (<= 2 步回首页 §3)
            onOpenLibrary: {
                stack.pop(null)
                stack.push(libraryComponent)
            }
        }
    }

    Component {
        id: achievementsComponent
        AchievementsPage {
            onBack: stack.pop()
        }
    }

    Component {
        id: parentGateComponent
        ParentGatePage {
            // 过门后原位替换为目标页 (家长中心或订阅页, 导航深度保持 1,
            // <= 2 步回首页); 目标由 openParentZone/openSubscriptionZone 设定
            onPassed: stack.replace(window.parentZoneTarget === "subscription"
                                    ? subscriptionComponent : parentAreaComponent)
            onDismissed: stack.pop()
        }
    }

    Component {
        id: parentAreaComponent
        ParentAreaPage {
            onBack: stack.pop()
            onOpenSettings: stack.push(settingsComponent)
            onOpenSubscription: stack.push(subscriptionComponent)
            // 「锁定家长区」只结束会话, 退回首页由下方会话守卫统一处理
        }
    }

    Component {
        id: settingsComponent
        SettingsPage {
            onBack: stack.pop()
            // 设置页 -> 订阅: 原位替换 (不叠加深度, 保证订阅页也 <= 2 步回首页)
            onOpenSubscription: stack.replace(subscriptionComponent)
        }
    }

    Component {
        id: subscriptionComponent
        SubscriptionPage {
            onBack: stack.pop()
            onNotify: function(message) { window.showToast(message) }
        }
    }

    Component {
        id: libraryComponent
        LibraryPage {
            onBack: stack.pop()
            onOpenDetail: function(modelId) { stack.push(detailComponent, { modelId: modelId }) }
            onOpenInventory: stack.push(inventoryComponent)
            onNotify: function(message) { window.showToast(message) }
        }
    }

    Component {
        id: inventoryComponent
        InventoryPage {
            onBack: stack.pop()
            onNotify: function(message) { window.showToast(message) }
            // 「保存, 看看我能搭什么」: 开启筛选后落到模型库
            // (导航深度保持 首页 -> 模型库, 任意界面 <= 2 步回首页)
            onLookWhatICanBuild: {
                studio.libraryFilter.buildableOnly = true
                stack.pop(null)
                stack.push(libraryComponent)
            }
        }
    }

    Component {
        id: detailComponent
        DetailPage {
            onBack: stack.pop()
            onNotify: function(message) { window.showToast(message) }
            // 订阅内容「请家长来解锁」: 与其余订阅入口同一路由 (先过
            // 家长门, 过门后原位替换为订阅页, §11)
            onOpenSubscription: window.openSubscriptionZone()
        }
    }

    Component {
        id: tutorialComponent
        TutorialPage {
            onBack: stack.pop()
            onHome: stack.pop(null)
            onNotify: function(message) { window.showToast(message) }
        }
    }

    Component {
        id: celebrationComponent
        CelebrationPage {
            // 「再搭一次」走统一的 startBuild 路由 (下方 buildRequested
            // 处理器会原位替换庆祝页, 导航深度不增长)
            onBuildAgain: studio.startBuild(modelId)
            // 「回模型库」落到 首页 -> 模型库 (<= 2 步回首页 §3)
            onBackToLibrary: {
                stack.pop(null)
                stack.push(libraryComponent)
            }
        }
    }

    // 「开始搭建」统一路由: 详情页 (或未来任何入口) 调 studio.startBuild,
    // 这里接 buildRequested 进教程页; 教程完成后接 buildCompleted 把
    // 教程页原位替换为完成庆祝页 (QT-4, 返回不会退回已完成的教程)
    Connections {
        target: studio
        function onBuildRequested(modelId, modelName, currentStep, stepCount) {
            var params = {
                modelId: modelId,
                modelName: modelName,
                currentStep: currentStep,
                stepCount: stepCount
            }
            if (stack.currentItem && stack.currentItem.isCelebrationPage === true) {
                stack.replace(tutorialComponent, params)   // 庆祝页「再搭一次」
            } else {
                stack.push(tutorialComponent, params)
            }
        }
        function onBuildCompleted(modelId, modelName, pieces, stepCount) {
            var params = {
                modelId: modelId,
                modelName: modelName,
                pieces: pieces,
                steps: stepCount
            }
            if (stack.currentItem && stack.currentItem.isTutorialPage === true) {
                stack.replace(celebrationComponent, params)
            } else {
                stack.push(celebrationComponent, params)   // 冒烟深链等非教程入口
            }
        }
    }

    // 家长会话守卫 (SECURITY_AND_PRIVACY.md §6.2): 会话到期或被锁定时,
    // 若仍停留在家长区任意页面 (requiresParentSession), 统一退回首页
    Connections {
        target: parentGate
        function onSessionChanged() {
            if (!parentGate.sessionActive && stack.currentItem
                    && stack.currentItem.requiresParentSession === true) {
                stack.pop(null)
                window.showToast("家长区已锁上, 再进入需要重新答题")
            }
        }
    }

    // ---- 冒烟自动驾驶 (--smoke-parent-flow, 无头 CI 专用) -------------
    // 进度页 -> 成就墙 (QT-4) -> 回首页 -> 家长门 -> 提交标准答案过门
    // -> 家长中心 -> 设置 -> 订阅, 逐页驻留; 全程无误后置
    // smokeParentFlowOk, main.cpp 在 --smoke-quit-ms 到点时据此决定
    // 退出码 —— 保证这些页面在 CI 里真实实例化过。
    property bool smokeParentFlowOk: false
    Timer {
        id: smokeFlowTimer
        property int stage: 0
        interval: 250
        repeat: true
        running: smokeParentFlow
        onTriggered: {
            stage += 1
            if (stage === 1) {
                stack.push(progressComponent)                        // 进度页 (QT-4)
            } else if (stage === 2) {
                stack.push(achievementsComponent)                    // 成就墙 (QT-4)
            } else if (stage === 3) {
                stack.pop(null)                                      // 回首页
                window.openParentZone()                              // 家长门
            } else if (stage === 4) {
                parentGate.submitAnswer(parentGate.expectedAnswer()) // 过门 -> 家长中心
            } else if (stage === 5) {
                stack.push(settingsComponent)                        // 设置页
            } else if (stage === 6) {
                stack.pop()
                stack.push(subscriptionComponent)                    // 订阅占位页
            } else {
                window.smokeParentFlowOk = parentGate.sessionActive
                    && stack.currentItem !== null
                    && stack.currentItem.requiresParentSession === true
                stop()
            }
        }
    }

    // ---- 首启年龄段引导冒烟 (--smoke-age-onboarding, 无头 CI 专用) ----
    // 首启 (存档无 age_mode): 断言引导已出现 -> 选 4-6 档 (与卡片点击
    // 同一条 choose 路径) -> 断言引导收起且档位落盘; 二次启动 (已有
    // 标记): 断言引导确实不再出现。全程无误后置 smokeAgeOnboardingOk,
    // main.cpp 在 --smoke-quit-ms 到点时据此决定退出码。
    property bool smokeAgeOnboardingOk: false
    Timer {
        id: smokeAgeTimer
        property int stage: 0
        interval: 400
        repeat: true
        running: smokeAgeOnboarding
        onTriggered: {
            stage += 1
            if (stage === 1) {
                if (appSettings.ageOnboardingPending) {
                    if (!ageOnboarding.visible) { stop(); return }  // 该出现没出现: 判负
                    ageOnboarding.choose("age_4_6")
                }
                // 已完成过引导: 本拍不动作, 下一拍复核引导确实没出现
            } else {
                window.smokeAgeOnboardingOk = !appSettings.ageOnboardingPending
                    && !ageOnboarding.visible
                    && appSettings.ageModeId !== ""
                stop()
            }
        }
    }

    // ---- 底部浮出提示 (琥珀软底, 2.5s 自动消失) ----------------------
    Popup {
        id: toast
        x: Math.round((window.width - width) / 2)
        y: window.height - height - Theme.spacingLarge
        padding: Theme.spacing
        background: Rectangle {
            radius: Theme.radiusSheet
            color: Theme.warningSoft
            border.color: Theme.warning
            border.width: 1
        }
        contentItem: Text {
            id: toastLabel
            font.pixelSize: Theme.fontBody
            color: Theme.textPrimary
        }
        Timer {
            id: toastTimer
            interval: 2500
            onTriggered: toast.close()
        }
    }
}

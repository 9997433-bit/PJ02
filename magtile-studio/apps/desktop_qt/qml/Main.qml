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
            onNotify: function(message) { window.showToast(message) }
            // 清除本地数据后 (SECURITY_AND_PRIVACY.md §4 C4/Z8): 设置与
            // 朗读内存复位、模型库重读空存档, 温和回到首次启动状态;
            // 先退回首页再锁家长会话 (顺序保证守卫不重复弹提示)
            onDataCleared: {
                appSettings.resetToDefaults()
                tts.resetToDefaults()
                studio.reload()
                stack.pop(null)
                parentGate.lockSession()
                window.showToast("本机数据已清除, 一切都回到了最初的样子")
            }
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

    // ---- 库存页深链冒烟 (--smoke-open-inventory, 无头 CI 专用) --------
    // E2E-09a: 直开库存录入页 -> 断言片型行全量加载 -> 与 + 按钮同一条
    // updateCount 路径给第一种片型 +3 -> 与「保存库存」按钮同一条
    // saveAll 路径落盘 (保存后自动返回) -> 断言库存已登记且总数一致。
    // 全程无误后置 smokeInventoryOk, main.cpp 在 --smoke-quit-ms 到点时
    // 据此决定退出码; 存档侧行数/总数由 tests/test_qt_ui_paths_smoke.sh
    // 直读 SQLite 补齐断言。
    property bool smokeInventoryOk: false
    Timer {
        id: smokeInventoryTimer
        property int stage: 0
        property int expectedTotal: 0
        interval: 300
        repeat: true
        running: smokeOpenInventory
        onTriggered: {
            stage += 1
            if (stage === 1) {
                stack.push(inventoryComponent)                       // 库存页深链
            } else if (stage === 2) {
                var page = stack.currentItem
                if (!page || page.rowsData === undefined
                        || page.rowsData.length === 0) { stop(); return }
                var shapeId = page.rowsData[0].shapeId
                page.updateCount(shapeId, page.counts[shapeId] + 3)  // 与 + 按钮同一条路径
                expectedTotal = page.totalCount
                page.saveAll(false)                                  // 与「保存库存」同一条路径
            } else {
                window.smokeInventoryOk = expectedTotal > 0
                    && inventory.configured
                    && inventory.totalCount === expectedTotal
                    && studio.inventoryConfigured
                stop()
            }
        }
    }

    // ---- 模型库筛选切换冒烟 (--smoke-library-filters, 无头 CI 专用) ---
    // E2E-04a: 打开模型库后走 FilterChip 同一条属性写路径逐项切换并
    // 对账: 基线全量 -> 「🎁 免费模型」数量 = freeModelCount -> 「↺ 看
    // 全部模型」复位 -> 主题筛选真在过滤 -> 难度 1~5 分片求和 = 全库
    // (互斥且完备) -> 最终复位。全程无误后置 smokeLibraryFiltersOk。
    property bool smokeLibraryFiltersOk: false
    Timer {
        id: smokeFiltersTimer
        property int stage: 0
        interval: 300
        repeat: true
        running: smokeLibraryFilters
        onTriggered: {
            stage += 1
            var filter = studio.libraryFilter
            if (stage === 1) {
                stack.push(libraryComponent)
            } else if (stage === 2) {
                if (studio.modelCount === 0 || filter.count !== studio.modelCount
                        || filter.hasActiveFilters) { stop(); return }
                filter.freeOnly = true                                // 「🎁 免费模型」筛选片
            } else if (stage === 3) {
                if (!filter.hasActiveFilters
                        || filter.count !== studio.freeModelCount
                        || filter.count >= studio.modelCount) { stop(); return }
                filter.clearFilters()                                 // 「↺ 看全部模型」
            } else if (stage === 4) {
                if (filter.hasActiveFilters || filter.freeOnly
                        || filter.count !== studio.modelCount
                        || studio.themes.length === 0) { stop(); return }
                filter.theme = studio.themes[0]                       // 主题筛选片
            } else if (stage === 5) {
                if (filter.count === 0 || filter.count >= studio.modelCount) { stop(); return }
                filter.theme = ""
                // 难度分片互斥且完备: 1~5 星逐档筛选求和应恰为全库
                var sum = 0
                for (var d = 1; d <= 5; ++d) {
                    filter.difficulty = d                             // 难度星级筛选片
                    sum += filter.count
                }
                filter.difficulty = 0
                if (sum !== studio.modelCount) { stop(); return }
                filter.clearFilters()
            } else {
                window.smokeLibraryFiltersOk = !filter.hasActiveFilters
                    && filter.count === studio.modelCount
                stop()
            }
        }
    }

    // ---- 非免费锁冒烟 (--smoke-locked-model <ID>, 无头 CI 专用) -------
    // E2E-11c 订阅内容付费边界 (§11): 直开该模型详情页, 断言 locked
    // 上锁 (isFree 显式 false 且未订阅), 再走「请家长来解锁」大按钮
    // 同一条 openSubscription 路由 —— 必须落在家长门 (不开教程、订阅页
    // 不得先于过门出现)。全程无误后置 smokeLockedModelOk; 教程未被
    // 误开 (无进度写档) 由 tests/test_qt_ui_paths_smoke.sh 直读 SQLite
    // 补齐断言。
    property bool smokeLockedModelOk: false
    Timer {
        id: smokeLockedTimer
        property int stage: 0
        interval: 300
        repeat: true
        running: smokeLockedModelId !== ""
        onTriggered: {
            stage += 1
            if (stage === 1) {
                var d = studio.modelDetail(smokeLockedModelId)
                if (d.found !== true || d.isFree !== false
                        || billing.subscriptionActive) { stop(); return }
                stack.push(detailComponent, { modelId: smokeLockedModelId })
            } else if (stage === 2) {
                var page = stack.currentItem
                if (!page || page.locked !== true) { stop(); return }
                page.openSubscription()          // 与「请家长来解锁」大按钮同一条路由
            } else {
                var current = stack.currentItem
                window.smokeLockedModelOk = current !== null
                    && current.answerInput !== undefined      // 家长门 (软键盘输入缓冲)
                    && current.isTutorialPage !== true        // 教程没被误开
                    && current.requiresParentSession !== true // 订阅页不得先于过门出现
                    && window.parentZoneTarget === "subscription"
                    && !parentGate.sessionActive
                stop()
            }
        }
    }

    // ---- 进度页有数据冒烟 (--smoke-progress-data, 无头 CI 专用) -------
    // E2E-12b: 存档已有完成记录时 (先以 --smoke-complete-model 造档)
    // 直开进度页, 断言已完成列表与统计对账、成就列表非空且至少一枚
    // 徽章点亮 (完成即解锁首搭成就), 再走「看看全部徽章 ▶」同一路由进
    // 成就墙全览复核同一数据源。全程无误后置 smokeProgressDataOk。
    property bool smokeProgressDataOk: false
    Timer {
        id: smokeProgressDataTimer
        property int stage: 0
        property bool progressPageOk: false
        interval: 300
        repeat: true
        running: smokeProgressData
        onTriggered: {
            stage += 1
            if (stage === 1) {
                stack.push(progressComponent)
            } else if (stage === 2) {
                var page = stack.currentItem
                if (!page || page.badges === undefined) { stop(); return }
                var unlocked = 0
                for (var i = 0; i < page.badges.length; ++i) {
                    if (page.badges[i].unlocked) ++unlocked
                }
                progressPageOk = studio.completedCount > 0
                    && page.completedRows.length === studio.completedCount
                    && page.badges.length > 0
                    && unlocked >= 1
                if (!progressPageOk) { stop(); return }
                stack.push(achievementsComponent)    // 「看看全部徽章 ▶」同一路由
            } else {
                var wall = stack.currentItem
                window.smokeProgressDataOk = progressPageOk
                    && wall !== null && wall.badges !== undefined
                    && wall.badges.length > 0
                    && studio.achievementCount >= 1
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

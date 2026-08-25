import QtQuick
import QtQuick.Controls
import MagTile.Studio

// =============================================================
// 主窗口: StackView 导航 (首页 -> 模型库 -> 模型详情 -> 教程,
// 任意界面 <= 2 步回首页, UI_UX_SPEC.md §3 导航铁律)。
// 最小窗口 1024x640 (§13)。后端桥 "studio" (StudioBackend) 由
// main.cpp 注入; 「开始搭建」统一走 studio.buildRequested 信号
// 路由 —— QT-3 教程视口就绪后只换 TutorialPage 内容, 路由不变。
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

    /// 温和的占位提示 (P3 零挫败: 只说"即将上线", 永不弹"失败")
    function showToast(message) {
        toastLabel.text = message
        toast.open()
        toastTimer.restart()
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

    Component {
        id: homeComponent
        HomePage {
            onOpenLibrary: stack.push(libraryComponent)
            onOpenModel: function(modelId) { stack.push(detailComponent, { modelId: modelId }) }
            onOpenInventory: stack.push(inventoryComponent)
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

    // 「开始搭建」统一路由: 详情页 (或未来任何入口) 调 studio.startBuild,
    // 这里接 buildRequested 进教程页 (QT-3 前为占位页)
    Connections {
        target: studio
        function onBuildRequested(modelId, modelName, currentStep, stepCount) {
            stack.push(tutorialComponent, {
                modelId: modelId,
                modelName: modelName,
                currentStep: currentStep,
                stepCount: stepCount
            })
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

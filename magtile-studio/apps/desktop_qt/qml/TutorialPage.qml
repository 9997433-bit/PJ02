import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 教程播放器 (QT-3, UI_UX_SPEC.md §6 核心屏 ★):
// 左侧 3D 视口 (TutorialViewport = QQuickFramebufferObject +
// GlSceneRenderer): 已放置片实体 / 本步新片呼吸高亮 / 未来片 ghost /
// 拖动旋转·右键平移·滚轮缩放; 右侧步骤面板: 步骤分数 + 中文说明 +
// 💡提示 + 上一步/下一步大按钮 (>= 64); 底部总进度条 + 已放置片数。
// 路由契约与占位版一致 (modelId / modelName / currentStep /
// stepCount 由 Main.qml 经 studio.buildRequested 注入); 「返回」
// 直接退 (已自动存档, 不弹确认框, §4.4), 退出时刷新模型库徽标。
//
// QT-4 接入:
//   - 🔊 朗读按钮 (页眉, §4.2) 读当前步骤说明; 4-6 岁启蒙模式切步
//     自动朗读; 切步/离开自动停旧朗读 (无叠音);
//   - 全部步骤完成 -> 短暂停留后 studio.completeBuild: 写存档完成
//     状态 + 发 buildCompleted, Main.qml 原位替换为完成庆祝页 (§6.2)。
// =============================================================
Page {
    id: page

    property string modelId: ""
    property string modelName: ""
    property int currentStep: 0
    property int stepCount: 0

    /// Main.qml 路由判定用 (完成时 replace 本页为庆祝页)
    readonly property bool isTutorialPage: true

    /// 已朗读/已停读的步骤号 (防同一步的多次状态信号重复触发)
    property int spokenStep: -1
    /// 完成链路已启动 (防 finished 状态多次信号重复触发庆祝)
    property bool completionPending: false

    signal back()
    signal home()
    signal notify(string message)

    /// 离开教程前统一收尾: 停止朗读 + 落盘进度 + 刷新模型库进度徽标
    function leave() {
        tts.stop()
        viewport.finishSession()
        studio.reload()
    }

    /// 当前步骤的朗读文本 (§4.2): 步骤说明 + 💡技巧提示
    function stepSpeechText() {
        var text = viewport.stepDescription
        if (viewport.stepTip !== "")
            text += "。小提示，" + viewport.stepTip
        return text
    }

    /// 🔊 按钮入口: 引擎缺失/开关关闭时温和提示, 不弹"失败" (P3)
    function speakCurrentStep() {
        if (!tts.available) {
            page.notify("这台设备还没有语音引擎, 先看文字说明吧")
        } else if (!tts.enabled) {
            page.notify("朗读开关是关着的, 可以在家长设置里打开")
        } else if (tts.speaking) {
            tts.stop()
        } else {
            tts.speak(page.stepSpeechText())
        }
    }

    Component.onDestruction: tts.stop()   // 离开教程即停, 无叠音 (§4.2)

    // 步骤状态桥 (QT-4): 切步朗读管理 + 完成触发庆祝
    Connections {
        target: viewport
        function onStateChanged() {
            if (viewport.sessionReady && viewport.stepNumber !== page.spokenStep) {
                page.spokenStep = viewport.stepNumber
                if (tts.autoRead && viewport.stepDescription !== "") {
                    tts.speak(page.stepSpeechText())   // 启蒙模式自动朗读 (§4.2)
                } else {
                    tts.stop()                          // 切步停旧朗读, 无叠音
                }
            }
            if (viewport.finished && !page.completionPending) {
                page.completionPending = true
                celebrateTimer.restart()
            }
        }
    }

    // 最后一片落位后短暂停留再进庆祝页 (让孩子看见成品的完成瞬间);
    // 期间按「⏮ 从头再来」/「◀ 上一步」可自然取消
    Timer {
        id: celebrateTimer
        interval: 900
        onTriggered: {
            if (!viewport.finished) {
                page.completionPending = false
                return
            }
            tts.stop()
            viewport.finishSession()             // 先落盘步骤进度 (幂等)
            studio.completeBuild(page.modelId)   // 写完成状态 -> buildCompleted -> 庆祝页
        }
    }

    background: Rectangle { color: Theme.surfaceAlt }

    // 键盘也能切步 (与 GL 版一致: 左右方向键)
    focus: true
    Keys.onRightPressed: viewport.nextStep()
    Keys.onLeftPressed: viewport.previousStep()

    // ---- 页眉: 返回 + 标题 + 回首页 (导航铁律: <= 2 步回首页 §3) ---------
    header: Item {
        height: 72

        AbstractButton {
            id: backButton
            width: 140
            height: Theme.touchTarget
            anchors.left: parent.left
            anchors.leftMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: { page.leave(); page.back() }
            scale: pressed ? 0.97 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: backButton.pressed ? Theme.primaryPressed : Theme.primary
            }
            contentItem: Text {
                text: "← 返回"
                color: "white"
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        Text {
            anchors.centerIn: parent
            text: (viewport.sessionReady ? viewport.modelName : page.modelName)
                  + (viewport.stepCount > 0
                     ? " · 第 " + viewport.stepNumber + "/" + viewport.stepCount + " 步"
                     : "")
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        // 🔊 步骤朗读 (§4.2, >= 48 触控目标); 朗读中变主色底提示
        AbstractButton {
            id: speakButton
            width: speakLabel.implicitWidth + 2 * Theme.spacing
            height: Theme.touchTarget
            anchors.right: homeButton.left
            anchors.rightMargin: Theme.spacing
            anchors.verticalCenter: parent.verticalCenter
            visible: viewport.sessionReady
            onClicked: page.speakCurrentStep()
            scale: pressed ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: tts.speaking ? Theme.primarySoft
                                    : (speakButton.pressed ? Theme.primarySoft : Theme.surface)
                border.color: tts.speaking ? Theme.primary : Theme.cardBorder
                border.width: 1
            }
            contentItem: Text {
                id: speakLabel
                text: tts.speaking ? "🔊 朗读中…" : "🔊 朗读"
                color: tts.speaking ? Theme.primary : Theme.textPrimary
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }

        AbstractButton {
            id: homeButton
            width: homeLabel.implicitWidth + 2 * Theme.spacing
            height: Theme.touchTarget
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: { page.leave(); page.home() }
            scale: pressed ? 0.96 : 1.0
            Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
            background: Rectangle {
                radius: Theme.radiusButton
                color: homeButton.pressed ? Theme.primarySoft : Theme.surface
                border.color: Theme.cardBorder
                border.width: 1
            }
            contentItem: Text {
                id: homeLabel
                text: "🏠 回首页"
                color: Theme.textPrimary
                font.pixelSize: Theme.fontBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingLarge
        anchors.topMargin: 0
        spacing: Theme.spacing

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Theme.spacingLarge

            // ---- 3D 视口 (>= 70% 宽, §6.1) --------------------------------
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: Theme.radiusCard
                color: "#E6ECF2"   // 与场景清屏色同族, 圆角边不突兀
                border.color: Theme.cardBorder
                border.width: 1

                TutorialViewport {
                    id: viewport
                    anchors.fill: parent
                    anchors.margins: 2
                    modelFile: studio.modelFilePath(page.modelId)
                    dataDir: studio.dataDirText
                    dbFile: studio.dbFileText
                    resumeStep: page.currentStep
                }

                // 操作提示 (左下角浮层, 常驻但视觉很轻)
                Rectangle {
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    anchors.margins: Theme.spacing
                    radius: Theme.radiusButton
                    color: "#CCFFFFFF"
                    width: hintLabel.implicitWidth + 2 * Theme.spacing
                    height: 40
                    visible: viewport.sessionReady
                    Text {
                        id: hintLabel
                        anchors.centerIn: parent
                        text: "🖱 拖动转圈看 · 滚轮放大 · 右键平移"
                        font.pixelSize: Theme.fontSmall
                        color: Theme.textSecondary
                    }
                }

                // 复位视角 (右下角, >= 48 触控目标)
                AbstractButton {
                    id: resetViewButton
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.margins: Theme.spacing
                    width: resetViewLabel.implicitWidth + 2 * Theme.spacing
                    height: Theme.touchTarget
                    visible: viewport.sessionReady
                    onClicked: viewport.resetView()
                    scale: pressed ? 0.96 : 1.0
                    Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                    background: Rectangle {
                        radius: Theme.radiusButton
                        color: resetViewButton.pressed ? Theme.primarySoft : Theme.surface
                        border.color: Theme.cardBorder
                        border.width: 1
                    }
                    contentItem: Text {
                        id: resetViewLabel
                        text: "🔄 回到最佳视角"
                        color: Theme.textPrimary
                        font.pixelSize: Theme.fontSmall
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                }

                // 教程未就绪的温和浮层 (P3 零挫败: 不说 "失败")
                ColumnLayout {
                    anchors.centerIn: parent
                    width: Math.min(parent.width - 2 * Theme.spacingLarge, 480)
                    spacing: Theme.spacing
                    visible: !viewport.sessionReady
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: "🧲"
                        font.pixelSize: 72
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.fillWidth: true
                        text: viewport.statusText !== ""
                              ? viewport.statusText
                              : "教程正在准备中, 稍等一下下…"
                        font.pixelSize: Theme.fontBody
                        color: Theme.textSecondary
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        lineHeight: 1.4
                    }
                    BigButton {
                        Layout.alignment: Qt.AlignHCenter
                        emoji: "🧲"
                        text: "先去挑别的模型"
                        accent: Theme.primary
                        onClicked: { page.leave(); page.back() }
                    }
                }
            }

            // ---- 步骤面板 (右侧, §6.1) ------------------------------------
            ColumnLayout {
                Layout.fillWidth: false
                Layout.preferredWidth: 360
                Layout.fillHeight: true
                spacing: Theme.spacing
                visible: viewport.sessionReady

                // 步骤分数 (大号, 图形+数字双编码)
                RowLayout {
                    spacing: Theme.spacing
                    Rectangle {
                        radius: Theme.radiusButton
                        height: 44
                        width: stepBadge.implicitWidth + 2 * Theme.spacing
                        color: Theme.primarySoft
                        Text {
                            id: stepBadge
                            anchors.centerIn: parent
                            text: viewport.stepNumber > 0
                                  ? "第 " + viewport.stepNumber + " / " + viewport.stepCount + " 步"
                                  : "准备开始"
                            font.pixelSize: Theme.fontButton
                            font.bold: true
                            color: Theme.primary
                        }
                    }
                    Text {
                        text: viewport.finished ? "✓ 全部搭完" : ""
                        font.pixelSize: Theme.fontBody
                        font.bold: true
                        color: Theme.success
                    }
                }

                // 步骤说明 (可滚动, 长文案不挤压按钮)
                Flickable {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentHeight: stepColumn.implicitHeight
                    clip: true
                    boundsBehavior: Flickable.StopAtBounds

                    ColumnLayout {
                        id: stepColumn
                        width: parent.width
                        spacing: Theme.spacing

                        Text {
                            Layout.fillWidth: true
                            text: viewport.stepDescription
                            font.pixelSize: Theme.fontButton
                            color: Theme.textPrimary
                            wrapMode: Text.WordWrap
                            lineHeight: 1.4
                        }

                        // 💡 提示行: 只放搭建技巧 (§6.3), 琥珀色不表达 "错误"
                        Rectangle {
                            Layout.fillWidth: true
                            visible: viewport.stepTip !== ""
                            radius: Theme.radiusCard
                            implicitHeight: tipLabel.implicitHeight + 2 * Theme.spacing
                            color: Theme.warningSoft
                            Text {
                                id: tipLabel
                                anchors.fill: parent
                                anchors.margins: Theme.spacing
                                text: "💡 " + viewport.stepTip
                                font.pixelSize: Theme.fontBody
                                color: Theme.textPrimary
                                wrapMode: Text.WordWrap
                                lineHeight: 1.4
                            }
                        }

                        // 🎉 完成庆祝 (完整庆祝页属 QT-4, 先给足肯定)
                        Rectangle {
                            Layout.fillWidth: true
                            visible: viewport.finished
                            radius: Theme.radiusCard
                            implicitHeight: doneColumn.implicitHeight + 2 * Theme.spacing
                            color: Theme.successSoft
                            ColumnLayout {
                                id: doneColumn
                                anchors.fill: parent
                                anchors.margins: Theme.spacing
                                spacing: 8
                                Text {
                                    Layout.alignment: Qt.AlignHCenter
                                    text: "🎉"
                                    font.pixelSize: 44
                                }
                                Text {
                                    Layout.fillWidth: true
                                    text: "搭好啦, 你真棒! 摆在桌上给家人看看吧。"
                                    font.pixelSize: Theme.fontBody
                                    font.bold: true
                                    color: Theme.success
                                    wrapMode: Text.WordWrap
                                    horizontalAlignment: Text.AlignHCenter
                                }
                            }
                        }
                    }
                }

                // ---- 导航按钮 (>= 64 高, §6.2) -----------------------------
                BigButton {
                    Layout.fillWidth: true
                    visible: !viewport.finished
                    emoji: "▶"
                    text: viewport.stepNumber > 0 ? "下一步" : "开始搭建"
                    accent: Theme.primary
                    onClicked: viewport.nextStep()
                }
                BigButton {
                    Layout.fillWidth: true
                    visible: viewport.finished
                    emoji: "🧲"
                    text: "再挑一个模型"
                    accent: Theme.success
                    onClicked: { page.leave(); page.back() }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: Theme.spacing

                    AbstractButton {
                        id: prevButton
                        Layout.fillWidth: true
                        height: Theme.touchTarget + 8
                        enabled: viewport.stepNumber > 0
                        onClicked: viewport.previousStep()
                        scale: pressed ? 0.97 : 1.0
                        Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: prevButton.pressed ? Theme.primarySoft : Theme.surface
                            border.color: Theme.cardBorder
                            border.width: 1
                            opacity: prevButton.enabled ? 1.0 : 0.45
                        }
                        contentItem: Text {
                            text: "◀ 上一步"
                            color: Theme.textPrimary
                            opacity: prevButton.enabled ? 1.0 : 0.45
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    AbstractButton {
                        id: restartButton
                        Layout.fillWidth: true
                        height: Theme.touchTarget + 8
                        enabled: viewport.stepNumber > 0
                        onClicked: {
                            viewport.restart()
                            page.notify("回到开头啦, 先转一转看看成品吧")
                        }
                        scale: pressed ? 0.97 : 1.0
                        Behavior on scale { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                        background: Rectangle {
                            radius: Theme.radiusButton
                            color: restartButton.pressed ? Theme.primarySoft : Theme.surface
                            border.color: Theme.cardBorder
                            border.width: 1
                            opacity: restartButton.enabled ? 1.0 : 0.45
                        }
                        contentItem: Text {
                            text: "⏮ 从头再来"
                            color: Theme.textPrimary
                            opacity: restartButton.enabled ? 1.0 : 0.45
                            font.pixelSize: Theme.fontBody
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
            }
        }

        // ---- 底部总进度 (§6.1: 进度条 + 已放置片数) -----------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacing
            visible: viewport.sessionReady

            Rectangle {
                Layout.fillWidth: true
                height: 14
                radius: 7
                color: Theme.primarySoft
                Rectangle {
                    width: Math.round(parent.width * viewport.progress)
                    height: parent.height
                    radius: 7
                    color: viewport.finished ? Theme.success : Theme.primary
                    Behavior on width { NumberAnimation { duration: Theme.animMs; easing.type: Easing.OutQuad } }
                }
            }
            Text {
                text: "已放好 " + viewport.tilesPlaced + " / " + viewport.tilesTotal + " 片"
                font.pixelSize: Theme.fontBody
                font.bold: true
                color: Theme.textSecondary
            }
        }
    }
}

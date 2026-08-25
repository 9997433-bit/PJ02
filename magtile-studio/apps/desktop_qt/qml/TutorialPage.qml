import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 教程页 (占位, QT-3 前身): 3D 视口 (QQuickFramebufferObject +
// magtile_render_gl) 就绪前, 先温和告知"教程马上就来", 并保留
// 与真教程一致的路由入口 (modelId / currentStep / stepCount 由
// Main.qml 经 studio.buildRequested 信号注入)。QT-3 落地时只替换
// 本页内容区, 详情页与路由契约不变 (docs/QT_UI_PLAN.md)。
// =============================================================
Page {
    id: page

    property string modelId: ""
    property string modelName: ""
    property int currentStep: 0
    property int stepCount: 0

    signal back()
    signal home()
    signal notify(string message)

    background: Rectangle { color: Theme.surfaceAlt }

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
            onClicked: page.back()
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
            text: page.modelName + (page.stepCount > 0 ? " · 共 " + page.stepCount + " 步" : "")
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }

        AbstractButton {
            id: homeButton
            width: homeLabel.implicitWidth + 2 * Theme.spacing
            height: Theme.touchTarget
            anchors.right: parent.right
            anchors.rightMargin: Theme.spacingLarge
            anchors.verticalCenter: parent.verticalCenter
            onClicked: page.home()
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

    // ---- 内容区 (QT-3 时整块替换为 3D 视口 + 步骤面板) -------------------
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - 2 * Theme.spacingLarge, 640)
        spacing: Theme.spacing

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "🚧"
            font.pixelSize: 96
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "3D 搭建教程马上就来"
            font.pixelSize: Theme.fontHero
            font.bold: true
            color: Theme.textPrimary
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            text: "一步一步的 3D 教程正在赶来的路上。"
                  + (page.currentStep > 0
                     ? "你的进度 (第 " + page.currentStep + "/" + page.stepCount + " 步) 已经存好, 一上线就能接着搭。"
                     : "等它上线后, 从这里就能开始搭『" + page.modelName + "』。")
            font.pixelSize: Theme.fontBody
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
            lineHeight: 1.4
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            text: "现在就想搭? 可以让爸爸妈妈打开电脑版:  magtile_app library --gui"
            font.pixelSize: Theme.fontSmall
            color: Theme.textSecondary
            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignHCenter
        }

        BigButton {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Theme.spacing
            emoji: "🧲"
            text: "先去挑别的模型"
            accent: Theme.success
            onClicked: page.back()
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import MagTile.Studio

// =============================================================
// 订阅页占位 (UI_UX_SPEC.md §11): 必须在家长门之后才可见 (由
// Main.qml 路由与会话守卫保证)。正式订阅页 (三卡横排 / 透明条款 /
// 恢复购买) 在 QT-5 落地, 当前只做温和的 "即将上线" 占位 ——
// 无倒计时、无催促、不索取任何信息 (P3 零挫败 / 反套路即信任)。
// =============================================================
Page {
    id: page

    signal back()

    /// Main.qml 会话守卫: 会话失效时该页自动退回首页
    readonly property bool requiresParentSession: true

    background: Rectangle { color: Theme.surfaceAlt }

    // ---- 页眉: 大返回键 + 标题 ---------------------------------------
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
            text: "订阅"
            font.pixelSize: Theme.fontTitle
            font.bold: true
            color: Theme.textPrimary
        }
    }

    // ---- 主体: 温和占位卡片 ------------------------------------------
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(page.width - 2 * Theme.spacingLarge, 560)
        height: placeholderColumn.implicitHeight + 2 * Theme.spacingLarge
        radius: Theme.radiusCard
        color: Theme.surface
        border.color: Theme.cardBorder
        border.width: 1

        ColumnLayout {
            id: placeholderColumn
            anchors.centerIn: parent
            width: parent.width - 2 * Theme.spacingLarge
            spacing: Theme.spacing

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "🌱"
                font.pixelSize: 44
            }
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "订阅功能即将上线"
                font.pixelSize: Theme.fontTitle
                font.bold: true
                color: Theme.textPrimary
            }
            Text {
                Layout.fillWidth: true
                text: "正式版将在这里提供全库订阅、恢复购买与透明的续费/退订说明。"
                font.pixelSize: Theme.fontBody
                color: Theme.textSecondary
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
            Text {
                Layout.fillWidth: true
                text: "在那之前, 无需付费也可以玩精选模型; 儿童界面永远不会出现价格信息。"
                font.pixelSize: Theme.fontSmall
                color: Theme.textSecondary
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}
